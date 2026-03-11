#!/usr/bin/env python3
"""
Audio Metrics CLI - Enhanced Version v2.0
Unified analysis with automatic speaker detection, summary generation, and rich JSON output
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import click
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import setup_logging, get_logger
from core.config import Config
from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.emotion_analyzer import EmotionAnalyzer
from modules.filler_detector import FillerDetector
from modules.speaker_diarization import SpeakerDiarization
from modules.timeline_builder import TimelineBuilder
from modules.segment_metrics import SegmentMetricsExtractor
from modules.speaker_metrics import SpeakerMetricsAggregator
from modules.timing_relation import TimingRelationAnalyzer
from modules.summary_generator import SummaryGenerator
from modules.keyword_extractor import KeywordExtractor
from exporters.enhanced_json_exporter import EnhancedJSONExporter

logger = get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--log-file", type=click.Path(), default=None, help="Log file path")
@click.pass_context
def main(ctx, verbose, log_file):
    """Audio Metrics CLI v2.0 - Enhanced audio analysis with automatic speaker detection"""
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level, log_file=log_file, json_output=False)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = Config()


@main.command("analyze")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output JSON file")
@click.option("-m", "--model", "stt_model", default="base", help="Whisper model")
@click.option("--no-emotion", is_flag=True, help="Skip emotion analysis")
@click.option("--diarization", type=click.Choice(["auto", "on", "off"]), default="auto", help="Speaker diarization mode")
@click.option("--min-speakers", type=int, default=1, help="Minimum speakers (hint)")
@click.option("--max-speakers", type=int, default=10, help="Maximum speakers (hint)")
@click.option("--summary", type=click.Choice(["auto", "llm", "cloud", "heuristic", "none"]), default="auto", help="Summary generation method")
@click.option("--show-progress", is_flag=True, help="Show progress steps")
@click.pass_context
def analyze(
    ctx,
    audio_file,
    output_file,
    stt_model,
    no_emotion,
    diarization,
    min_speakers,
    max_speakers,
    summary,
    show_progress
):
    """
    Analyze audio file with automatic speaker detection and rich JSON output.
    
    Automatically detects single vs multi-speaker, generates summary, extracts keywords,
    and outputs enriched JSON with segments, speakers, topics, and action items.
    
    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    """
    verbose = ctx.obj.get("verbose", False)
    config = ctx.obj.get("config", Config())
    
    if stt_model:
        config.models.speech_to_text.model = stt_model
    if no_emotion:
        config.features.enable_emotion = False
    
    click.echo("=" * 60)
    click.echo("Audio Metrics CLI v2.0 - Enhanced Analysis")
    click.echo("=" * 60)
    click.echo(f"Input: {Path(audio_file).name}")
    click.echo(f"Diarization: {diarization}")
    click.echo(f"Summary: {summary}")
    click.echo("")
    
    start_time = time.time()
    
    try:
        # STEP 1: Load audio
        if show_progress:
            click.echo("[1/9] Loading audio...")
        loader = AudioLoader(audio_file)
        loader.load()
        audio_info = loader.get_audio_info()
        audio_data = loader.get_audio_data()
        if show_progress:
            click.echo(f"  [OK] Duration: {audio_info['duration_seconds']:.2f}s")
        
        # STEP 2: VAD analysis
        if show_progress:
            click.echo("[2/9] Voice activity detection...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(audio_data)
        if show_progress:
            click.echo(f"  [OK] Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        
        # STEP 3: Speech-to-text
        if show_progress:
            click.echo("[3/9] Speech-to-text...")
        stt = SpeechToText(model_name=config.models.speech_to_text.model)
        transcript = stt.transcribe(audio_file)
        if show_progress:
            click.echo(f"  [OK] Language: {transcript.get('language', 'unknown')}")
        
        # STEP 4: Prosody analysis
        if show_progress:
            click.echo("[4/9] Prosody analysis...")
        prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
        prosody_metrics = prosody.analyze(audio_data)
        
        # STEP 5: Emotion analysis
        emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
        if config.features.enable_emotion:
            if show_progress:
                click.echo("[5/9] Emotion analysis...")
            try:
                emotion = EmotionAnalyzer()
                emotion_metrics = emotion.analyze(audio_file)
            except Exception as e:
                logger.warning(f"Emotion analysis failed: {e}")
        
        # STEP 6: Filler detection
        if show_progress:
            click.echo("[6/9] Filler word detection...")
        filler = FillerDetector(language=transcript.get('language', 'en'))
        filler_metrics = filler.detect(transcript.get('text', ''))
        
        # STEP 7: Speaker diarization (auto/on/off)
        diarization_result = None
        segments = []
        
        if diarization != "off":
            if show_progress:
                click.echo("[7/9] Speaker diarization...")
            try:
                diarizer = SpeakerDiarization()
                diarization_result = diarizer.diarize(
                    audio_file,
                    min_speakers=min_speakers if diarization == "on" else None,
                    max_speakers=max_speakers if diarization == "on" else None
                )
                
                # Build segments with timestamps
                timeline_builder = TimelineBuilder()
                conversation_timeline = timeline_builder.build(
                    diarization_segments=diarization_result.get('segments', []),
                    audio_duration=audio_info['duration_seconds']
                )
                
                # Extract segment-level metrics
                segment_extractor = SegmentMetricsExtractor(sample_rate=audio_info['sample_rate'])
                segment_metrics_list = segment_extractor.extract(audio_data, diarization_result.get('segments', []))
                
                # Build enriched segments
                segments = _build_enriched_segments(
                    diarization_result.get('segments', []),
                    transcript.get('text', ''),
                    segment_metrics_list
                )
                
                if show_progress:
                    click.echo(f"  [OK] Detected {diarization_result['num_speakers']} speakers")
                    
            except Exception as e:
                logger.warning(f"Diarization failed: {e}")
                if diarization == "on":
                    click.echo(f"  [WARN] Diarization failed (required): {e}")
                else:
                    click.echo(f"  [SKIP] Diarization skipped (auto): {e}")
        
        # STEP 8: Generate summary and keywords
        if show_progress:
            click.echo("[8/9] Generating summary and keywords...")
        
        # Summary generation
        summary_gen = SummaryGenerator(method=summary)
        summary_result = summary_gen.generate(transcript.get('text', ''), {
            "duration": audio_info['duration_seconds'],
            "speech_ratio": vad_analysis.get('speech_ratio', 0)
        })
        
        # Keyword extraction
        keyword_ext = KeywordExtractor(language=transcript.get('language', 'zh'))
        keywords_result = keyword_ext.extract(transcript.get('text', ''), segments)
        
        if show_progress:
            click.echo(f"  [OK] Summary: {summary_result.get('method', 'none')}")
            click.echo(f"  [OK] Topics: {len(keywords_result.get('topics', []))}")
        
        # STEP 9: Export enhanced JSON
        if show_progress:
            click.echo("[9/9] Exporting JSON...")
        
        if output_file is None:
            audio_path = Path(audio_file)
            output_dir = Path("outputs") / audio_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "analysis_result.json"
        
        exporter = EnhancedJSONExporter()
        output_path = exporter.export(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript,
            prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics,
            filler_metrics=filler_metrics,
            diarization_result=diarization_result,
            segments=segments,
            summary=summary_result,
            keywords=keywords_result,
            output_path=str(output_file)
        )
        
        # Summary output
        processing_time = time.time() - start_time
        click.echo("")
        click.echo("=" * 60)
        click.echo("Analysis Complete")
        click.echo("=" * 60)
        click.echo(f"Duration: {audio_info['duration_seconds']:.1f}s")
        click.echo(f"Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        click.echo(f"Speakers: {diarization_result['num_speakers'] if diarization_result else 'N/A'}")
        click.echo(f"Words: {len(transcript.get('text', ''))} chars")
        click.echo(f"Summary: {summary_result.get('one_liner', 'N/A')[:50]}...")
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


def _build_enriched_segments(
    diarization_segments: List[Dict],
    full_transcript: str,
    segment_metrics: List[Dict]
) -> List[Dict]:
    """Build enriched segments with text, speaker, and acoustic features"""
    
    enriched = []
    transcript_chars = list(full_transcript)
    char_index = 0
    
    for i, seg in enumerate(diarization_segments[:50]):
        seg_duration = seg.get('duration', 1.0)
        estimated_chars = max(10, int(seg_duration * 5))
        
        start_idx = char_index
        end_idx = min(char_index + estimated_chars, len(transcript_chars))
        seg_text = ''.join(transcript_chars[start_idx:end_idx])
        char_index = end_idx
        
        acoustic = segment_metrics[i] if i < len(segment_metrics) else {}
        
        enriched.append({
            "start": round(seg.get('start', 0), 2),
            "end": round(seg.get('end', 0), 2),
            "speaker": seg.get('speaker', 'SPEAKER_00'),
            "text": seg_text,
            "emotion": "neutral",
            "pitch": acoustic.get('pitch_mean_hz', 0),
            "energy": acoustic.get('energy_mean', 0)
        })
    
    return enriched


if __name__ == "__main__":
    main()
