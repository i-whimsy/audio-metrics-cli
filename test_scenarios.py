#!/usr/bin/env python3
"""
Test multiple audio scenarios
"""
import os
import subprocess
from pathlib import Path

audio_dir = Path(r"C:\Users\clawbot\Downloads\AudioTest")
output_dir = Path(r"C:\Users\clawbot\.openclaw\workspace\projects\audio-metrics-cli")

m4a_files = list(audio_dir.rglob("*.m4a"))

print("Found", len(m4a_files), "audio files")

# Select test files
samples = [
    ("CTK-PD.m4a", "sales_sample_60s.m4a"),
    ("GSX-TS.m4a", "phone_sample_60s.m4a"),
]

for src_pattern, dst_name in samples:
    for f in m4a_files:
        if src_pattern in f.name:
            src_file = f
            break
    else:
        print("NOT FOUND:", src_pattern)
        continue
    
    dst_file = output_dir / dst_name
    
    cmd = ["ffmpeg", "-i", str(src_file), "-t", "60", "-c", "copy", "-y", str(dst_file)]
    
    print("Creating", dst_name, "...")
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        print("  OK:", dst_file.name)
    else:
        print("  Failed:", result.stderr[:200])

print()
print("Done. Run these commands:")
print("  python -m audio_metrics.cli_enhanced analyze sales_sample_60s.m4a --output outputs/sales_analysis.json --summary heuristic --show-progress")
print("  python -m audio_metrics.cli_enhanced analyze phone_sample_60s.m4a --output outputs/phone_analysis.json --summary heuristic --show-progress")
