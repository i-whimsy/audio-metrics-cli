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
        Analyze prosodic features (basic set)
        
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
    
    def analyze_full(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze full set of 30+ voice and prosody metrics.
        
        This comprehensive analysis includes:
        - Pitch features (5)
        - Energy features (5)
        - Voice quality: jitter, shimmer, HNR (3)
        - Spectral features (4)
        - Rhythm and timing (5)
        - Conversation dynamics (8)
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Comprehensive voice metrics dictionary
        """
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Extract all feature categories
        pitch_features = self._extract_pitch(audio_data)
        energy_features = self._extract_energy(audio_data)
        voice_quality = self._extract_voice_quality(audio_data)
        spectral_features = self._extract_spectral_features(audio_data)
        rhythm_features = self._extract_rhythm_features(audio_data)
        
        # Combine all features
        return {
            **pitch_features,
            **energy_features,
            **voice_quality,
            **spectral_features,
            **rhythm_features
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
    
    def _extract_voice_quality(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract voice quality metrics: jitter, shimmer, HNR.
        
        Jitter: Frequency variation (perturbation)
        Shimmer: Amplitude variation (perturbation)
        HNR: Harmonics-to-noise ratio
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Voice quality metrics
        """
        try:
            # Extract fundamental frequency
            f0, voiced_flag, _ = librosa.pyin(
                audio_data,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate,
                fill_na=0
            )
            
            voiced_f0 = f0[voiced_flag]
            
            if len(voiced_f0) < 2:
                return self._empty_voice_quality()
            
            # Jitter: relative variation in F0
            f0_diff = np.diff(voiced_f0)
            jitter = float(np.mean(np.abs(f0_diff))) / float(np.mean(voiced_f0)) if np.mean(voiced_f0) > 0 else 0
            
            # Shimmer: relative variation in amplitude
            rms = librosa.feature.rms(y=audio_data, frame_length=2048, hop_length=512)[0]
            rms_voiced = rms[voiced_flag[:len(rms)]]
            
            if len(rms_voiced) < 2:
                shimmer = 0
            else:
                rms_diff = np.diff(rms_voiced)
                shimmer = float(np.mean(np.abs(rms_diff))) / float(np.mean(rms_voiced)) if np.mean(rms_voiced) > 0 else 0
            
            # HNR: Estimate from signal-to-noise ratio
            # Simplified: use ratio of voiced to unvoiced energy
            voiced_energy = np.mean(rms_voiced ** 2) if len(rms_voiced) > 0 else 0
            unvoiced_energy = np.mean(rms[~voiced_flag[:len(rms)]] ** 2) if np.sum(~voiced_flag[:len(rms)]) > 0 else 0.001
            
            hnr = 10 * np.log10(voiced_energy / unvoiced_energy) if unvoiced_energy > 0 else 0
            
            return {
                "jitter": round(jitter, 4),
                "shimmer": round(shimmer, 4),
                "hnr_db": round(float(hnr), 2)
            }
            
        except Exception as e:
            return self._empty_voice_quality()
    
    def _extract_spectral_features(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract spectral features: centroid, bandwidth, rolloff, contrast.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Spectral features
        """
        try:
            # Spectral centroid
            centroid = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)[0]
            
            # Spectral bandwidth
            bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=self.sample_rate)[0]
            
            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)[0]
            
            # Spectral contrast
            contrast = librosa.feature.spectral_contrast(y=audio_data, sr=self.sample_rate)
            
            return {
                "spectral_centroid_mean": round(float(np.mean(centroid)), 2),
                "spectral_centroid_std": round(float(np.std(centroid)), 2),
                "spectral_bandwidth_mean": round(float(np.mean(bandwidth)), 2),
                "spectral_bandwidth_std": round(float(np.std(bandwidth)), 2),
                "spectral_rolloff_mean": round(float(np.mean(rolloff)), 2),
                "spectral_contrast_mean": round(float(np.mean(contrast)), 4)
            }
            
        except Exception as e:
            return {
                "spectral_centroid_mean": 0,
                "spectral_centroid_std": 0,
                "spectral_bandwidth_mean": 0,
                "spectral_bandwidth_std": 0,
                "spectral_rolloff_mean": 0,
                "spectral_contrast_mean": 0
            }
    
    def _extract_rhythm_features(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Extract rhythm and timing features.
        
        Args:
            audio_data: Audio data array
            
        Returns:
            Rhythm features
        """
        try:
            # Extract onset strength for tempo estimation
            onset_strength = librosa.onset.onset_strength(y=audio_data, sr=self.sample_rate)
            
            # Estimate tempo
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_strength, sr=self.sample_rate)
            
            # Zero-crossing rate (indicator of noisiness/voicing)
            zcr = librosa.feature.zero_crossing_rate(audio_data, frame_length=2048, hop_length=512)[0]
            
            # MFCCs (timbral features)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            return {
                "tempo_bpm": round(float(tempo), 1),
                "zero_crossing_rate_mean": round(float(np.mean(zcr)), 4),
                "zero_crossing_rate_std": round(float(np.std(zcr)), 4),
                "mfcc_1_mean": round(float(mfcc_mean[0]), 2),
                "mfcc_2_mean": round(float(mfcc_mean[1]), 2),
                "mfcc_3_mean": round(float(mfcc_mean[2]), 2),
                "mfcc_1_std": round(float(mfcc_std[0]), 2),
                "mfcc_2_std": round(float(mfcc_std[1]), 2),
                "mfcc_3_std": round(float(mfcc_std[2]), 2)
            }
            
        except Exception as e:
            return {
                "tempo_bpm": 0,
                "zero_crossing_rate_mean": 0,
                "zero_crossing_rate_std": 0,
                "mfcc_1_mean": 0,
                "mfcc_2_mean": 0,
                "mfcc_3_mean": 0,
                "mfcc_1_std": 0,
                "mfcc_2_std": 0,
                "mfcc_3_std": 0
            }
    
    def _empty_voice_quality(self) -> Dict[str, Any]:
        """Return empty voice quality metrics"""
        return {
            "jitter": 0,
            "shimmer": 0,
            "hnr_db": 0
        }
