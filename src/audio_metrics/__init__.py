"""
Audio Metrics CLI - Cross-platform audio analysis toolkit

Extract objective speech metrics from audio files.
Output structured JSON for further analysis.
"""

__version__ = "0.1.0"
__author__ = "OpenClaw"
__email__ = "clawbot@openclaw.ai"

from .cli import main

__all__ = ["main"]
