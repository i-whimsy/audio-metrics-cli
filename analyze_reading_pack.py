#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
朗读语音包分析
"""

import json
import os
from pathlib import Path
from datetime import datetime
import librosa

AUDIO_DIR = Path("C:/Users/clawbot/Downloads/朗读语音包")
OUTPUT_DIR = AUDIO_DIR / "analysis_results"
OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac", ".ogg"}

def analyze_file(audio_file: str, verbose: bool = True) -> dict:
    """分析单个音频文件"""
    file_path = Path(audio_file)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"分析文件：{file_path.name}")
        print(f"{'='*60}")
    
    try:
        # 加载音频
        if verbose:
            print("[1/2] 加载音频...")
        y, sr = librosa.load(str(audio_file), sr=None)
        duration = len(y) / sr
        file_size_mb = os.path.getsize(audio_file) / 1024 / 1024
        
        audio_info = {
            "duration_seconds": round(duration, 2),
            "duration_minutes": round(duration/60, 2),
            "sample_rate": sr,
            "file_size_mb": round(file_size_mb, 2)
        }
        
        if verbose:
            print(f"  [OK] 时长：{duration:.2f}秒 = {duration/60:.2f}分钟")
            print(f"  [OK] 采样率：{sr} Hz")
            print(f"  [OK] 文件大小：{file_size_mb:.2f} MB")
        
        # 能量分析
        if verbose:
            print("[2/2] 能量分析...")
        rms = librosa.feature.rms(y=y)[0]
        energy_mean = float(rms.mean())
        energy_std = float(rms.std())
        
        prosody_metrics = {
            "energy_mean": round(energy_mean, 4),
            "energy_std": round(energy_std, 4)
        }
        
        if verbose:
            print(f"  [OK] 平均能量：{energy_mean:.4f}")
            print(f"  [OK] 能量标准差：{energy_std:.4f}")
        
        metrics = {
            "audio_info": audio_info,
            "prosody_metrics": prosody_metrics
        }
        
        # 保存结果
        result_file = OUTPUT_DIR / f"{file_path.stem}_analysis.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        if verbose:
            print(f"\n  [OK] 结果已保存：{result_file}")
        
        return {
            "file": file_path.name,
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        import traceback
        if verbose:
            print(f"\n  [FAIL] 分析失败：{e}")
        return {
            "file": file_path.name,
            "status": "failed",
            "error": str(e)
        }


def generate_report(results: list):
    """生成汇总报告"""
    print(f"\n{'='*80}")
    print("朗读语音包 - 分析报告")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功：{success_count}/{len(results)}")
    
    # 表格
    print(f"\n{'文件名':<20} {'时长':<12} {'采样率':<10} {'大小':<10} {'能量'}")
    print("-"*70)
    for r in results:
        if r['status'] == 'success':
            info = r['metrics']['audio_info']
            energy = r['metrics']['prosody_metrics']['energy_mean']
            print(f"{r['file']:<20} {info['duration_minutes']:<12.2f}分钟 {info['sample_rate']:<10} {info['file_size_mb']:<10.2f}MB {energy:.4f}")
    
    # 保存 JSON
    summary_file = OUTPUT_DIR / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "audio_dir": str(AUDIO_DIR),
            "total_files": len(results),
            "success_count": success_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    # Markdown 报告
    md_file = OUTPUT_DIR / "summary.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 朗读语音包分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 汇总\n\n")
        f.write(f"- 总文件数：{len(results)}\n")
        f.write(f"- 成功：{success_count}\n\n")
        f.write(f"## 文件列表\n\n")
        f.write(f"| 文件名 | 时长 | 采样率 | 大小 | 平均能量 |\n")
        f.write(f"|--------|------|--------|------|----------|\n")
        
        for r in results:
            if r['status'] == 'success':
                info = r['metrics']['audio_info']
                energy = r['metrics']['prosody_metrics']['energy_mean']
                f.write(f"| {r['file']} | {info['duration_minutes']:.2f}分钟 | {info['sample_rate']}Hz | {info['file_size_mb']:.2f}MB | {energy:.4f} |\n")
    
    print(f"\n[OK] 报告已保存:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")


def main():
    print("="*80)
    print("朗读语音包分析")
    print("="*80)
    
    audio_files = [
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if not audio_files:
        print(f"[FAIL] 未找到支持的音频文件！")
        return
    
    print(f"找到 {len(audio_files)} 个音频文件\n")
    
    results = []
    for f in sorted(audio_files):
        result = analyze_file(f, verbose=True)
        results.append(result)
    
    generate_report(results)
    print("\n[OK] 完成！")


if __name__ == "__main__":
    main()
