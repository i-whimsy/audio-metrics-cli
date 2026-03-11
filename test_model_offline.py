#!/usr/bin/env python3
"""
Model Offline Loading Test
Tests all model loading with offline-first strategy
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "audio_metrics"))

from core.model_config import ModelConfig
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.speaker_diarization import SpeakerDiarization

def test_model_status():
    """Test model cache status"""
    print("\n" + "=" * 60)
    print("MODEL CACHE STATUS")
    print("=" * 60)
    
    ModelConfig.print_model_status()
    return ModelConfig.get_model_status()

def test_vad_loading():
    """Test Silero VAD loading"""
    print("\n" + "=" * 60)
    print("TEST 1: Silero VAD Loading")
    print("=" * 60)
    
    result = {"name": "Silero VAD", "success": False, "error": None}
    
    try:
        vad = VADAnalyzer()
        vad.load_model()
        
        if vad.model is not None:
            print("✓ Silero VAD loaded successfully")
            result["success"] = True
        else:
            print("✗ Silero VAD loading failed (model is None)")
            result["error"] = "Model loading returned None"
            
    except Exception as e:
        print(f"✗ Silero VAD loading failed: {e}")
        result["error"] = str(e)
    
    return result

def test_whisper_loading():
    """Test Whisper loading"""
    print("\n" + "=" * 60)
    print("TEST 2: Whisper Loading")
    print("=" * 60)
    
    result = {"name": "Whisper base", "success": False, "error": None}
    
    try:
        stt = SpeechToText(model_name="base")
        stt.load_model()
        
        if stt.model is not None:
            print("✓ Whisper base loaded successfully")
            result["success"] = True
        else:
            print("✗ Whisper loading failed (model is None)")
            result["error"] = "Model loading returned None"
            
    except Exception as e:
        print(f"✗ Whisper loading failed: {e}")
        result["error"] = str(e)
    
    return result

def test_pyannote_loading():
    """Test pyannote loading"""
    print("\n" + "=" * 60)
    print("TEST 3: Pyannote Speaker Diarization Loading")
    print("=" * 60)
    
    result = {"name": "Pyannote diarization", "success": False, "error": None}
    
    try:
        diarizer = SpeakerDiarization()
        diarizer.load_model()
        
        if diarizer.model is not None:
            print("✓ Pyannote loaded successfully")
            result["success"] = True
            result["fallback"] = False
        elif diarizer.use_fallback:
            print("⚠ Pyannote using fallback VAD-based segmentation")
            result["success"] = True
            result["fallback"] = True
        else:
            print("✗ Pyannote loading failed")
            result["error"] = "Model loading failed"
            
    except Exception as e:
        print(f"✗ Pyannote loading failed: {e}")
        result["error"] = str(e)
    
    return result

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MODEL OFFLINE LOADING TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "cache_status": None,
        "tests": []
    }
    
    # Test 1: Check cache status
    results["cache_status"] = test_model_status()
    
    # Test 2: VAD loading
    vad_result = test_vad_loading()
    results["tests"].append(vad_result)
    
    # Test 3: Whisper loading
    whisper_result = test_whisper_loading()
    results["tests"].append(whisper_result)
    
    # Test 4: Pyannote loading
    pyannote_result = test_pyannote_loading()
    results["tests"].append(pyannote_result)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results["tests"])
    success = sum(1 for t in results["tests"] if t["success"])
    failed = total - success
    
    print(f"Total tests: {total}")
    print(f"Passed: {success}")
    print(f"Failed: {failed}")
    
    results["summary"] = {
        "total": total,
        "passed": success,
        "failed": failed
    }
    
    # Save results
    output_file = Path("outputs") / "test_results" / "model_offline_test.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nResults saved to: {output_file}")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    main()
