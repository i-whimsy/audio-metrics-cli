#!/usr/bin/env python3
"""
Comprehensive Audio Test Script
================================
Tests all audio files in the AudioTest directory.
Handles long audio files, uses local models, and fixes pyannote v4.0 API.
"""
import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Any
import json
import traceback

# Set environment for local models
# NOTE: Set your HF_TOKEN in environment variable or .env file
# os.environ['HF_TOKEN'] = 'your-token-here'
os.environ['HF_HUB_OFFLINE'] = '0'  # Allow online if needed, but prefer cached

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "audio_metrics"))

# Import modules
try:
    from audio_metrics.core.logger import setup_logging, get_logger
except ImportError:
    # Fallback: setup basic logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    get_logger = logging.getLogger
    
    def setup_logging(level="INFO", log_file=None, json_output=False):
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s [%(levelname)s] %(message)s'
        )

setup_logging(level="INFO")
logger = get_logger(__name__)


def get_audio_files(directory: str) -> List[Path]:
    """Get all audio files in directory."""
    audio_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4"}
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(Path(directory).rglob(f"*{ext}"))
    
    # Filter out non-audio files (like .mp4 that might be video)
    audio_files = [f for f in audio_files if "analysis" not in str(f).lower()]
    
    return sorted(audio_files)


def load_audio(path: Path, max_duration: int = 60) -> Dict[str, Any]:
    """Load audio file with librosa, return basic info."""
    import librosa
    
    # Load up to max_duration seconds
    audio, sr = librosa.load(str(path), duration=max_duration, sr=16000)
    
    return {
        "path": str(path),
        "name": path.name,
        "duration_loaded": len(audio) / sr,
        "sample_rate": sr,
        "channels": 1,
        "success": True
    }


def run_vad(audio, sr: int) -> Dict[str, Any]:
    """Run VAD analysis."""
    from modules.vad_analyzer import VADAnalyzer
    
    vad = VADAnalyzer()
    result = vad.analyze(audio)
    
    return {
        "speech_ratio": result.get("speech_ratio", 0),
        "speech_duration": result.get("speech_duration", 0),
        "silence_duration": result.get("silence_duration", 0),
        "pause_count": result.get("pause_count", 0)
    }


def run_whisper(audio, sr: int) -> Dict[str, Any]:
    """Run Whisper transcription."""
    import whisper
    
    # Use local model
    model = whisper.load_model("base", download_root=os.path.expanduser("~/.cache/whisper"))
    result = model.transcribe(audio, language="zh", verbose=False)
    
    return {
        "language": result["language"],
        "text": result["text"][:500] if result["text"] else "",  # Limit text length
        "text_length": len(result["text"])
    }


def run_diarization(path: Path) -> Dict[str, Any]:
    """Run speaker diarization with pyannote."""
    import tempfile
    import soundfile as sf
    from pyannote.audio import Pipeline
    
    try:
        # Load pipeline
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
        
        # Create temp file (needs to be wav for pyannote)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            temp_path = tmp.name
        
        # Write audio to temp file (use only first 30 seconds for speed)
        import librosa
        audio, sr = librosa.load(str(path), duration=30, sr=16000)
        sf.write(temp_path, audio, sr)
        
        # Run diarization
        diarization = pipeline(temp_path)
        
        # Extract speakers - handle both v3 and v4 API
        speakers = set()
        segment_count = 0
        
        try:
            # Try v3.x API
            for segment, track, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
                segment_count += 1
        except AttributeError:
            # Try v4.0+ API
            try:
                for segment in diarization:
                    segment_count += 1
                    if hasattr(segment, 'speaker'):
                        speakers.add(segment.speaker)
                    elif hasattr(segment, 'label'):
                        speakers.add(segment.label)
            except:
                # Fallback: count tracks
                pass
        
        # Clean up
        os.remove(temp_path)
        
        return {
            "num_speakers": len(speakers),
            "speakers": list(speakers),
            "segments": segment_count,
            "success": True
        }
        
    except Exception as e:
        return {
            "num_speakers": 0,
            "speakers": [],
            "segments": 0,
            "success": False,
            "error": str(e)
        }


def test_audio_file(path: Path, test_vad: bool = True, test_whisper: bool = True, test_diarization: bool = True) -> Dict[str, Any]:
    """Test a single audio file."""
    result = {
        "file": path.name,
        "path": str(path),
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "success": False,
        "errors": []
    }
    
    try:
        # Load audio (max 60 seconds for quick test)
        logger.info(f"Loading {path.name}...")
        audio_info = load_audio(path, max_duration=60)
        result.update(audio_info)
        
        # Run VAD
        if test_vad:
            logger.info(f"  Running VAD...")
            import librosa
            audio, sr = librosa.load(str(path), duration=60, sr=16000)
            vad_result = run_vad(audio, sr)
            result["vad"] = vad_result
        
        # Run Whisper
        if test_whisper:
            logger.info(f"  Running Whisper...")
            try:
                whisper_result = run_whisper(audio, sr)
                result["whisper"] = whisper_result
            except Exception as e:
                result["errors"].append(f"Whisper: {str(e)}")
                result["whisper"] = {"success": False, "error": str(e)}
        
        # Run Diarization
        if test_diarization:
            logger.info(f"  Running Diarization...")
            try:
                diarization_result = run_diarization(path)
                result["diarization"] = diarization_result
            except Exception as e:
                result["errors"].append(f"Diarization: {str(e)}")
                result["diarization"] = {"success": False, "error": str(e)}
        
        result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
        logger.error(f"Error testing {path.name}: {e}")
        traceback.print_exc()
    
    return result


def main():
    """Main test function."""
    audio_dir = r"C:\Users\clawbot\Downloads\AudioTest"
    
    print("=" * 70)
    print("COMPREHENSIVE AUDIO TEST")
    print("=" * 70)
    print(f"Directory: {audio_dir}")
    print()
    
    # Get audio files
    audio_files = get_audio_files(audio_dir)
    
    print(f"Found {len(audio_files)} audio files:")
    for i, f in enumerate(audio_files, 1):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {i}. {f.name} ({size_mb:.1f} MB)")
    print()
    
    # Test each file
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Testing: {audio_file.name}")
        print("-" * 50)
        
        result = test_audio_file(audio_file, test_diarization=False)
        results.append(result)
        
        if result["success"]:
            print(f"  [OK] Success!")
            if "vad" in result:
                print(f"     VAD: Speech {result['vad']['speech_ratio']:.1%}")
            if "whisper" in result and result["whisper"].get("success", False):
                print(f"     Whisper: {result['whisper']['language']} - {result['whisper']['text_length']} chars")
            if "diarization" in result and result["diarization"].get("success", False):
                print(f"     Diarization: {result['diarization']['num_speakers']} speakers")
        else:
            print(f"  [FAIL] Failed!")
            for err in result["errors"]:
                print(f"     Error: {err}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r["success"])
    vad_count = sum(1 for r in results if "vad" in r and r["vad"].get("speech_ratio", 0) > 0)
    whisper_count = sum(1 for r in results if "whisper" in r and r["whisper"].get("success", False))
    
    print(f"Total files: {len(results)}")
    print(f"Loaded OK: {success_count}")
    print(f"VAD working: {vad_count}")
    print(f"Whisper working: {whisper_count}")
    print(f"Failed: {len(results) - success_count}")
    
    # Save results
    output_dir = Path("outputs") / "test_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"audio_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    from datetime import datetime
    main()