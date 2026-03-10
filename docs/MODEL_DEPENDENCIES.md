# 📦 模型依赖完整指南

**最后更新**: 2026-03-10  
**适用版本**: v0.3.0+

---

## 🎯 概述

Audio Metrics CLI 依赖多个机器学习模型。本指南详细说明每个模型的用途、大小、下载方法和验证步骤。

---

## 📊 模型依赖总览

| 模型 | 用途 | 大小 | 必需性 | 下载方式 |
|------|------|------|--------|----------|
| **Silero VAD** | 语音活动检测 | ~2MB | ✅ 必需 | GitHub 自动下载 |
| **Whisper** | 语音转文字 | 39MB-1.5GB | ✅ 必需 | 首次使用自动下载 |
| **PyAnnotate 主模型** | 说话人分离 | ~400MB | ⚠️ 可选 | HuggingFace (需授权) |
| **PyAnnotate 子模型** | 嵌入/分割 | ~500MB | ⚠️ 可选 | HuggingFace 自动下载 |

---

## 1️⃣ Silero VAD（语音活动检测）

### 用途
- 检测音频中的语音段和静音段
- 计算语音比例、停顿次数等指标

### 模型信息
- **名称**: silero-vad
- **大小**: ~2MB
- **来源**: https://github.com/snakers4/silero-vad
- **必需性**: ✅ 必需（所有分析都需要）

### 下载方法

#### 方法 A：自动下载（推荐）
首次运行时自动从 GitHub 下载：
```python
import torch
torch.hub.load('snakers4/silero-vad', 'model')
```

#### 方法 B：手动下载
```powershell
# 进入缓存目录
cd C:\Users\<用户名>\.cache\torch\hub

# 使用镜像下载
git clone https://ghproxy.com/https://github.com/snakers4/silero-vad.git silero-vad_master

# 或直接使用 GitHub（需要良好网络）
git clone https://github.com/snakers4/silero-vad.git silero-vad_master
```

### 验证
```powershell
# 检查目录是否存在
Test-Path "C:\Users\<用户名>\.cache\torch\hub\snakers4_silero-vad_master"

# 应该返回 True
```

### 存储位置
```
C:\Users\<用户名>\.cache\torch\hub\snakers4_silero-vad_master\
```

---

## 2️⃣ Whisper（语音转文字）

### 用途
- 将语音转换为文字
- 支持多语言识别（中文、英文等）

### 模型信息

| 模型 | 大小 | 速度 | 精度 | 推荐用途 |
|------|------|------|------|----------|
| tiny | 39MB | 最快 | 基础 | 快速测试 |
| base | 74MB | 快 | 良好 | 日常使用 ✅ |
| small | 244MB | 中等 | 较好 | 高精度需求 |
| medium | 769MB | 慢 | 很好 | 专业场景 |
| large | 1550MB | 最慢 | 最佳 | 最高精度 |

### 下载方法

#### 方法 A：首次使用自动下载
```python
import whisper
model = whisper.load_model('base')  # 自动下载 base 模型
```

#### 方法 B：预下载
```powershell
# 使用清华镜像加速
pip install openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple

# 预下载指定模型
python -c "import whisper; whisper.load_model('base')"
```

### 验证
```python
import whisper
model = whisper.load_model('base')
print(f"Whisper 模型已就绪：{model}")
```

### 存储位置
```
C:\Users\<用户名>\.cache\whisper\
```

---

## 3️⃣ PyAnnotate Speaker Diarization 3.1（说话人分离）

### 用途
- 识别"谁在什么时候说话"
- 区分不同的说话人
- 用于多说话人对话分析

### 模型信息
- **主模型**: speaker-diarization-3.1
- **大小**: ~400MB
- **来源**: https://huggingface.co/pyannote/speaker-diarization-3.1
- **必需性**: ⚠️ 可选（仅多说话人分析需要）
- **特殊要求**: 需要 HuggingFace 账户授权

### ⚠️ 重要：授权步骤

PyAnnotate 是受限模型，必须先授权才能下载：

1. **创建 HuggingFace 账户**
   - 访问：https://huggingface.co/join
   - 免费注册

2. **接受使用条款**
   - 访问：https://huggingface.co/pyannote/speaker-diarization-3.1
   - 登录账户
   - 点击 "Agree and access repository"

3. **获取 Access Token**
   - 访问：https://huggingface.co/settings/tokens
   - 创建新 Token（类型：Read）
   - 复制 Token（类似：`hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### 下载方法

#### 方法 A：使用 HuggingFace CLI（推荐）

```powershell
# 1. 安装 huggingface-hub
pip install huggingface-hub -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 登录（粘贴你的 Token）
huggingface-cli login

# 3. 下载主模型（使用镜像）
$env:HF_ENDPOINT = "https://hf-mirror.com"
huggingface-cli download pyannote/speaker-diarization-3.1 --local-dir "C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--speaker-diarization-3.1"
```

#### 方法 B：使用 Python 下载

```python
from huggingface_hub import login, snapshot_download

