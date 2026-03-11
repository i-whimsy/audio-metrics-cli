# Audio Metrics CLI v3 - Architecture Documentation

**Version**: 3.0.0  
**Date**: 2026-03-11  
**Status**: Production Ready

---

## 1. System Overview

Audio Metrics CLI v3 is a professional voice analysis engine with a clean three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer                               │
│  (cli/cli.py) - Argument parsing, pipeline orchestration    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Pipeline Layer                             │
│  (core/pipeline.py) - Analysis flow orchestration          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Module Layer                               │
│  (modules/*) - Individual analysis components              │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: CLI only handles arguments, Pipeline orchestrates, Modules analyze
2. **Single Responsibility**: Each module has one clear purpose
3. **Testability**: Layers can be tested independently
4. **Extensibility**: New modules can be added without changing core architecture

---

## 2. Directory Structure

```
src/audio_metrics/
├── cli/
│   ├── __init__.py
│   └── cli.py                    # CLI interface (v3)
├── core/
│   ├── __init__.py
│   ├── pipeline.py               # Main analysis pipeline
│   ├── model_config.py           # Offline model management
│   ├── config.py                 # Configuration
│   └── logger.py                 # Logging system
├── modules/
│   ├── __init__.py
│   ├── audio_loader.py           # Audio file loading
│   ├── vad_analyzer.py           # Voice activity detection
│   ├── speech_to_text.py         # Whisper transcription
│   ├── speaker_diarization.py    # Speaker separation
│   ├── prosody_analyzer.py       # 30+ voice metrics
│   ├── segment_metrics.py        # Per-segment features
│   ├── speaker_metrics.py        # Speaker aggregation
│   ├── timing_relation.py        # Timing analysis
│   ├── emotion_analyzer.py       # Emotion recognition
│   └── filler_detector.py        # Filler word detection
├── conversation/
│   ├── __init__.py
│   ├── timeline_builder.py       # Conversation timeline
│   └── conversation_dynamics.py  # Dynamics analysis (NEW)
├── nlp/
│   ├── __init__.py
│   ├── summary_generator.py      # One-liner summary
│   └── keyword_extractor.py      # Keywords & topics
└── exporters/
    ├── __init__.py
    └── enhanced_json_exporter.py # JSON output
```

---

## 3. Pipeline Flow

```
Audio File
    ↓
[1] Load Audio → AudioLoader
    ↓
[2] VAD Analysis → VADAnalyzer (Silero)
    ↓
[3] Speaker Diarization → SpeakerDiarization (pyannote)
    ↓
[4] Build Timeline → TimelineBuilder
    ↓
[5] Speech-to-Text → SpeechToText (Whisper)
    ↓
[6] Align Segments → align_segments_with_transcript()
    ↓
[7] Segment Metrics → SegmentMetricsExtractor
    ↓
[8] Speaker Metrics → SpeakerMetricsAggregator
    ↓
[9] Conversation Dynamics → ConversationDynamicsAnalyzer
    ↓
[10] Prosody Metrics (30+) → ProsodyAnalyzer
    ↓
[11] Emotion Analysis → EmotionAnalyzer (optional)
    ↓
[12] Filler Detection → FillerDetector
    ↓
[13] Keywords → KeywordExtractor
    ↓
[14] Summary → SummaryGenerator
    ↓
[15] Export JSON → EnhancedJSONExporter
```

### Pipeline Code Example

```python
from core.pipeline import AnalysisPipeline

# Initialize pipeline
pipeline = AnalysisPipeline(
    config={'stt_model': 'base', 'enable_emotion': True},
    debug=True
)

# Run analysis
result = pipeline.run(
    audio_path="meeting.wav",
    output_path="result.json"
)

# Access results
print(f"Speakers: {result['speakers']['num_speakers']}")
print(f"Interruptions: {result['conversation_dynamics']['interruptions']}")
```

---

## 4. JSON Schema v3

```json
{
  "meta": {
    "version": "3.0.0",
    "analyzer": "audio-metrics-cli",
    "timestamp": "2026-03-11T10:00:00",
    "file": "meeting.wav",
    "file_path": "/path/to/meeting.wav",
    "analysis_complete": true
  },
  "audio": {
    "duration_seconds": 60.0,
    "sample_rate": 48000,
    "channels": 1,
    "file_size_mb": 5.2
  },
  "speakers": {
    "detected": true,
    "num_speakers": 2,
    "total_speech_duration": 45.5,
    "profiles": [
      {
        "id": "SPEAKER_00",
        "label": "发言人 00",
        "total_time": 40.2,
        "ratio": 0.884,
        "turn_count": 15,
        "speech_turns": 15
      }
    ]
  },
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "speaker": "SPEAKER_00",
      "text": "Hello everyone, let's start the meeting...",
      "emotion": "neutral",
      "pitch": 145.2,
      "energy": 0.035,
      "duration": 5.2
    }
  ],
  "conversation_dynamics": {
    "interruptions": 3,
    "overlap_seconds": 1.4,
    "overlap_ratio": 0.023,
    "avg_response_latency": 0.8,
    "response_latency_std": 0.3,
    "turn_switch_rate": 0.12,
    "avg_turn_duration": 4.5,
    "turn_duration_std": 2.1,
    "long_pause_count": 5,
    "avg_pause_duration": 1.2,
    "total_silence_ratio": 0.15
  },
  "metrics": {
    "vad": {
      "speech_ratio": 0.75,
      "speech_duration": 45.0,
      "pause_count": 12
    },
    "prosody": {
      "pitch_mean_hz": 145.2,
      "pitch_std_hz": 25.3,
      "energy_mean": 0.035,
      "jitter": 0.012,
      "shimmer": 0.025,
      "hnr_db": 18.5,
      "spectral_centroid_mean": 1250.5,
      "tempo_bpm": 120.0,
      "mfcc_1_mean": -550.2
    },
    "emotion": {
      "dominant_emotion": "neutral",
      "confidence": 0.65
    },
    "filler_words": {
      "filler_word_count": 15,
      "fillers_per_100_words": 5.2
    }
  },
  "transcript": {
    "full_text": "Hello everyone, let's start...",
    "language": "en",
    "model": "base"
  },
  "topics": {
    "keywords": [...],
    "topics": [...]
  },
  "summary": {
    "one_liner": "Team meeting discussing project progress and next steps",
    "method": "heuristic",
    "confidence": 0.5
  }
}
```

---

## 5. Voice Metrics (30+ Features)

### Pitch Features (5)
- `pitch_mean_hz` - Mean fundamental frequency
- `pitch_std_hz` - Standard deviation
- `pitch_min_hz` - Minimum frequency
- `pitch_max_hz` - Maximum frequency
- `pitch_range_hz` - Frequency range

### Energy Features (5)
- `energy_mean` - Mean RMS energy
- `energy_std` - Energy standard deviation
- `energy_min` - Minimum energy
- `energy_max` - Maximum energy
- `energy_cv` - Coefficient of variation

### Voice Quality (3)
- `jitter` - Frequency perturbation
- `shimmer` - Amplitude perturbation
- `hnr_db` - Harmonics-to-noise ratio

### Spectral Features (6)
- `spectral_centroid_mean` - Brightness
- `spectral_centroid_std`
- `spectral_bandwidth_mean` - Bandwidth
- `spectral_bandwidth_std`
- `spectral_rolloff_mean` - Rolloff frequency
- `spectral_contrast_mean` - Timbral contrast

### Rhythm & Timing (5)
- `tempo_bpm` - Estimated tempo
- `zero_crossing_rate_mean` - Noisiness
- `zero_crossing_rate_std`
- `mfcc_1_mean` - Timbre (MFCC 1)
- `mfcc_2_mean` - Timbre (MFCC 2)
- `mfcc_3_mean` - Timbre (MFCC 3)

### Conversation Dynamics (10)
- `interruptions` - Count of interruptions
- `overlap_seconds` - Total overlap duration
- `overlap_ratio` - Overlap / total duration
- `avg_response_latency` - Mean gap between turns
- `response_latency_std`
- `turn_switch_rate` - Switches per second
- `avg_turn_duration` - Mean turn length
- `turn_duration_std`
- `long_pause_count` - Pauses > 2s
- `avg_pause_duration`

---

## 6. CLI Commands

### Analyze Audio

```bash
# Basic analysis
audio-metrics analyze meeting.wav

# With output file
audio-metrics analyze meeting.wav -o result.json

# Debug mode (show pipeline steps)
audio-metrics analyze meeting.wav --debug-pipeline

# Custom STT model
audio-metrics analyze meeting.wav -m small

# Disable emotion analysis
audio-metrics analyze meeting.wav --no-emotion
```

### Show Version

```bash
audio-metrics version
```

---

## 7. Configuration

### Pipeline Config

```python
config = {
    'stt_model': 'base',           # Whisper model
    'enable_emotion': True,        # Enable emotion analysis
    'summary_method': 'heuristic', # Summary generation method
    'language': 'zh'               # Language code
}

pipeline = AnalysisPipeline(config=config, debug=True)
```

### Environment Variables

```bash
# Offline mode
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# Model cache
export TORCH_HOME=~/.cache/torch
```

---

## 8. Migration Guide (v2 → v3)

### Breaking Changes

1. **CLI entry point moved**: `cli/cli.py` instead of `cli.py`
2. **JSON structure updated**: New top-level keys
3. **Pipeline required**: Can't call modules directly from CLI

### Migration Steps

1. Update import paths:
   ```python
   # Old
   from audio_metrics.cli_enhanced import analyze
   
   # New
   from audio_metrics.core.pipeline import AnalysisPipeline
   ```

2. Update JSON parsing:
   ```python
   # Old
   speakers = result['speakers']['profiles']
   
   # New (same, but more fields)
   speakers = result['speakers']['profiles']
   dynamics = result['conversation_dynamics']
   ```

3. Use pipeline for analysis:
   ```python
   pipeline = AnalysisPipeline()
   result = pipeline.run("audio.wav")
   ```

---

## 9. Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Test pipeline
pytest tests/test_pipeline.py

# Test modules
pytest tests/test_modules/
```

### Integration Test

```bash
# Analyze test audio
audio-metrics analyze tests/audio/sample.wav --debug-pipeline

# Verify JSON output
python -c "import json; print(json.load(open('result.json'))['meta'])"
```

---

## 10. Performance

### Typical Processing Times (60s audio)

| Step | Time |
|------|------|
| Audio Loading | 0.1s |
| VAD | 0.5s |
| Diarization | 15s |
| STT (Whisper base) | 5s |
| Metrics Extraction | 2s |
| **Total** | **~23s** |

### Optimization Tips

1. Use GPU for pyannote: `pipeline.model.to('cuda')`
2. Use smaller Whisper model: `-m tiny`
3. Disable emotion if not needed: `--no-emotion`

---

**End of Architecture Documentation**
