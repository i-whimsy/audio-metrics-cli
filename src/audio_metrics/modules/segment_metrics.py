"""
Segment Metrics Module
======================
Extracts acoustic metrics for individual speech segments.

Computes pitch, energy, and other features per segment.
"""

import numpy as np
from typing import Dict, Any, List, Optional
import librosa

from core.logger import get_logger

logger = get_logger(__name__)


class SegmentMetricsExtractor:
    """
    Extract acoustic metrics for individual speech segments.
    
    Computes features like pitch, energy, and spectral characteristics
    for each segment in the conversation.
    """
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize segment metrics extractor.
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.frame_size = 0.025  # 25ms frames
        self.hop_size = 0.010    # 10ms hop
        
    def extract(
        self,
        audio_data: np.ndarray,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract metrics for each segment.
        
        Args:
            audio_data: Full audio data array
            segments: List of segments with start/end times
            
        Returns:
            List of segment metrics
        """
        segment_metrics = []
        
        for i, segment in enumerate(segments):
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            
            # Extract audio for this segment
            start_sample = int(start * self.sample_rate)
            end_sample = int(end * self.sample_rate)
            
            if start_sample >= len(audio_data):
                continue
            if end_sample > len(audio_data):
                end_sample = len(audio_data)
            
            segment_audio = audio_data[start_sample:end_sample]
            
            if len(segment_audio) == 0:
                continue
            
            # Extract metrics
            metrics = self._extract_segment_metrics(segment_audio, i)
            
            # Add segment info
            metrics["segment_index"] = i
            metrics["start"] = round(start, 3)
            metrics["end"] = round(end, 3)
            metrics["duration"] = round(end - start, 3)
            metrics["speaker"] = segment.get("speaker", "unknown")
            
            segment_metrics.append(metrics)
        
        logger.info(
            "Segment metrics extracted",
            num_segments=len(segment_metrics)
        )
        
        return segment_metrics
    
    def _extract_segment_metrics(
        self,
        audio: np.ndarray,
        index: int
    ) -> Dict[str, Any]:
        """
        Extract metrics for a single segment.
        
        Args:
            audio: Audio data for segment
            index: Segment index
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Ensure mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Pitch features
        try:
            f0, voiced_flag, voiced_prob = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate,
                frame_length=int(self.frame_size * self.sample_rate),
                hop_length=int(self.hop_size * self.sample_rate)
            )
            
            # Filter out unvoiced frames
            voiced_f0 = f0[voiced_flag]
            
            if len(voiced_f0) > 0:
                metrics["pitch_mean_hz"] = round(float(np.mean(voiced_f0)), 2)
                metrics["pitch_std_hz"] = round(float(np.std(voiced_f0)), 2)
                metrics["pitch_min_hz"] = round(float(np.min(voiced_f0)), 2)
                metrics["pitch_max_hz"] = round(float(np.max(voiced_f0)), 2)
                metrics["pitch_median_hz"] = round(float(np.median(voiced_f0)), 2)
                metrics["voiced_ratio"] = round(float(np.mean(voiced_flag)), 3)
            else:
                metrics["pitch_mean_hz"] = 0
                metrics["pitch_std_hz"] = 0
                metrics["pitch_min_hz"] = 0
                metrics["pitch_max_hz"] = 0
                metrics["pitch_median_hz"] = 0
                metrics["voiced_ratio"] = 0
                
        except Exception as e:
            logger.warning("Pitch extraction failed", segment=index, error=str(e))
            metrics["pitch_mean_hz"] = 0
            metrics["pitch_std_hz"] = 0
            metrics["pitch_min_hz"] = 0
            metrics["pitch_max_hz"] = 0
            metrics["pitch_median_hz"] = 0
            metrics["voiced_ratio"] = 0
        
        # Energy features
        try:
            rms = librosa.feature.rms(
                y=audio,
                frame_length=int(self.frame_size * self.sample_rate),
                hop_length=int(self.hop_size * self.sample_rate)
            )[0]
            
            metrics["energy_mean"] = round(float(np.mean(rms)), 6)
            metrics["energy_std"] = round(float(np.std(rms)), 6)
            metrics["energy_min"] = round(float(np.min(rms)), 6)
            metrics["energy_max"] = round(float(np.max(rms)), 6)
            
            # Coefficient of variation
            if np.mean(rms) > 0:
                metrics["energy_cv"] = round(float(np.std(rms) / np.mean(rms)), 3)
            else:
                metrics["energy_cv"] = 0
                
        except Exception as e:
            logger.warning("Energy extraction failed", segment=index, error=str(e))
            metrics["energy_mean"] = 0
            metrics["energy_std"] = 0
            metrics["energy_min"] = 0
            metrics["energy_max"] = 0
            metrics["energy_cv"] = 0
        
        # Spectral features
        try:
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio,
                sr=self.sample_rate,
                frame_length=int(self.frame_size * self.sample_rate),
                hop_length=int(self.hop_size * self.sample_rate)
            )[0]
            
            metrics["spectral_centroid_mean"] = round(float(np.mean(spectral_centroids)), 2)
            metrics["spectral_centroid_std"] = round(float(np.std(spectral_centroids)), 2)
            
        except Exception as e:
            logger.warning("Spectral feature extraction failed", segment=index, error=str(e))
            metrics["spectral_centroid_mean"] = 0
            metrics["spectral_centroid_std"] = 0
        
        # Zero crossing rate
        try:
            zcr = librosa.feature.zero_crossing_rate(
                y=audio,
                frame_length=int(self.frame_size * self.sample_rate),
                hop_length=int(self.hop_size * self.sample_rate)
            )[0]
            
            metrics["zero_crossing_rate_mean"] = round(float(np.mean(zcr)), 4)
            metrics["zero_crossing_rate_std"] = round(float(np.std(zcr)), 4)
            
        except Exception as e:
            logger.warning("ZCR extraction failed", segment=index, error=str(e))
            metrics["zero_crossing_rate_mean"] = 0
            metrics["zero_crossing_rate_std"] = 0
        
        return metrics
    
    def aggregate_by_speaker(
        self,
        segment_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate segment metrics by speaker.
        
        Args:
            segment_metrics: List of segment metrics
            
        Returns:
            Dictionary mapping speaker to aggregated metrics
        """
        from collections import defaultdict
        
        speaker_data = defaultdict(lambda: {
            "pitch_values": [],
            "energy_values": [],
            "segment_count": 0,
            "total_duration": 0
        })
        
        for metrics in segment_metrics:
            speaker = metrics.get("speaker", "unknown")
            
            speaker_data[speaker]["segment_count"] += 1
            speaker_data[speaker]["total_duration"] += metrics.get("duration", 0)
            
            if metrics.get("pitch_mean_hz", 0) > 0:
                speaker_data[speaker]["pitch_values"].append(metrics["pitch_mean_hz"])
            
            speaker_data[speaker]["energy_values"].append(metrics.get("energy_mean", 0))
        
        # Aggregate
        aggregated = {}
        for speaker, data in speaker_data.items():
            pitch_values = data["pitch_values"]
            energy_values = data["energy_values"]
            
            aggregated[speaker] = {
                "segment_count": data["segment_count"],
                "total_duration": round(data["total_duration"], 2),
                "avg_pitch_hz": round(np.mean(pitch_values), 2) if pitch_values else 0,
                "pitch_std_hz": round(np.std(pitch_values), 2) if pitch_values else 0,
                "avg_energy": round(np.mean(energy_values), 6) if energy_values else 0,
                "energy_std": round(np.std(energy_values), 6) if energy_values else 0
            }
        
        return aggregated
