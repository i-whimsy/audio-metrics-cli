"""
Model Manager Module
===================
Centralized model loading and caching.
"""

from typing import Any, Dict, Optional
import threading

from .logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Singleton model manager for caching and sharing loaded models.

    This prevents loading the same model multiple times, reducing memory
    usage and improving performance.
    """

    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the model manager."""
        if self._initialized:
            return
        self._models: Dict[str, Any] = {}
        self._model_lock = threading.Lock()
        self._initialized = True
        logger.info("ModelManager initialized")

    def get_model(
        self,
        model_type: str,
        loader_fn: callable,
        **kwargs
    ) -> Any:
        """
        Get a model from cache or load it.

        Args:
            model_type: Unique identifier for the model type
            loader_fn: Function to load the model if not cached
            **kwargs: Additional arguments for the loader function

        Returns:
            The model instance
        """
        cache_key = self._make_key(model_type, kwargs)

        if cache_key in self._models:
            logger.debug(f"Model cache hit: {cache_key}")
            return self._models[cache_key]

        with self._model_lock:
            # Double-check after acquiring lock
            if cache_key in self._models:
                return self._models[cache_key]

            logger.info(f"Loading model: {cache_key}")
            model = loader_fn(**kwargs)
            self._models[cache_key] = model
            logger.info(f"Model loaded and cached: {cache_key}")
            return model

    def preload_models(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """
        Preload multiple models.

        Args:
            configs: Dictionary of model configurations
                {
                    "whisper": {"loader": fn, "kwargs": {...}},
                    "vad": {"loader": fn, "kwargs": {...}},
                    ...
                }
        """
        for model_name, config in configs.items():
            loader_fn = config.get("loader")
            kwargs = config.get("kwargs", {})
            if loader_fn:
                self.get_model(model_name, loader_fn, **kwargs)

    def unload_model(self, model_type: str, **kwargs) -> bool:
        """
        Unload a specific model from cache.

        Args:
            model_type: Model type identifier
            **kwargs: Model configuration kwargs

        Returns:
            True if model was unloaded, False if not found
        """
        cache_key = self._make_key(model_type, kwargs)

        with self._model_lock:
            if cache_key in self._models:
                del self._models[cache_key]
                logger.info(f"Model unloaded: {cache_key}")
                return True
        return False

    def clear_cache(self) -> None:
        """Clear all cached models."""
        with self._model_lock:
            count = len(self._models)
            self._models.clear()
            logger.info(f"Model cache cleared ({count} models released)")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached models.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_models": list(self._models.keys()),
            "cache_size": len(self._models),
        }

    @staticmethod
    def _make_key(model_type: str, kwargs: Dict[str, Any]) -> str:
        """
        Create a unique cache key from model type and kwargs.

        Args:
            model_type: Model type identifier
            kwargs: Model configuration

        Returns:
            Cache key string
        """
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = "-".join(f"{k}={v}" for k, v in sorted_kwargs)
        return f"{model_type}:{kwargs_str}" if kwargs_str else model_type


# Global instance accessor
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """
    Get the global ModelManager instance.

    Returns:
        ModelManager singleton
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