# 登录
login(token="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

# 下载模型
snapshot_download(
    repo_id="pyannote/speaker-diarization-3.1",
    cache_dir="C:/Users/<用户名>/.cache/huggingface/hub",
    endpoint="https://hf-mirror.com"  # 使用镜像
)
```

#### 方法 C：在一台电脑上完整运行

最简单的方法：在有网络且已授权的电脑上运行一次分析：

```powershell
audio-metrics analyze-multi some_audio.wav --show-progress
```

这会自动下载所有需要的子模型，然后复制整个缓存目录。

### 子模型依赖

PyAnnotate 主模型会自动下载以下子模型：

| 子模型 | 用途 | 大小 |
|--------|------|------|
| segmentation-3.0 | 语音分割 | ~100MB |
| wespeaker-voxceleb-resnet34-LM | 说话人嵌入 | ~100MB |
| 其他 | 辅助功能 | ~300MB |

**总计**: 约 500MB

### 验证

```python
try:
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    print("✅ PyAnnotate 模型已就绪")
except Exception as e:
    print(f"❌ PyAnnotate 未就绪：{e}")
```

### 存储位置
```
C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--speaker-diarization-3.1\
C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--segmentation-3.0\
C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--wespeaker-voxceleb-resnet34-LM\
```

---

## 🔄 从其他电脑复制模型

如果在一台电脑上已下载完整模型，可以复制到另一台电脑：

### 步骤

1. **在已下载的电脑上打包**
   ```powershell
   # 压缩整个 huggingface 缓存
   Compress-Archive -Path "C:\Users\<用户名>\.cache\huggingface\hub" -DestinationPath "huggingface_hub.zip"
   ```

2. **复制到目标电脑**
   - 使用 U 盘、网络传输等方式

3. **在目标电脑上解压**
   ```powershell
   # 解压到目标位置
   Expand-Archive -Path "huggingface_hub.zip" -DestinationPath "C:\Users\clawbot\.cache\huggingface\" -Force
   ```

4. **验证**
   ```powershell
   python test_pyannote.py
   ```

### ⚠️ 注意事项

1. **必须复制整个 `hub` 文件夹**，包括所有子模型
2. **保持目录结构不变**
3. **确保 HuggingFace 账户已授权**（即使复制也需要授权）

---

## 🛠️ 故障排查

### 问题 1: "GatedRepoError: Access to model is restricted"

**原因**: 未接受 HuggingFace 使用条款

**解决**:
1. 访问 https://huggingface.co/pyannote/speaker-diarization-3.1
2. 登录并接受条款
3. 重新运行下载命令

### 问题 2: "Connection timeout" 或 "WinError 10060"

**原因**: 网络连接问题

**解决**:
1. 使用镜像：`$env:HF_ENDPOINT = "https://hf-mirror.com"`
2. 检查代理设置
3. 在另一台网络良好的电脑上下载后复制

### 问题 3: "Model not found in cache"

**原因**: 模型文件不完整或缓存损坏

**解决**:
1. 删除缓存目录
2. 重新下载
3. 或从其他电脑复制完整缓存

### 问题 4: PyAnnotate 导入成功但运行失败

**原因**: 子模型缺失

**解决**:
```powershell
# 运行一次完整分析，自动下载所有子模型
audio-metrics analyze-multi short_audio.wav --show-progress
```

---

## 📋 检查清单

### 基本分析（无需 PyAnnotate）
- [ ] Silero VAD 已下载
- [ ] Whisper 模型已下载
- [ ] librosa 已安装

### 多说话人分析（需要 PyAnnotate）
- [ ] HuggingFace 账户已创建
- [ ] 已接受 PyAnnotate 使用条款
- [ ] Access Token 已获取
- [ ] 已登录 HuggingFace CLI
- [ ] 主模型已下载
- [ ] 子模型已下载（segmentation-3.0, wespeaker 等）
- [ ] 验证脚本运行成功

---

## 🚀 快速测试命令

```powershell
# 测试 Silero VAD
python -c "import torch; torch.hub.load('snakers4/silero-vad', 'model'); print('VAD OK')"

# 测试 Whisper
python -c "import whisper; whisper.load_model('base'); print('Whisper OK')"

# 测试 PyAnnotate
python -c "from pyannote.audio import Pipeline; print('PyAnnotate OK')"

# 测试完整功能
audio-metrics analyze test.wav --show-progress
audio-metrics analyze-multi test.wav --show-progress
```

---

## 📞 获取帮助

- **GitHub Issues**: https://github.com/i-whimsy/audio-metrics-cli/issues
- **HuggingFace 模型页**: https://huggingface.co/pyannote/speaker-diarization-3.1
- **Silero VAD 项目**: https://github.com/snakers4/silero-vad

---

**提示**: 建议先测试基本分析功能，确认核心依赖正常后再配置 PyAnnotate。
