#!/usr/bin/env python3
"""
Audio Metrics CLI - Cross-platform audio analysis toolkit

Usage:
    audio-metrics analyze audio.wav --output result.json
    audio-metrics transcribe audio.mp3 -o transcript.txt
    audio-metrics compare v1.wav v2.wav
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import click
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.emotion_analyzer import EmotionAnalyzer
from modules.filler_detector import FillerDetector
from modules.metrics_builder import MetricsBuilder
from modules.json_exporter import JSONExporter


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Audio Metrics CLI - Cross-platform audio analysis toolkit
    
    Extract objective speech metrics from audio files.
    Output structured JSON for further analysis.
    """
    pass


@main.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output JSON file path")
@click.option("-c", "--config", "config_file", type=click.Path(exists=True), default=None, help="Configuration file")
@click.option("-m", "--model", "stt_model", default="base", help="Whisper model (tiny/base/small/medium/large)")
@click.option("--no-emotion", is_flag=True, help="Skip emotion analysis")
@click.option("--show-progress", is_flag=True, help="Show progress bars")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def analyze(audio_file, output_file, config_file, stt_model, no_emotion, show_progress, verbose):
    """
    Analyze audio file and extract objective metrics.
    
    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    """
    use_tqdm = show_progress or verbose
    
    click.echo("=" * 60)
    click.echo("Audio Metrics CLI v0.1.0")
    click.echo("=" * 60)
    click.echo(f"Input: {audio_file}")
    click.echo(f"Model: {stt_model}")
    click.echo("")
    
    try:
        # STEP 1: Load audio
        click.echo("[STEP 1/7] Loading audio...")
        loader = AudioLoader(audio_file)
        loader.load()
        loader.validate(max_duration=3600)
        audio_info = loader.get_audio_info()
        
        if verbose:
            click.echo(f"  Duration: {audio_info['duration_seconds']:.2f}s")
            click.echo(f"  Sample rate: {audio_info['sample_rate']} Hz")
            click.echo(f"  File size: {audio_info['file_size_mb']:.2f} MB")
        click.echo("  [OK] Audio loaded")
        click.echo("")
        
        # STEP 2: VAD analysis
        click.echo("[STEP 2/7] Voice activity detection...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(loader.get_audio_data())
        
        if verbose:
            click.echo(f"  Speech ratio: {vad_analysis['speech_ratio']:.1%}")
            click.echo(f"  Pause count: {vad_analysis['pause_count']}")
        click.echo("  [OK] VAD complete")
        click.echo("")
        
        # STEP 3: Speech to text
        click.echo("[STEP 3/7] Speech to text...")
        stt = SpeechToText(model_name=stt_model)
        transcript = stt.transcribe(audio_file)
        
        if verbose:
            click.echo(f"  Language: {transcript['language']}")
            click.echo(f"  Word count: {transcript['words_total']}")
        click.echo("  [OK] Transcription complete")
        click.echo("")
        
        # STEP 4: Prosody analysis
        click.echo("[STEP 4/7] Prosody analysis...")
        prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
        prosody_metrics = prosody.analyze(loader.get_audio_data())
        speech_rate = prosody.calculate_speech_rate(transcript['text'], audio_info['duration_seconds'])
        prosody_metrics.update(speech_rate)
        
        if verbose:
            click.echo(f"  Pitch mean: {prosody_metrics['pitch_mean_hz']:.1f} Hz")
            click.echo(f"  Speaking rate: {prosody_metrics['words_per_minute']:.1f} WPM")
        click.echo("  [OK] Prosody complete")
        click.echo("")
        
        # STEP 5: Emotion (optional)
        if not no_emotion:
            click.echo("[STEP 5/7] Emotion recognition...")
            try:
                emotion = EmotionAnalyzer()
                emotion_metrics = emotion.analyze(audio_file)
                
                if verbose:
                    click.echo(f"  Dominant emotion: {emotion_metrics['dominant_emotion']}")
                    click.echo(f"  Confidence: {emotion_metrics['confidence']:.1%}")
                click.echo("  [OK] Emotion complete")
            except Exception as e:
                if verbose:
                    click.echo(f"  [WARN] Emotion analysis skipped: {e}")
                emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
        else:
            click.echo("[STEP 5/7] Emotion recognition... (skipped)")
            emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
        click.echo("")
        
        # STEP 6: Filler detection
        click.echo("[STEP 6/7] Filler word detection...")
        filler = FillerDetector(language=transcript.get('language', 'en'))
        filler_metrics = filler.detect(transcript['text'])
        
        if verbose:
            click.echo(f"  Filler count: {filler_metrics['filler_word_count']}")
            click.echo(f"  Ratio: {filler_metrics['fillers_per_100_words']:.1f} per 100 words")
        click.echo("  [OK] Filler detection complete")
        click.echo("")
        
        # STEP 7: Build metrics
        click.echo("[STEP 7/7] Building metrics...")
        builder = MetricsBuilder()
        metrics = builder.build(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript,
            prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics,
            filler_metrics=filler_metrics
        )
        click.echo("  [OK] Metrics built")
        click.echo("")
        
        # Export
        if output_file is None:
            audio_path = Path(audio_file)
            output_dir = Path("outputs") / audio_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "analysis_result.json"
        
        exporter = JSONExporter()
        path = exporter.export(metrics, output_file)
        click.echo(f"[OK] JSON exported: {path}")
        click.echo("")
        
        # Summary
        click.echo("=" * 60)
        click.echo("Analysis Summary")
        click.echo("=" * 60)
        click.echo(
            f"Duration: {audio_info['duration_seconds']:.1f}s | "
            f"Speed: {prosody_metrics['words_per_minute']:.1f} WPM | "
            f"Speech: {vad_analysis['speech_ratio']:.1%} | "
            f"Fillers: {filler_metrics['fillers_per_100_words']:.1f}/100w"
        )
        click.echo("")
        click.echo("[OK] Analysis complete!")
        click.echo("")
        
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
            speech_rate = prosody.calculate_speech_rate(transcript['text'], loader.get_audio_info()['duration_seconds'])
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


if __name__ == "__main__":
    main()
