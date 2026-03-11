"""
Model Configuration - Centralized model loading with offline-first strategy
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from core.logger import get_logger

logger = get_logger(__name__)


class ModelConfig:
    """Centralized model configuration with offline-first strategy"""
    
    # Cache directories
    TORCH_CACHE = Path(os.path.expanduser("~/.cache/torch"))
    WHISPER_CACHE = Path(os.path.expanduser("~/.cache/whisper"))
    HUGGINGFACE_CACHE = Path(os.path.expanduser("~/.cache/huggingface"))
    SPEECHBRAIN_CACHE = Path("pretrained_models")
    
    # Model availability cache
    _model_cache: Dict[str, Any] = {}
    
    @classmethod
    def set_offline_mode(cls):
        """Set environment variables for offline mode"""
        os.environ['HF_HUB_OFFLINE'] = '1'  # HuggingFace offline
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # Transformers offline
        os.environ['TORCH_HOME'] = str(cls.TORCH_CACHE)  # Torch cache location
        logger.info("Offline mode enabled")
    
    @classmethod
    def check_silero_vad(cls) -> bool:
        """Check if Silero VAD model is cached"""
        cache_dir = cls.TORCH_CACHE / "hub" / "snakers4_silero-vad_master" / "src"
        model_files = [
            "silero_vad.jit",
            "silero_vad_16k.safetensors"
        ]
        
        for model_file in model_files:
            if (cache_dir / model_file).exists():
                logger.debug(f"Silero VAD cached: {model_file}")
                return True
        
        logger.warning(f"Silero VAD not found in cache: {cache_dir}")
        return False
    
    @classmethod
    def check_whisper(cls, model_name: str = "base") -> bool:
        """Check if Whisper model is cached"""
        # Whisper stores models in ~/.cache/whisper
        model_file = cls.WHISPER_CACHE / f"{model_name}.pt"
        
        if model_file.exists():
            logger.debug(f"Whisper {model_name} cached")
            return True
        
        # Also check for .ckpt files
        model_file_ckpt = cls.WHISPER_CACHE / f"{model_name}.ckpt"
        if model_file_ckpt.exists():
            logger.debug(f"Whisper {model_name} cached (ckpt)")
            return True
        
        logger.warning(f"Whisper {model_name} not found in cache")
        return False
    
    @classmethod
    def check_pyannote(cls, model_name: str = "pyannote/speaker-diarization-3.1") -> bool:
        """Check if pyannote model is cached"""
        # HuggingFace cache structure
        # ~/.cache/huggingface/hub/models--pyannote--speaker-diarization-3.1/
        model_dir_name = f"models--{model_name.replace('/', '--')}"
        cache_dir = cls.HUGGINGFACE_CACHE / "hub" / model_dir_name
        
        if cache_dir.exists():
            logger.debug(f"Pyannote {model_name} cached")
            return True
        
        logger.warning(f"Pyannote {model_name} not found in cache")
        return False
    
    @classmethod
    def check_speechbrain(cls, model_name: str = "emotion-recognition-wav2vec2") -> bool:
        """Check if SpeechBrain model is cached"""
        cache_dir = cls.SPEECHBRAIN_CACHE / f"speechbrain/{model_name}"
        
        if cache_dir.exists():
            logger.debug(f"SpeechBrain {model_name} cached")
            return True
        
        logger.debug(f"SpeechBrain {model_name} not cached (will download)")
        return False
    
    @classmethod
    def get_model_status(cls) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            "silero_vad": {
                "cached": cls.check_silero_vad(),
                "cache_path": str(cls.TORCH_CACHE / "hub" / "snakers4_silero-vad_master")
            },
            "whisper_base": {
                "cached": cls.check_whisper("base"),
                "cache_path": str(cls.WHISPER_CACHE)
            },
            "whisper_small": {
                "cached": cls.check_whisper("small"),
                "cache_path": str(cls.WHISPER_CACHE)
            },
            "pyannote_diarization": {
                "cached": cls.check_pyannote(),
                "cache_path": str(cls.HUGGINGFACE_CACHE / "hub")
            },
            "speechbrain_emotion": {
                "cached": cls.check_speechbrain(),
                "cache_path": str(cls.SPEECHBRAIN_CACHE)
            }
        }
    
    @classmethod
    def load_silero_vad_offline(cls):
        """Load Silero VAD in offline mode"""
        import torch
        
        # Set offline environment
        cls.set_offline_mode()
        
        # Check cache first
        if not cls.check_silero_vad():
            raise RuntimeError(
                "Silero VAD not cached. Please run: "
                "python -c \"import torch; torch.hub.load('snakers4/silero-vad', 'silero_vad', force_reload=True)\""
            )
        
        # Load from cache
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )
        
        logger.info("Silero VAD loaded from cache")
        return model, utils
    
    @classmethod
    def load_whisper_offline(cls, model_name: str = "base"):
        """Load Whisper in offline mode"""
        import whisper
        
        # Check cache first
        if not cls.check_whisper(model_name):
            logger.warning(f"Whisper {model_name} not cached, will attempt download")
        
        # Load model (Whisper handles its own caching)
        model = whisper.load_model(model_name, download_root=str(cls.WHISPER_CACHE))
        
        logger.info(f"Whisper {model_name} loaded")
        return model
    
    @classmethod
    def load_pyannote_offline(cls, model_name: str = "pyannote/speaker-diarization-3.1"):
        """Load pyannote in offline mode"""
        import torch
        from pyannote.audio import Pipeline
        
        # Set offline environment
        cls.set_offline_mode()
        
        # Check cache first
        if not cls.check_pyannote(model_name):
            logger.warning(f"Pyannote {model_name} not cached, will attempt download")
        
        # Load pipeline
        pipeline = Pipeline.from_pretrained(model_name)
        
        logger.info(f"Pyannote {model_name} loaded")
        return pipeline
    
    @classmethod
    def print_model_status(cls):
        """Print model status to console"""
        print("=" * 60)
        print("Model Cache Status")
        print("=" * 60)
        
        status = cls.get_model_status()
        
        for model_name, info in status.items():
            status_icon = "✓" if info["cached"] else "✗"
            print(f"{status_icon} {model_name}: {'Cached' if info['cached'] else 'Not cached'}")
            if info["cached"]:
                print(f"  Path: {info['cache_path']}")
        
        print("=" * 60)
