#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
准确的音频时长分析
"""

import json
import os
from pathlib import Path
from datetime import datetime
import librosa

AUDIO_DIR = Path("C:/Users/clawbot/Downloads/202407")
OUTPUT_DIR = Path("C:/Users/clawbot/Downloads/202407/analysis_results")

SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac", ".ogg"}

def get_duration(audio_file):
    """获取实际时长"""
    y, sr = librosa.load(str(audio_file), sr=None)
    duration = len(y) / sr
    return duration, sr

def main():
    print("="*80)
    print("音频时长重新分析")
    print("="*80)
    
    audio_files = [f for f in AUDIO_DIR.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]
    
    results = []
    for f in sorted(audio_files):
        print(f"\n分析：{f.name}")
        duration, sr = get_duration(f)
        size_mb = f.stat().st_size / 1024 / 1024
        
        print(f"  实际时长：{duration:.2f}秒 = {duration/60:.2f}分钟")
        print(f"  采样率：{sr} Hz")
        print(f"  文件大小：{size_mb:.2f} MB")
        
        results.append({
            "file": f.name,
            "duration_seconds": round(duration, 2),
            "duration_minutes": round(duration/60, 2),
            "sample_rate": sr,
            "file_size_mb": round(size_mb, 2)
        })
    
    # 保存结果
    output_file = OUTPUT_DIR / "accurate_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "files": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存：{output_file}")
    
    # 打印汇总表格
    print("\n" + "="*80)
    print("汇总表格")
    print("="*80)
    print(f"\n{'文件名':<45} {'时长':<12} {'采样率':<10} {'大小'}")
    print("-"*80)
    for r in results:
        print(f"{r['file']:<45} {r['duration_minutes']:<12.2f}分钟 {r['sample_rate']:<10} {r['file_size_mb']:.1f} MB")

if __name__ == "__main__":
    main()
