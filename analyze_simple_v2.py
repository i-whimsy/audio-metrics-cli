#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超简单音频分析脚本 - 只提取基本信息
"""

import json
import os
from pathlib import Path
from datetime import datetime
import librosa

# 文件目录
AUDIO_DIR = Path("C:/Users/clawbot/Downloads/202407")
OUTPUT_DIR = Path("C:/Users/clawbot/Downloads/202407/analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# 支持的文件格式
SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac", ".ogg"}


def analyze_file(audio_file: str, verbose: bool = True) -> dict:
    """分析单个音频文件"""
    file_path = Path(audio_file)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"分析文件：{file_path.name}")
        print(f"{'='*60}")
    
    try:
        # 加载音频（只获取时长）
        if verbose:
            print("[1/2] 加载音频...")
        # 加载完整音频（移除 duration 限制）
        audio_data, sample_rate = librosa.load(str(audio_file), sr=None)

        # 计算实际时长
        duration_seconds = len(audio_data) / sample_rate
        file_size_mb = os.path.getsize(audio_file) / 1024 / 1024

        audio_info = {
            "duration_seconds": round(duration_seconds, 2),
            "sample_rate": sample_rate,
            "file_size_mb": round(file_size_mb, 2)
        }
        
        if verbose:
            print(f"  [OK] 实际时长：{audio_info['duration_seconds']:.1f}s ({audio_info['duration_seconds']/60:.1f}分钟)")
            print(f"  [OK] 采样率：{audio_info['sample_rate']} Hz")
            print(f"  [OK] 文件大小：{audio_info['file_size_mb']:.1f} MB")
        
        # 简单能量分析
        if verbose:
            print("[2/2] 能量分析...")
        rms = librosa.feature.rms(y=audio_data)[0]
        energy_mean = float(rms.mean())
        energy_std = float(rms.std())
        
        prosody_metrics = {
            "energy_mean": round(energy_mean, 4),
            "energy_std": round(energy_std, 4)
        }
        
        if verbose:
            print(f"  [OK] 平均能量：{prosody_metrics['energy_mean']:.4f}")
        
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
            traceback.print_exc()
        return {
            "file": file_path.name,
            "status": "failed",
            "error": str(e)
        }


def generate_summary_report(results: list):
    """生成汇总报告"""
    print(f"\n{'='*80}")
    print("批量分析汇总报告")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功：{success_count}/{len(results)}")
    
    # 保存汇总报告
    summary_file = OUTPUT_DIR / "summary_report.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "total_files": len(results),
            "success_count": success_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    # Markdown 报告
    md_file = OUTPUT_DIR / "summary_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 音频分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 汇总\n\n")
        f.write(f"- 总文件数：{len(results)}\n")
        f.write(f"- 成功：{success_count}\n\n")
        f.write(f"## 文件列表\n\n")
        f.write(f"| 文件名 | 状态 | 时长 (估算) | 采样率 | 文件大小 |\n")
        f.write(f"|--------|------|-------------|--------|----------|\n")
        
        for result in results:
            if result['status'] == 'success':
                metrics = result['metrics']
                duration = metrics['audio_info']['duration_seconds'] / 60
                sr = metrics['audio_info']['sample_rate']
                size = metrics['audio_info']['file_size_mb']
                f.write(f"| {result['file']} | ✅ | {duration:.1f} 分钟 | {sr} Hz | {size:.1f} MB |\n")
            else:
                f.write(f"| {result['file']} | ❌ | - | - | - |\n")
    
    print(f"\n[OK] 报告已保存:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")


def main():
    """主函数"""
    print("="*80)
    print("Audio Metrics CLI - 超简单分析")
    print("="*80)
    
    # 查找所有支持的音频文件
    audio_files = [
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if not audio_files:
        print(f"[FAIL] 未找到支持的音频文件！")
        return
    
    print(f"找到 {len(audio_files)} 个音频文件\n")
    
    # 批量分析
    results = []
    for audio_file in audio_files:
        result = analyze_file(audio_file, verbose=True)
        results.append(result)
    
    # 生成汇总报告
    generate_summary_report(results)
    print("\n[OK] 完成！")


if __name__ == "__main__":
    main()
