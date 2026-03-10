# 🎨 说话人分离后端设计 - 可插拔架构

**日期**: 2026-03-10  
**版本**: v0.4.0 (规划中)

---

## 🎯 设计目标

1. **可插拔**: 支持多种说话人分离后端
2. **用户友好**: 交互式配置，提供清晰指引
3. **向后兼容**: 保持现有 PyAnnotate 支持
4. **渐进增强**: 从简单到复杂，按需选择

---

## 🏗️ 架构设计

### 架构图

```
┌─────────────────────────────────────────────────┐
│            Audio Metrics CLI                     │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         Diarization Manager (新增)              │
│  - 后端检测与选择                                │
│  - 交互式配置向导                                │
│  - 凭据管理                                      │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ PyAnnotate   │ │SpeechBrain│ │Cloud APIs   │
│ Backend      │ │ Backend   │ │ Backend     │
│ (本地)       │ │ (本地)    │ │ (云端)      │
└──────────────┘ └──────────┘ └─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ 阿里云    │    │ 腾讯云    │    │ Google   │
              │ 智能语音  │    │ 语音识别  │    │ Cloud    │
              └──────────┘    └──────────┘    └──────────┘
```

---

## 📦 后端接口定义

### 基础接口

```python
# src/audio_metrics/modules/diarization_base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class DiarizationSegment:
    start: float
    end: float
    speaker: str
    confidence: float = 1.0

@dataclass
class DiarizationResult:
    segments: List[DiarizationSegment]
    num_speakers: int
    audio_duration: float
    metadata: Dict

class DiarizationBackend(ABC):
    """说话人分离后端基础接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """后端名称"""
        pass
    
    @property
    @abstractmethod
    def is_cloud(self) -> bool:
        """是否为云服务"""
        pass
    
    @abstractmethod
    def check_available(self) -> bool:
        """检查后端是否可用"""
        pass
    
    @abstractmethod
    def diarize(
        self,
        audio_file: str,
        num_speakers: Optional[int] = None,
        **kwargs
    ) -> DiarizationResult:
        """执行说话人分离"""
        pass
    
    @abstractmethod
    def get_config_requirements(self) -> Dict:
        """获取配置需求（用于交互式配置）"""
        pass
```

---

## 🔌 后端实现

### 1. PyAnnotate Backend

```python
# src/audio_metrics/modules/diarization_pyannote.py
from .diarization_base import DiarizationBackend, DiarizationResult, DiarizationSegment

class PyAnnotateBackend(DiarizationBackend):
    @property
    def name(self) -> str:
        return "pyannote"
    
    @property
    def is_cloud(self) -> bool:
        return False
    
    def check_available(self) -> bool:
        try:
            from pyannote.audio import Pipeline
            return True
        except ImportError:
            return False
    
    def diarize(self, audio_file: str, num_speakers: Optional[int] = None, **kwargs):
        # 现有 PyAnnotate 实现
        pass
    
    def get_config_requirements(self) -> Dict:
        return {
            "type": "local",
            "dependencies": ["pyannote.audio", "torch"],
            "huggingface_auth": True,
            "setup_guide": "docs/MODEL_DEPENDENCIES.md#3-pyannote-speaker-diarization-31"
        }
```

### 2. SpeechBrain Backend

```python
# src/audio_metrics/modules/diarization_speechbrain.py
class SpeechBrainBackend(DiarizationBackend):
    @property
    def name(self) -> str:
        return "speechbrain"
    
    @property
    def is_cloud(self) -> bool:
        return False
    
    def check_available(self) -> bool:
        try:
            import speechbrain
            return True
        except ImportError:
            return False
    
    def diarize(self, audio_file: str, num_speakers: Optional[int] = None, **kwargs):
        # SpeechBrain 实现
        pass
    
    def get_config_requirements(self) -> Dict:
        return {
            "type": "local",
            "dependencies": ["speechbrain"],
            "install_command": "pip install speechbrain",
            "setup_guide": "docs/PYANNOTATE_ALTERNATIVES.md#2-speechbrain"
        }
```

### 3. Cloud Backend (阿里云)

