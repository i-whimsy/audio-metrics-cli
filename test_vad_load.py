#!/usr/bin/env python3
"""Test Silero VAD model loading"""
import torch

print("Testing Silero VAD loading...")
print("Cache directory: ~/.cache/torch/hub/snakers4_silero-vad_master")

try:
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False,
        trust_repo=True
    )
    print("✓ Model loaded successfully!")
    print(f"  Model type: {type(model)}")
    (get_speech_timestamps, _, _, _, _) = utils
    print(f"  Utils loaded: get_speech_timestamps")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
    print("\nTrying force_reload...")
    try:
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=True,
            trust_repo=True
        )
        print("✓ Model loaded with force_reload!")
    except Exception as e2:
        print(f"✗ Force reload also failed: {e2}")
