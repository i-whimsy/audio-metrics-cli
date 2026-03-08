"""
Audio Loader Module
Loads audio file and extracts basic information
"""

import os
from pathlib import Path
from typing import Dict, Any
import soundfile as sf
import numpy as np

# Try to import librosa for m4a/mp3 support
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


class AudioLoader:
    """Load audio file and extract metadata"""
    
    def __init__(self, audio_path: str):
        """
        Initialize audio loader
        
        Args:
            audio_path: Path to audio file
        """
        self.audio_path = Path(audio_path)
        self.audio_data = None
        self.sample_rate = None
        self.duration = None
        self.file_size = None
        
    def load(self) -> bool:
        """
        Load audio file
        
        Returns:
            True if successful, False otherwise
        """
        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")
        
        # Get file size
        self.file_size = self.audio_path.stat().st_size
        
        # Load audio data
        # Try soundfile first (for wav files)
        try:
            self.audio_data, self.sample_rate = sf.read(self.audio_path)
        except Exception as e:
            # If soundfile fails, try librosa (for m4a/mp3)
            if HAS_LIBROSA:
                print(f"  Note: Using librosa for {self.audio_path.suffix} format")
                self.audio_data, self.sample_rate = librosa.load(str(self.audio_path), sr=None)
            else:
                raise e
        
        # Calculate duration
        if len(self.audio_data.shape) == 1:
            # Mono
            self.duration = len(self.audio_data) / self.sample_rate
        else:
            # Stereo - convert to mono for analysis
            self.audio_data = np.mean(self.audio_data, axis=1)
            self.duration = len(self.audio_data) / self.sample_rate
        
        return True
    
    def get_audio_info(self) -> Dict[str, Any]:
        """
        Get audio metadata
        
        Returns:
            Dictionary with audio information
        """
        return {
            "file_path": str(self.audio_path.absolute()),
            "file_name": self.audio_path.name,
            "duration_seconds": round(self.duration, 2),
            "sample_rate": self.sample_rate,
            "channels": 1 if len(self.audio_data.shape) == 1 else 2,
            "file_size_bytes": self.file_size,
            "file_size_mb": round(self.file_size / (1024 * 1024), 2)
        }
    
    def get_audio_data(self) -> np.ndarray:
        """
        Get audio data as numpy array
        
        Returns:
            Audio data array
        """
        if self.audio_data is None:
            raise ValueError("Audio not loaded. Call load() first.")
        return self.audio_data
    
    def validate(self, max_duration: int = 3600) -> bool:
        """
        Validate audio file
        
        Args:
            max_duration: Maximum allowed duration in seconds
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If audio is invalid or too long
        """
        if self.duration is None:
            raise ValueError("Audio not loaded")
        
        if self.duration > max_duration:
            raise ValueError(
                f"Audio too long: {self.duration:.1f}s > {max_duration}s"
            )
        
        if self.duration < 1:
            raise ValueError(f"Audio too short: {self.duration:.1f}s")
        
        return True
