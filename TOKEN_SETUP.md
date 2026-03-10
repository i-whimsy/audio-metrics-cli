# HuggingFace Token Setup

**日期**: 2026-03-10

---

## Token 已配置 ✅

Token 已保存到环境变量，可以直接使用 pyannote 的完整功能。

---

## 使用方法

### 方法 1: PowerShell (当前会话)
```powershell
$env:HF_TOKEN="your_huggingface_token"
```

### 方法 2: 永久设置 (Windows)
```powershell
# 设置用户环境变量
[Environment]::SetEnvironmentVariable(
    "HF_TOKEN", 
    "your_huggingface_token", 
    "User"
)
```

### 方法 3: 代码中设置
```python
import os
os.environ['HF_TOKEN'] = 'your_huggingface_token'

from audio_metrics.modules.speaker_diarization import SpeakerDiarization
diarizer = SpeakerDiarization()
```

### 方法 4: HuggingFace CLI
```bash
huggingface-cli login
# 然后输入 token
```

---

## 使用 pyannote 说话人分离

设置 token 后，直接运行:

```bash
# 命令行
audio-metrics analyze-multi your_audio.wav --show-progress

# Python
from audio_metrics.core.pipeline import MultiSpeakerPipeline
pipeline = MultiSpeakerPipeline()
result = pipeline.analyze("your_audio.wav")
```

---

## 注意事项

⚠️ **不要将 token 提交到 Git!**

Token 已添加到 `.gitignore`，请确保:
- 不要将包含 token 的文件 commit
- 不要在代码中硬编码 token
- 使用环境变量或配置文件

---

## 验证 Token

```python
from huggingface_hub import HfApi
api = HfApi()
user = api.whoami()  # 如果已设置 HF_TOKEN 环境变量
print(f"Logged in as: {user['name']}")
```

---

## 所需权限

使用 pyannote 说话人分离需要接受以下模型的用户协议:

1. https://huggingface.co/pyannote/speaker-diarization-3.1
2. https://huggingface.co/pyannote/segmentation-3.0

在浏览器中打开上述链接，登录 HuggingFace 并接受用户协议。
