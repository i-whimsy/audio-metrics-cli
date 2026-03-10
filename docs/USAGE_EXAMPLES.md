# 📖 使用示例大全

**最后更新**: 2026-03-10  
**适用版本**: v0.3.0+

---

## 🚀 快速开始示例

### 示例 1: 首次使用 - 交互式配置

```bash
# 第一次运行，不知道用什么后端？
audio-metrics configure --interactive
```

**输出示例**:
```
🎙️ 说话人分离后端配置向导

可用的后端:
  1. pyannote 💻
  2. speechbrain 💻
  3. simple 💻
  4. aliyun ☁️

选择后端 [auto]: 2

✓ 已选择：speechbrain

✅ 配置已保存!
配置文件：C:\Users\clawbot\.audio_metrics\diarization_config.json
```

---

### 示例 2: 分析会议录音（自动选择）

```bash
# 让系统自动选择最优后端
audio-metrics analyze-multi "会议录音.m4a" --show-progress
```

**输出示例**:
```
============================================================
Audio Metrics CLI - Multi-Speaker Analysis v0.3.0
============================================================
Input: 会议录音.m4a

STEP 1 Loading audio...
  Duration: 3224.64s
  Sample rate: 16000 Hz

STEP 2 Voice activity detection...
  Speech ratio: 68.0%

STEP 3 Speaker diarization...
  Using backend: speechbrain
  Number of speakers: 3

STEP 4 Building conversation timeline...
  Timeline segments: 45

STEP 5 Extracting speaker metrics...
  Speaker profiles: 3

============================================================
Analysis Complete
============================================================
Duration: 3224.6s
Speakers: 3
Total turns: 45
Fluency: 0.850
Engagement: 0.720
Balance: 0.680
Processing time: 125.3s

[OK] Exported: outputs/会议录音/multi_speaker_analysis.json
```

---

### 示例 3: 指定后端（简单模式）

```bash
# 使用最简单的后端（无需额外安装）
audio-metrics analyze-multi "会议录音.m4a" --backend simple
```

**输出示例**:
```
============================================================
Audio Metrics CLI - Multi-Speaker Analysis v0.3.0
============================================================
Using backend: simple (VAD + Clustering)

STEP 1 Loading audio...
STEP 2 Voice activity detection...
STEP 3 Extracting speech segments...
STEP 4 Clustering segments...
  Estimated speakers: 2

[OK] Analysis complete!
```

---

### 示例 4: 使用云服务（可选）

```bash
# 使用阿里云（高精度，付费）
audio-metrics analyze "会议录音.m4a" --backend aliyun

# 或使用其他云服务
audio-metrics analyze "会议录音.m4a" --backend azure
audio-metrics analyze "会议录音.m4a" --backend google
```

**首次使用输出**:
```
☁️ 云服务 'aliyun' 需要配置凭据

📖 详细指引：docs/PYANNOTATE_ALTERNATIVES.md
🔗 注册链接：https://www.aliyun.com/product/speech
💰 价格参考：约 0.012 元/分钟

配置 阿里云智能语音:

输入 ALIYUN_ACCESS_KEY (Access Key ID): []: LTAI5t...
输入 ALIYUN_ACCESS_SECRET (Access Key Secret): []: ********

✅ 凭据已保存
✅ 开始分析...
```

**再次使用**:
```bash
# 凭据已保存，直接分析
audio-metrics analyze-multi "会议录音.m4a" --backend aliyun
```

---

### 示例 5: 使用环境变量（CI/CD 友好）

```bash
# 设置环境变量
export ALIYUN_ACCESS_KEY="LTAI5t..."
export ALIYUN_ACCESS_SECRET="..."

# 直接运行（无需交互式输入）
audio-metrics analyze-multi "会议录音.m4a" --backend aliyun
```

---

### 示例 6: 查看后端状态

```bash
audio-metrics diarization-status
```

