#!/usr/bin/env python3
"""
Full Parameter Test for Department Meeting Audio
=================================================
Runs all audio metrics parameters on the meeting recording.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "audio_metrics"))

# Setup environment
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.filler_detector import FillerDetector
from modules.speaker_diarization import SpeakerDiarization
from modules.timeline_builder import TimelineBuilder
from modules.metrics_builder import MetricsBuilder

# Audio file path (department meeting)
AUDIO_FILE = r"C:\Users\clawbot\Downloads\AudioTest\会议录音\2026-03-06_部门例会.m4a"
MAX_DURATION = 60  # Test with first 60 seconds

def run_full_test():
    """Run all parameter tests."""
    print("=" * 70)
    print("FULL PARAMETER TEST - Department Meeting Audio")
    print("=" * 70)
    print(f"Audio File: {AUDIO_FILE}")
    print(f"Test Duration: First {MAX_DURATION} seconds")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = {
        "audio_file": AUDIO_FILE,
        "test_duration": MAX_DURATION,
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # ========== TEST 1: Audio Loading ==========
    print("[1/8] Audio Loading...")
    print("-" * 50)
    try:
        import librosa
        audio_data, sample_rate = librosa.load(AUDIO_FILE, duration=MAX_DURATION, sr=16000)
        
        audio_info = {
            "file_path": AUDIO_FILE,
            "duration_seconds": len(audio_data) / sample_rate,
            "sample_rate": sample_rate,
            "channels": 1,
            "file_size_mb": round(os.path.getsize(AUDIO_FILE) / (1024 * 1024), 2)
        }
        
        results["tests"]["audio_loading"] = {
            "status": "SUCCESS",
            "data": audio_info,
            "interpretation": f"音频文件成功加载，时长{audio_info.get('duration_seconds', 0):.2f}秒，采样率{sample_rate}Hz"
        }
        
        print(f"  [OK] Duration: {audio_info.get('duration_seconds', 0):.2f}s")
        print(f"  [OK] Sample Rate: {sample_rate}Hz")
        print(f"  [OK] Channels: {audio_info.get('channels', 1)}")
        print(f"  [OK] File Size: {audio_info.get('file_size_mb', 0):.2f}MB")
    except Exception as e:
        results["tests"]["audio_loading"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
        return results
    print()
    
    # ========== TEST 2: Voice Activity Detection ==========
    print("[2/8] Voice Activity Detection (VAD)...")
    print("-" * 50)
    try:
        vad = VADAnalyzer()
        vad_result = vad.analyze(audio_data)
        
        results["tests"]["vad"] = {
            "status": "SUCCESS",
            "data": vad_result,
            "interpretation": f"语音活动检测完成，语音比例{vad_result.get('speech_ratio', 0)*100:.1f}%，检测到{vad_result.get('pause_count', 0)}次停顿"
        }
        
        print(f"  [OK] Speech Ratio: {vad_result.get('speech_ratio', 0)*100:.1f}%")
        print(f"  [OK] Speech Duration: {vad_result.get('speech_duration', 0):.2f}s")
        print(f"  [OK] Silence Duration: {vad_result.get('silence_duration', 0):.2f}s")
        print(f"  [OK] Pause Count: {vad_result.get('pause_count', 0)}")
        print(f"  [OK] Avg Pause Duration: {vad_result.get('avg_pause_duration', 0):.2f}s")
    except Exception as e:
        results["tests"]["vad"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 3: Speech-to-Text (Whisper) ==========
    print("[3/8] Speech-to-Text (Whisper)...")
    print("-" * 50)
    try:
        stt = SpeechToText(model="base", download_root=os.path.expanduser("~/.cache/whisper"))
        transcript = stt.transcribe(audio_data, sample_rate, language="zh")
        
        results["tests"]["transcription"] = {
            "status": "SUCCESS",
            "data": {
                "language": transcript.get("language", "unknown"),
                "text_length": len(transcript.get("text", "")),
                "text_preview": transcript.get("text", "")[:200]
            },
            "interpretation": f"语音转录完成，检测到语言为{transcript.get('language', 'unknown')}，转录文本{len(transcript.get('text', ''))}字符"
        }
        
        print(f"  [OK] Language: {transcript.get('language', 'unknown')}")
        print(f"  [OK] Text Length: {len(transcript.get('text', ''))} chars")
        print(f"  [OK] Preview: {transcript.get('text', '')[:100]}...")
    except Exception as e:
        results["tests"]["transcription"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 4: Prosody Analysis ==========
    print("[4/8] Prosody Analysis...")
    print("-" * 50)
    try:
        prosody = ProsodyAnalyzer()
        prosody_result = prosody.analyze(audio_data, sample_rate)
        
        results["tests"]["prosody"] = {
            "status": "SUCCESS",
            "data": prosody_result,
            "interpretation": f"韵律分析完成，平均基频{prosody_result.get('pitch_mean_hz', 0):.1f}Hz，能量变异系数{prosody_result.get('energy_cv', 0):.2f}"
        }
        
        print(f"  [OK] Pitch Mean: {prosody_result.get('pitch_mean_hz', 0):.1f}Hz")
        print(f"  [OK] Pitch Std: {prosody_result.get('pitch_std_hz', 0):.1f}Hz")
        print(f"  [OK] Energy Mean: {prosody_result.get('energy_mean', 0):.4f}")
        print(f"  [OK] Energy CV: {prosody_result.get('energy_cv', 0):.2f}")
        print(f"  [OK] Speech Rate: {prosody_result.get('speech_rate', 0):.1f} syllables/s")
    except Exception as e:
        results["tests"]["prosody"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 5: Filler Word Detection ==========
    print("[5/8] Filler Word Detection...")
    print("-" * 50)
    try:
        if "transcription" in results["tests"] and results["tests"]["transcription"]["status"] == "SUCCESS":
            filler = FillerDetector()
            filler_result = filler.detect(transcript.get("text", ""))
            
            results["tests"]["filler_words"] = {
                "status": "SUCCESS",
                "data": filler_result,
                "interpretation": f"填充词检测完成，共检测到{filler_result.get('filler_count', 0)}个填充词，密度{filler_result.get('fillers_per_100_words', 0):.1f}个/百词"
            }
            
            print(f"  [OK] Filler Count: {filler_result.get('filler_count', 0)}")
            print(f"  [OK] Fillers per 100 words: {filler_result.get('fillers_per_100_words', 0):.1f}")
        else:
            results["tests"]["filler_words"] = {
                "status": "SKIPPED",
                "reason": "Transcription not available"
            }
            print("  [SKIP] Skipped (no transcript)")
    except Exception as e:
        results["tests"]["filler_words"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 6: Speaker Diarization ==========
    print("[6/8] Speaker Diarization...")
    print("-" * 50)
    try:
        diarization = SpeakerDiarization()
        diarization_result = diarization.run(AUDIO_FILE, max_duration=MAX_DURATION)
        
        results["tests"]["diarization"] = {
            "status": "SUCCESS",
            "data": {
                "num_speakers": diarization_result.get("num_speakers", 0),
                "segments": len(diarization_result.get("segments", [])),
                "speakers": list(set([s.get("speaker", "") for s in diarization_result.get("segments", [])]))
            },
            "interpretation": f"说话人分离完成，检测到{diarization_result.get('num_speakers', 0)}位说话人，共{len(diarization_result.get('segments', []))}个语音片段"
        }
        
        print(f"  [OK] Num Speakers: {diarization_result.get('num_speakers', 0)}")
        print(f"  [OK] Segments: {len(diarization_result.get('segments', []))}")
    except Exception as e:
        results["tests"]["diarization"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 7: Timeline Building ==========
    print("[7/8] Timeline Building...")
    print("-" * 50)
    try:
        if "diarization" in results["tests"] and results["tests"]["diarization"]["status"] == "SUCCESS":
            timeline_builder = TimelineBuilder()
            timeline = timeline_builder.build(diarization_result.get("segments", []))
            
            results["tests"]["timeline"] = {
                "status": "SUCCESS",
                "data": {
                    "total_events": len(timeline),
                    "timeline_preview": timeline[:5] if len(timeline) > 5 else timeline
                },
                "interpretation": f"时间线构建完成，共{len(timeline)}个事件"
            }
            
            print(f"  [OK] Total Events: {len(timeline)}")
        else:
            results["tests"]["timeline"] = {
                "status": "SKIPPED",
                "reason": "Diarization not available"
            }
            print("  [SKIP] Skipped (no diarization)")
    except Exception as e:
        results["tests"]["timeline"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== TEST 8: Metrics Building ==========
    print("[8/8] Metrics Building...")
    print("-" * 50)
    try:
        builder = MetricsBuilder()
        combined = {
            "audio_info": audio_info,
            "vad_analysis": results["tests"].get("vad", {}).get("data", {}),
            "transcription": results["tests"].get("transcription", {}).get("data", {}),
            "prosody": results["tests"].get("prosody", {}).get("data", {}),
            "filler_words": results["tests"].get("filler_words", {}).get("data", {}),
            "diarization": results["tests"].get("diarization", {}).get("data", {})
        }
        
        metrics = builder.build(combined)
        
        results["tests"]["final_metrics"] = {
            "status": "SUCCESS",
            "data": metrics,
            "interpretation": "综合指标构建完成"
        }
        
        print(f"  [OK] Metrics built successfully")
        print(f"  [OK] Output keys: {list(metrics.keys()) if isinstance(metrics, dict) else 'N/A'}")
    except Exception as e:
        results["tests"]["final_metrics"] = {
            "status": "FAILED",
            "error": str(e)
        }
        print(f"  [FAIL] Failed: {e}")
    print()
    
    # ========== SUMMARY ==========
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    success_count = sum(1 for t in results["tests"].values() if t.get("status") == "SUCCESS")
    failed_count = sum(1 for t in results["tests"].values() if t.get("status") == "FAILED")
    skipped_count = sum(1 for t in results["tests"].values() if t.get("status") == "SKIPPED")
    
    print(f"Total Tests: {len(results['tests'])}")
    print(f"  [OK] Success: {success_count}")
    print(f"  [FAIL] Failed: {failed_count}")
    print(f"  [SKIP] Skipped: {skipped_count}")
    print()
    
    # Save results
    output_dir = Path("outputs") / "test_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"full_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    def serialize(obj):
        if isinstance(obj, (set, tuple)):
            return list(obj)
        return str(obj)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=serialize)
    
    print(f"Results saved to: {output_file}")
    print()
    
    # Print interpretations
    print("=" * 70)
    print("DATA INTERPRETATIONS")
    print("=" * 70)
    for test_name, test_result in results["tests"].items():
        if "interpretation" in test_result:
            print(f"\n[{test_name.upper()}]")
            print(f"  {test_result['interpretation']}")
    
    return results


if __name__ == "__main__":
    run_full_test()
