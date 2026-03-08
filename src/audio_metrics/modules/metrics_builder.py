"""
Metrics Builder Module
Combines all analysis results into structured metrics
"""

from datetime import datetime
from typing import Dict, Any


class MetricsBuilder:
    """Build structured metrics from analysis results"""
    
    VERSION = "0.1.0"
    
    def __init__(self):
        """Initialize metrics builder"""
        self.metrics = {}
        
    def build(
        self,
        audio_info: Dict[str, Any],
        vad_analysis: Dict[str, Any],
        transcript_result: Dict[str, Any],
        prosody_metrics: Dict[str, Any],
        emotion_metrics: Dict[str, Any],
        filler_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build complete metrics structure
        
        Args:
            audio_info: Audio metadata
            vad_analysis: VAD analysis results
            transcript_result: Speech-to-text results
            prosody_metrics: Prosody analysis results
            emotion_metrics: Emotion analysis results
            filler_metrics: Filler word detection results
            
        Returns:
            Complete structured metrics
        """
        # Calculate speech rate
        transcript_text = transcript_result.get("text", "")
        audio_duration = audio_info.get("duration_seconds", 1)
        
        words = transcript_text.split()
        words_total = len(words)
        words_per_minute = (words_total / audio_duration) * 60 if audio_duration > 0 else 0
        
        # Build metrics
        self.metrics = {
            "audio_info": {
                "file_path": audio_info.get("file_path", ""),
                "file_name": audio_info.get("file_name", ""),
                "duration_seconds": audio_info.get("duration_seconds", 0),
                "sample_rate": audio_info.get("sample_rate", 0),
                "channels": audio_info.get("channels", 1),
                "file_size_bytes": audio_info.get("file_size_bytes", 0),
                "file_size_mb": audio_info.get("file_size_mb", 0)
            },
            
            "vad_analysis": {
                "speech_duration": vad_analysis.get("speech_duration", 0),
                "silence_duration": vad_analysis.get("silence_duration", 0),
                "speech_ratio": vad_analysis.get("speech_ratio", 0),
                "pause_count": vad_analysis.get("pause_count", 0),
                "avg_pause_duration": vad_analysis.get("avg_pause_duration", 0),
                "long_pause_count": vad_analysis.get("long_pause_count", 0)
            },
            
            "speech_metrics": {
                "words_total": words_total,
                "words_per_minute": round(words_per_minute, 1),
                "language": transcript_result.get("language", "unknown")
            },
            
            "prosody_metrics": {
                "pitch_mean_hz": prosody_metrics.get("pitch_mean_hz", 0),
                "pitch_std_hz": prosody_metrics.get("pitch_std_hz", 0),
                "pitch_range_hz": prosody_metrics.get("pitch_range_hz", 0),
                "energy_mean": prosody_metrics.get("energy_mean", 0),
                "energy_std": prosody_metrics.get("energy_std", 0),
                "energy_dynamic_range": prosody_metrics.get("energy_dynamic_range", 0),
                "energy_cv": prosody_metrics.get("energy_cv", 0)
            },
            
            "emotion_metrics": {
                "dominant_emotion": emotion_metrics.get("dominant_emotion", "neutral"),
                "confidence": emotion_metrics.get("confidence", 0),
                "emotion_probabilities": emotion_metrics.get("emotion_probabilities", {})
            },
            
            "transcript": {
                "text": transcript_text,
                "model": transcript_result.get("model", "unknown"),
                "language": transcript_result.get("language", "unknown")
            },
            
            "filler_metrics": {
                "filler_word_count": filler_metrics.get("filler_word_count", 0),
                "filler_ratio": filler_metrics.get("filler_ratio", 0),
                "fillers_per_100_words": filler_metrics.get("fillers_per_100_words", 0),
                "filler_by_type": filler_metrics.get("filler_by_type", {})
            },
            
            "processing_meta": {
                "timestamp": datetime.now().isoformat(),
                "pipeline_version": self.VERSION,
                "analysis_complete": True
            }
        }
        
        return self.metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of key metrics
        
        Returns:
            Summary metrics
        """
        if not self.metrics:
            return {}
        
        return {
            "duration_seconds": self.metrics["audio_info"]["duration_seconds"],
            "words_per_minute": self.metrics["speech_metrics"]["words_per_minute"],
            "speech_ratio": self.metrics["vad_analysis"]["speech_ratio"],
            "pitch_mean_hz": self.metrics["prosody_metrics"]["pitch_mean_hz"],
            "energy_cv": self.metrics["prosody_metrics"]["energy_cv"],
            "dominant_emotion": self.metrics["emotion_metrics"]["dominant_emotion"],
            "fillers_per_100_words": self.metrics["filler_metrics"]["fillers_per_100_words"]
        }
    
    def validate(self) -> bool:
        """
        Validate metrics structure
        
        Returns:
            True if valid
        """
        required_keys = [
            "audio_info",
            "vad_analysis",
            "speech_metrics",
            "prosody_metrics",
            "emotion_metrics",
            "transcript",
            "filler_metrics",
            "processing_meta"
        ]
        
        for key in required_keys:
            if key not in self.metrics:
                print(f"Warning: Missing key in metrics: {key}")
                return False
        
        return True