**输出示例**:
```
📊 说话人分离后端状态

当前选择：auto

可用后端:
  ✅ pyannote 💻
  ✅ speechbrain 💻
  ✅ simple 💻
  ❌ aliyun ☁️ (未配置凭据)

✓ 当前可用：speechbrain

提示:
  - 运行 'audio-metrics configure --interactive' 进行配置
  - 运行 'audio-metrics analyze-multi audio.wav --backend simple' 指定后端
```

---

## 📊 实际工作场景示例

### 场景 1: 快速转写会议记录

```bash
# 只需要文字稿，不需要说话人分离
audio-metrics transcribe "会议录音.m4a" -o 会议记录.txt

# 输出:
# Transcribing: 会议录音.m4a
# Model: base
# Detected language: Chinese
# 
# Transcript saved: 会议记录.txt
```

**会议记录.txt 内容**:
```
[00:00:00] 好的，我们开始今天的例会。
[00:00:05] 首先请张三汇报一下项目进度。
[00:00:10] 好的，目前项目进展顺利...
```

---

### 场景 2: 分析多人对话（区分说话人）

```bash
# 使用 PyAnnotate（如果已安装）
audio-metrics analyze-multi "访谈录音.wav" --backend pyannote --output 访谈分析.json
```

**输出 JSON 内容**:
```json
{
  "audio_info": {
    "duration_seconds": 1800.5,
    "sample_rate": 44100
  },
  "conversation_timeline": [
    {
      "start": 0.0,
      "end": 15.2,
      "speakers": ["SPEAKER_00"],
      "type": "speech"
    },
    {
      "start": 15.5,
      "end": 28.3,
      "speakers": ["SPEAKER_01"],
      "type": "speech"
    }
  ],
  "speaker_profiles": [
    {
      "speaker_id": "SPEAKER_00",
      "speaker_label": "Speaker_1",
      "total_speaking_time": 900.3,
      "turn_count": 25,
      "avg_turn_duration": 36.01
    },
    {
      "speaker_id": "SPEAKER_01",
      "speaker_label": "Speaker_2",
      "total_speaking_time": 850.5,
      "turn_count": 22,
      "avg_turn_duration": 38.66
    }
  ],
  "conversation_metrics": {
    "num_speakers": 2,
    "total_turns": 47,
    "fluency_score": 0.85,
    "engagement_score": 0.72,
    "balance_score": 0.94
  }
}
```

---

### 场景 3: 批量分析多个录音

```bash
# 分析整个目录的录音
audio-metrics analyze --batch "./录音文件夹/" --format csv --output 批量分析结果.csv

# 输出:
# Files to process: 15
# Processing: 100%|████████████████████| 15/15 [05:32<00:00, 22.05s/file]
# [OK] Batch exported: 批量分析结果.csv
```

**批量分析结果.csv**:
```csv
filename,duration,speech_ratio,wpm,fillers_per_100w,pitch_mean
录音 001.m4a,1820.5,0.68,185,2.3,145.2
录音 002.m4a,2100.3,0.72,192,1.8,152.1
录音 003.m4a,1650.8,0.65,178,3.1,138.9
...
```

---

### 场景 4: 对比两个版本的录音

```bash
# 对比同一演讲的两个版本
audio-metrics compare "演讲_v1.wav" "演讲_v2.wav" --format markdown
```

**输出**:
```markdown
# 音频对比报告

| Metric | 演讲_v1.wav | 演讲_v2.wav | 差异 |
|--------|-------------|-------------|------|
| Duration (s) | 1800.5 | 1750.2 | -50.3s ⬇️ |
| Speaking Rate (WPM) | 185.3 | 195.8 | +10.5 ⬆️ |
| Fillers/100w | 2.5 | 1.8 | -0.7 ✅ |
| Pitch Mean (Hz) | 145.2 | 148.1 | +2.9 |

## 分析
- v2 版本语速更快（+10.5 WPM）
- v2 版本填充词更少（-0.7/100w）✅
- 整体表现：v2 更优
```

---

### 场景 5: 生成详细分析报告（HTML）

```bash
# 生成 HTML 报告（适合分享）
audio-metrics analyze "演讲录音.wav" --format html --output 分析报告.html
```