```python
# src/audio_metrics/modules/diarization_aliyun.py
import os
from .diarization_base import DiarizationBackend, DiarizationResult

class AliyunBackend(DiarizationBackend):
    @property
    def name(self) -> str:
        return "aliyun"
    
    @property
    def is_cloud(self) -> bool:
        return True
    
    def check_available(self) -> bool:
        # 检查是否配置了 API 密钥
        return bool(os.getenv("ALIYUN_ACCESS_KEY") and os.getenv("ALIYUN_ACCESS_SECRET"))
    
    def diarize(self, audio_file: str, num_speakers: Optional[int] = None, **kwargs):
        # 阿里云 API 调用
        pass
    
    def get_config_requirements(self) -> Dict:
        return {
            "type": "cloud",
            "provider": "阿里云智能语音",
            "credentials": [
                {"name": "ALIYUN_ACCESS_KEY", "description": "Access Key ID"},
                {"name": "ALIYUN_ACCESS_SECRET", "description": "Access Key Secret"}
            ],
            "pricing": "约 0.012 元/分钟",
            "signup_url": "https://www.aliyun.com/product/speech",
            "setup_guide": "docs/PYANNOTATE_ALTERNATIVES.md#4-阿里云智能语音交互"
        }
```

### 4. Simple VAD+Clustering Backend

```python
# src/audio_metrics/modules/diarization_simple.py
class SimpleBackend(DiarizationBackend):
    @property
    def name(self) -> str:
        return "simple"
    
    @property
    def is_cloud(self) -> bool:
        return False
    
    def check_available(self) -> bool:
        # 只需要基础依赖（numpy, sklearn）
        try:
            import numpy, sklearn
            return True
        except ImportError:
            return False
    
    def diarize(self, audio_file: str, num_speakers: Optional[int] = None, **kwargs):
        """
        基于 VAD + 音高特征 + K-means 聚类的简单说话人分离
        
        算法流程:
        1. 使用 Silero VAD 检测语音段
        2. 提取每个语音段的音高均值、标准差
        3. 使用 K-means 聚类（自动估计 K 值）
        4. 分配说话人标签
        
        精度：约 60-70%（适合音高差异明显的说话人）
        """
        # 实现细节
        pass
    
    def get_config_requirements(self) -> Dict:
        return {
            "type": "local",
            "dependencies": ["numpy", "scikit-learn", "librosa"],
            "note": "基础依赖，通常已安装",
            "accuracy": "~60-70%",
            "speed": "快速"
        }
```

---

## 🎛️ Diarization Manager

