# 🎨 CLI 命令重新设计 - 自动化说话人检测

**日期**: 2026-03-10  
**问题**: 用户不应该预先知道是否有多个说话人

---

## ❌ 当前设计的问题

```bash
# 用户需要预先知道是否多人
audio-metrics analyze audio.wav          # 单说话人
audio-metrics analyze-multi audio.wav    # 多说话人
```

**问题**:
- ❌ 用户怎么知道录音里有几个人？
- ❌ 如果选错命令怎么办？
- ❌ 增加了用户认知负担
- ❌ 不符合直觉

---

## ✅ 重新设计：统一 `analyze` 命令

### 新设计

```bash
# 一个命令搞定，自动检测
audio-metrics analyze audio.wav

# 输出:
# 自动检测：单说话人 → 使用基本分析模式
# 或
# 自动检测：3 个说话人 → 使用多说话人分析模式
```

---

## 🏗️ 实现方案

### 方案 A: 智能检测（推荐）

```python
# src/audio_metrics/cli.py

@main.command("analyze")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--force-multi", is_flag=True, help="强制使用多说话人分析")
@click.option("--force-single", is_flag=True, help="强制使用单说话人分析")
@click.option("--backend", type=str, default="auto", help="说话人分离后端")
@click.pass_context
def analyze(ctx, audio_file, force_multi, force_single, backend):
    """
    智能分析音频文件
    
    自动检测说话人数量并选择合适的分析模式：
    - 单说话人：基本分析（转录 + 韵律 + 填充词）
    - 多说话人：完整分析（+ 说话人分离 + 对话指标）
    """
    
    # STEP 1: 加载音频
    loader = AudioLoader(audio_file)
    loader.load()
    
    # STEP 2: VAD 检测
    vad = VADAnalyzer()
    vad_result = vad.analyze(loader.get_audio_data())
    
    # STEP 3: 自动检测说话人数量
    if force_single:
        speaker_count = 1
        click.echo("📌 强制使用单说话人模式")
    elif force_multi:
        # 需要运行说话人分离
        speaker_count = "multi"
        click.echo("📌 强制使用多说话人模式")
    else:
        # 智能检测
        speaker_count = _auto_detect_speakers(
            audio_file, 
            vad_result,
            backend=backend
        )
    
    # STEP 4: 根据检测结果选择分析模式
    if speaker_count == 1:
        click.echo("🎯 检测到单说话人，使用基本分析模式")
        result = _analyze_single(audio_file, vad_result)
    else:
        click.echo(f"🎯 检测到 {speaker_count} 个说话人，使用多说话人分析模式")
        result = _analyze_multi(audio_file, vad_result, backend=backend)
    
    # STEP 5: 输出结果
    _export_result(result)
```

### 自动检测逻辑

```python
def _auto_detect_speakers(audio_file, vad_result, backend="auto") -> int:
    """
    自动检测说话人数量
    
    策略:
    1. 先用简单方法快速估计（VAD 片段数 + 音高变化）
    2. 如果明显是单说话人 → 返回 1
    3. 如果可能是多说话人 → 运行完整说话人分离
    """
    
    # 快速启发式检测
    speech_segments = vad_result.get('speech_segments', [])
    
    # 如果语音段很少，可能是单说话人
    if len(speech_segments) < 5:
        return 1
    
    # 提取音高特征
    pitch_features = _extract_pitch_features(audio_file, speech_segments)
    
    # 计算音高变化程度
    pitch_variance = np.var(pitch_features)
    
    # 如果音高变化很小，可能是单说话人
    if pitch_variance < PITCH_THRESHOLD:
        return 1
    
    # 否则，需要运行完整的说话人分离
    diarization_manager = DiarizationManager()
    backend = diarization_manager.get_backend(backend)
    
    if backend and not backend.is_cloud:
        # 本地后端可以快速运行
        result = backend.diarize(audio_file)
        return result.num_speakers
    else:
        # 没有可用的本地后端，保守估计
        # 根据语音段数量和音高变化推测
        estimated = _estimate_speakers_from_segments(speech_segments, pitch_features)
        return estimated if estimated > 1 else "multi"  # 标记为需要进一步分析
```

---

## 🎯 新的命令设计

### 主命令：`analyze`（智能）

```bash
# 基本用法（自动检测）
audio-metrics analyze audio.wav

# 强制模式（如果用户确定）
audio-metrics analyze audio.wav --force-single   # 强制单说话人
audio-metrics analyze audio.wav --force-multi    # 强制多说话人

# 指定后端
audio-metrics analyze audio.wav --backend speechbrain
audio-metrics analyze audio.wav --backend aliyun

# 输出控制
audio-metrics analyze audio.wav --output result.json
audio-metrics analyze audio.wav --format html
```

### 输出示例

**单说话人**:
```
============================================================
Audio Metrics CLI - Intelligent Analysis
============================================================
Input: 演讲录音.wav

🔍 自动检测说话人...
  VAD 语音段：15
  音高变化：低
  检测结果：单说话人

📊 使用基本分析模式...

[1/5] Loading audio...
[2/5] Voice activity detection...
[3/5] Speech-to-text...
[4/5] Prosody analysis...
[5/5] Filler detection...

============================================================
Analysis Complete
============================================================
Duration: 1820.5s
Speaking rate: 185 WPM
Speech ratio: 72%
Fillers: 1.8/100w

[OK] Exported: outputs/演讲录音/analysis_result.json
```

