"""
Prosody Analyzer Module
Extracts pitch, energy, and other prosodic features
"""

import numpy as np
from typing import Dict, Any
import librosa


class ProsodyAnalyzer:
    """Analyze prosodic features of speech"""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize prosody analyzer
        
        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        
    def analyze(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze prosodic features
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Prosody analysis results
        """
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Extract features
        pitch_features = self._extract_pitch(audio_data)
        energy_features = self._extract_energy(audio_data)
        
        return {
            **pitch_features,
            **energy_features
        }
    
    def _extract_pitch(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract pitch (F0) features using YIN algorithm
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Pitch features
        """
        try:
            # Extract fundamental frequency using YIN
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio_data,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate,
                fill_na=0
            )
            
            # Filter out unvoiced frames
            voiced_f0 = f0[voiced_flag]
            
            if len(voiced_f0) > 0:
                pitch_mean = float(np.mean(voiced_f0))
                pitch_std = float(np.std(voiced_f0))
                pitch_min = float(np.min(voiced_f0))
                pitch_max = float(np.max(voiced_f0))
                pitch_range = pitch_max - pitch_min
            else:
                pitch_mean = pitch_std = pitch_min = pitch_max = pitch_range = 0.0
            
            return {
                "pitch_mean_hz": round(pitch_mean, 2),
                "pitch_std_hz": round(pitch_std, 2),
                "pitch_min_hz": round(pitch_min, 2),
                "pitch_max_hz": round(pitch_max, 2),
                "pitch_range_hz": round(pitch_range, 2),
                "voiced_ratio": round(float(np.mean(voiced_flag)), 3)
            }
            
        except Exception as e:
            print(f"Warning: Pitch extraction failed: {e}")
            return {
                "pitch_mean_hz": 0,
                "pitch_std_hz": 0,
                "pitch_min_hz": 0,
                "pitch_max_hz": 0,
                "pitch_range_hz": 0,
                "voiced_ratio": 0,
                "error": str(e)
            }
    
    def _extract_energy(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract energy (RMS) features
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Energy features
        """
        try:
            # Extract RMS energy
            rms = librosa.feature.rms(y=audio_data, frame_length=2048, hop_length=512)[0]
            
            energy_mean = float(np.mean(rms))
            energy_std = float(np.std(rms))
            energy_min = float(np.min(rms))
            energy_max = float(np.max(rms))
            energy_dynamic_range = energy_max - energy_min
            
            # Calculate energy variation coefficient
            energy_cv = energy_std / energy_mean if energy_mean > 0 else 0
            
            return {
                "energy_mean": round(energy_mean, 4),
                "energy_std": round(energy_std, 4),
                "energy_min": round(energy_min, 4),
                "energy_max": round(energy_max, 4),
                "energy_dynamic_range": round(energy_dynamic_range, 4),
                "energy_cv": round(energy_cv, 3)
            }
            
        except Exception as e:
            print(f"Warning: Energy extraction failed: {e}")
            return {
                "energy_mean": 0,
                "energy_std": 0,
                "energy_min": 0,
                "energy_max": 0,
                "energy_dynamic_range": 0,
                "energy_cv": 0,
                "error": str(e)
            }
    
    def calculate_speech_rate(
        self,
        transcript: str,
        audio_duration: float
    ) -> Dict[str, Any]:
        """
        Calculate speech rate metrics
        
        Args:
            transcript: Transcribed text
            audio_duration: Audio duration in seconds
            
        Returns:
            Speech rate metrics
        """
        if not transcript or audio_duration <= 0:
            return {
                "words_total": 0,
                "words_per_minute": 0,
                "syllables_per_second": 0
            }
        
        # Count words
        words = transcript.split()
        words_total = len(words)
        
        # Calculate WPM
        words_per_minute = (words_total / audio_duration) * 60
        
        # Estimate syllables (simple heuristic for Chinese/English)
        # For Chinese: assume 1 char = 1 syllable
        # For English: count vowels
        syllables = 0
        for word in words:
            if any('\u4e00' <= c <= '\u9fff' for c in word):
                # Chinese text
                syllables += len([c for c in word if '\u4e00' <= c <= '\u9fff'])
            else:
                # English text - count vowel groups
                vowels = 'aeiouAEIOU'
                prev_vowel = False
                for char in word:
                    is_vowel = char in vowels
                    if is_vowel and not prev_vowel:
                        syllables += 1
                    prev_vowel = is_vowel
                if syllables == 0:
                    syllables += 1  # At least one syllable per word
        
        syllables_per_second = syllables / audio_duration
        
        return {
            "words_total": words_total,
            "words_per_minute": round(words_per_minute, 1),
            "syllables_total": syllables,
            "syllables_per_second": round(syllables_per_second, 2)
        }
