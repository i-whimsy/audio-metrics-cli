"""
Speech to Text Module
Transcribes audio using OpenAI Whisper
"""

import os
import whisper
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core.logger import get_logger

logger = get_logger(__name__)


# Retry decorator for transient failures
def _retry_decorator():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((IOError, OSError)),
        before_sleep=lambda retry_state: logger.warning(
            "STT retry",
            attempt=retry_state.attempt_number,
            remaining=3 - retry_state.attempt_number
        )
    )


class SpeechToText:
    """Transcribe audio to text using Whisper"""
    
    def __init__(self, model_name: str = "base", device: str = "auto"):
        """
        Initialize STT
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cpu, cuda, auto)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.transcript = None
        
    @_retry_decorator()
    def load_model(self):
        """Load Whisper model with offline-first strategy"""
        # Set cache directory
        cache_dir = Path.home() / ".cache" / "whisper"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set offline environment
        os.environ['HF_HUB_OFFLINE'] = '1'
        
        if self.device == "auto":
            self.model = whisper.load_model(
                self.model_name,
                download_root=str(cache_dir)
            )
        else:
            self.model = whisper.load_model(
                self.model_name,
                device=self.device,
                download_root=str(cache_dir)
            )
        
        logger.info("Whisper model loaded", model=self.model_name, device=self.device, cache=str(cache_dir))
    
    @_retry_decorator()
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'zh', 'en')
            task: Task type (transcribe or translate)

        Returns:
            Transcription results
        """
        if self.model is None:
            self.load_model()
        
        # Transcribe
        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False
        )
        
        self.transcript = result
        
        # Calculate word count
        text = result["text"].strip()
        words = text.split()
        
        # Get language
        detected_language = result.get("language", "unknown")
        
        return {
            "text": text,
            "language": detected_language,
            "words_total": len(words),
            "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0,
            "segments": result.get("segments", []),
            "model": self.model_name
        }
    
    def transcribe_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from numpy array
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            language: Language code
            
        Returns:
            Transcription results
        """
        if self.model is None:
            self.load_model()
        
        result = self.model.transcribe(
            audio_data,
            language=language,
            sample_rate=sample_rate,
            verbose=False
        )
        
        self.transcript = result
        
        text = result["text"].strip()
        words = text.split()
        
        return {
            "text": text,
            "language": result.get("language", "unknown"),
            "words_total": len(words),
            "segments": result.get("segments", []),
            "model": self.model_name
        }
    
    def save_transcript(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Save transcript to file
        
        Args:
            audio_path: Original audio path
            output_path: Output file path (optional)
            
        Returns:
            Path to saved transcript
        """
        if self.transcript is None:
            raise ValueError("No transcript available. Call transcribe() first.")
        
        if output_path is None:
            # Generate output path
            audio_file = Path(audio_path)
            output_dir = Path("outputs") / audio_file.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "transcript.txt"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save transcript
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.transcript["text"])
        
        return str(output_path)
    
    def get_segments_with_timestamps(self) -> list:
        """
        Get transcript segments with timestamps
        
        Returns:
            List of segments with start/end times and text
        """
        if self.transcript is None:
            return []
        
        segments = []
        for seg in self.transcript.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"]
            })
        
        return segments
