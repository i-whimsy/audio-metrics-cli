"""
Speaker Metrics Module
======================
Aggregates and computes speaker-level statistics.

Creates speaker profiles with speaking time, turn statistics, and acoustic features.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
import numpy as np


class SpeakerMetricsAggregator:
    """
    Aggregate metrics at the speaker level.
    
    Creates comprehensive speaker profiles from segment-level data.
    """
    
    def __init__(self):
        """Initialize speaker metrics aggregator."""
        self.speaker_profiles = []
        
    def aggregate(
        self,
        timeline_segments: List[Dict[str, Any]],
        segment_acoustic_metrics: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate metrics by speaker.
        
        Args:
            timeline_segments: Timeline segments with speaker info
            segment_acoustic_metrics: Optional acoustic metrics per segment
            
        Returns:
            List of speaker profiles
        """
        # Group segments by speaker
        speaker_data = defaultdict(lambda: {
            "segments": [],
            "total_duration": 0,
            "turn_count": 0,
            "acoustic_metrics": []
        })
        
        # Create acoustic metrics lookup
        acoustic_lookup = {}
        if segment_acoustic_metrics:
            for metrics in segment_acoustic_metrics:
                key = (metrics.get("start", 0), metrics.get("speaker", "unknown"))
                acoustic_lookup[key] = metrics
        
        # Process timeline segments
        for segment in timeline_segments:
            if segment.get("type") not in ["speech", "overlap"]:
                continue
            
            speakers = segment.get("speakers", [])
            duration = segment.get("duration", 0)
            start = segment.get("start", 0)
            
            for speaker in speakers:
                speaker_data[speaker]["segments"].append({
                    "start": start,
                    "end": segment.get("end", 0),
                    "duration": duration,
                    "is_overlap": segment.get("type") == "overlap"
                })
                speaker_data[speaker]["total_duration"] += duration
                speaker_data[speaker]["turn_count"] += 1
                
                # Add acoustic metrics if available
                acoustic_key = (start, speaker)
                if acoustic_key in acoustic_lookup:
                    speaker_data[speaker]["acoustic_metrics"].append(
                        acoustic_lookup[acoustic_key]
                    )
        
        # Build speaker profiles
        self.speaker_profiles = []
        all_speakers = sorted(speaker_data.keys())
        
        for i, speaker in enumerate(all_speakers):
            data = speaker_data[speaker]
            
            # Calculate turn statistics
            turn_durations = [seg["duration"] for seg in data["segments"]]
            overlap_count = sum(1 for seg in data["segments"] if seg["is_overlap"])
            
            # Calculate acoustic statistics
            acoustic_stats = self._compute_acoustic_stats(data["acoustic_metrics"])
            
            profile = {
                "speaker_id": speaker,
                "speaker_label": f"Speaker_{i+1}",
                "total_speaking_time": round(data["total_duration"], 2),
                "turn_count": data["turn_count"],
                "avg_turn_duration": round(np.mean(turn_durations), 2) if turn_durations else 0,
                "min_turn_duration": round(min(turn_durations), 2) if turn_durations else 0,
                "max_turn_duration": round(max(turn_durations), 2) if turn_durations else 0,
                "overlap_turns": overlap_count,
                "overlap_ratio": round(overlap_count / data["turn_count"], 3) if data["turn_count"] > 0 else 0,
                "acoustic_profile": acoustic_stats
            }
            
            self.speaker_profiles.append(profile)
        
        return self.speaker_profiles
    
    def _compute_acoustic_stats(
        self,
        acoustic_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute aggregate acoustic statistics.
        
        Args:
            acoustic_metrics: List of acoustic metric dicts
            
        Returns:
            Aggregated acoustic statistics
        """
        if not acoustic_metrics:
            return {
                "avg_pitch_hz": 0,
                "pitch_std_hz": 0,
                "pitch_range_hz": 0,
                "avg_energy": 0,
                "energy_cv": 0,
                "avg_spectral_centroid": 0
            }
        
        # Extract values
        pitch_values = [m.get("pitch_mean_hz", 0) for m in acoustic_metrics if m.get("pitch_mean_hz", 0) > 0]
        energy_values = [m.get("energy_mean", 0) for m in acoustic_metrics]
        spectral_values = [m.get("spectral_centroid_mean", 0) for m in acoustic_metrics]
        
        # Compute statistics
        pitch_std = np.std(pitch_values) if pitch_values else 0
        pitch_range = (max(pitch_values) - min(pitch_values)) if len(pitch_values) > 1 else 0
        
        energy_std = np.std(energy_values) if energy_values else 0
        energy_mean = np.mean(energy_values) if energy_values else 0
        energy_cv = (energy_std / energy_mean) if energy_mean > 0 else 0
        
        return {
            "avg_pitch_hz": round(np.mean(pitch_values), 2) if pitch_values else 0,
            "pitch_std_hz": round(pitch_std, 2),
            "pitch_range_hz": round(pitch_range, 2),
            "avg_energy": round(energy_mean, 6),
            "energy_cv": round(energy_cv, 3),
            "avg_spectral_centroid": round(np.mean(spectral_values), 2) if spectral_values else 0
        }
    
    def compute_conversation_roles(
        self,
        speaker_profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Infer conversation roles based on speaking patterns.
        
        Args:
            speaker_profiles: List of speaker profiles
            
        Returns:
            Speaker profiles with inferred roles
        """
        if not speaker_profiles:
            return []
        
        # Find dominant speaker
        total_time = sum(p["total_speaking_time"] for p in speaker_profiles)
        
        enhanced_profiles = []
        for profile in speaker_profiles:
            speaking_ratio = profile["total_speaking_time"] / total_time if total_time > 0 else 0
            
            # Infer role based on speaking ratio
            if speaking_ratio > 0.6:
                role = "dominant_speaker"
            elif speaking_ratio > 0.3:
                role = "active_participant"
            elif speaking_ratio > 0.1:
                role = "occasional_speaker"
            else:
                role = "minimal_speaker"
            
            enhanced_profile = profile.copy()
            enhanced_profile["speaking_ratio"] = round(speaking_ratio, 3)
            enhanced_profile["inferred_role"] = role
            
            enhanced_profiles.append(enhanced_profile)
        
        return enhanced_profiles
    
    def get_profiles(self) -> List[Dict[str, Any]]:
        """
        Get speaker profiles.
        
        Returns:
            List of speaker profiles
        """
        return self.speaker_profiles
