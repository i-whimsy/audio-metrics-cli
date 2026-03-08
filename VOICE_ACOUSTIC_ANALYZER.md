# Voice Acoustic Analyzer CLI v0.3.0

## 🎯 定位

**General Voice Acoustic Analyzer**（通用语音声学分析器）

- ✅ 只做声学客观指标提取
- ✅ 不包含销售/内容/语义评价
- ✅ 输出标准化声学特征 JSON
- ✅ 可用于任何上层任务（销售训练/播客分析/演讲训练/情绪识别/LLM 分析）

## 📦 CLI 命令

```bash
# 基本用法
audio-metrics voice-acoustic audio.mp3 -o result.json

# 参数
-o, --output        输出 JSON 文件路径
--show-progress     显示进度条
```

## 🔄 分析流程

```
[1/8] Loading audio...
[2/8] Voice Activity Detection...
[3/8] Prosody features...
[4/8] Pitch features...
[5/8] Energy features...
[6/8] Stability features...
[7/8] Emotion (acoustic)...
[8/8] Gender inference & voice range...
```

## 📊 输出指标

### 1. 音频基础指标
- duration_seconds
- sample_rate
- file_size_mb
- channels

### 2. VAD（语音活动检测）
- speech_ratio
- pause_count
- avg_pause_duration
- speech_duration

### 3. Prosody 节奏特征
- pitch_mean_hz
- energy_mean
- energy_cv
- words_per_minute

### 4. Pitch 音高特征
- pitch_mean_hz
- pitch_std_hz
- pitch_min_hz
- pitch_max_hz
- pitch_median_hz

### 5. Energy 音量特征
- energy_mean
- energy_std
- energy_cv (变异系数)

### 6. Stability 稳定度特征
- jitter (可选，需 parselmouth)
- shimmer (可选)
- hnr_db (可选)

### 7. Emotion 情绪声学特征
- dominant_emotion
- confidence

### 8. Gender 推断
- gender (male/female)
- confidence
- method: pitch_threshold

### 9. Voice Range 音域分类
- range (soprano/mezzo_soprano/alto/tenor/baritone/bass)
- gender
- pitch_mean_hz

## 📁 JSON 输出结构

```json
{
  "version": "0.3.0",
  "analyzer": "voice-acoustic-analyzer",
  "type": "acoustic_features",
  "audio_info": {
    "duration_seconds": 185.2,
    "sample_rate": 44100,
    "file_size_mb": 2.8,
    "channels": 1
  },
  "vad": {
    "speech_ratio": 0.81,
    "pause_count": 23,
    "avg_pause_duration": 1.1,
    "speech_duration": 150.0
  },
  "prosody": {
    "pitch_mean_hz": 145.3,
    "energy_mean": 0.0456,
    "energy_cv": 0.33
  },
  "pitch": {
    "pitch_mean_hz": 145.3,
    "pitch_std_hz": 32.1,
    "pitch_min_hz": 85.2,
    "pitch_max_hz": 280.5,
    "pitch_median_hz": 142.0
  },
  "energy": {
    "energy_mean": 0.0456,
    "energy_std": 0.0152,
    "energy_cv": 0.333
  },
  "stability": {
    "jitter": 0,
    "shimmer": 0,
    "hnr_db": 0,
    "note": "parselmouth optional"
  },
  "emotion": {
    "dominant_emotion": "neutral",
    "confidence": 0.5
  },
  "gender_inference": {
    "gender": "male",
    "confidence": 0.85,
    "method": "pitch_threshold"
  },
  "voice_range": {
    "range": "baritone",
    "gender": "male",
    "pitch_mean_hz": 145.3
  }
}
```

## 🔧 使用示例

```bash
# 分析播客录音
audio-metrics voice-acoustic podcast_ep01.mp3 -o analysis.json

# 分析演讲录音
audio-metrics voice-acoustic keynote.wav -o speech.json

# 分析有声书
audio-metrics voice-acoustic audiobook_ch01.m4a -o chapter1.json
```

## 📦 依赖

```toml
[dependencies]
numpy>=1.23.0
librosa>=0.10.0
soundfile>=0.12.0
openai-whisper>=20230314
click>=8.1.0
tqdm>=4.65.0
pydantic>=2.0.0
structlog>=23.0.0
tenacity>=8.0.0

[optional]
praat-parselmouth>=0.4.0  # 稳定度分析
torch>=2.0.0              # 情感分析
speechbrain>=0.5.14       # 情感分析
```

## 🎯 设计原则

1. **所有模块独立** - 每个特征提取模块可单独使用
2. **CLI 使用 click** - 标准命令行接口
3. **所有指标客观可重复** - 无随机性
4. **不做任何评分或解释** - 只输出原始数据
5. **JSON 结构稳定** - 供上层系统使用

## 🚀 上层应用场景

- 📊 销售通话训练
- 🎙️ 播客分析
- 🎤 演讲训练
- 😊 情绪识别
- 🤖 LLM 分析
- 📚 有声书质量评估
- 🎵 语音合成评估

## 📝 代码位置

- `src/audio_metrics/cli.py` - CLI 入口（voice-acoustic 命令）
- `src/audio_metrics/modules/` - 各分析模块

---

**版本**: v0.3.0  
**日期**: 2026-03-08  
**定位**: General Voice Acoustic Analyzer  
**状态**: ✅ 已完成
