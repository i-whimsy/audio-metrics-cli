# 摘要生成 API 配置指南

Audio Metrics CLI v2.0 支持三种摘要生成方式，自动降级。

---

## 🎯 配置方式

### 方式一：命令行参数（推荐测试用）

```bash
# 使用启发式方法（无需配置，立即使用）
audio-metrics analyze meeting.wav --summary heuristic

# 使用本地 LLM（需要安装 Ollama）
audio-metrics analyze meeting.wav --summary llm

# 使用云端 API（需要配置 API Key）
audio-metrics analyze meeting.wav --summary cloud

# 自动模式（优先 LLM，失败则降级）
audio-metrics analyze meeting.wav --summary auto
```

---

### 方式二：环境变量（推荐生产用）

#### 1. 本地 LLM（Ollama）

```bash
# Windows PowerShell
$env:OLLAMA_HOST = "http://localhost:11434"
$env:OLLAMA_MODEL = "qwen2.5:7b"

# Linux/macOS
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="qwen2.5:7b"

# 永久配置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OLLAMA_HOST="http://localhost:11434"' >> ~/.bashrc
echo 'export OLLAMA_MODEL="qwen2.5:7b"' >> ~/.bashrc
```

**安装 Ollama**：
```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - 下载安装包
# https://ollama.com/download/windows

# 安装模型
ollama pull qwen2.5:7b
```

#### 2. 云端 API（Moonshot/通义/文心）

```bash
# Moonshot（月之暗面）
$env:SUMMARY_CLOUD_PROVIDER = "moonshot"
$env:SUMMARY_CLOUD_API_KEY = "sk-xxxxxxxxxxxxxxxx"

# 通义千问（阿里云）
$env:SUMMARY_CLOUD_PROVIDER = "bailian"
$env:SUMMARY_CLOUD_API_KEY = "sk-xxxxxxxxxxxxxxxx"

# 文心一言（百度）
$env:SUMMARY_CLOUD_PROVIDER = "wenxin"
$env:SUMMARY_CLOUD_API_KEY = "xxxxxxxxxxxxxxxx"
```

---

### 方式三：配置文件（推荐团队用）

在项目根目录创建 `.env` 文件：

```bash
# .env 文件示例

# Ollama 本地 LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# 云端 API（二选一）
SUMMARY_CLOUD_PROVIDER=moonshot
SUMMARY_CLOUD_API_KEY=sk-xxxxxxxxxxxxxxxx

# 或者使用通义千问
# SUMMARY_CLOUD_PROVIDER=bailian
# SUMMARY_CLOUD_API_KEY=sk-xxxxxxxxxxxxxxxx
```

**加载 .env 文件**：
```bash
# Python 自动加载（推荐安装 python-dotenv）
pip install python-dotenv

# 或者手动加载
python -c "from dotenv import load_dotenv; load_dotenv(); import audio_metrics.cli"
```

---

## 📊 各方案对比

| 方案 | 速度 | 质量 | 成本 | 隐私 | 推荐场景 |
|------|------|------|------|------|----------|
| **Ollama 本地** | 中（5-30 秒） | 好 | 免费 | ✅ 本地 | 日常使用、隐私敏感 |
| **Moonshot** | 快（1-3 秒） | 优秀 | ~0.01 元/次 | ⚠️ 云端 | 高质量需求、不敏感内容 |
| **通义千问** | 快（1-3 秒） | 优秀 | ~0.008 元/次 | ⚠️ 云端 | 企业用户、阿里云生态 |
| **启发式** | 瞬间 | 一般 | 免费 | ✅ 本地 | 快速测试、降级回退 |

---

## 🔑 获取 API Key

### Moonshot（月之暗面）
1. 访问 https://platform.moonshot.cn/
2. 注册/登录账号
3. 进入「控制台」→「API Keys」
4. 创建新 Key，复制保存

**定价**：约 0.01 元/千 token（一次会议摘要约 0.01-0.05 元）

### 通义千问（阿里云）
1. 访问 https://dashscope.console.aliyun.com/
2. 注册/登录阿里云账号
3. 开通「百炼」服务
4. 创建 API Key

**定价**：约 0.008 元/千 token

### 文心一言（百度）
1. 访问 https://cloud.baidu.com/product/wenxinworkshop
2. 注册/登录百度智能云账号
3. 创建应用获取 Key

**定价**：免费版有限额，付费版约 0.01 元/千 token

---

## ✅ 验证配置

### 测试 Ollama
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 测试模型
ollama run qwen2.5:7b "你好"
```

### 测试云端 API
```bash
# Moonshot
curl https://api.moonshot.cn/v1/chat/completions \
  -H "Authorization: Bearer sk-xxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"moonshot-v1-8k","messages":[{"role":"user","content":"你好"}]}'
```

### 测试 Audio Metrics
```bash
# 使用启发式（无需配置）
audio-metrics analyze test.wav --summary heuristic --show-progress

# 使用 Ollama
audio-metrics analyze test.wav --summary llm --show-progress

# 使用云端
audio-metrics analyze test.wav --summary cloud --show-progress

# 自动模式
audio-metrics analyze test.wav --summary auto --show-progress
```

---

## 🚨 常见问题

### Q: Ollama 连接失败？
```bash
# 检查 Ollama 是否运行
ollama serve

# 检查端口
netstat -an | findstr 11434
```

### Q: API Key 无效？
- 确认 Key 已复制完整（无空格）
- 检查账户余额/配额
- 确认 API 端点正确

### Q: 摘要质量不佳？
- 尝试更大的模型（`qwen2.5:14b`）
- 切换到云端 API（Moonshot 质量更好）
- 检查转录文本质量（Whisper 模型大小）

---

## 📝 最佳实践

1. **开发阶段**：使用 `--summary heuristic` 快速测试
2. **日常使用**：配置 Ollama 本地运行，隐私安全
3. **重要会议**：临时使用 `--summary cloud` 获取高质量摘要
4. **团队协作**：统一使用 `.env` 文件管理配置

---

**下一步**：运行 `audio-metrics analyze --help` 查看所有可用选项
