"""
Configuration Module
===================
Configuration management for audio metrics.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WhisperConfig(BaseModel):
    """Whisper model configuration."""
    provider: str = "whisper"
    model: str = "base"
    device: str = "auto"


class VADConfig(BaseModel):
    """Voice Activity Detection configuration."""
    provider: str = "silero"
    threshold: float = 0.5
    sample_rate: int = 16000


class AudioAnalysisConfig(BaseModel):
    """Audio analysis configuration."""
    enable_pitch: bool = True
    enable_energy: bool = True
    enable_pause: bool = True


class FeaturesConfig(BaseModel):
    """Features configuration."""
    enable_emotion: bool = True
    skip_if_too_long: int = 3600  # seconds


class ModelsConfig(BaseModel):
    """Models configuration."""
    speech_to_text: WhisperConfig = Field(default_factory=WhisperConfig)
    vad: VADConfig = Field(default_factory=VADConfig)


class Config(BaseModel):
    """Main configuration class."""
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    audio_analysis: AudioAnalysisConfig = Field(default_factory=AudioAnalysisConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    # Processing options
    max_workers: int = 4
    enable_parallel: bool = True
    retry_attempts: int = 3
    retry_wait: int = 2

    # Output options
    default_output_format: str = "json"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create from dictionary."""
        return cls(**data)


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file or return defaults.

    Args:
        config_path: Path to config file (JSON)

    Returns:
        Configuration instance
    """
    if config_path is None:
        return Config()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Config.from_dict(data)


def merge_configs(base: Config, override: Dict[str, Any]) -> Config:
    """
    Merge override dict into base config.

    Args:
        base: Base configuration
        override: Override dictionary

    Returns:
        Merged configuration
    """
    base_dict = base.to_dict()

    def deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    merged = deep_merge(base_dict, override)
    return Config.from_dict(merged)