**HTML 报告包含**:
- 📊 音频基本信息
- 📈 语音/静音时间线可视化
- 🎯 语速变化曲线
- 📝 完整转录稿
- 🔤 填充词位置标注
- 🎼 音高/能量图表

---

### 场景 6: 仅分析声学特征（无需转录）

```bash
# 快速声学分析（不需要 Whisper，速度快）
audio-metrics voice-acoustic "录音.wav" --output 声学特征.json
```

**输出**:
```json
{
  "version": "0.3.0",
  "analyzer": "voice-acoustic-analyzer",
  "audio_info": {
    "duration_seconds": 180.5,
    "sample_rate": 44100,
    "file_size_mb": 3.2
  },
  "vad": {
    "speech_ratio": 0.72,
    "pause_count": 15
  },
  "pitch": {
    "pitch_mean_hz": 145.3,
    "pitch_std_hz": 25.1,
    "pitch_min_hz": 98.5,
    "pitch_max_hz": 210.8
  },
  "energy": {
    "energy_mean": 0.035,
    "energy_cv": 0.42
  },
  "gender_inference": {
    "gender": "male",
    "confidence": 0.85
  },
  "voice_range": {
    "range": "baritone",
    "gender": "male"
  }
}
```

---

## 🔧 高级用法示例

### 示例 7: 自定义配置分析

```bash
# 使用自定义配置文件
audio-metrics analyze "录音.wav" --config my_config.json
```

**my_config.json**:
```json
{
  "models": {
    "speech_to_text": {
      "provider": "whisper",
      "model": "small",
      "language": "zh"
    },
    "vad": {
      "provider": "silero",
      "threshold": 0.6
    }
  },
  "features": {
    "enable_emotion": false,
    "enable_pitch": true,
    "enable_energy": true,
    "skip_if_too_long": 3600
  }
}
```

---

### 示例 8: 并行处理多个文件

```bash
# 使用 8 个工作进程并行处理
audio-metrics analyze --glob "./recordings/*.wav" --parallel --workers 8
```

**输出**:
```
Files to process: 50
Parallel: True (8 workers)
Processing: 100%|████████████████████| 50/50 [10:23<00:00, 12.46s/file]
Successfully processed: 50/50 files
[OK] Batch exported: outputs/batch_results_20260310_153045.json
```

---

### 示例 9: 长音频分段处理

```bash
# 处理超长音频（>1 小时），自动分段
audio-metrics analyze "超长会议录音.m4a" \
  --config chunk_config.json \
  --output 分段分析结果.json
```

**chunk_config.json**:
```json
{
  "audio_analysis": {
    "chunk_duration": 1800,
    "chunk_overlap": 30
  }
}
```

---

### 示例 10: 结合多个命令的工作流

```bash
# 1. 转录
audio-metrics transcribe "会议录音.m4a" -o 转录稿.txt

# 2. 分析
audio-metrics analyze-multi "会议录音.m4a" --output 分析报告.json

# 3. 生成 HTML 报告
audio-metrics analyze "会议录音.m4a" --format html --output 完整报告.html

# 4. 生成摘要（需要额外工具）
cat 转录稿.txt | summarize > 会议摘要.md
```

---

## 📝 输出示例

### 完整 JSON 输出

