"""
CLI Interface - Command-line interface for Audio Metrics CLI v3

This module only handles:
- Argument parsing
- Calling pipeline.run()
- Output formatting

All analysis logic is in the Pipeline layer.
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import AnalysisPipeline
from core.logger import setup_logging, get_logger
from core.config import Config

logger = get_logger(__name__)


@click.group()
@click.version_option(version="3.0.0")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--debug", is_flag=True, help="Debug mode with step-by-step output")
@click.option("--log-file", type=click.Path(), default=None, help="Log file path")
@click.pass_context
def main(ctx, verbose, debug, log_file):
    """
    Audio Metrics CLI v3 - Professional Voice Analysis Engine
    
    Analyze audio files for speech metrics, speaker dynamics, and conversation quality.
    """
    # Setup logging
    level = "DEBUG" if verbose or debug else "INFO"
    setup_logging(level=level, log_file=log_file, json_output=False)
    
    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['config'] = Config()


@main.command("analyze")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, 
              help="Output JSON file path")
@click.option("-m", "--model", "stt_model", default="base", 
              help="Whisper model (tiny/base/small/medium/large)")
@click.option("--no-emotion", is_flag=True, help="Skip emotion analysis")
@click.option("--summary-method", type=click.Choice(["auto", "llm", "cloud", "heuristic", "none"]), 
              default="heuristic", help="Summary generation method")
@click.option("--language", default="zh", help="Language code for analysis")
@click.option("--debug-pipeline", is_flag=True, help="Show detailed pipeline step output")
@click.pass_context
def analyze(ctx, audio_file, output_file, stt_model, no_emotion, summary_method, language, debug_pipeline):
    """
    Analyze audio file and generate comprehensive metrics.
    
    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    
    Examples:
    
    \b
        audio-metrics analyze meeting.wav
        audio-metrics analyze meeting.wav -o result.json
        audio-metrics analyze meeting.wav --debug-pipeline
    """
    debug = ctx.obj.get('debug', False) or debug_pipeline
    config = ctx.obj.get('config', Config())
    
    # Build pipeline configuration
    pipeline_config = {
        'stt_model': stt_model,
        'enable_emotion': not no_emotion,
        'summary_method': summary_method,
        'language': language
    }
    
    # Override config
    if stt_model:
        config.models.speech_to_text.model = stt_model
    if no_emotion:
        config.features.enable_emotion = False
    
    click.echo("=" * 60)
    click.echo("Audio Metrics CLI v3.0 - Professional Voice Analysis Engine")
    click.echo("=" * 60)
    click.echo(f"Input: {Path(audio_file).name}")
    click.echo(f"STT Model: {stt_model}")
    click.echo(f"Emotion Analysis: {'Enabled' if not no_emotion else 'Disabled'}")
    click.echo(f"Summary Method: {summary_method}")
    click.echo("")
    
    # Initialize pipeline
    pipeline = AnalysisPipeline(config=pipeline_config, debug=debug_pipeline)
    
    try:
        # Run analysis
        result = pipeline.run(audio_file, output_file)
        
        # Print summary
        click.echo("")
        click.echo("=" * 60)
        click.echo("Analysis Summary")
        click.echo("=" * 60)
        
        if result.get('meta', {}).get('analysis_complete', False):
            audio = result.get('audio', {})
            speakers = result.get('speakers', {})
            dynamics = result.get('conversation_dynamics', {})
            summary = result.get('summary', {})
            
            click.echo(f"Duration: {audio.get('duration_seconds', 0):.1f}s")
            click.echo(f"Speakers: {speakers.get('num_speakers', 0)}")
            click.echo(f"Interruptions: {dynamics.get('interruptions', 0)}")
            click.echo(f"Avg Response Latency: {dynamics.get('avg_response_latency', 0):.2f}s")
            click.echo(f"Summary: {summary.get('one_liner', 'N/A')[:60]}...")
            
            if output_file:
                click.echo("")
                click.echo(f"[OK] Exported: {output_file}")
        else:
            click.echo(f"[ERROR] Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        click.echo("")
        click.echo("[OK] Analysis complete!")
        click.echo("")
        
        # Print timings if debug
        if debug_pipeline:
            click.echo("=" * 60)
            click.echo("Pipeline Timings")
            click.echo("=" * 60)
            timings = pipeline.get_timings()
            for step, duration in timings.items():
                click.echo(f"  {step}: {duration:.2f}s")
            click.echo("")
        
    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command("version")
def version():
    """Show version information"""
    click.echo("Audio Metrics CLI v3.0.0")
    click.echo("Architecture: CLI → Pipeline → Modules")
    click.echo("")
    click.echo("Core Components:")
    click.echo("  - Analysis Pipeline (core/pipeline.py)")
    click.echo("  - Voice Metrics (30+ features)")
    click.echo("  - Conversation Dynamics")
    click.echo("  - Speaker Diarization")
    click.echo("  - Speech-to-Text (Whisper)")


if __name__ == "__main__":
    main()
