#!/usr/bin/env python3
"""
Audio Metrics CLI - Cross-platform audio analysis toolkit

Usage:
    audio-metrics analyze audio.wav --output result.json
    audio-metrics analyze --batch ./recordings/ --format csv
    audio-metrics transcribe audio.mp3 -o transcript.txt
    audio-metrics compare v1.wav v2.wav
    audio-metrics serve
"""

import asyncio
import glob
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List

import click
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import setup_logging, get_logger
from core.config import load_config, Config
from core.model_manager import get_model_manager
from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.emotion_analyzer import EmotionAnalyzer
from modules.filler_detector import FillerDetector
from modules.metrics_builder import MetricsBuilder
from modules.json_exporter import JSONExporter
from modules.speaker_diarization import SpeakerDiarization
from modules.timeline_builder import TimelineBuilder
from modules.segment_metrics import SegmentMetricsExtractor
from modules.speaker_metrics import SpeakerMetricsAggregator
from modules.timing_relation import TimingRelationAnalyzer
from exporters.csv_exporter import BatchCSVExporter
from exporters.html_exporter import BatchHTMLExporter

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.2.0")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--log-file", type=click.Path(), default=None, help="Log file path")
@click.pass_context
def main(ctx, verbose, log_file):
    """Audio Metrics CLI - Cross-platform audio analysis toolkit"""
    # Setup logging
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level, log_file=log_file, json_output=False)

    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = Config()


def _analyze_single_file(
    audio_file: str,
    config: Config,
    verbose: bool = False
) -> dict:
    """
    Analyze a single audio file.

    Args:
        audio_file: Path to audio file
        config: Configuration
        verbose: Verbose output

    Returns:
        Analysis metrics
    """
    # STEP 1: Load audio
    if verbose:
        logger.info("Loading audio", file=audio_file)

    loader = AudioLoader(audio_file)
    loader.load()
    loader.validate(max_duration=config.features.skip_if_too_long)
    audio_info = loader.get_audio_info()

    # STEP 2: VAD analysis
    if verbose:
        logger.info("Running VAD analysis")

    vad = VADAnalyzer()
    vad_analysis = vad.analyze(loader.get_audio_data())

    # STEP 3: Speech to text
    if verbose:
        logger.info("Running speech-to-text")

    stt = SpeechToText(model_name=config.models.speech_to_text.model)
    transcript = stt.transcribe(audio_file)

    # STEP 4: Prosody analysis
    if verbose:
        logger.info("Running prosody analysis")

    prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
    prosody_metrics = prosody.analyze(loader.get_audio_data())
    speech_rate = prosody.calculate_speech_rate(
        transcript['text'],
        audio_info['duration_seconds']
    )
    prosody_metrics.update(speech_rate)

    # STEP 5: Emotion (optional)
    if config.features.enable_emotion:
        if verbose:
            logger.info("Running emotion analysis")

        try:
            emotion = EmotionAnalyzer()
            emotion_metrics = emotion.analyze(audio_file)
        except Exception as e:
            logger.warning("Emotion analysis failed, using default", error=str(e))
            emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
    else:
        emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}

    # STEP 6: Filler detection
    if verbose:
        logger.info("Running filler detection")

    filler = FillerDetector(language=transcript.get('language', 'en'))
    filler_metrics = filler.detect(transcript['text'])

    # STEP 7: Build metrics
    builder = MetricsBuilder()
    metrics = builder.build(
        audio_info=audio_info,
        vad_analysis=vad_analysis,
        transcript_result=transcript,
        prosody_metrics=prosody_metrics,
        emotion_metrics=emotion_metrics,
        filler_metrics=filler_metrics
    )

    return metrics


