#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量分析音频文件
生成综合报告
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 添加路径
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio_metrics.modules.audio_loader import AudioLoader
from audio_metrics.modules.vad_analyzer import VADAnalyzer
from audio_metrics.modules.speech_to_text import SpeechToText
from audio_metrics.modules.prosody_analyzer import ProsodyAnalyzer
from audio_metrics.modules.filler_detector import FillerDetector
from audio_metrics.modules.metrics_builder import MetricsBuilder
from audio_metrics.modules.json_exporter import JSONExporter

# 文件目录
AUDIO_DIR = Path("C:/Users/clawbot/Downloads/202407")
OUTPUT_DIR = Path("C:/Users/clawbot/Downloads/202407/analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# 支持的文件格式
SUPPORTED_FORMATS = {".mp4", ".m4a", ".wav", ".mp3", ".flac"}

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
            print("[1/6] 加载音频...")
        loader = AudioLoader(str(audio_file))
        loader.load()
        loader.validate(max_duration=7200)  # 支持最长 2 小时
        audio_info = loader.get_audio_info()
        
        if verbose:
            print(f"  ✓ 时长：{audio_info['duration_seconds']:.1f}s ({audio_info['duration_seconds']/60:.1f}分钟)")
            print(f"  ✓ 采样率：{audio_info['sample_rate']} Hz")
            print(f"  ✓ 文件大小：{audio_info['file_size_mb']:.1f} MB")
        
        # STEP 2: VAD 分析
        if verbose:
            print("[2/6] 语音活动检测...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(loader.get_audio_data())
        
        if verbose:
            print(f"  ✓ 语音占比：{vad_analysis['speech_ratio']:.1%}")
            print(f"  ✓ 停顿次数：{vad_analysis['pause_count']}")
        
        # STEP 3: 语音转文本
        if verbose:
            print("[3/6] 语音转文本...")
        stt = SpeechToText(model_name="base")
        transcript = stt.transcribe(str(audio_file))
        
        if verbose:
            print(f"  ✓ 语言：{transcript['language']}")
            print(f"  ✓ 词数：{transcript['words_total']}")
        
        # STEP 4: 韵律分析
        if verbose:
            print("[4/6] 韵律分析...")
        prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
        prosody_metrics = prosody.analyze(loader.get_audio_data())
        speech_rate = prosody.calculate_speech_rate(transcript['text'], audio_info['duration_seconds'])
        prosody_metrics.update(speech_rate)
        
        if verbose:
            print(f"  ✓ 平均音高：{prosody_metrics['pitch_mean_hz']:.1f} Hz")
            print(f"  ✓ 语速：{prosody_metrics['words_per_minute']:.1f} WPM")
        
        # STEP 5: 填充词检测
        if verbose:
            print("[5/6] 填充词检测...")
        filler = FillerDetector(language=transcript.get('language', 'zh'))
        filler_metrics = filler.detect(transcript['text'])
        
        if verbose:
            print(f"  ✓ 填充词数：{filler_metrics['filler_word_count']}")
            print(f"  ✓ 频率：{filler_metrics['fillers_per_100_words']:.1f}/100 词")
        
        # STEP 6: 构建指标
        if verbose:
            print("[6/6] 构建综合指标...")
        builder = MetricsBuilder()
        metrics = builder.build(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript,
            prosody_metrics=prosody_metrics,
            emotion_metrics={"dominant_emotion": "neutral", "confidence": 0.5},
            filler_metrics=filler_metrics
        )
        
        # 保存结果
        result_file = OUTPUT_DIR / f"{file_path.stem}_analysis.json"
        exporter = JSONExporter()
        exporter.export(metrics, str(result_file))
        
        # 保存转录文本
        transcript_file = OUTPUT_DIR / f"{file_path.stem}_transcript.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript['text'])
        
        if verbose:
            print(f"\n  ✓ 结果已保存:")
            print(f"    - {result_file}")
            print(f"    - {transcript_file}")
        
        return {
            "file": file_path.name,
            "status": "success",
            "metrics": metrics,
            "transcript_length": len(transcript['text'])
        }
        
    except Exception as e:
        if verbose:
            print(f"\n  ✗ 分析失败：{e}")
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
    
    print(f"\n{'文件名':<40} {'时长 (分钟)':<12} {'语速 (WPM)':<12} {'填充词/100 词':<15} {'语音占比'}")
    print("-" * 100)
    
    for result in results:
        if result['status'] == 'success':
            metrics = result['metrics']
            file_name = result['file'][:38] + "..." if len(result['file']) > 40 else result['file']
            duration_min = metrics['audio_info']['duration_seconds'] / 60
            wpm = metrics['speech_metrics']['words_per_minute']
            fillers = metrics['filler_metrics']['fillers_per_100_words']
            speech_ratio = metrics['vad_analysis']['speech_ratio']
            
            print(f"{file_name:<40} {duration_min:<12.1f} {wpm:<12.1f} {fillers:<15.1f} {speech_ratio:.1%}")
    
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
    
    print(f"\n✓ 汇总报告已保存：{summary_file}")
    print(f"{'='*80}")


def main():
    """主函数"""
    print("="*80)
    print("Audio Metrics CLI - 批量分析工具")
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
