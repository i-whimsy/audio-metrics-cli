"""
Timing Relation Module
======================
Computes timing relationships between conversation segments.

Analyzes turn-taking patterns, response times, and conversational dynamics.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class TimingRelationAnalyzer:
    """
    Analyze timing relationships between conversation segments.
    
    Computes metrics like response latency, turn-taking patterns,
    and conversational flow characteristics.
    """
    
    def __init__(self, gap_threshold: float = 0.5):
        """
        Initialize timing relation analyzer.
        
        Args:
            gap_threshold: Maximum gap to consider as immediate response (seconds)
        """
        self.gap_threshold = gap_threshold
        self.timing_metrics = {}
        
    def analyze(
        self,
        timeline_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze timing relationships in conversation.
        
        Args:
            timeline_segments: Timeline segments with speaker info
            
        Returns:
            Dictionary of timing metrics
        """
        # Filter to speech segments only
        speech_segments = [
            seg for seg in timeline_segments
            if seg.get("type") in ["speech", "overlap"]
        ]
        
        if not speech_segments:
            return self._empty_metrics()
        
        # Sort by start time
        sorted_segments = sorted(speech_segments, key=lambda x: x["start"])
        
        # Compute inter-segment gaps
        gap_stats = self._compute_gaps(sorted_segments)
        
        # Compute turn-taking metrics
        turn_metrics = self._compute_turn_taking(sorted_segments)
        
        # Compute response latencies
        response_metrics = self._compute_response_latencies(sorted_segments)
        
        # Compute overlap statistics
        overlap_metrics = self._compute_overlap_stats(timeline_segments)
        
        # Compute raw gaps list for flow metrics
        gaps_list = []
        for i in range(1, len(sorted_segments)):
            gap = sorted_segments[i]["start"] - sorted_segments[i-1]["end"]
            if gap > 0:
                gaps_list.append(gap)
        
        # Aggregate
        self.timing_metrics = {
            "gap_statistics": gap_stats,
            "turn_taking": turn_metrics,
            "response_latency": response_metrics,
            "overlap_statistics": overlap_metrics,
            "conversational_flow": self._compute_flow_metrics(sorted_segments, gaps_list)
        }
        
        return self.timing_metrics
    
    def _compute_gaps(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute gaps between consecutive segments.
        
        Args:
            segments: Sorted speech segments
            
        Returns:
            Gap statistics
        """
        if len(segments) < 2:
            return {
                "mean_gap": 0,
                "std_gap": 0,
                "min_gap": 0,
                "max_gap": 0,
                "gap_count": 0
            }
        
        gaps = []
        for i in range(1, len(segments)):
            gap = segments[i]["start"] - segments[i-1]["end"]
            if gap > 0:  # Only positive gaps (silence between segments)
                gaps.append(gap)
        
        if not gaps:
            return {
                "mean_gap": 0,
                "std_gap": 0,
                "min_gap": 0,
                "max_gap": 0,
                "gap_count": 0
            }
        
        return {
            "mean_gap": round(np.mean(gaps), 3),
            "std_gap": round(np.std(gaps), 3),
            "min_gap": round(min(gaps), 3),
            "max_gap": round(max(gaps), 3),
            "gap_count": len(gaps),
            "short_gaps": sum(1 for g in gaps if g < self.gap_threshold),
            "long_gaps": sum(1 for g in gaps if g > 2.0)
        }
    
    def _compute_turn_taking(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute turn-taking patterns.
        
        Args:
            segments: Sorted speech segments
            
        Returns:
            Turn-taking metrics
        """
        if len(segments) < 2:
            return {
                "turn_count": len(segments),
                "speaker_changes": 0,
                "speaker_change_ratio": 0,
                "avg_turn_duration": 0
            }
        
        # Count speaker changes
        speaker_changes = 0
        for i in range(1, len(segments)):
            current_speakers = set(segments[i].get("speakers", []))
            prev_speakers = set(segments[i-1].get("speakers", []))
            
            if current_speakers != prev_speakers:
                speaker_changes += 1
        
        turn_durations = [seg.get("duration", 0) for seg in segments]
        
        return {
            "turn_count": len(segments),
            "speaker_changes": speaker_changes,
            "speaker_change_ratio": round(speaker_changes / (len(segments) - 1), 3) if len(segments) > 1 else 0,
            "avg_turn_duration": round(np.mean(turn_durations), 2) if turn_durations else 0,
            "min_turn_duration": round(min(turn_durations), 2) if turn_durations else 0,
            "max_turn_duration": round(max(turn_durations), 2) if turn_durations else 0
        }
    
    def _compute_response_latencies(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute response latency between different speakers.
        
        Args:
            segments: Sorted speech segments
            
        Returns:
            Response latency metrics
        """
        if len(segments) < 2:
            return {
                "mean_response_latency": 0,
                "std_response_latency": 0,
                "quick_responses": 0,
                "slow_responses": 0
            }
        
        latencies = []
        
        for i in range(1, len(segments)):
            current_speakers = set(segments[i].get("speakers", []))
            prev_speakers = set(segments[i-1].get("speakers", []))
            
            # Only count when different speakers
            if current_speakers != prev_speakers:
                latency = segments[i]["start"] - segments[i-1]["end"]
                if latency > 0:
                    latencies.append(latency)
        
        if not latencies:
            return {
                "mean_response_latency": 0,
                "std_response_latency": 0,
                "quick_responses": 0,
                "slow_responses": 0,
                "response_count": 0
            }
        
        return {
            "mean_response_latency": round(np.mean(latencies), 3),
            "std_response_latency": round(np.std(latencies), 3),
            "min_response_latency": round(min(latencies), 3),
            "max_response_latency": round(max(latencies), 3),
            "quick_responses": sum(1 for l in latencies if l < self.gap_threshold),
            "slow_responses": sum(1 for l in latencies if l > 1.0),
            "response_count": len(latencies)
        }
    
    def _compute_overlap_stats(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute overlap statistics.
        
        Args:
            segments: All timeline segments
            
        Returns:
            Overlap metrics
        """
        overlap_segments = [seg for seg in segments if seg.get("type") == "overlap"]
        speech_segments = [seg for seg in segments if seg.get("type") in ["speech", "overlap"]]
        
        total_overlap_duration = sum(seg.get("duration", 0) for seg in overlap_segments)
        total_speech_duration = sum(seg.get("duration", 0) for seg in speech_segments)
        
        return {
            "overlap_count": len(overlap_segments),
            "total_overlap_duration": round(total_overlap_duration, 2),
            "overlap_ratio": round(total_overlap_duration / total_speech_duration, 3) if total_speech_duration > 0 else 0,
            "avg_overlap_duration": round(np.mean([seg.get("duration", 0) for seg in overlap_segments]), 2) if overlap_segments else 0
        }
    
    def _compute_flow_metrics(
        self,
        segments: List[Dict[str, Any]],
        gaps: List[float]
    ) -> Dict[str, Any]:
        """
        Compute overall conversational flow metrics.
        
        Args:
            segments: Sorted speech segments
            gaps: List of gaps between segments
            
        Returns:
            Flow metrics
        """
        if not segments:
            return {
                "fluency_score": 0,
                "engagement_score": 0,
                "balance_score": 0
            }
        
        # Fluency: based on gap statistics
        mean_gap = np.mean(gaps) if gaps else 0
        fluency_score = max(0, min(1, 1 - (mean_gap / 2.0)))  # Lower gaps = higher fluency
        
        # Engagement: based on speaker changes and overlap
        speaker_changes = sum(
            1 for i in range(1, len(segments))
            if set(segments[i].get("speakers", [])) != set(segments[i-1].get("speakers", []))
        )
        change_ratio = speaker_changes / (len(segments) - 1) if len(segments) > 1 else 0
        engagement_score = min(1, change_ratio * 1.5)  # More changes = more engagement
        
        # Balance: based on speaker distribution
        speaker_times = {}
        for seg in segments:
            for speaker in seg.get("speakers", []):
                speaker_times[speaker] = speaker_times.get(speaker, 0) + seg.get("duration", 0)
        
        if len(speaker_times) > 1:
            times = list(speaker_times.values())
            balance_score = 1 - (np.std(times) / np.mean(times)) if np.mean(times) > 0 else 0
            balance_score = max(0, min(1, balance_score))
        else:
            balance_score = 0
        
        return {
            "fluency_score": round(fluency_score, 3),
            "engagement_score": round(engagement_score, 3),
            "balance_score": round(balance_score, 3)
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics dict."""
        return {
            "gap_statistics": {},
            "turn_taking": {},
            "response_latency": {},
            "overlap_statistics": {},
            "conversational_flow": {}
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get timing metrics.
        
        Returns:
            Timing metrics dictionary
        """
        return self.timing_metrics
