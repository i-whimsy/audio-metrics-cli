"""
Emotion Analyzer Module
Recognizes emotions in speech using SpeechBrain
"""

import numpy as np
from typing import Dict, Any, Optional
import torch
import torchaudio


class EmotionAnalyzer:
    """Analyze emotions in speech"""
    
    EMOTION_LABELS = [
        'neutral',
        'happy',
        'angry',
        'sad',
        'fear',
        'surprise',
        'disgust'
    ]
    
    def __init__(self, model_name: str = "emotion-recognition-wav2vec2"):
        """
        Initialize emotion analyzer
        
        Args:
            model_name: SpeechBrain model name
        """
        self.model_name = model_name
        self.model = None
        self.classifier = None
        
    def load_model(self):
        """Load SpeechBrain emotion model"""
        try:
            from speechbrain.pretrained import EncoderClassifier
            
            print("Loading SpeechBrain emotion model...")
            self.model = EncoderClassifier.from_hparams(
                source=f"speechbrain/{self.model_name}",
                savedir=f"pretrained_models/{self.model_name}"
            )
            print("Emotion model loaded successfully")
            
        except Exception as e:
            print(f"Warning: Failed to load emotion model: {e}")
            self.model = None
    
    def analyze(
        self,
        audio_path: str,
        segments: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotions in audio
        
        Args:
            audio_path: Path to audio file
            segments: Optional list of segments to analyze
            
        Returns:
            Emotion analysis results
        """
        if self.model is None:
            return self._fallback_analysis()
        
        try:
            # Load audio
            signal, sample_rate = torchaudio.load(audio_path)
            
            # Analyze whole audio or segments
            if segments and len(segments) > 0:
                # Analyze each segment
                segment_emotions = []
                for seg in segments[:10]:  # Limit to 10 segments
                    if 'start' in seg and 'end' in seg:
                        start_sample = int(seg['start'] * sample_rate)
                        end_sample = int(seg['end'] * sample_rate)
                        segment_signal = signal[:, start_sample:end_sample]
                        
                        if len(segment_signal[0]) > 16000:  # At least 1 second
                            emotion = self._classify_emotion(segment_signal, sample_rate)
                            segment_emotions.append({
                                "segment": seg,
                                "emotion": emotion
                            })
                
                # Aggregate emotions
                emotion_counts = {}
                for seg_emotion in segment_emotions:
                    emo = seg_emotion['emotion']['dominant_emotion']
                    emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
                
                # Find dominant emotion
                if emotion_counts:
                    dominant = max(emotion_counts, key=emotion_counts.get)
                    confidence = emotion_counts[dominant] / len(segment_emotions)
                else:
                    dominant = 'neutral'
                    confidence = 0.5
                
                return {
                    "dominant_emotion": dominant,
                    "confidence": round(confidence, 2),
                    "emotion_distribution": {
                        k: round(v / len(segment_emotions), 2)
                        for k, v in emotion_counts.items()
                    },
                    "segment_emotions": segment_emotions,
                    "model": self.model_name
                }
            else:
                # Analyze whole audio
                emotion = self._classify_emotion(signal, sample_rate)
                return {
                    **emotion,
                    "model": self.model_name,
                    "analysis_type": "full_audio"
                }
                
        except Exception as e:
            print(f"Warning: Emotion analysis failed: {e}")
            return self._fallback_analysis(str(e))
    
    def _classify_emotion(
        self,
        signal: torch.Tensor,
        sample_rate: int
    ) -> Dict[str, Any]:
        """
        Classify emotion for a signal
        
        Args:
            signal: Audio signal
            sample_rate: Sample rate
            
        Returns:
            Emotion classification
        """
        try:
            # Get embeddings
            embeddings = self.model.encode_batch(signal)
            
            # Classify emotion
            emotion_probs = self.model.hparams.classifier(embeddings)
            emotion_probs = torch.softmax(emotion_probs, dim=1)
            
            # Get top emotion
            top_prob, top_idx = torch.max(emotion_probs, dim=1)
            
            emotion_label = self.EMOTION_LABELS[top_idx[0]] if top_idx[0] < len(self.EMOTION_LABELS) else 'neutral'
            confidence = top_prob[0].item()
            
            # Get all probabilities
            all_probs = emotion_probs[0].tolist()
            emotion_distribution = {
                self.EMOTION_LABELS[i]: round(prob, 3)
                for i, prob in enumerate(all_probs)
                if i < len(self.EMOTION_LABELS)
            }
            
            return {
                "dominant_emotion": emotion_label,
                "confidence": round(confidence, 3),
                "emotion_probabilities": emotion_distribution
            }
            
        except Exception as e:
            return {
                "dominant_emotion": "neutral",
                "confidence": 0.5,
                "emotion_probabilities": {emo: 0.14 for emo in self.EMOTION_LABELS},
                "error": str(e)
            }
    
    def _fallback_analysis(self, error: str = "") -> Dict[str, Any]:
        """
        Fallback analysis when model unavailable
        
        Returns:
            Fallback emotion results
        """
        return {
            "dominant_emotion": "neutral",
            "confidence": 0.5,
            "emotion_probabilities": {
                emo: round(1.0 / len(self.EMOTION_LABELS), 3)
                for emo in self.EMOTION_LABELS
            },
            "model": None,
            "note": "Fallback analysis (emotion model unavailable)",
            "error": error
        }
