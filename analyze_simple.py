#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版音频分析脚本 - 无需额外依赖
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import librosa
import soundfile as sf
import whisper

# 文件目录
AUDIO_DIR = Path("C:/Users/clawbot/Downloads/202407")
OUTPUT_DIR = Path("C:/Users/clawbot/Downloads/202407/analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# 支持的文件格式
SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac", ".ogg"}

# 填充词列表（中文）
FILLER_WORDS_CN = ["嗯", "呃", "啊", "这个", "那个", "然后", "就是", "其实", "好像", "可能", "大概", "也许"]
FILLER_WORDS_EN = ["um", "uh", "like", "you know", "actually", "basically", "probably", "maybe"]


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
            print("[1/5] 加载音频...")
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
            print("[2/5] 语音活动检测...")
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
        
        # STEP 3: 语音转文本
        if verbose:
            print("[3/5] 语音转文本（使用本地base模型）...")
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_file), language="zh")
        transcript_text = result["text"].strip()
        words = transcript_text.split()
        
        transcript = {
            "text": transcript_text,
            "language": result.get("language", "zh"),
            "words_total": len(words)
        }
        
        if verbose:
            print(f"  [OK] 语言：{transcript['language']}")
            print(f"  [OK] 词数：{transcript['words_total']}")
        
        # STEP 4: 韵律分析
        if verbose:
            print("[4/5] 韵律分析...")
        # 音高分析
        f0, voiced_flag, voiced_prob = librosa.pyin(audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sample_rate)
        f0_valid = f0[~np.isnan(f0)]
        pitch_mean = float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0
        pitch_std = float(np.std(f0_valid)) if len(f0_valid) > 0 else 0
        
        # 能量分析
        energy = rms
        energy_mean = float(np.mean(energy))
        energy_std = float(np.std(energy))
        energy_cv = energy_std / energy_mean if energy_mean > 0 else 0
        
        # 语速
        speech_duration = duration_seconds * speech_ratio
        words_per_minute = len(words) / (speech_duration / 60) if speech_duration > 0 else 0
        
        prosody_metrics = {
            "pitch_mean_hz": round(pitch_mean, 1),
            "pitch_std_hz": round(pitch_std, 1),
            "energy_mean": round(energy_mean, 4),
            "energy_cv": round(energy_cv, 3),
            "words_per_minute": round(words_per_minute, 1)
        }
        
        if verbose:
            print(f"  [OK] 平均音高：{prosody_metrics['pitch_mean_hz']:.1f} Hz")
            print(f"  [OK] 语速：{prosody_metrics['words_per_minute']:.1f} WPM")
        
        # STEP 5: 填充词检测
        if verbose:
            print("[5/5] 填充词检测...")
        filler_count = 0
        for filler in FILLER_WORDS_CN + FILLER_WORDS_EN:
            filler_count += transcript_text.lower().count(filler)
        
        fillers_per_100_words = (filler_count / len(words) * 100) if len(words) > 0 else 0
        
        filler_metrics = {
            "filler_word_count": filler_count,
            "fillers_per_100_words": round(fillers_per_100_words, 1)
        }
        
        if verbose:
            print(f"  [OK] 填充词数：{filler_metrics['filler_word_count']}")
            print(f"  [OK] 频率：{filler_metrics['fillers_per_100_words']:.1f}/100 词")
        
        # 构建综合指标
        metrics = {
            "audio_info": audio_info,
            "vad_analysis": vad_analysis,
            "transcript": transcript,
            "speech_metrics": {
                "words_total": len(words),
                "words_per_minute": prosody_metrics["words_per_minute"]
            },
            "prosody_metrics": prosody_metrics,
            "filler_metrics": filler_metrics
        }
        
        # 保存结果
        result_file = OUTPUT_DIR / f"{file_path.stem}_analysis.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        # 保存转录文本
        transcript_file = OUTPUT_DIR / f"{file_path.stem}_transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        if verbose:
            print(f"\n  [OK] 结果已保存:")
            print(f"    - {result_file}")
            print(f"    - {transcript_file}")
        
        return {
            "file": file_path.name,
            "status": "success",
            "metrics": metrics,
            "transcript_length": len(transcript_text)
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
    
    print(f"\n{'文件名':<45} {'时长 (分钟)':<12} {'语速 (WPM)':<12} {'填充词/100 词':<15} {'语音占比'}")
    print("-" * 100)
    
    for result in results:
        if result['status'] == 'success':
            metrics = result['metrics']
            file_name = result['file'][:43] + "..." if len(result['file']) > 45 else result['file']
            duration_min = metrics['audio_info']['duration_seconds'] / 60
            wpm = metrics['speech_metrics']['words_per_minute']
            fillers = metrics['filler_metrics']['fillers_per_100_words']
            speech_ratio = metrics['vad_analysis']['speech_ratio']
            
            print(f"{file_name:<45} {duration_min:<12.1f} {wpm:<12.1f} {fillers:<15.1f} {speech_ratio:.1%}")
    
    # 保存汇总报告
    summary_file = OUTPUT_DIR / "summary_report.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_time": datetime.now().isoformat(),
            "audio_dir": str(AUDIO_DIR),
            "output_dir": str(OUTPUT_DIR),
            "total_files": len(results),
            "success_count": success_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    md_file = OUTPUT_DIR / "summary_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 音频分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**文件目录**: `{AUDIO_DIR}`\n\n")
        f.write(f"**输出目录**: `{OUTPUT_DIR}`\n\n")
        f.write(f"## 汇总\n\n")
        f.write(f"- 总文件数：{len(results)}\n")
        f.write(f"- 成功：{success_count}\n")
        f.write(f"- 失败：{len(results) - success_count}\n\n")
        f.write(f"## 详细统计\n\n")
        f.write(f"| 文件名 | 时长 (分钟) | 语速 (WPM) | 填充词/100 词 | 语音占比 |\n")
        f.write(f"|--------|-------------|------------|---------------|----------|\n")
        
        for result in results:
            if result['status'] == 'success':
                metrics = result['metrics']
                file_name = result['file']
                duration_min = metrics['audio_info']['duration_seconds'] / 60
                wpm = metrics['speech_metrics']['words_per_minute']
                fillers = metrics['filler_metrics']['fillers_per_100_words']
                speech_ratio = metrics['vad_analysis']['speech_ratio']
                
                f.write(f"| {file_name} | {duration_min:.1f} | {wpm:.1f} | {fillers:.1f} | {speech_ratio:.1%} |\n")
    
    print(f"\n[OK] 汇总报告已保存:")
    print(f"  - {summary_file}")
    print(f"  - {md_file}")
    print(f"{'='*80}")


def main():
    """主函数"""
    print("="*80)
    print("Audio Metrics CLI - 批量分析工具（简化版）")
    print("="*80)
    
    # 查找所有支持的音频文件
    audio_files = [
        f for f in AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if not audio_files:
        print(f"❌ 未找到支持的音频文件！")
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
    
    print("\n🎉 批量分析完成！")


if __name__ == "__main__":
    main()
