"""
Conversation Dynamics Analyzer

Analyzes conversation structure and dynamics including:
- Interruptions and overlaps
- Response latency
- Turn-taking patterns
- Pause analysis

This module provides metrics for understanding conversation flow and quality.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from core.logger import get_logger

logger = get_logger(__name__)


class ConversationDynamicsAnalyzer:
    """
    Analyze conversation dynamics from segmented audio.
    
    Computes metrics for:
    - Interruptions (overlapping speech)
    - Response latency (gap between turns)
    - Turn-taking patterns
    - Pause distribution
    """
    
    def __init__(self, overlap_threshold: float = 0.3):
        """
        Initialize conversation dynamics analyzer.
        
        Args:
            overlap_threshold: Minimum overlap duration (seconds) to count as interruption
        """
        self.overlap_threshold = overlap_threshold
    
    def analyze_dynamics(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze conversation dynamics from segments.
        
        Args:
            segments: List of segment dictionaries with start, end, speaker, duration
            
        Returns:
            Dictionary with conversation dynamics metrics
        """
        if not segments or len(segments) < 2:
            return self._empty_dynamics()
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x.get('start', 0))
        
        # Calculate metrics
        interruptions = self._detect_interruptions(sorted_segments)
        overlaps = self._calculate_overlaps(sorted_segments)
        response_latencies = self._calculate_response_latencies(sorted_segments)
        turn_stats = self._calculate_turn_statistics(sorted_segments)
        pause_stats = self._calculate_pause_statistics(sorted_segments)
        
        return {
            "interruptions": interruptions,
            "overlap_seconds": round(overlaps['total_overlap'], 2),
            "overlap_ratio": round(overlaps['overlap_ratio'], 3),
            "avg_response_latency": round(response_latencies['mean'], 2),
            "response_latency_std": round(response_latencies['std'], 2),
            "turn_switch_rate": round(turn_stats['switch_rate'], 3),
            "avg_turn_duration": round(turn_stats['mean_duration'], 2),
            "turn_duration_std": round(turn_stats['std_duration'], 2),
            "long_pause_count": pause_stats['long_pauses'],
            "avg_pause_duration": round(pause_stats['mean_pause'], 2),
            "total_silence_ratio": round(pause_stats['silence_ratio'], 3)
        }
    
    def _detect_interruptions(self, segments: List[Dict]) -> int:
        """
        Detect interruptions (overlapping speech between different speakers).
        
        An interruption occurs when:
        - Speaker B starts speaking while Speaker A is still talking
        - Overlap duration > threshold
        """
        interruption_count = 0
        
        for i in range(len(segments) - 1):
            seg_a = segments[i]
            seg_b = segments[i + 1]
            
            # Check if different speakers
            speaker_a = seg_a.get('speaker', '')
            speaker_b = seg_b.get('speaker', '')
            
            if speaker_a == speaker_b:
                continue
            
            # Check for overlap
            overlap = self._calculate_overlap_duration(seg_a, seg_b)
            
            if overlap > self.overlap_threshold:
                interruption_count += 1
        
        return interruption_count
    
    def _calculate_overlaps(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        Calculate total overlap duration and ratio.
        
        Returns:
            Dictionary with total_overlap (seconds) and overlap_ratio
        """
        total_overlap = 0.0
        total_duration = 0.0
        
        for i in range(len(segments) - 1):
            seg_a = segments[i]
            seg_b = segments[i + 1]
            
            overlap = self._calculate_overlap_duration(seg_a, seg_b)
            if overlap > 0:
                total_overlap += overlap
            
            total_duration += seg_a.get('duration', 0)
        
        # Add last segment duration
        if segments:
            total_duration += segments[-1].get('duration', 0)
        
        overlap_ratio = total_overlap / total_duration if total_duration > 0 else 0
        
        return {
            'total_overlap': total_overlap,
            'overlap_ratio': overlap_ratio
        }
    
    def _calculate_overlap_duration(self, seg_a: Dict, seg_b: Dict) -> float:
        """Calculate overlap duration between two segments"""
        start_a = seg_a.get('start', 0)
        end_a = seg_a.get('end', 0)
        start_b = seg_b.get('start', 0)
        end_b = seg_b.get('end', 0)
        
        # Check for overlap
        if start_b >= end_a:
            return 0.0  # No overlap
        
        overlap_start = max(start_a, start_b)
        overlap_end = min(end_a, end_b)
        
        return max(0.0, overlap_end - overlap_start)
    
    def _calculate_response_latencies(self, segments: List[Dict]) -> Dict[str, float]:
        """
        Calculate response latencies (gaps between speaker turns).
        
        Response latency is the time between when one speaker stops
        and the next speaker starts.
        """
        latencies = []
        
        for i in range(len(segments) - 1):
            seg_a = segments[i]
            seg_b = segments[i + 1]
            
            speaker_a = seg_a.get('speaker', '')
            speaker_b = seg_b.get('speaker', '')
            
            # Only count latency between different speakers
            if speaker_a != speaker_b:
                end_a = seg_a.get('end', 0)
                start_b = seg_b.get('start', 0)
                
                latency = start_b - end_a
                
                # Only count positive latencies (gaps, not overlaps)
                if latency > 0:
                    latencies.append(latency)
        
        if not latencies:
            return {'mean': 0.0, 'std': 0.0}
        
        return {
            'mean': float(np.mean(latencies)),
            'std': float(np.std(latencies))
        }
    
    def _calculate_turn_statistics(self, segments: List[Dict]) -> Dict[str, float]:
        """
        Calculate turn-taking statistics.
        
        Includes:
        - Mean turn duration
        - Turn duration standard deviation
        - Turn switch rate (switches per second)
        """
        durations = [seg.get('duration', 0) for seg in segments]
        
        if not durations:
            return {
                'mean_duration': 0.0,
                'std_duration': 0.0,
                'switch_rate': 0.0
            }
        
        total_duration = sum(durations)
        
        # Count speaker switches
        switch_count = 0
        for i in range(len(segments) - 1):
            if segments[i].get('speaker') != segments[i + 1].get('speaker'):
                switch_count += 1
        
        switch_rate = switch_count / total_duration if total_duration > 0 else 0
        
        return {
            'mean_duration': float(np.mean(durations)),
            'std_duration': float(np.std(durations)),
            'switch_rate': switch_rate
        }
    
    def _calculate_pause_statistics(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        Calculate pause/silence statistics.
        
        Includes:
        - Number of long pauses (>2 seconds)
        - Mean pause duration
        - Total silence ratio
        """
        pauses = []
        total_silence = 0.0
        total_duration = 0.0
        
        for i in range(len(segments) - 1):
            seg_a = segments[i]
            seg_b = segments[i + 1]
            
            end_a = seg_a.get('end', 0)
            start_b = seg_b.get('start', 0)
            
            pause_duration = start_b - end_a
            
            if pause_duration > 0:
                pauses.append(pause_duration)
                total_silence += pause_duration
            
            total_duration += seg_a.get('duration', 0)
        
        # Add last segment
        if segments:
            total_duration += segments[-1].get('duration', 0)
        
        long_pauses = sum(1 for p in pauses if p > 2.0)
        mean_pause = float(np.mean(pauses)) if pauses else 0.0
        silence_ratio = total_silence / total_duration if total_duration > 0 else 0
        
        return {
            'long_pauses': long_pauses,
            'mean_pause': mean_pause,
            'silence_ratio': silence_ratio
        }
    
    def _empty_dynamics(self) -> Dict[str, Any]:
        """Return empty dynamics for insufficient data"""
        return {
            "interruptions": 0,
            "overlap_seconds": 0.0,
            "overlap_ratio": 0.0,
            "avg_response_latency": 0.0,
            "response_latency_std": 0.0,
            "turn_switch_rate": 0.0,
            "avg_turn_duration": 0.0,
            "turn_duration_std": 0.0,
            "long_pause_count": 0,
            "avg_pause_duration": 0.0,
            "total_silence_ratio": 0.0
        }
