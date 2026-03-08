#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
朗读语音包 - 深度分析
包括：音高、VAD、频谱特征、节奏分析
"""

import json
import os
from pathlib import Path
from datetime import datetime
import numpy as np
import librosa

AUDIO_DIR = Path("C:/Users/clawbot/Downloads/朗读语音包")
OUTPUT_DIR = AUDIO_DIR / "analysis_results_deep"
OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac", ".ogg"}


def analyze_deep(audio_file: str, verbose: bool = True) -> dict:
    """深度分析单个音频文件"""
    file_path = Path(audio_file)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"深度分析：{file_path.name}")
        print(f"{'='*70}")
    
    try:
        # 加载完整音频
        if verbose:
            print("[1/5] 加载音频...")
        y, sr = librosa.load(str(audio_file), sr=None)
        duration = len(y) / sr
        
        # 基础信息
        audio_info = {
            "duration_seconds": round(duration, 2),
            "sample_rate": sr,
            "file_size_mb": round(os.path.getsize(audio_file) / 1024 / 1024, 2)
        }
        
        # 音高分析 (F0)
        if verbose:
            print("[2/5] 音高分析...")
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'), 
            sr=sr
        )
        f0_valid = f0[~np.isnan(f0)]
        
        pitch_analysis = {
            "mean_hz": round(float(np.mean(f0_valid)), 1) if len(f0_valid) > 0 else 0,
            "std_hz": round(float(np.std(f0_valid)), 1) if len(f0_valid) > 0 else 0,
            "min_hz": round(float(np.min(f0_valid)), 1) if len(f0_valid) > 0 else 0,
            "max_hz": round(float(np.max(f0_valid)), 1) if len(f0_valid) > 0 else 0,
            "voiced_ratio": round(float(np.mean(voiced_flag)), 3)
        }
        
        if verbose:
            print(f"  平均音高：{pitch_analysis['mean_hz']} Hz")
            print(f"  音高范围：{pitch_analysis['min_hz']} - {pitch_analysis['max_hz']} Hz")
            print(f"  有声占比：{pitch_analysis['voiced_ratio']:.1%}")
        
        # 语音活动检测 (VAD)
        if verbose:
            print("[3/5] 语音活动检测...")
        rms = librosa.feature.rms(y=y)[0]
        threshold = np.mean(rms) * 0.5
        speech_frames = rms > threshold
        speech_ratio = float(np.mean(speech_frames))
        
        # 计算停顿
        pause_count = 0
        in_pause = False
        pause_durations = []
        current_pause = 0
        frame_duration = 0.023  # 约 23ms per frame (默认 hop_length)
        
        for is_speech in speech_frames:
            if not is_speech:
                if not in_pause:
                    pause_count += 1
                    in_pause = True
                current_pause += 1
            else:
                if in_pause:
                    pause_durations.append(current_pause * frame_duration)
                    in_pause = False
                current_pause = 0
        
        vad_analysis = {
            "speech_ratio": round(speech_ratio, 3),
            "pause_count": pause_count,
            "avg_pause_duration_sec": round(np.mean(pause_durations) if pause_durations else 0, 2),
            "total_pause_time_sec": round(sum(pause_durations), 2)
        }
        
        if verbose:
            print(f"  语音占比：{vad_analysis['speech_ratio']:.1%}")
            print(f"  停顿次数：{vad_analysis['pause_count']}")
            print(f"  平均停顿：{vad_analysis['avg_pause_duration_sec']:.2f}秒")
        
        # 频谱特征
        if verbose:
            print("[4/5] 频谱特征...")
        # 频谱质心（亮度）
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        # 频谱带宽
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        # 频谱对比度
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        spectrum_analysis = {
            "centroid_mean_hz": round(float(np.mean(spectral_centroids)), 1),
            "bandwidth_mean_hz": round(float(np.mean(spectral_bandwidth)), 1),
            "contrast_mean_db": round(float(np.mean(spectral_contrast)), 2)
        }
        
        if verbose:
            print(f"  频谱质心：{spectrum_analysis['centroid_mean_hz']} Hz")
            print(f"  频谱带宽：{spectrum_analysis['bandwidth_mean_hz']} Hz")
        
        # 节奏/能量变化
        if verbose:
            print("[5/5] 节奏分析...")
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
        
        # tempo 可能是数组，取第一个值
        tempo_val = float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)
        
        rhythm_analysis = {
            "tempo_bpm": round(tempo_val, 1),
            "onset_strength_mean": round(float(np.mean(onset_strength)), 4),
            "energy_cv": round(float(np.std(rms) / np.mean(rms)), 3) if np.mean(rms) > 0 else 0
        }
        
        if verbose:
            print(f"  估计节奏：{rhythm_analysis['tempo_bpm']} BPM")
            print(f"  能量变异：{rhythm_analysis['energy_cv']:.3f}")
        
        # 综合指标
        metrics = {
            "audio_info": audio_info,
            "pitch_analysis": pitch_analysis,
            "vad_analysis": vad_analysis,
            "spectrum_analysis": spectrum_analysis,
            "rhythm_analysis": rhythm_analysis
        }
        
        # 保存结果
        result_file = OUTPUT_DIR / f"{file_path.stem}_deep.json"
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
    print(f"\n{'='*70}")
    print("深度分析报告")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"成功：{success_count}/{len(results)}")
    
    # 汇总表格
    print(f"\n{'文件名':<15} {'时长':<8} {'音高':<12} {'语音占比':<10} {'停顿':<8} {'节奏'}")
    print("-"*70)
    
    for r in results:
        if r['status'] == 'success':
            m = r['metrics']
            duration = m['audio_info']['duration_seconds']
            pitch = m['pitch_analysis']['mean_hz']
            speech = m['vad_analysis']['speech_ratio']
            pauses = m['vad_analysis']['pause_count']
            tempo = m['rhythm_analysis']['tempo_bpm']
            
            print(f"{r['file']:<15} {duration:<8.1f}秒 {pitch:<12.1f}Hz {speech:<10.1%} {pauses:<8} {tempo:.1f}BPM")
    
    # 保存 JSON
    summary_file = OUTPUT_DIR / "summary_deep.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "total_files": len(results),
            "success_count": success_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    # Markdown 报告
    md_file = OUTPUT_DIR / "summary_deep.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 朗读语音包 - 深度分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## 汇总\n\n")
        f.write(f"| 文件名 | 时长 | 平均音高 | 音高范围 | 语音占比 | 停顿次数 | 节奏 |\n")
        f.write(f"|--------|------|----------|----------|----------|----------|------|\n")
        
        for r in results:
            if r['status'] == 'success':
                m = r['metrics']
                pitch = m['pitch_analysis']
                vad = m['vad_analysis']
                rhythm = m['rhythm_analysis']
                
                f.write(f"| {r['file']} | {m['audio_info']['duration_seconds']:.1f}秒 | ")
                f.write(f"{pitch['mean_hz']:.1f}Hz | {pitch['min_hz']:.0f}-{pitch['max_hz']:.0f}Hz | ")
                f.write(f"{vad['speech_ratio']:.1%} | {vad['pause_count']} | {rhythm['tempo_bpm']:.1f}BPM |\n")
        
        f.write(f"\n## 分析说明\n\n")
        f.write(f"- **平均音高**: 语音的基频 (F0) 平均值，反映声音高低\n")
        f.write(f"- **语音占比**: 有声部分占总时长的比例\n")
        f.write(f"- **停顿次数**: 基于能量阈值检测的停顿/呼吸次数\n")
        f.write(f"- **节奏 (BPM)**: 估计的语速节奏\n")
        f.write(f"- **频谱质心**: 反映声音的明亮度，越高越清脆\n")
    
    print(f"\n[OK] 报告已保存:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")


def main():
    print("="*70)
    print("朗读语音包 - 深度分析")
    print("="*70)
    
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
        result = analyze_deep(f, verbose=True)
        results.append(result)
    
    generate_report(results)
    print("\n[OK] 深度分析完成！")


if __name__ == "__main__":
    main()
