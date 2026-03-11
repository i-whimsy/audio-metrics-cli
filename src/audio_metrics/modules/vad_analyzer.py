"""
VAD (Voice Activity Detection) Analyzer Module
Detects speech segments and silence periods using Silero VAD
"""

import os
import numpy as np
from typing import Dict, Any, List, Tuple
from pathlib import Path
import torch
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
            "VAD retry",
            attempt=retry_state.attempt_number,
            remaining=3 - retry_state.attempt_number
        )
    )


class VADAnalyzer:
    """Analyze voice activity in audio"""
    
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        """
        Initialize VAD analyzer
        
        Args:
            threshold: VAD threshold (0-1)
            sample_rate: Audio sample rate
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.model = None
        self.speech_segments = []
        
    @_retry_decorator()
    def load_model(self):
        """Load Silero VAD model with offline-first strategy"""
        try:
            # Set offline environment variables
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['TORCH_HOME'] = str(Path.home() / ".cache" / "torch")
            
            # Load from cache (force_reload=False means use cache if available)
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,  # Use cached version
                trust_repo=True,
                verbose=False  # Suppress verbose output
            )
            (get_speech_timestamps, _, _, _, _) = utils
            self.get_speech_timestamps = get_speech_timestamps
            logger.info("Silero VAD model loaded from cache")
        except Exception as e:
            logger.warning("Failed to load Silero VAD", error=str(e))
            self.model = None
    
    def analyze(self, audio_data: np.ndarray, original_sr: int = None) -> Dict[str, Any]:
        """
        Analyze voice activity
        
        Args:
            audio_data: Audio data array
            original_sr: Original sample rate (if already known)
            
        Returns:
            VAD analysis results
        """
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Store original sample rate
        if original_sr:
            orig_sample_rate = original_sr
        else:
            orig_sample_rate = self.sample_rate
        
        # Resample to 16kHz if needed (Silero requirement)
        if orig_sample_rate != 16000:
            # Simple resampling
            num_samples = int(len(audio_data) * 16000 / orig_sample_rate)
            audio_data_16k = np.interp(
                np.linspace(0, len(audio_data), num_samples),
                np.arange(len(audio_data)),
                audio_data
            )
        else:
            audio_data_16k = audio_data
        
        # Load model if not loaded
        if self.model is None:
            self.load_model()
        
        # Detect speech segments
        if self.model is not None:
            try:
                audio_tensor = torch.from_numpy(audio_data_16k).float()
                speech_timestamps = self.get_speech_timestamps(
                    audio_tensor,
                    self.model,
                    threshold=self.threshold,
                    sampling_rate=16000
                )
                
                # Convert to seconds (using 16k sample rate)
                self.speech_segments = []
                total_speech = 0
                total_silence = 0
                pause_durations = []
                
                prev_end = 0
                for segment in speech_timestamps:
                    start = segment['start'] / 16000
                    end = segment['end'] / 16000
                    
                    self.speech_segments.append({
                        'start': start,
                        'end': end,
                        'duration': end - start
                    })
                    
                    total_speech += (end - start)
                    
                    # Calculate silence before this segment
                    if start > prev_end:
                        silence_duration = start - prev_end
                        total_silence += silence_duration
                        if silence_duration > 0.5:  # Count pauses > 0.5s
                            pause_durations.append(silence_duration)
                    
                    prev_end = end
                
                # Calculate silence after last segment
                audio_duration_16k = len(audio_data_16k) / 16000
                if prev_end < audio_duration_16k:
                    total_silence += (audio_duration_16k - prev_end)
                
            except Exception as e:
                print(f"Warning: VAD analysis failed: {e}")
                return self._fallback_analysis(audio_data, orig_sample_rate)
        else:
            return self._fallback_analysis(audio_data, orig_sample_rate)
        
        # Calculate metrics using ORIGINAL duration
        audio_duration = len(audio_data) / orig_sample_rate
        speech_ratio = total_speech / audio_duration if audio_duration > 0 else 0
        avg_pause = sum(pause_durations) / len(pause_durations) if pause_durations else 0
        long_pauses = sum(1 for p in pause_durations if p > 2.0)
        
        return {
            "speech_segments": self.speech_segments,
            "speech_duration": round(total_speech, 2),
            "silence_duration": round(total_silence, 2),
            "speech_ratio": round(speech_ratio, 2),
            "pause_count": len(pause_durations),
            "avg_pause_duration": round(avg_pause, 2),
            "long_pause_count": long_pauses
        }
    
    def _fallback_analysis(self, audio_data: np.ndarray, orig_sample_rate: int = None) -> Dict[str, Any]:
        """
        Fallback analysis when VAD model unavailable
        
        Uses simple energy-based detection
        """
        sr = orig_sample_rate if orig_sample_rate else self.sample_rate
        
        # Calculate energy envelope
        frame_size = int(sr * 0.03)  # 30ms frames
        hop_size = int(sr * 0.01)    # 10ms hop
        
        energy = []
        for i in range(0, len(audio_data) - frame_size, hop_size):
            frame = audio_data[i:i + frame_size]
            energy.append(np.mean(frame ** 2))
        
        # Simple thresholding
        threshold = np.mean(energy) * 0.5
        speech_frames = sum(1 for e in energy if e > threshold)
        
        total_frames = len(energy)
        speech_ratio = speech_frames / total_frames if total_frames > 0 else 0
        audio_duration = len(audio_data) / sr
        
        return {
            "speech_segments": [],
            "speech_duration": round(speech_ratio * audio_duration, 2),
            "silence_duration": round((1 - speech_ratio) * audio_duration, 2),
            "speech_ratio": round(speech_ratio, 2),
            "pause_count": 0,
            "avg_pause_duration": 0,
            "long_pause_count": 0,
            "note": "Fallback analysis (VAD model unavailable)"
        }