**多说话人**:
```
============================================================
Audio Metrics CLI - Intelligent Analysis
============================================================
Input: 会议录音.wav

🔍 自动检测说话人...
  VAD 语音段：89
  音高变化：高
  运行说话人分离...
  检测结果：3 个说话人

📊 使用多说话人分析模式...

[1/6] Loading audio...
[2/6] Voice activity detection...
[3/6] Speaker diarization...
[4/6] Timeline building...
[5/6] Speaker metrics...
[6/6] Conversation analysis...

============================================================
Analysis Complete
============================================================
Duration: 3224.6s
Speakers: 3
Total turns: 87
Fluency: 0.85
Balance: 0.92

[OK] Exported: outputs/会议录音/multi_speaker_analysis.json
```

---

### 移除的旧命令

```bash
# ❌ 已移除（不兼容旧版本）
audio-metrics analyze-multi audio.wav  # 已删除

# ✅ 使用新命令
audio-metrics analyze audio.wav  # 自动检测说话人
```

**理由**: 
- 保留旧命令会增加维护成本
- 旧命令本身设计有缺陷（需要预先知道说话人数）
- 新版本应该直接使用正确的设计
- 用户迁移成本低（只需改一个命令）

---

### 新增辅助命令

```bash
# 查看音频信息（快速）
audio-metrics info audio.wav

# 输出:
# Duration: 1820.5s
# Sample rate: 44100 Hz
# Estimated speakers: 1-2
# Speech ratio: 72%

# 仅检测说话人数量
audio-metrics detect-speakers audio.wav

# 输出:
# Detected speakers: 3
# Confidence: 0.85
# Backend: speechbrain
```

---

## 📋 配置选项

### 自动检测策略配置

```json
{
  "auto_detection": {
    "strategy": "smart",  // "fast", "smart", "accurate"
    
    // 快速模式：只用启发式检测
    "fast": {
      "use_vad": true,
      "use_pitch": true,
      "threshold": 0.7
    },
    
    // 智能模式：启发式 + 轻量分离
    "smart": {
      "fast_check": true,
      "confirm_with_diarization": true,
      "prefer_local_backend": true
    },
    
    // 精确模式：总是运行完整分离
    "accurate": {
      "always_run_diarization": true,
      "prefer_backend": "pyannote"
    }
  }
}
```

---

## 🎯 用户体验改进

### Before（旧设计）

```bash
# 用户困惑:
# "我应该用 analyze 还是 analyze-multi?"
# "我怎么知道录音里有几个人?"

audio-metrics analyze-multi meeting.wav  # 猜错了怎么办？
```

### After（新设计）

```bash
# 用户简单:
audio-metrics analyze meeting.wav  # 自动检测，无需担心

# 如果需要强制:
audio-metrics analyze meeting.wav --force-multi  # 明确意图
```

---

## 🔧 实现步骤

### Phase 1: 核心逻辑（1 天）
- [ ] 实现 `_auto_detect_speakers()` 函数
- [ ] 修改 `analyze` 命令支持自动检测
- [ ] 添加 `--force-single` 和 `--force-multi` 选项

### Phase 2: 清理旧命令（0.5 天）
- [ ] 删除 `analyze-multi` 命令
- [ ] 更新所有内部调用
- [ ] 更新测试用例

### Phase 3: 辅助命令（0.5 天）
- [ ] 实现 `info` 命令
- [ ] 实现 `detect-speakers` 命令

### Phase 4: 文档更新（0.5 天）
- [ ] 更新 README
- [ ] 更新使用示例
- [ ] 添加迁移指南

**总计**: 2.5 天

---

## 📊 检测策略对比

| 策略 | 速度 | 精度 | 适用场景 |
|------|------|------|----------|
| **快速** | ⚡⚡⚡ | ⭐⭐ | 批量预处理 |
| **智能** | ⚡⚡ | ⭐⭐⭐⭐ | 日常使用（默认） |
| **精确** | ⚡ | ⭐⭐⭐⭐⭐ | 重要分析 |

---

## 💡 额外优化

### 1. 缓存检测结果

```python
# 检测过的文件缓存结果
cache_key = hash(audio_file)
if cache_key in speaker_cache:
    return speaker_cache[cache_key]
```

### 2. 渐进式检测

```python
# 先快速检测，如果不确定再精确检测
result = fast_detect()
if result.confidence < 0.8:
    result = accurate_detect()
```

### 3. 用户反馈学习

```python
# 记录用户的强制选择，优化阈值
if user_used_force_multi and auto_detected == 1:
    # 调整阈值
    adjust_threshold()
```

---

## ✅ 优势总结

| 方面 | 旧设计 | 新设计 |
|------|--------|--------|
| **用户认知** | 需要预先知道说话人数 | 无需关心，自动检测 |
| **命令数量** | 2 个主命令 | 1 个主命令 |
| **灵活性** | 固定模式 | 自动 + 强制选项 |
| **容错性** | 选错命令结果错误 | 自动选择最优模式 |
| **学习成本** | 需要理解区别 | 直观简单 |

---

## 🎉 最终效果

```bash
# 用户只需:
audio-metrics analyze audio.wav

# 系统自动:
# 1. 检测说话人数量
# 2. 选择合适分析模式
# 3. 执行分析
# 4. 输出结果

# 完美！✨
```

---

**下一步**: 开始实现 Phase 1！
