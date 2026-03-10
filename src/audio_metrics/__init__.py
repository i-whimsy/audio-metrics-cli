"""
Audio Metrics CLI - Cross-platform audio analysis toolkit

Extract objective speech metrics from audio files.
Supports both single-speaker and multi-speaker conversation analysis.
Output structured JSON for further analysis.
"""

__version__ = "0.3.1"
__author__ = "OpenClaw"
__email__ = "clawbot@openclaw.ai"

from .cli import main

# Core modules
from .core.pipeline import AudioAnalysisPipeline, MultiSpeakerPipeline, run_parallel_analysis, run_multi_speaker_analysis
from .modules import (
    AudioLoader,
    VADAnalyzer,
    SpeechToText,
    ProsodyAnalyzer,
    EmotionAnalyzer,
    FillerDetector,
    MetricsBuilder,
    JSONExporter,
    SpeakerDiarization,
    TimelineBuilder,
    SegmentMetricsExtractor,
    SpeakerMetricsAggregator,
    TimingRelationAnalyzer,
)

__all__ = [
    "main",
    # Pipelines
    "AudioAnalysisPipeline",
    "MultiSpeakerPipeline",
    "run_parallel_analysis",
    "run_multi_speaker_analysis",
    # Modules
    "AudioLoader",
    "VADAnalyzer",
    "SpeechToText",
    "ProsodyAnalyzer",
    "EmotionAnalyzer",
    "FillerDetector",
    "MetricsBuilder",
    "JSONExporter",
    "SpeakerDiarization",
    "TimelineBuilder",
    "SegmentMetricsExtractor",
    "SpeakerMetricsAggregator",
    "TimingRelationAnalyzer",
]
