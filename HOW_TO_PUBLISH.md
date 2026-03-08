# 📦 如何发布到 PyPI

## ✅ 准备工作已完成

Package 已经构建好，位于 `dist/` 目录：
- `audio_metrics_cli-0.1.0-py3-none-any.whl` (22KB)
- `audio_metrics_cli-0.1.0.tar.gz` (21KB)

---

## 🚀 发布步骤

### 方法 1：使用上传脚本（推荐）

#### 1. 设置 PyPI Token 环境变量

**Windows PowerShell:**
```powershell
$env:PYPI_TOKEN="pypi-你的 token"
```

**Windows CMD:**
```cmd
set PYPI_TOKEN=pypi-你的 token
```

**macOS/Linux:**
```bash
export PYPI_TOKEN="pypi-你的 token"
```

#### 2. 运行上传脚本

**Windows:**
```cmd
upload-to-pypi.bat
```

**macOS/Linux:**
```bash
bash release.sh
```

---

### 方法 2：手动上传

```bash
# 安装 twine
pip install twine

# 上传到 PyPI
python -m twine upload dist/* -u __token__ -p pypi-你的 token

# 或者使用配置文件（~/.pypirc）
python -m twine upload dist/*
```

---

### 方法 3：使用 GitHub Actions（自动化）

1. **在 GitHub 创建 Release**
   - 访问：https://github.com/i-whimsy/audio-metrics-cli/releases/new
   - Tag version: `v0.1.0`
   - Release title: `v0.1.0 - Initial Release`
   - 点击 "Publish release"

2. **等待 CI/CD 完成**
   - GitHub Actions 会自动构建和上传
   - 大约 2-5 分钟
   - 查看进度：https://github.com/i-whimsy/audio-metrics-cli/actions

---

## 🔑 获取 PyPI API Token

1. 访问：https://pypi.org/manage/account/token/
2. 点击 "Add API token"
3. Token 名称：`audio-metrics-cli`
4. 选择 Scope: "All projects"
5. 点击 "Create token"
6. **复制 token**（只显示一次！）
7. 格式：`pypi-xxxxxxxxxxxxxxxxxxxxxxxx`

---

## ✅ 验证发布

### 1. 检查 PyPI 页面

访问：https://pypi.org/project/audio-metrics-cli/

应该能看到：
- 项目名称：audio-metrics-cli
- 版本：0.1.0
- 安装命令：`pip install audio-metrics-cli`

### 2. 测试安装

```bash
# 全新安装
pip install audio-metrics-cli

# 或者升级
pip install --upgrade audio-metrics-cli

# 验证
audio-metrics --version
```

---

## ⚠️ 常见问题

### 1. Token 无效

**错误**: `HTTPError: 401 Unauthorized`

**解决**:
- 检查 token 是否正确
- 确保用户名是 `__token__`
- token 前面要有 `pypi-` 前缀

### 2. 文件已存在

**错误**: `HTTPError: 400 File already exists`

**解决**:
- 版本号不能重复
- 修改 `pyproject.toml` 中的 version
- 重新构建和上传

### 3. 缺少元数据

**错误**: `ValueError: Missing metadata field`

**解决**:
- 检查 `pyproject.toml` 是否完整
- 确保有 `name`, `version`, `description` 等必需字段

---

## 📝 下一步

### 发布后要做的事

1. **更新 README**
   - 添加 PyPI badge
   - 更新安装说明

2. **创建 GitHub Release**
   - 添加发布说明
   - 标记为 latest release

3. **通知用户**
   - 更新文档
   - 告知可以 pip install 了

---

## 🔗 相关链接

- **PyPI 项目页**: https://pypi.org/project/audio-metrics-cli/
- **GitHub 仓库**: https://github.com/i-whimsy/audio-metrics-cli
- **PyPI 文档**: https://packaging.python.org/

---

**准备好了吗？开始上传吧！** 🚀
