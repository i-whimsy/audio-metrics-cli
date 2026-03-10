"""
Audio Metrics - Core Analysis Modules

Cross-platform audio analysis toolkit for speech metrics extraction.
Supports both single-speaker and multi-speaker conversation analysis.
"""

from .audio_loader import AudioLoader
from .vad_analyzer import VADAnalyzer
from .speech_to_text import SpeechToText
from .prosody_analyzer import ProsodyAnalyzer
from .emotion_analyzer import EmotionAnalyzer
from .filler_detector import FillerDetector
from .metrics_builder import MetricsBuilder
from .json_exporter import JSONExporter

# Multi-speaker conversation analysis modules
from .speaker_diarization import SpeakerDiarization
from .timeline_builder import TimelineBuilder
from .segment_metrics import SegmentMetricsExtractor
from .speaker_metrics import SpeakerMetricsAggregator
from .timing_relation import TimingRelationAnalyzer

__version__ = "0.3.0"
__all__ = [
    # Core modules
    "AudioLoader",
    "VADAnalyzer",
    "SpeechToText",
    "ProsodyAnalyzer",
    "EmotionAnalyzer",
    "FillerDetector",
    "MetricsBuilder",
    "JSONExporter",
    
    # Multi-speaker modules
    "SpeakerDiarization",
    "TimelineBuilder",
    "SegmentMetricsExtractor",
    "SpeakerMetricsAggregator",
    "TimingRelationAnalyzer",
]