```json
{
  "audio_info": {
    "file_path": "会议录音.m4a",
    "duration_seconds": 3224.64,
    "sample_rate": 16000,
    "file_size_mb": 24.46
  },
  "vad_analysis": {
    "speech_ratio": 0.68,
    "pause_count": 156,
    "avg_pause_duration": 2.3,
    "speech_segments": 89
  },
  "speech_metrics": {
    "words_total": 8520,
    "words_per_minute": 158.5,
    "unique_words": 1250,
    "vocabulary_richness": 0.147
  },
  "prosody_metrics": {
    "pitch_mean_hz": 145.3,
    "pitch_std_hz": 25.1,
    "energy_mean": 0.035,
    "energy_cv": 0.42,
    "speech_rate": 158.5
  },
  "filler_metrics": {
    "filler_word_count": 125,
    "fillers_per_100_words": 1.47,
    "filler_types": {
      "嗯": 45,
      "啊": 32,
      "这个": 28,
      "那个": 20
    }
  },
  "conversation_timeline": [
    {
      "start": 0.0,
      "end": 15.2,
      "duration": 15.2,
      "type": "speech",
      "speakers": ["SPEAKER_00"],
      "speaker_count": 1
    },
    {
      "start": 15.5,
      "end": 28.3,
      "duration": 12.8,
      "type": "speech",
      "speakers": ["SPEAKER_01"],
      "speaker_count": 1
    }
  ],
  "speaker_profiles": [
    {
      "speaker_id": "SPEAKER_00",
      "speaker_label": "Speaker_1",
      "total_speaking_time": 1650.3,
      "turn_count": 45,
      "avg_turn_duration": 36.67,
      "overlap_ratio": 0.08,
      "acoustic_profile": {
        "avg_pitch_hz": 145.3,
        "pitch_std_hz": 25.1,
        "avg_energy": 0.035
      }
    },
    {
      "speaker_id": "SPEAKER_01",
      "speaker_label": "Speaker_2",
      "total_speaking_time": 1520.5,
      "turn_count": 42,
      "avg_turn_duration": 36.20,
      "overlap_ratio": 0.12,
      "acoustic_profile": {
        "avg_pitch_hz": 210.5,
        "pitch_std_hz": 30.2,
        "avg_energy": 0.042
      }
    }
  ],
  "conversation_metrics": {
    "num_speakers": 2,
    "total_turns": 87,
    "speaker_changes": 72,
    "overlap_ratio": 0.10,
    "mean_response_latency": 0.45,
    "fluency_score": 0.85,
    "engagement_score": 0.72,
    "balance_score": 0.92
  }
}
```

---

## 💡 实用技巧

### 技巧 1: 快速测试（短音频）

```bash
# 先用短音频测试配置
audio-metrics analyze "测试录音_30 秒.wav" --show-progress
```

### 技巧 2: 后台处理长音频

```bash
# 长音频在后台运行
nohup audio-metrics analyze "超长录音.m4a" --output result.json > log.txt 2>&1 &

# 查看进度
tail -f log.txt
```

### 技巧 3: 使用管道

```bash
# 转录后直接搜索关键词
audio-metrics transcribe "录音.wav" | grep "重要关键词"
```

### 技巧 4: 批量重命名输出

```bash
# 为输出文件添加时间戳
audio-metrics analyze "录音.wav" \
  --output "outputs/分析_$(date +%Y%m%d_%H%M%S).json"
```

---

## 🎯 典型应用场景

### 场景 A: 会议纪要生成

```bash
# 1. 转录
audio-metrics transcribe "会议录音.m4a" -o 会议记录.txt

# 2. 分析说话人
audio-metrics analyze-multi "会议录音.m4a" --output 会议分析.json

# 3. 提取关键信息（结合其他工具）
# ... 使用 NLP 工具处理转录稿
```

### 场景 B: 播客分析

```bash
# 分析播客节目质量
audio-metrics analyze "播客 EP01.wav" \
  --format html \
  --output "播客分析报告_EP01.html"
```

### 场景 C: 语音训练反馈

```bash
# 对比训练前后
audio-metrics compare "训练前.wav" "训练后.wav" \
  --format markdown \
  --output 训练效果对比.md
```

### 场景 D: 客服质量监控

```bash
# 批量分析客服录音
audio-metrics analyze --batch "./客服录音/" \
  --format csv \
  --output 客服质量报告.csv

# 在 Excel 中进一步分析
```

---

## 📞 获取帮助

```bash
# 查看所有命令
audio-metrics --help

# 查看特定命令帮助
audio-metrics analyze --help
audio-metrics analyze-multi --help
audio-metrics configure --help

# 查看版本
audio-metrics --version
```

---

**更多示例**: 查看项目仓库的 `examples/` 目录

**最后更新**: 2026-03-10