@main.command("analyze")
@click.argument("audio_file", type=click.Path(exists=True), required=False)
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output file path")
@click.option("-c", "--config", "config_file", type=click.Path(exists=True), default=None, help="Configuration file")
@click.option("-m", "--model", "stt_model", default=None, help="Whisper model (tiny/base/small/medium/large)")
@click.option("--no-emotion", is_flag=True, help="Skip emotion analysis")
@click.option("--show-progress", is_flag=True, help="Show progress bars")
@click.option("-f", "--format", "output_format", type=click.Choice(["json", "csv", "html"]), default="json", help="Output format")
@click.option("--parallel", is_flag=True, help="Use parallel processing")
@click.option("--batch", "batch_dir", type=click.Path(exists=True), default=None, help="Process all audio files in directory")
@click.option("--glob", "glob_pattern", type=str, default=None, help="Glob pattern for batch processing")
@click.option("-j", "--workers", type=int, default=4, help="Number of parallel workers")
@click.pass_context
def analyze(
    ctx,
    audio_file,
    output_file,
    config_file,
    stt_model,
    no_emotion,
    show_progress,
    output_format,
    parallel,
    batch_dir,
    glob_pattern,
    workers
):
    """
    Analyze audio file(s) and extract objective metrics.

    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    """
    verbose = ctx.obj.get("verbose", False)

    # Load config
    config = load_config(Path(config_file)) if config_file else Config()

    # Override config with CLI options
    if stt_model:
        config.models.speech_to_text.model = stt_model
    if no_emotion:
        config.features.enable_emotion = False
    if parallel:
        config.enable_parallel = True

    click.echo("=" * 60)
    click.echo("Audio Metrics CLI v0.2.0")
    click.echo("=" * 60)

    # Determine files to process
    files_to_process = []

    if batch_dir:
        # Batch processing
        audio_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
        for ext in audio_extensions:
            files_to_process.extend(Path(batch_dir).glob(f"*{ext}"))
        files_to_process = [str(f) for f in files_to_process]
    elif glob_pattern:
        # Glob pattern
        files_to_process = glob.glob(glob_pattern)
    elif audio_file:
        # Single file
        files_to_process = [audio_file]
    else:
        click.echo("Error: Please specify audio_file, --batch, or --glob", err=True)
        sys.exit(1)

    if not files_to_process:
        click.echo("Error: No audio files found", err=True)
        sys.exit(1)

    click.echo(f"Files to process: {len(files_to_process)}")
    click.echo(f"Model: {config.models.speech_to_text.model}")
    click.echo(f"Parallel: {parallel}")
    click.echo("")

    try:
        results = []

        if parallel and len(files_to_process) > 1:
            # Parallel processing
            logger.info("Starting parallel processing", num_files=len(files_to_process), workers=workers)

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                for f in files_to_process:
                    future = executor.submit(_analyze_single_file, f, config, verbose)
                    futures.append((f, future))

                for f, future in tqdm(futures, disable=not show_progress, desc="Processing"):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error("File processing failed", file=f, error=str(e))
                        if verbose:
                            click.echo(f"  [ERROR] {f}: {e}")
        else:
            # Sequential processing
            for f in tqdm(files_to_process, disable=not show_progress, desc="Processing"):
                try:
                    result = _analyze_single_file(f, config, verbose)
                    results.append(result)
                except Exception as e:
                    logger.error("File processing failed", file=f, error=str(e))
                    if verbose:
                        click.echo(f"  [ERROR] {f}: {e}")

        if not results:
            click.echo("Error: No files were successfully processed", err=True)
            sys.exit(1)

        # Export results
        if len(results) == 1:
            # Single file - export normally
            if output_file is None:
                audio_path = Path(files_to_process[0])
                output_dir = Path("outputs") / audio_path.stem
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"analysis_result.{output_format}"

            if output_format == "json":
                exporter = JSONExporter()
            elif output_format == "csv":
                exporter = BatchCSVExporter()
            else:
                from exporters.html_exporter import HTMLExporter
                exporter = HTMLExporter()

            path = exporter.export(results[0], str(output_file))
            click.echo(f"[OK] Exported: {path}")
        else:
            # Batch - export combined
            if output_file is None:
                output_dir = Path("outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = output_dir / f"batch_results_{timestamp}.{output_format}"

            if output_format == "csv":
                exporter = BatchCSVExporter()
                path = exporter.export_batch(results, str(output_file))
            elif output_format == "html":
                exporter = BatchHTMLExporter()
                path = exporter.export_batch(results, str(output_file))
            else:
                # JSON - save as array
                output_file = str(output_file).replace(".json", "_batch.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                path = output_file

            click.echo(f"[OK] Batch exported: {path}")
            click.echo(f"Successfully processed: {len(results)}/{len(files_to_process)} files")

        # Summary
        click.echo("")
        click.echo("=" * 60)
        click.echo("Summary")
        click.echo("=" * 60)

        if len(results) == 1:
            r = results[0]
            click.echo(
                f"Duration: {r['audio_info']['duration_seconds']:.1f}s | "
                f"Speed: {r['speech_metrics']['words_per_minute']:.1f} WPM | "
                f"Speech: {r['vad_analysis']['speech_ratio']:.1%} | "
                f"Fillers: {r['filler_metrics']['fillers_per_100_words']:.1f}/100w"
            )
        else:
            # Aggregate stats
            total_duration = sum(r['audio_info']['duration_seconds'] for r in results)
            avg_wpm = sum(r['speech_metrics']['words_per_minute'] for r in results) / len(results)
            avg_speech = sum(r['vad_analysis']['speech_ratio'] for r in results) / len(results)

            click.echo(f"Total files: {len(results)}")
            click.echo(f"Total duration: {total_duration:.1f}s")
            click.echo(f"Avg WPM: {avg_wpm:.1f}")
            click.echo(f"Avg speech ratio: {avg_speech:.1%}")

        click.echo("")
        click.echo("[OK] Analysis complete!")
        click.echo("")

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command("analyze-multi")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output JSON file")
@click.option("--num-speakers", type=int, default=None, help="Number of speakers (if known)")
@click.option("--min-speakers", type=int, default=None, help="Minimum number of speakers")
@click.option("--max-speakers", type=int, default=None, help="Maximum number of speakers")
@click.option("--show-progress", is_flag=True, help="Show progress steps")
@click.pass_context
def analyze_multi(
    ctx,
    audio_file,
    output_file,
    num_speakers,
    min_speakers,
    max_speakers,
    show_progress
):
    """
    Analyze multi-speaker conversation and extract dialogue timeline.
    
    Performs speaker diarization, builds conversation timeline, and extracts
    acoustic metrics for each speaker. Outputs structured JSON with:
    
    - audio_info: Audio metadata
    - conversation_timeline: Chronological sequence of speech segments
    - speaker_profiles: Per-speaker statistics and acoustic features
    - conversation_metrics: Overall conversation dynamics
    - global_acoustic_metrics: Aggregate acoustic features
    - processing_meta: Processing information
    
    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    """
    verbose = ctx.obj.get("verbose", False)
    
    click.echo("=" * 60)
    click.echo("Audio Metrics CLI - Multi-Speaker Analysis v0.3.0")
    click.echo("=" * 60)
    click.echo(f"Input: {Path(audio_file).name}")
    click.echo("")
    
    start_time = time.time()
    
    try:
        # STEP 1: Loading audio
        if show_progress:
            click.echo("STEP 1 Loading audio...")
        loader = AudioLoader(audio_file)
        loader.load()
        audio_info = loader.get_audio_info()
        audio_data = loader.get_audio_data()
        if show_progress:
            click.echo(f"  Duration: {audio_info['duration_seconds']:.2f}s")
            click.echo(f"  Sample rate: {audio_info['sample_rate']} Hz")
        
        # STEP 2: Extracting audio metadata
        if show_progress:
            click.echo("STEP 2 Extracting audio metadata...")
        # Already done in loader.get_audio_info()
        
        # STEP 3: Voice activity detection
        if show_progress:
            click.echo("STEP 3 Voice activity detection...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(audio_data, audio_info['sample_rate'])
        if show_progress:
            click.echo(f"  Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        
        # STEP 4: Speaker diarization
        if show_progress:
            click.echo("STEP 4 Speaker diarization...")
        diarizer = SpeakerDiarization()
        diarization_result = diarizer.diarize(
            audio_file,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        if show_progress:
            click.echo(f"  Number of speakers: {diarization_result['num_speakers']}")
        
        # STEP 5: Building conversation timeline
        if show_progress:
            click.echo("STEP 5 Building conversation timeline...")
        timeline_builder = TimelineBuilder()
        conversation_timeline = timeline_builder.build(
            diarization_segments=diarization_result['segments'],
            vad_segments=vad_analysis.get('speech_segments', []),
            audio_duration=audio_info['duration_seconds']
        )
        timeline_stats = timeline_builder.get_statistics()
        if show_progress:
            click.echo(f"  Timeline segments: {len(conversation_timeline)}")
        
        # STEP 6: Extracting segment acoustic metrics
        if show_progress:
            click.echo("STEP 6 Extracting segment acoustic metrics...")
        segment_extractor = SegmentMetricsExtractor(sample_rate=audio_info['sample_rate'])
        segment_acoustic_metrics = segment_extractor.extract(
            audio_data,
            diarization_result['segments']
        )
        if show_progress:
            click.echo(f"  Segments analyzed: {len(segment_acoustic_metrics)}")
        
        # STEP 7: Computing timing relations
        if show_progress:
            click.echo("STEP 7 Computing timing relations...")
        timing_analyzer = TimingRelationAnalyzer()
        timing_metrics = timing_analyzer.analyze(conversation_timeline)
        if show_progress:
            flow = timing_metrics.get('conversational_flow', {})
            click.echo(f"  Fluency score: {flow.get('fluency_score', 0):.3f}")
        
        # STEP 8: Aggregating speaker metrics
        if show_progress:
            click.echo("STEP 8 Aggregating speaker metrics...")
        speaker_aggregator = SpeakerMetricsAggregator()
        speaker_profiles = speaker_aggregator.aggregate(
            conversation_timeline,
            segment_acoustic_metrics
        )
        speaker_profiles = speaker_aggregator.compute_conversation_roles(speaker_profiles)
        if show_progress:
            click.echo(f"  Speaker profiles: {len(speaker_profiles)}")
        
        # Compute global acoustic metrics
        global_acoustic_metrics = _compute_global_acoustic_metrics(segment_acoustic_metrics)
        
        # Build conversation metrics
        conversation_metrics = {
            "num_speakers": diarization_result['num_speakers'],
            "total_turns": timeline_stats.get('speech_segments', 0) + timeline_stats.get('overlap_segments', 0),
            "speaker_changes": timing_metrics.get('turn_taking', {}).get('speaker_changes', 0),
            "overlap_ratio": timing_metrics.get('overlap_statistics', {}).get('overlap_ratio', 0),
            "mean_response_latency": timing_metrics.get('response_latency', {}).get('mean_response_latency', 0),
            "fluency_score": timing_metrics.get('conversational_flow', {}).get('fluency_score', 0),
            "engagement_score": timing_metrics.get('conversational_flow', {}).get('engagement_score', 0),
            "balance_score": timing_metrics.get('conversational_flow', {}).get('balance_score', 0)
        }
        
        # Processing metadata
        processing_time = time.time() - start_time
        processing_meta = {
            "version": "0.3.0",
            "analyzer": "audio-metrics-multi-speaker",
            "timestamp": datetime.now().isoformat(),
            "processing_time_seconds": round(processing_time, 2),
            "model": "pyannote/speaker-diarization-3.1"
        }
        
        # STEP 9: Exporting JSON
        if show_progress:
            click.echo("STEP 9 Exporting JSON...")
        
        if output_file is None:
            audio_path = Path(audio_file)
            output_dir = Path("outputs") / audio_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "multi_speaker_analysis.json"
        
        exporter = JSONExporter()
        output_path = exporter.export_multi_speaker(
            audio_info=audio_info,
            conversation_timeline=conversation_timeline,
            speaker_profiles=speaker_profiles,
            conversation_metrics=conversation_metrics,
            global_acoustic_metrics=global_acoustic_metrics,
            processing_meta=processing_meta,
            output_path=str(output_file)
        )
        
        # Summary
        click.echo("")
        click.echo("=" * 60)
        click.echo("Analysis Complete")
        click.echo("=" * 60)
        click.echo(f"Duration: {audio_info['duration_seconds']:.1f}s")
        click.echo(f"Speakers: {conversation_metrics['num_speakers']}")
        click.echo(f"Total turns: {conversation_metrics['total_turns']}")
        click.echo(f"Fluency: {conversation_metrics['fluency_score']:.3f}")
        click.echo(f"Engagement: {conversation_metrics['engagement_score']:.3f}")
        click.echo(f"Balance: {conversation_metrics['balance_score']:.3f}")
        click.echo(f"Processing time: {processing_time:.2f}s")
        click.echo("")
        click.echo(f"[OK] Exported: {output_path}")
        click.echo("")
        
    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _compute_global_acoustic_metrics(segment_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute global acoustic metrics from segment metrics."""
    import numpy as np
    
    if not segment_metrics:
        return {
            "pitch_mean_hz": 0,
            "pitch_std_hz": 0,
            "pitch_min_hz": 0,
            "pitch_max_hz": 0,
            "energy_mean": 0,
            "energy_cv": 0,
            "spectral_centroid_mean": 0
        }
    
    pitch_values = [m.get("pitch_mean_hz", 0) for m in segment_metrics if m.get("pitch_mean_hz", 0) > 0]
    energy_values = [m.get("energy_mean", 0) for m in segment_metrics]
    spectral_values = [m.get("spectral_centroid_mean", 0) for m in segment_metrics]
    
    return {
        "pitch_mean_hz": round(np.mean(pitch_values), 2) if pitch_values else 0,
        "pitch_std_hz": round(np.std(pitch_values), 2) if pitch_values else 0,
        "pitch_min_hz": round(min(pitch_values), 2) if pitch_values else 0,
        "pitch_max_hz": round(max(pitch_values), 2) if pitch_values else 0,
        "energy_mean": round(np.mean(energy_values), 6) if energy_values else 0,
        "energy_cv": round(np.std(energy_values) / np.mean(energy_values), 3) if np.mean(energy_values) > 0 else 0,
        "spectral_centroid_mean": round(np.mean(spectral_values), 2) if spectral_values else 0
    }


@main.command("voice-acoustic")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output JSON file")
@click.option("--show-progress", is_flag=True, help="Show progress")
@click.pass_context
def voice_acoustic(ctx, audio_file, output_file, show_progress):
    """
    Voice Acoustic Analyzer - Extract objective acoustic features.
    
    Analyzes audio and outputs structured JSON with:
    - Audio basic metrics
    - VAD (Voice Activity Detection)
    - Prosody features
    - Pitch features
    - Energy features
    - Stability features
    - Emotion (acoustic only)
    - Gender inference
    - Voice range classification
    
    No semantic analysis. No scoring. No interpretation.
    
    AUDIO_FILE: Path to audio file
    """
    verbose = ctx.obj.get("verbose", False)
    
    click.echo("=" * 60)
    click.echo("Voice Acoustic Analyzer v0.3.0")
    click.echo("=" * 60)
    click.echo(f"Input: {Path(audio_file).name}")
    click.echo("")
    
    try:
        # STEP 1: Load audio
        click.echo("[1/8] Loading audio...")
        loader = AudioLoader(audio_file)
        loader.load()
        audio_info = loader.get_audio_info()
        click.echo(f"  Duration: {audio_info['duration_seconds']:.2f}s")
        click.echo(f"  Sample rate: {audio_info['sample_rate']} Hz")
        click.echo(f"  File size: {audio_info['file_size_mb']:.2f} MB")
        
        # STEP 2: VAD analysis
        click.echo("[2/8] Voice Activity Detection...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(loader.get_audio_data(), audio_info['sample_rate'])
        click.echo(f"  Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        click.echo(f"  Pause count: {vad_analysis['pause_count']}")
        
        # STEP 3: Prosody analysis
        click.echo("[3/8] Prosody features...")
        prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
        prosody_metrics = prosody.analyze(loader.get_audio_data())
        click.echo(f"  Pitch mean: {prosody_metrics['pitch_mean_hz']:.1f} Hz")
        
        # STEP 4: Pitch features
        click.echo("[4/8] Pitch features...")
        pitch_features = {
            "pitch_mean_hz": prosody_metrics['pitch_mean_hz'],
            "pitch_std_hz": prosody_metrics.get('pitch_std_hz', 0),
            "pitch_min_hz": prosody_metrics.get('pitch_min_hz', 0),
            "pitch_max_hz": prosody_metrics.get('pitch_max_hz', 0),
            "pitch_median_hz": prosody_metrics.get('pitch_median_hz', 0)
        }
        click.echo(f"  Range: {pitch_features['pitch_min_hz']:.1f} - {pitch_features['pitch_max_hz']:.1f} Hz")
        
        # STEP 5: Energy features
        click.echo("[5/8] Energy features...")
        energy_features = {
            "energy_mean": prosody_metrics.get('energy_mean', 0),
            "energy_std": prosody_metrics.get('energy_std', 0),
            "energy_cv": prosody_metrics.get('energy_cv', 0)
        }
        click.echo(f"  Energy CV: {energy_features['energy_cv']:.3f}")
        
        # STEP 6: Stability features
        click.echo("[6/8] Stability features...")
        stability_features = {
            "jitter": 0,
            "shimmer": 0,
            "hnr_db": 0,
            "note": "parselmouth optional"
        }
        click.echo(f"  (parselmouth optional)")
        
        # STEP 7: Emotion (acoustic only)
        click.echo("[7/8] Emotion (acoustic)...")
        try:
            emotion = EmotionAnalyzer()
            emotion_features = emotion.analyze(audio_file)
        except Exception as e:
            emotion_features = {"dominant_emotion": "neutral", "confidence": 0.5}
        click.echo(f"  Dominant: {emotion_features['dominant_emotion']}")
        
        # STEP 8: Gender inference & voice range
        click.echo("[8/8] Gender inference & voice range...")
        pitch_mean = pitch_features['pitch_mean_hz']
        if pitch_mean > 250:
            gender = "female"
            confidence = min(0.95, 0.5 + (pitch_mean - 250) / 100)
        elif pitch_mean < 150:
            gender = "male"
            confidence = min(0.95, 0.5 + (150 - pitch_mean) / 50)
        else:
            gender = "female" if pitch_mean > 200 else "male"
            confidence = 0.6
        
        # Voice range
        if gender == "female":
            if pitch_mean > 246:
                voice_range = "soprano"
            elif pitch_mean > 196:
                voice_range = "mezzo_soprano"
            else:
                voice_range = "alto"
        else:
            if pitch_mean > 130:
                voice_range = "tenor"
            elif pitch_mean > 98:
                voice_range = "baritone"
            else:
                voice_range = "bass"
        
        click.echo(f"  Gender: {gender} ({confidence:.0%})")
        click.echo(f"  Range: {voice_range}")
        
        # Build result
        result = {
            "version": "0.3.0",
            "analyzer": "voice-acoustic-analyzer",
            "type": "acoustic_features",
            "audio_info": audio_info,
            "vad": vad_analysis,
            "prosody": prosody_metrics,
            "pitch": pitch_features,
            "energy": energy_features,
            "stability": stability_features,
            "emotion": emotion_features,
            "gender_inference": {
                "gender": gender,
                "confidence": round(confidence, 3),
                "method": "pitch_threshold"
            },
            "voice_range": {
                "range": voice_range,
                "gender": gender,
                "pitch_mean_hz": pitch_mean
            }
        }
        
        # Export
        if output_file is None:
            output_file = "voice_acoustic_result.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        click.echo("")
        click.echo("=" * 60)
        click.echo(f"[OK] Exported: {output_file}")
        click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="Output transcript file")
@click.option("-m", "--model", "stt_model", default="base", help="Whisper model")
@click.option("--language", default=None, help="Language code")
def transcribe(audio_file, output, stt_model, language):
    """
    Transcribe audio to text only.

    AUDIO_FILE: Path to audio file
    """
    click.echo(f"Transcribing: {audio_file}")
    click.echo(f"Model: {stt_model}")
    click.echo("")

    try:
        stt = SpeechToText(model_name=stt_model)
        result = stt.transcribe(audio_file, language=language)

        if output:
            output_path = stt.save_transcript(audio_file, output)
            click.echo(f"Transcript saved: {output_path}")
        else:
            click.echo("Transcript:")
            click.echo("-" * 60)
            click.echo(result['text'])
            click.echo("-" * 60)

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("audio_file1", type=click.Path(exists=True))
@click.argument("audio_file2", type=click.Path(exists=True))
@click.option("--format", "output_format", default="text", help="Output format (text/json/markdown)")
def compare(audio_file1, audio_file2, output_format):
    """
    Compare two audio files.

    AUDIO_FILE1: First audio file
    AUDIO_FILE2: Second audio file
    """
    click.echo("Comparing two audio files...")
    click.echo("")

    try:
        files = [audio_file1, audio_file2]
        results = []

        for audio_file in files:
            click.echo(f"Analyzing: {Path(audio_file).name}")

            loader = AudioLoader(audio_file)
            loader.load()

            stt = SpeechToText(model_name='base')
            transcript = stt.transcribe(audio_file)

            prosody = ProsodyAnalyzer(sample_rate=loader.get_audio_info()['sample_rate'])
            prosody_metrics = prosody.analyze(loader.get_audio_data())
            speech_rate = prosody.calculate_speech_rate(
                transcript['text'],
                loader.get_audio_info()['duration_seconds']
            )
            prosody_metrics.update(speech_rate)

            filler = FillerDetector()
            filler_metrics = filler.detect(transcript['text'])

            results.append({
                'file': Path(audio_file).name,
                'duration': loader.get_audio_info()['duration_seconds'],
                'wpm': prosody_metrics['words_per_minute'],
                'fillers_per_100w': filler_metrics['fillers_per_100_words'],
                'pitch_mean': prosody_metrics['pitch_mean_hz']
            })

            click.echo("  [OK]")
            click.echo("")

        # Display comparison
        click.echo("=" * 60)
        click.echo("Comparison Results")
        click.echo("=" * 60)
        click.echo(f"{'Metric':<25} {results[0]['file']:<15} {results[1]['file']:<15}")
        click.echo("-" * 60)
        click.echo(f"{'Duration (s)':<25} {results[0]['duration']:<15.1f} {results[1]['duration']:<15.1f}")
        click.echo(f"{'Speaking Rate (WPM)':<25} {results[0]['wpm']:<15.1f} {results[1]['wpm']:<15.1f}")
        click.echo(f"{'Fillers/100w':<25} {results[0]['fillers_per_100w']:<15.1f} {results[1]['fillers_per_100w']:<15.1f}")
        click.echo(f"{'Pitch Mean (Hz)':<25} {results[0]['pitch_mean']:<15.1f} {results[1]['pitch_mean']:<15.1f}")
        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("-p", "--port", type=int, default=8000, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host, port, reload):
    """
    Start the API server.
    """
    click.echo(f"Starting API server on {host}:{port}")
    click.echo("Press Ctrl+C to stop")

    try:
        from audio_metrics.api.main import run_server
        run_server(host=host, port=port, reload=reload)
    except ImportError as e:
        click.echo(f"Error: API dependencies not installed", err=True)
        click.echo("Install with: pip install audio-metrics-cli[api]", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
