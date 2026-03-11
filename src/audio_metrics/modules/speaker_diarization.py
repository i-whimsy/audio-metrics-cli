"""
Speaker Diarization Module
==========================
Identifies and separates different speakers in audio.

Uses pyannote.audio when available, falls back to simple VAD-based segmentation.

Outputs speaker segments with timestamps and speaker labels.
"""

import os
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


class SpeakerDiarization:
    """
    Speaker diarization.
    
    Identifies "who spoke when" in multi-speaker audio.
    Uses pyannote.audio when available, falls back to VAD-based segmentation.
    """
    
    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1"):
        """
        Initialize speaker diarization.
        
        Args:
            model_name: pyannote diarization model name
        """
        self.model_name = model_name
        self.model = None
        self.segments = []
        self.use_fallback = False
        
    def load_model(self):
        """Load speaker diarization model (pyannote or fallback) with offline-first strategy."""
        if self.model is not None:
            return
        
        import torch
        
        # Set offline environment variables
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['TORCH_HOME'] = str(Path.home() / ".cache" / "torch")
            
        try:
            from pyannote.audio import Pipeline
            
            # Load pretrained pipeline (will use cache if available)
            self.model = Pipeline.from_pretrained(self.model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model.to(torch.device("cuda"))
                logger.info("Speaker diarization model loaded on GPU")
            else:
                logger.info("Speaker diarization model loaded on CPU")
                
            self.use_fallback = False
                
        except Exception as e:
            logger.warning("pyannote.audio not available, using fallback VAD-based segmentation", error=str(e))
            self.use_fallback = True
            self.model = None
    
    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            Diarization results with speaker segments
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load model if not loaded
        if self.model is None:
            self.load_model()
        
        # Use fallback if pyannote not available
        if self.use_fallback:
            return self._fallback_diarize(
                str(audio_path),
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )
        
        # Prepare diarization parameters
        diarization_params = {}
        if num_speakers is not None:
            diarization_params["num_speakers"] = num_speakers
        elif min_speakers is not None or max_speakers is not None:
            if min_speakers is not None:
                diarization_params["min_speakers"] = min_speakers
            if max_speakers is not None:
                diarization_params["max_speakers"] = max_speakers
        
        try:
            # Run diarization
            logger.info("Running speaker diarization", file=str(audio_path))
            diarization = self.model(str(audio_path), **diarization_params)
            
            # Extract segments - pyannote v4.0 API compatibility
            self.segments = []
            speaker_times = {}
            
            # pyannote v4.0+: diarization.speaker_diarization is a property that returns Annotation
            # Use annotation.itertracks(yield_label=True) to iterate
            try:
                # Try pyannote v4.0+ API first
                annotation = diarization.speaker_diarization
                for turn, track, speaker in annotation.itertracks(yield_label=True):
                    segment = {
                        "start": round(turn.start, 3),
                        "end": round(turn.end, 3),
                        "duration": round(turn.end - turn.start, 3),
                        "speaker": speaker
                    }
                    self.segments.append(segment)
                    
                    # Track speaker time ranges
                    if speaker not in speaker_times:
                        speaker_times[speaker] = {"first": turn.start, "last": turn.end}
                    else:
                        speaker_times[speaker]["last"] = max(speaker_times[speaker]["last"], turn.end)
                        
                logger.info("Using pyannote v4.0+ API")
                
            except AttributeError:
                # Fallback to v3.x API - try itertracks directly on diarization
                try:
                    for turn, track, speaker in diarization.itertracks(yield_label=True):
                        segment = {
                            "start": round(turn.start, 3),
                            "end": round(turn.end, 3),
                            "duration": round(turn.end - turn.start, 3),
                            "speaker": speaker
                        }
                        self.segments.append(segment)
                        
                        if speaker not in speaker_times:
                            speaker_times[speaker] = {"first": turn.start, "last": turn.end}
                        else:
                            speaker_times[speaker]["last"] = max(speaker_times[speaker]["last"], turn.end)
                            
                    logger.info("Using pyannote v3.x API")
                    
                except AttributeError:
                    # Both APIs failed, use fallback
                    logger.warning("pyannote API failed, using fallback")
                    return self._fallback_diarize(
                        str(audio_path),
                        num_speakers=num_speakers,
                        min_speakers=min_speakers,
                        max_speakers=max_speakers
                    )
            
            # Count unique speakers
            unique_speakers = list(set(seg["speaker"] for seg in self.segments))
            num_unique_speakers = len(unique_speakers)
            
            logger.info(
                "Diarization complete",
                num_segments=len(self.segments),
                num_speakers=num_unique_speakers
            )
            
            return {
                "segments": self.segments,
                "num_speakers": num_unique_speakers,
                "speakers": unique_speakers,
                "speaker_times": speaker_times
            }
            
        except Exception as e:
            logger.error("Speaker diarization failed", error=str(e))
            # Fall back to simple method
            logger.info("Falling back to VAD-based segmentation")
            return self._fallback_diarize(
                str(audio_path),
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )
    
    def _fallback_diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fallback diarization using VAD-based segmentation.

        This is a simple approach that alternates speakers based on VAD segments.
        Not as accurate as pyannote.audio but works without additional dependencies.

        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers

        Returns:
            Diarization results with speaker segments
        """
        logger.info("Using fallback VAD-based speaker segmentation")
        
        # CRITICAL WARNING: Inform user about fallback mode limitations
        logger.warning(
            "FALLBACK MODE: pyannote.audio is not installed. "
            "Speaker separation will be INACCURATE. "
            "To get accurate results, please install: pip install pyannote.audio"
        )
        
        # Import VAD analyzer
        from modules.vad_analyzer import VADAnalyzer
        import librosa
        
        # Load audio
        audio_data, sample_rate = librosa.load(audio_path, sr=None)
        
        # Run VAD
        vad = VADAnalyzer()
        vad_result = vad.analyze(audio_data, sample_rate)
        
        # Get VAD segments
        vad_segments = vad_result.get("speech_segments", [])
        
        if not vad_segments:
            logger.warning("No speech segments detected")
            return {
                "segments": [],
                "num_speakers": 0,
                "speakers": [],
                "speaker_times": {},
                "note": "Fallback mode - no speech detected"
            }
        
        # Determine number of speakers
        if num_speakers is not None:
            n_speakers = num_speakers
        elif max_speakers is not None:
            n_speakers = max(2, max_speakers)
        elif min_speakers is not None:
            n_speakers = min_speakers
        else:
            # Default to 1 speaker in fallback mode
            # This is more accurate for most scenarios where pyannote is not installed
            n_speakers = 1
            logger.info("Defaulting to 1 speaker in fallback mode. Use --num-speakers to override.")
        
        # For single speaker mode, assign all segments to speaker_0
        if n_speakers == 1:
            logger.info("Single speaker mode - assigning all speech to speaker_0")
            self.segments = []
            speaker_times = {"speaker_0": {"first": None, "last": None}}
            
            for seg in vad_segments:
                segment = {
                    "start": round(seg["start"], 3),
                    "end": round(seg["end"], 3),
                    "duration": round(seg["duration"], 3),
                    "speaker": "speaker_0"
                }
                self.segments.append(segment)
                
                # Track speaker time ranges
                if speaker_times["speaker_0"]["first"] is None:
                    speaker_times["speaker_0"]["first"] = seg["start"]
                speaker_times["speaker_0"]["last"] = seg["end"]
            
            logger.info(
                "Fallback diarization complete (single speaker)",
                num_segments=len(self.segments)
            )
            
            return {
                "segments": self.segments,
                "num_speakers": 1,
                "speakers": ["speaker_0"],
                "speaker_times": speaker_times,
                "note": "Fallback mode (single speaker) - pyannote.audio not installed"
            }
        
        # For multi-speaker mode, use alternating assignment (simple heuristic)
        # This is the original logic, but with a warning about accuracy
        logger.warning(
            "Multi-speaker fallback mode is UNRELIABLE. "
            "Results may show ~50/50 split even when one person talks 90% of the time. "
            "For accurate speaker separation, install pyannote.audio"
        )
        
        self.segments = []
        speaker_times = {}
        
        for i, seg in enumerate(vad_segments):
            speaker_id = f"speaker_{i % n_speakers}"
            
            segment = {
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "duration": round(seg["duration"], 3),
                "speaker": speaker_id
            }
            self.segments.append(segment)
            
            # Track speaker time ranges
            if speaker_id not in speaker_times:
                speaker_times[speaker_id] = {"first": seg["start"], "last": seg["end"]}
            else:
                speaker_times[speaker_id]["last"] = max(speaker_times[speaker_id]["last"], seg["end"])
        
        # Count unique speakers actually used
        unique_speakers = list(set(seg["speaker"] for seg in self.segments))
        num_unique_speakers = len(unique_speakers)
        
        logger.info(
            "Fallback diarization complete",
            num_segments=len(self.segments),
            num_speakers=num_unique_speakers
        )
        
        return {
            "segments": self.segments,
            "num_speakers": num_unique_speakers,
            "speakers": unique_speakers,
            "speaker_times": speaker_times,
            "note": "Fallback mode - VAD-based segmentation with alternating speaker assignment (UNRELIABLE)"
        }
    
    def get_segments(self) -> List[Dict[str, Any]]:
        """
        Get diarization segments.
        
        Returns:
            List of speaker segments
        """
        return self.segments
    
    def merge_adjacent_segments(
        self,
        segments: List[Dict[str, Any]],
        gap_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Merge adjacent segments from the same speaker.
        
        Args:
            segments: List of segments
            gap_threshold: Maximum gap to merge (seconds)
            
        Returns:
            Merged segments
        """
        if not segments:
            return []
        
        # Sort by start time
        sorted_segments = sorted(segments, key=lambda x: x["start"])
        merged = [sorted_segments[0].copy()]
        
        for segment in sorted_segments[1:]:
            last = merged[-1]
            
            # Check if same speaker and gap is small enough
            if (segment["speaker"] == last["speaker"] and
                segment["start"] - last["end"] <= gap_threshold):
                # Merge segments
                last["end"] = max(last["end"], segment["end"])
                last["duration"] = last["end"] - last["start"]
            else:
                # Add as new segment
                merged.append(segment.copy())
        
        return merged