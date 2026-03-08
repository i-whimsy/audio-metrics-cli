# Audio Metrics CLI

🎙️ **Cross-platform audio analysis toolkit for speech metrics extraction**

[![PyPI version](https://badge.fury.io/py/audio-metrics-cli.svg)](https://badge.fury.io/py/audio-metrics-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install audio-metrics-cli

# Or install from source
git clone https://github.com/i-whimsy/audio-metrics-cli.git
cd audio-metrics-cli
pip install -e .
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

## 📦 Features

### Core Metrics

- **🎵 Audio Information**: Duration, sample rate, file size
- **🗣️ Voice Activity Detection**: Speech/silence segmentation
- **📝 Speech-to-Text**: Whisper-powered transcription
- **🎼 Prosody Analysis**: Pitch, energy, speech rate
- **😊 Emotion Recognition**: Emotional state detection (optional)
- **🔤 Filler Word Detection**: "um", "uh", "like" detection

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

---

## 📊 Output Example

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