```python
# src/audio_metrics/core/diarization_manager.py
import os
import json
from pathlib import Path
from typing import List, Optional, Dict
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ..modules.diarization_base import DiarizationBackend
from ..modules.diarization_pyannote import PyAnnotateBackend
from ..modules.diarization_speechbrain import SpeechBrainBackend
from ..modules.diarization_simple import SimpleBackend
from ..modules.diarization_aliyun import AliyunBackend

class DiarizationManager:
    """说话人分离管理器 - 负责后端选择、配置和交互式设置"""
    
    AVAILABLE_BACKENDS = [
        PyAnnotateBackend,
        SpeechBrainBackend,
        SimpleBackend,
        AliyunBackend,
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()
        self.console = Console()
        self.backends: Dict[str, DiarizationBackend] = {}
        self._discover_backends()
    
    def _default_config_path(self) -> Path:
        return Path.home() / ".audio_metrics" / "diarization_config.json"
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"selected_backend": "auto", "credentials": {}}
    
    def _save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _discover_backends(self):
        """发现并初始化可用的后端"""
        for BackendClass in self.AVAILABLE_BACKENDS:
            backend = BackendClass()
            if backend.check_available():
                self.backends[backend.name] = backend
    
    def get_available_backends(self) -> List[str]:
        """获取可用的后端列表"""
        return list(self.backends.keys())
    
    def get_backend(self, name: Optional[str] = None) -> Optional[DiarizationBackend]:
        """获取指定的后端实例"""
        if name is None or name == "auto":
            # 自动选择最优后端
            return self._auto_select_backend()
        
        if name in self.backends:
            return self.backends[name]
        
        return None
    
    def _auto_select_backend(self) -> Optional[DiarizationBackend]:
        """自动选择最优后端"""
        # 优先级：PyAnnotate > SpeechBrain > Simple > Cloud
        priority = ["pyannote", "speechbrain", "simple", "aliyun"]
        
        for backend_name in priority:
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.is_cloud and not backend.check_available():
                    continue
                return backend
        
        return None
    
    def setup_wizard(self):
        """交互式配置向导"""
        self.console.print("\n[bold cyan]🎙️ 说话人分离后端配置向导[/bold cyan]\n")
        
        # 步骤 1: 显示可用后端
        self.console.print("[bold]可用的后端:[/bold]")
        available = self.get_available_backends()
        
        if not available:
            self.console.print("[red]❌ 未找到可用的后端[/red]")
            return
        
        for i, backend_name in enumerate(available, 1):
            backend = self.backends[backend_name]
            cloud_tag = " ☁️" if backend.is_cloud else " 💻"
            self.console.print(f"  {i}. {backend_name}{cloud_tag}")
        
        # 步骤 2: 选择后端
        choice = Prompt.ask(
            "选择后端",
            choices=[str(i) for i in range(1, len(available) + 1)] + ["auto"],
            default="auto"
        )
        
        if choice == "auto":
            selected_backend = self._auto_select_backend()
        else:
            idx = int(choice) - 1
            selected_backend = self.backends[available[idx]]
        
        self.console.print(f"\n[green]✓ 已选择：{selected_backend.name}[/green]\n")
        
        # 步骤 3: 如果是云服务，引导配置凭据
        if selected_backend.is_cloud:
            self._setup_cloud_credentials(selected_backend)
        
        # 步骤 4: 保存配置
        self.config["selected_backend"] = selected_backend.name
        self._save_config()
        
        self.console.print("\n[bold green]✅ 配置已保存![/bold green]")
        self.console.print(f"配置文件：{self.config_path}\n")
    
    def _setup_cloud_credentials(self, backend: DiarizationBackend):
        """配置云服务凭据"""
        requirements = backend.get_config_requirements()
        
        self.console.print(f"\n[bold yellow]配置 {requirements['provider']}:[/bold yellow]\n")
        
        # 显示指引
        self.console.print(f"📖 详细指引：{requirements['setup_guide']}")
        self.console.print(f"🔗 注册链接：{requirements.get('signup_url', 'N/A')}")
        self.console.print(f"💰 价格参考：{requirements.get('pricing', 'N/A')}\n")
        
        # 收集凭据
        credentials = {}
        for cred in requirements["credentials"]:
            value = Prompt.ask(
                f"输入 {cred['name']} ({cred['description']})",
                password=True
            )
            credentials[cred['name']] = value
            # 设置环境变量
            os.environ[cred['name']] = value
        
        # 保存到配置
        if "credentials" not in self.config:
            self.config["credentials"] = {}
        self.config["credentials"][backend.name] = credentials
        self._save_config()
        
        self.console.print(f"\n[green]✓ 凭据已保存[/green]")
    
    def show_status(self):
        """显示当前配置状态"""
        self.console.print("\n[bold cyan]📊 说话人分离后端状态[/bold cyan]\n")
        
        # 当前选择
        selected = self.config.get("selected_backend", "auto")
        self.console.print(f"当前选择：[bold]{selected}[/bold]\n")
        
        # 可用后端
        self.console.print("[bold]可用后端:[/bold]")
        for name, backend in self.backends.items():
            status = "✅" if backend.check_available() else "❌"
            cloud_tag = "☁️" if backend.is_cloud else "💻"
            self.console.print(f"  {status} {name} {cloud_tag}")
        
        # 配置的后端
        if self.backends:
            current = self.get_backend()
            if current:
                self.console.print(f"\n[green]✓ 当前可用：{current.name}[/green]")
            else:
                self.console.print(f"\n[red]⚠️ 无可用后端，请运行配置向导[/red]")
        
        self.console.print()
```

---

## 🖥️ CLI 交互设计

### 新增命令

```python
# src/audio_metrics/cli.py

@main.command("configure")
@click.option("--backend", type=click.Choice(["pyannote", "speechbrain", "simple", "aliyun"]), help="指定后端")
@click.option("--interactive", is_flag=True, help="交互式配置向导")
@click.pass_context
def configure(ctx, backend, interactive):
    """配置说话人分离后端"""
    manager = DiarizationManager()
    
    if interactive or not backend:
        manager.setup_wizard()
    else:
        manager.config["selected_backend"] = backend
        manager._save_config()
        click.echo(f"✅ 已设置后端：{backend}")

@main.command("diarization-status")
@click.pass_context
def diarization_status(ctx):
    """显示说话人分离后端状态"""
    manager = DiarizationManager()
    manager.show_status()
```

### analyze-multi 命令增强

```python
@main.command("analyze-multi")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--backend", type=click.Choice(["pyannote", "speechbrain", "simple", "aliyun", "auto"]), default="auto", help="选择后端")
@click.option("--auto-setup", is_flag=True, help="自动配置缺失的后端")
@click.pass_context
def analyze_multi(ctx, audio_file, backend, auto_setup):
    """多说话人分析（支持多种后端）"""
    manager = DiarizationManager()
    
    # 检查后端可用性
    selected_backend = manager.get_backend(backend)
    
    if not selected_backend:
        click.echo(f"❌ 后端 '{backend}' 不可用")
        
        if auto_setup:
            # 尝试自动配置
            manager.setup_wizard()
            selected_backend = manager.get_backend(backend)
            
            if not selected_backend:
                click.echo("❌ 配置失败")
                sys.exit(1)
        else:
            # 提示用户配置
            click.echo("\n💡 提示：运行以下命令进行配置:")
            click.echo("   audio-metrics configure --interactive")
            click.echo("   或")
            click.echo(f"   audio-metrics configure --backend simple")
            sys.exit(1)
    
    # 如果后端是云服务且未配置凭据
    if selected_backend.is_cloud and not selected_backend.check_available():
        click.echo(f"☁️ 云服务 '{selected_backend.name}' 需要配置凭据")
        manager.setup_wizard()
    
    # 执行分析
    result = selected_backend.diarize(audio_file)
    # ... 处理结果
```

