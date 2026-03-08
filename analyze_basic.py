#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础版音频分析脚本 - 不依赖 Whisper（网络问题）
只进行音频特征分析
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import librosa
import soundfile as sf

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
        # STEP 1: 加载音频
        if verbose:
            print("[1/3] 加载音频...")
        audio_data, sample_rate = librosa.load(str(audio_file), sr=None)
        duration_seconds = len(audio_data) / sample_rate
        file_size_mb = os.path.getsize(audio_file) / 1024 / 1024
        
        audio_info = {
            "duration_seconds": round(duration_seconds, 2),
            "sample_rate": sample_rate,
            "file_size_mb": round(file_size_mb, 2),
            "channels": 1 if len(audio_data.shape) == 1 else audio_data.shape[0]
        }
        
        if verbose:
            print(f"  [OK] 时长：{audio_info['duration_seconds']:.1f}s ({audio_info['duration_seconds']/60:.1f}分钟)")
            print(f"  [OK] 采样率：{audio_info['sample_rate']} Hz")
            print(f"  [OK] 文件大小：{audio_info['file_size_mb']:.1f} MB")
        
        # STEP 2: 语音活动检测（简化版 - 基于能量）
        if verbose:
            print("[2/3] 语音活动检测...")
        rms = librosa.feature.rms(y=audio_data)[0]
        threshold = np.mean(rms) * 0.5
        speech_frames = rms > threshold
        speech_ratio = float(np.mean(speech_frames))
        
        # 计算停顿
        pause_count = 0
        in_pause = False
        for is_speech in speech_frames:
            if not is_speech and not in_pause:
                pause_count += 1
                in_pause = True
            elif is_speech:
                in_pause = False
        
        vad_analysis = {
            "speech_ratio": round(speech_ratio, 3),
            "pause_count": pause_count,
            "avg_pause_duration": round((1 - speech_ratio) * duration_seconds / max(pause_count, 1), 2)
        }
        
        if verbose:
            print(f"  [OK] 语音占比：{vad_analysis['speech_ratio']:.1%}")
            print(f"  [OK] 停顿次数：{vad_analysis['pause_count']}")
        
        # STEP 3: 韵律分析
        if verbose:
            print("[3/3] 韵律分析...")
        
        # 音高分析
        f0, voiced_flag, voiced_prob = librosa.pyin(
            audio_data, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'), 
            sr=sample_rate
        )
        f0_valid = f0[~np.isnan(f0)]
        pitch_mean = float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0
        pitch_std = float(np.std(f0_valid)) if len(f0_valid) > 0 else 0
        
        # 能量分析
        energy = rms
        energy_mean = float(np.mean(energy))
        energy_std = float(np.std(energy))
        energy_cv = energy_std / energy_mean if energy_mean > 0 else 0
        
        # 估算语速（基于能量峰值变化）
        energy_changes = np.diff(energy)
        speech_rate_estimate = float(np.mean(np.abs(energy_changes)) * 1000)
        
        prosody_metrics = {
            "pitch_mean_hz": round(pitch_mean, 1),
            "pitch_std_hz": round(pitch_std, 1),
            "energy_mean": round(energy_mean, 4),
            "energy_cv": round(energy_cv, 3),
            "speech_rate_estimate": round(speech_rate_estimate, 2)
        }
        
        if verbose:
            print(f"  [OK] 平均音高：{prosody_metrics['pitch_mean_hz']:.1f} Hz")
            print(f"  [OK] 能量变异系数：{prosody_metrics['energy_cv']:.3f}")
        
        # 构建综合指标
        metrics = {
            "audio_info": audio_info,
            "vad_analysis": vad_analysis,
            "prosody_metrics": prosody_metrics,
            "note": "基础分析（无转录）- 因网络问题跳过 Whisper"
        }
        
        # 保存结果
        result_file = OUTPUT_DIR / f"{file_path.stem}_basic_analysis.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        if verbose:
            print(f"\n  [OK] 结果已保存: {result_file}")
        
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
    print("批量分析汇总报告（基础版）")
    print(f"{'='*80}")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"文件目录：{AUDIO_DIR}")
    print(f"输出目录：{OUTPUT_DIR}")
    print(f"\n总文件数：{len(results)}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功：{success_count}")
    print(f"失败：{len(results) - success_count}")
    
    # 详细统计
    print(f"\n{'='*80}")
    print("详细统计")
    print(f"{'='*80}")
    
    print(f"\n{'文件名':<50} {'时长 (分钟)':<12} {'语音占比':<12} {'平均音高 (Hz)'}")
    print("-" * 90)
    
    for result in results:
        if result['status'] == 'success':
            metrics = result['metrics']
            file_name = result['file'][:48] + "..." if len(result['file']) > 50 else result['file']
            duration_min = metrics['audio_info']['duration_seconds'] / 60
            speech_ratio = metrics['vad_analysis']['speech_ratio']
            pitch = metrics['prosody_metrics']['pitch_mean_hz']
            
            print(f"{file_name:<50} {duration_min:<12.1f} {speech_ratio:<12.1%} {pitch:.1f}")
    
    # 保存汇总报告
    summary_file = OUTPUT_DIR / "summary_report.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "audio_dir": str(AUDIO_DIR),
            "output_dir": str(OUTPUT_DIR),
            "total_files": len(results),
            "success_count": success_count,
            "results": results,
            "note": "基础分析（无转录）"
        }, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    md_file = OUTPUT_DIR / "summary_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 音频分析报告（基础版）\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**文件目录**: `{AUDIO_DIR}`\n\n")
        f.write(f"**输出目录**: `{OUTPUT_DIR}`\n\n")
        f.write(f"**备注**: 基础分析（无转录）- 因网络问题跳过 Whisper\n\n")
        f.write(f"## 汇总\n\n")
        f.write(f"- 总文件数：{len(results)}\n")
        f.write(f"- 成功：{success_count}\n")
        f.write(f"- 失败：{len(results) - success_count}\n\n")
        f.write(f"## 详细统计\n\n")
        f.write(f"| 文件名 | 时长 (分钟) | 语音占比 | 平均音高 (Hz) |\n")
        f.write(f"|--------|-------------|----------|---------------|\n")
        
        for result in results:
            if result['status'] == 'success':
                metrics = result['metrics']
                file_name = result['file']
                duration_min = metrics['audio_info']['duration_seconds'] / 60
                speech_ratio = metrics['vad_analysis']['speech_ratio']
                pitch = metrics['prosody_metrics']['pitch_mean_hz']
                
                f.write(f"| {file_name} | {duration_min:.1f} | {speech_ratio:.1%} | {pitch:.1f} |\n")
        
        f.write(f"\n## 分析说明\n\n")
        f.write(f"- **语音占比**: 基于能量阈值计算的语音活动比例\n")
        f.write(f"- **平均音高**: 使用 librosa pyin 算法提取的基频 F0 平均值\n")
        f.write(f"- **能量变异系数**: 衡量语音信号的能量变化程度\n\n")
        f.write(f"> 注意：由于网络问题，无法使用 Whisper 进行语音转文本分析。\n")
    
    print(f"\n[OK] 汇总报告已保存:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")
    print(f"{'='*80}")


def main():
    """主函数"""
    print("="*80)
    print("Audio Metrics CLI - 批量分析工具（基础版）")
    print("="*80)
    
    # 查找所有支持的音频文件
    audio_files = [
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if not audio_files:
        print(f"[FAIL] 未找到支持的音频文件！")
        print(f"支持的格式：{SUPPORTED_FORMATS}")
        return
    
    print(f"找到 {len(audio_files)} 个音频文件:")
    for f in audio_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 批量分析
    results = []
    for audio_file in audio_files:
        result = analyze_file(audio_file, verbose=True)
        results.append(result)
    
    # 生成汇总报告
    generate_summary_report(results)
    
    print("\n[OK] 批量分析完成！")


if __name__ == "__main__":
    main()