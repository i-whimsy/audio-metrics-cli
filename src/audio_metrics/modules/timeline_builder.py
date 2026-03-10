"""
Timeline Builder Module
=======================
Builds conversation timeline from speaker diarization and VAD segments.

Creates a unified timeline showing who spoke when, with gaps and overlaps.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SegmentType(Enum):
    """Type of timeline segment."""
    SPEECH = "speech"
    SILENCE = "silence"
    OVERLAP = "overlap"


@dataclass
class TimelineSegment:
    """A segment in the conversation timeline."""
    start: float
    end: float
    duration: float
    segment_type: SegmentType
    speakers: List[str] = field(default_factory=list)
    speaker_count: int = 0
    text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "type": self.segment_type.value,
            "speakers": self.speakers,
            "speaker_count": self.speaker_count,
            "text": self.text
        }


class TimelineBuilder:
    """
    Build conversation timeline from diarization and VAD results.
    
    Creates a chronological sequence of speech segments with speaker information.
    """
    
    def __init__(self, gap_threshold: float = 0.5):
        """
        Initialize timeline builder.
        
        Args:
            gap_threshold: Minimum gap to create silence segment (seconds)
        """
        self.gap_threshold = gap_threshold
        self.timeline = []
        
    def build(
        self,
        diarization_segments: List[Dict[str, Any]],
        vad_segments: Optional[List[Dict[str, Any]]] = None,
        audio_duration: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Build conversation timeline.
        
        Args:
            diarization_segments: Segments from speaker diarization
            vad_segments: Optional VAD speech segments
            audio_duration: Total audio duration
            
        Returns:
            List of timeline segments
        """
        if not diarization_segments:
            return []
        
        # Sort segments by start time
        sorted_segments = sorted(diarization_segments, key=lambda x: x["start"])
        
        # Group overlapping segments
        grouped = self._group_overlapping_segments(sorted_segments)
        
        # Build timeline
        self.timeline = []
        current_time = 0.0
        
        for group in grouped:
            group_start = min(seg["start"] for seg in group)
            group_end = max(seg["end"] for seg in group)
            
            # Add silence gap if needed
            if group_start - current_time > self.gap_threshold:
                silence_segment = TimelineSegment(
                    start=current_time,
                    end=group_start,
                    duration=group_start - current_time,
                    segment_type=SegmentType.SILENCE,
                    speakers=[],
                    speaker_count=0
                )
                self.timeline.append(silence_segment.to_dict())
            
            # Create speech segment
            speakers = list(set(seg["speaker"] for seg in group))
            duration = group_end - group_start
            
            segment_type = SegmentType.OVERLAP if len(speakers) > 1 else SegmentType.SPEECH
            
            speech_segment = TimelineSegment(
                start=group_start,
                end=group_end,
                duration=duration,
                segment_type=segment_type,
                speakers=speakers,
                speaker_count=len(speakers)
            )
            self.timeline.append(speech_segment.to_dict())
            
            current_time = group_end
        
        # Add final silence if needed
        if audio_duration > 0 and current_time < audio_duration:
            if audio_duration - current_time > self.gap_threshold:
                silence_segment = TimelineSegment(
                    start=current_time,
                    end=audio_duration,
                    duration=audio_duration - current_time,
                    segment_type=SegmentType.SILENCE,
                    speakers=[],
                    speaker_count=0
                )
                self.timeline.append(silence_segment.to_dict())
        
        return self.timeline
    
    def _group_overlapping_segments(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group overlapping segments together.
        
        Args:
            segments: List of segments sorted by start time
            
        Returns:
            List of segment groups
        """
        if not segments:
            return []
        
        groups = []
        current_group = [segments[0]]
        current_end = segments[0]["end"]
        
        for segment in segments[1:]:
            # Check if overlaps with current group
            if segment["start"] < current_end:
                # Add to current group
                current_group.append(segment)
                current_end = max(current_end, segment["end"])
            else:
                # Start new group
                groups.append(current_group)
                current_group = [segment]
                current_end = segment["end"]
        
        # Add last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def add_transcript_to_timeline(
        self,
        timeline: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add transcript text to timeline segments.
        
        Args:
            timeline: Timeline segments
            transcript_segments: Segments with text and timestamps
            
        Returns:
            Timeline with text added
        """
        if not transcript_segments:
            return timeline
        
        # Create timeline with text
        enhanced_timeline = []
        
        for tl_segment in timeline:
            # Find matching transcript segments
            matching_text = []
            
            for ts_segment in transcript_segments:
                # Check for time overlap
                if (ts_segment.get("start", 0) < tl_segment["end"] and
                    ts_segment.get("end", 0) > tl_segment["start"]):
                    matching_text.append(ts_segment.get("text", ""))
            
            # Combine text
            tl_segment["text"] = " ".join(matching_text)
            enhanced_timeline.append(tl_segment)
        
        return enhanced_timeline
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get the built timeline.
        
        Returns:
            List of timeline segments
        """
        return self.timeline
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get timeline statistics.
        
        Returns:
            Statistics about the timeline
        """
        if not self.timeline:
            return {
                "total_segments": 0,
                "speech_segments": 0,
                "silence_segments": 0,
                "overlap_segments": 0,
                "total_speech_duration": 0,
                "total_silence_duration": 0,
                "total_overlap_duration": 0
            }
        
        speech_segments = sum(1 for s in self.timeline if s["type"] == "speech")
        silence_segments = sum(1 for s in self.timeline if s["type"] == "silence")
        overlap_segments = sum(1 for s in self.timeline if s["type"] == "overlap")
        
        speech_duration = sum(s["duration"] for s in self.timeline if s["type"] == "speech")
        silence_duration = sum(s["duration"] for s in self.timeline if s["type"] == "silence")
        overlap_duration = sum(s["duration"] for s in self.timeline if s["type"] == "overlap")
        
        return {
            "total_segments": len(self.timeline),
            "speech_segments": speech_segments,
            "silence_segments": silence_segments,
            "overlap_segments": overlap_segments,
            "total_speech_duration": round(speech_duration, 2),
            "total_silence_duration": round(silence_duration, 2),
            "total_overlap_duration": round(overlap_duration, 2)
        }