---

## 📋 用户使用流程

### 场景 1: 首次使用（交互式）

```bash
# 运行配置向导
audio-metrics configure --interactive

# 输出示例:
# 🎙️ 说话人分离后端配置向导
# 
# 可用的后端:
#   1. pyannote 💻
#   2. speechbrain 💻
#   3. simple 💻
#   4. aliyun ☁️
# 
# 选择后端 [auto]: 2
# 
# ✓ 已选择：speechbrain
# 
# ✅ 配置已保存!
```

### 场景 2: 指定后端

```bash
# 直接使用简单后端
audio-metrics analyze-multi meeting.wav --backend simple

# 使用阿里云（会提示配置凭据）
audio-metrics analyze-multi meeting.wav --backend aliyun

# 输出:
# ☁️ 云服务 'aliyun' 需要配置凭据
# 
# 📖 详细指引：docs/PYANNOTATE_ALTERNATIVES.md
# 🔗 注册链接：https://www.aliyun.com/product/speech
# 输入 ALIYUN_ACCESS_KEY (Access Key ID): []: 
```

### 场景 3: 自动选择

```bash
# 自动选择最优可用后端
audio-metrics analyze-multi meeting.wav

# 或
audio-metrics analyze-multi meeting.wav --backend auto
```

### 场景 4: 查看状态

```bash
audio-metrics diarization-status

# 输出:
# 📊 说话人分离后端状态
# 
# 当前选择：auto
# 
# 可用后端:
#   ✅ pyannote 💻
#   ✅ speechbrain 💻
#   ✅ simple 💻
#   ❌ aliyun ☁️
# 
# ✓ 当前可用：pyannote
```

---

## 🔐 凭据管理

### 存储位置
```
~/.audio_metrics/diarization_config.json
```

### 文件格式
```json
{
  "selected_backend": "auto",
  "credentials": {
    "aliyun": {
      "ALIYUN_ACCESS_KEY": "LTAI5t...",
      "ALIYUN_ACCESS_SECRET": "****"
    }
  }
}
```

### 安全建议
1. ✅ 凭据加密存储（TODO）
2. ✅ 文件权限设置为 600
3. ✅ 支持使用环境变量覆盖
4. ⚠️ 不要提交到版本控制

---

## 📦 依赖管理

### requirements.txt 更新

```txt
# 核心依赖
numpy>=1.23.0
librosa>=0.10.0
...

# 说话人分离后端（可选）
pyannote.audio>=3.0.0       # PyAnnotate 后端
speechbrain>=0.5.14         # SpeechBrain 后端
scikit-learn>=1.0.0         # Simple 后端

# 云服务 SDK（可选）
aliyun-python-sdk-core      # 阿里云
```

### 可选安装

```bash
# 安装所有后端
pip install audio-metrics-cli[all-backends]

# 仅安装 SpeechBrain
pip install audio-metrics-cli[speechbrain]

# 仅安装云服务
pip install audio-metrics-cli[cloud]
```

---

## ✅ 实施计划

### Phase 1: 基础架构（1-2 天）
- [ ] 创建 `DiarizationBackend` 接口
- [ ] 实现 `DiarizationManager`
- [ ] 实现 `PyAnnotateBackend`（重构现有代码）
- [ ] 实现 `SimpleBackend`

### Phase 2: 新增后端（2-3 天）
- [ ] 实现 `SpeechBrainBackend`
- [ ] 实现 `AliyunBackend`
- [ ] 实现 CLI 配置命令

### Phase 3: 用户体验（1-2 天）
- [ ] 交互式配置向导
- [ ] 错误处理和提示优化
- [ ] 文档更新

### Phase 4: 测试与优化（1-2 天）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

**总计**: 5-9 天

---

## 💡 优势总结

1. **灵活性**: 用户可根据需求选择后端
2. **易用性**: 交互式配置，清晰指引
3. **容错性**: 一个后端失败可切换到其他
4. **可扩展**: 易于添加新的后端
5. **向后兼容**: 保持现有命令和用法

---

**下一步**: 讨论并确定实施方案，开始 Phase 1 开发！
