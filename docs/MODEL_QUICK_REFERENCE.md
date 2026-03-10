# 🎯 模型依赖快速参考卡

**打印此页贴在桌边！**

---

## 📦 模型下载（中国区）

### 一键下载（推荐）
```powershell
.\download_models.bat
```

### 手动下载（完整步骤）
```powershell
# 1. 设置镜像
$env:HF_ENDPOINT = "https://hf-mirror.com"

# 2. 安装工具
pip install huggingface-hub openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 下载 Silero VAD
cd C:\Users\<用户名>\.cache\torch\hub
git clone https://ghproxy.com/https://github.com/snakers4/silero-vad.git silero-vad_master

# 4. 下载 PyAnnotate（需要授权）
huggingface-cli login
huggingface-cli download pyannote/speaker-diarization-3.1 --local-dir "C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--speaker-diarization-3.1"

# 5. 下载 Whisper
python -c "import whisper; whisper.load_model('base')"
```

---

## 🔑 PyAnnotate 授权步骤

1. 访问：https://huggingface.co/join（注册账户）
2. 访问：https://huggingface.co/pyannote/speaker-diarization-3.1
3. 点击 "Agree and access repository"
4. 访问：https://huggingface.co/settings/tokens
5. 创建 Read 类型 Token
6. 本地登录：`huggingface-cli login`

---

## ✅ 验证命令

```powershell
# 测试 Silero VAD
python -c "import torch; torch.hub.load('snakers4/silero-vad', 'model'); print('✅ VAD OK')"

# 测试 Whisper
python -c "import whisper; whisper.load_model('base'); print('✅ Whisper OK')"

# 测试 PyAnnotate
python -c "from pyannote.audio import Pipeline; print('✅ PyAnnotate OK')"
```

---

## 📂 模型存储位置

| 模型 | 路径 |
|------|------|
| Silero VAD | `C:\Users\<用户名>\.cache\torch\hub\snakers4_silero-vad_master\` |
| Whisper | `C:\Users\<用户名>\.cache\whisper\` |
| PyAnnotate | `C:\Users\<用户名>\.cache\huggingface\hub\models--pyannote--*` |

---

## 🚀 测试命令

```powershell
# 基本分析（不需要 PyAnnotate）
audio-metrics analyze audio.wav --show-progress

# 多说话人分析（需要 PyAnnotate）
audio-metrics analyze-multi conversation.wav --show-progress

# 仅转录
audio-metrics transcribe audio.m4a -o transcript.txt

# 声学分析
audio-metrics voice-acoustic audio.wav --output result.json
```

---

## ⚠️ 常见问题

| 错误 | 解决 |
|------|------|
| "GatedRepoError" | 未接受 HuggingFace 使用条款 |
| "Connection timeout" | 使用镜像 `$env:HF_ENDPOINT` |
| "Model not found" | 重新下载或从其他电脑复制 |
| "ModuleNotFoundError" | `pip install pyannote.audio` |

---

## 📚 完整文档

- **模型依赖详解**: [`docs/MODEL_DEPENDENCIES.md`](docs/MODEL_DEPENDENCIES.md)
- **快速参考**: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
- **多说话人指南**: [`MULTI_SPEAKER_GUIDE.md`](MULTI_SPEAKER_GUIDE.md)
- **项目总结**: [`PROJECT_SUMMARY_2026-03-10.md`](PROJECT_SUMMARY_2026-03-10.md)

---

## 💡 提示

1. **先测试基本功能**，确认核心依赖正常
2. **PyAnnotate 可选**，仅多说话人分析需要
3. **使用镜像加速**，避免网络超时
4. **从其他电脑复制**是最快的方式

---

**保存日期**: 2026-03-10
