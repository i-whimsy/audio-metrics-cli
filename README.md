# Audio Metrics CLI

🎙️ **Cross-platform audio analysis toolkit for speech metrics extraction**

[![PyPI version](https://badge.fury.io/py/audio-metrics-cli.svg)](https://badge.fury.io/py/audio-metrics-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🇨🇳 中国区用户 - 首次使用必读

### 🚀 一键下载模型（推荐）

**Windows 用户**: 双击运行 `download_models.bat` 脚本

**或手动执行**（PowerShell）:
```powershell
# 复制以下完整命令到 PowerShell 执行
$env:HF_ENDPOINT = "https://hf-mirror.com"
pip install huggingface-hub openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
cd C:\Users\clawbot\.cache\torch\hub
git clone https://ghproxy.com/https://github.com/snakers4/silero-vad.git silero-vad_master
huggingface-cli download pyannote/speaker-diarization-3.1 --local-dir "C:\Users\clawbot\.cache\huggingface\hub\models--pyannote--speaker-diarization-3.1"
python -c "import whisper; whisper.load_model('base')"
```

**详细说明**: 查看 [`docs/MODEL_DEPENDENCIES.md`](docs/MODEL_DEPENDENCIES.md)

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install audio-metrics-cli

# Or install from source (development)
git clone https://github.com/i-whimsy/audio-metrics-cli.git
cd audio-metrics-cli
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Analyze audio file
audio-metrics analyze your_audio.wav --output result.json

# With verbose output
audio-metrics analyze audio.mp3 --verbose --show-progress

# Transcribe only
audio-metrics transcribe audio.m4a -o transcript.txt

# Compare two audio files
audio-metrics compare v1.wav v2.wav
```

---

---

## ⚠️ Important: Dependency Check (READ BEFORE USE!)

Before using this tool, **especially for multi-speaker analysis**, you should check if all dependencies are properly installed:

```bash
# Check dependencies
python CHECK_DEPENDENCIES.py

# Or automatically install missing ones (may take a while)
python CHECK_DEPENDENCIES.py --fix
```

### Why This Matters

**pyannote.audio is required for accurate multi-speaker analysis!**

Without pyannote.audio installed, the tool falls back to a simple VAD-based method that:
- ❌ Cannot distinguish between different speakers
- ❌ Will show 50/50 speaking time even when one person talks 90% of the time
- ❌ Only alternates speakers based on speech segments

With pyannote.audio installed:
- ✅ Correctly identifies who spoke when
- ✅ Accurate speaker time statistics
- ✅ Works with any number of speakers

### Manual Installation (if pip fails)

If the automatic installation fails due to network issues:

```bash
# Option 1: CPU-only (faster install, recommended for testing)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install pyannote.audio

# Option 2: GPU (faster inference, requires CUDA)
pip install torch torchaudio
pip install pyannote.audio

# Option 3: Using conda (recommended)
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
pip install pyannote.audio
```

---

## 📦 Features

### Core Metrics

- **🎵 Audio Information**: Duration, sample rate, file size
- **🗣️ Voice Activity Detection**: Speech/silence segmentation
- **📝 Speech-to-Text**: Whisper-powered transcription
- **🎼 Prosody Analysis**: Pitch, energy, speech rate
- **😊 Emotion Recognition**: Emotional state detection (optional)
- **🔤 Filler Word Detection**: "um", "uh", "like" detection

### Multi-Speaker Conversation Analysis (v0.3.0+)

- **🎯 Speaker Diarization**: "Who spoke when" using pyannote.audio
- **📊 Conversation Timeline**: Chronological sequence of speech segments
- **👥 Speaker Profiles**: Per-speaker statistics and acoustic features
- **⏱️ Timing Analysis**: Response latency, turn-taking patterns
- **📈 Conversation Metrics**: Fluency, engagement, and balance scores

### Supported Formats

- ✅ WAV
- ✅ MP3
- ✅ M4A
- ✅ FLAC
- ✅ OGG

### Cross-Platform

- ✅ Windows
- ✅ macOS
- ✅ Linux

---

## 📖 Documentation

### Command Line Interface

#### `analyze` - Full Analysis

```bash
audio-metrics analyze audio.wav [OPTIONS]

Options:
  -o, --output PATH        Output JSON file path
  -c, --config PATH        Configuration file
  -m, --model TEXT         Whisper model (tiny/base/small/medium/large)
  --no-emotion            Skip emotion analysis
  --show-progress         Show progress bars
  -v, --verbose           Verbose output
  --help                  Show this message
```

#### `transcribe` - Speech to Text

```bash
audio-metrics transcribe audio.wav [OPTIONS]

Options:
  -o, --output PATH       Output transcript file
  -m, --model TEXT        Whisper model
  --language TEXT         Language code
  --help                  Show this message
```

#### `compare` - Compare Audio Files

```bash
audio-metrics compare audio1.wav audio2.wav [OPTIONS]

Options:
  --format TEXT          Output format (text/json/markdown)
  --help                 Show this message
```

#### `analyze-multi` - Multi-Speaker Conversation Analysis (v0.3.0+)

```bash
audio-metrics analyze-multi conversation.wav [OPTIONS]

Options:
  -o, --output PATH          Output JSON file path
  --num-speakers INT         Number of speakers (if known)
  --min-speakers INT         Minimum number of speakers
  --max-speakers INT         Maximum number of speakers
  --show-progress           Show progress steps
  -v, --verbose             Verbose output
  --help                    Show this message
```

**Example:**
```bash
# Analyze a 2-person conversation
audio-metrics analyze-multi interview.wav --num-speakers 2 --output result.json

# Analyze with speaker range estimation
audio-metrics analyze-multi meeting.wav --min-speakers 2 --max-speakers 5 --show-progress
```

---

## 📊 Output Example

### Single-Speaker Analysis

```json
{
  "audio_info": {
    "duration_seconds": 185.2,
    "sample_rate": 44100,
    "file_size_mb": 2.8
  },
  "vad_analysis": {
    "speech_ratio": 0.81,
    "pause_count": 23,
    "avg_pause_duration": 1.1
  },
  "speech_metrics": {
    "words_total": 820,
    "words_per_minute": 266
  },
  "prosody_metrics": {
    "pitch_mean_hz": 145.3,
    "energy_cv": 0.33
  },
  "filler_metrics": {
    "filler_word_count": 18,
    "fillers_per_100_words": 2.2
  }
}
```

### Multi-Speaker Conversation Analysis

```json
{
  "audio_info": {
    "file_path": "/path/to/conversation.wav",
    "duration_seconds": 300.5,
    "sample_rate": 44100,
    "file_size_mb": 5.2
  },
  "conversation_timeline": [
    {
      "start": 0.0,
      "end": 5.2,
      "duration": 5.2,
      "type": "speech",
      "speakers": ["SPEAKER_00"],
      "speaker_count": 1
    },
    {
      "start": 5.5,
      "end": 8.3,
      "duration": 2.8,
      "type": "speech",
      "speakers": ["SPEAKER_01"],
      "speaker_count": 1
    },
    {
      "start": 8.5,
      "end": 12.1,
      "duration": 3.6,
      "type": "overlap",
      "speakers": ["SPEAKER_00", "SPEAKER_01"],
      "speaker_count": 2
    }
  ],
  "speaker_profiles": [
    {
      "speaker_id": "SPEAKER_00",
      "speaker_label": "Speaker_1",
      "total_speaking_time": 150.3,
      "turn_count": 25,
      "avg_turn_duration": 6.01,
      "overlap_ratio": 0.12,
      "acoustic_profile": {
        "avg_pitch_hz": 145.3,
        "pitch_std_hz": 25.1,
        "avg_energy": 0.035
      }
    },
    {
      "speaker_id": "SPEAKER_01",
      "speaker_label": "Speaker_2",
      "total_speaking_time": 120.5,
      "turn_count": 20,
      "avg_turn_duration": 6.03,
      "overlap_ratio": 0.15,
      "acoustic_profile": {
        "avg_pitch_hz": 210.5,
        "pitch_std_hz": 30.2,
        "avg_energy": 0.042
      }
    }
  ],
  "conversation_metrics": {
    "num_speakers": 2,
    "total_turns": 45,
    "speaker_changes": 38,
    "overlap_ratio": 0.13,
    "mean_response_latency": 0.45,
    "fluency_score": 0.85,
    "engagement_score": 0.72,
    "balance_score": 0.68
  },
  "global_acoustic_metrics": {
    "pitch_mean_hz": 178.5,
    "pitch_std_hz": 35.2,
    "energy_mean": 0.038,
    "energy_cv": 0.42
  },
  "processing_meta": {
    "version": "0.3.0",
    "analyzer": "audio-metrics-multi-speaker",
    "timestamp": "2025-01-15T10:30:00",
    "processing_time_seconds": 45.2
  }
}
```

---

## 🔧 Configuration

Create a `config.json` file:

```json
{
  "models": {
    "speech_to_text": {
      "provider": "whisper",
      "model": "base",
      "device": "auto"
    },
    "vad": {
      "provider": "silero",
      "threshold": 0.5
    }
  },
  "audio_analysis": {
    "enable_pitch": true,
    "enable_energy": true,
    "enable_pause": true
  },
  "features": {
    "enable_emotion": true,
    "skip_if_too_long": 3600
  }
}
```

---

## 💻 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/i-whimsy/audio-metrics-cli.git
cd audio-metrics-cli

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/
ruff check src/
```

### Project Structure

```
audio-metrics-cli/
├── src/
│   └── audio_metrics/
│       ├── cli.py              # CLI entry point
│       ├── config.py           # Configuration
│       └── modules/            # Core modules
│           ├── audio_loader.py
│           ├── vad_analyzer.py
│           ├── speech_to_text.py
│           ├── prosody_analyzer.py
│           ├── emotion_analyzer.py
│           ├── filler_detector.py
│           ├── metrics_builder.py
│           └── json_exporter.py
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech-to-text
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [Librosa](https://librosa.org/) - Audio analysis
- [SpeechBrain](https://speechbrain.github.io/) - Emotion recognition

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/i-whimsy/audio-metrics-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/i-whimsy/audio-metrics-cli/discussions)
- **Email**: clawbot@openclaw.ai

---

**Built with ❤️ by OpenClaw Team**
