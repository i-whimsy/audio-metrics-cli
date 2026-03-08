"""
Speech to Text Module
Transcribes audio using OpenAI Whisper
"""

import whisper
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path


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
        
    def load_model(self):
        """Load Whisper model"""
        if self.device == "auto":
            self.model = whisper.load_model(self.model_name)
        else:
            self.model = whisper.load_model(self.model_name, device=self.device)
    
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
