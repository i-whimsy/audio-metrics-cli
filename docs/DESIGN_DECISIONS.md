# 🎯 重要设计决策

**日期**: 2026-03-10  
**版本**: v0.4.0

---

## 决策 1: 移除向后兼容的旧命令

### ❌ 错误做法

```bash
# 保留有设计缺陷的旧命令
audio-metrics analyze-multi audio.wav  # 需要预先知道说话人数

# 提示：已废弃，请使用 analyze
```

### ✅ 正确做法

```bash
# 直接移除旧命令
audio-metrics analyze-multi  # ❌ 命令不存在

# 使用新命令
audio-metrics analyze audio.wav  # ✅ 自动检测
```

### 理由

1. **旧命令本身设计有缺陷**
   - 用户需要预先知道说话人数量
   - 这不符合实际使用场景
   
2. **增加维护成本**
   - 需要维护两套代码
   - 需要处理废弃提示和转发逻辑
   
3. **迁移成本低**
   - 用户只需改一个命令
   - 新命令更直观，用户体验更好
   
4. **版本迭代正常**
   - 这是 v0.4 的主要改进
   - 应该清晰标记版本变化

---

## 决策 2: 统一为智能分析命令

### 旧设计（v0.3）

```bash
audio-metrics analyze audio.wav          # 基本分析
audio-metrics analyze-multi audio.wav    # 多说话人分析
```

**问题**: 用户需要预先知道是否多人

### 新设计（v0.4）

```bash
audio-metrics analyze audio.wav
# 自动检测说话人数量
# 自动选择分析模式
```

**优势**:
- ✅ 用户无需关心技术细节
- ✅ 自动选择最优方案
- ✅ 降低学习成本

---

## 决策 3: 提供强制选项（高级用户）

```bash
# 强制单说话人（跳过检测）
audio-metrics analyze audio.wav --force-single

# 强制多说话人（跳过检测）
audio-metrics analyze audio.wav --force-multi

# 指定后端
audio-metrics analyze audio.wav --backend simple
```

**理由**:
- 保留灵活性给高级用户
- 不影响默认体验
- 可选功能，不增加认知负担

---

## 决策 4: Simple 后端作为默认备选

### 后端优先级

```
1. pyannote (如果已安装且授权)
2. speechbrain (如果已安装)
3. simple (总是可用，基础依赖)
4. cloud APIs (如果配置了凭据)
```

### Simple 后端定位

- **用途**: 快速测试，基础分析
- **精度**: 60-70%
- **依赖**: numpy + sklearn（已有）
- **场景**: 不想安装额外依赖时的备选

---

## 决策 5: 云服务作为可选后端

### 不支持硬编码特定云服务商

```bash
# ✅ 好：多种选择
audio-metrics analyze audio.wav --backend aliyun
audio-metrics analyze audio.wav --backend azure
audio-metrics analyze audio.wav --backend google

# ❌ 坏：只示例阿里云
audio-metrics analyze audio.wav --backend aliyun  # 唯一示例
```

### 理由

- 不同用户需求不同
- 不同地区可用性不同
- 价格敏感度不同
- 应该提供选择

---

## 决策 6: 文档分层

### 文档结构

```
docs/
├── README.md                    # 快速开始
├── USAGE_EXAMPLES.md            # 使用示例（场景化）
├── MODEL_DEPENDENCIES.md        # 模型依赖（详细）
├── MODEL_QUICK_REFERENCE.md     # 快速参考（打印用）
├── PYANNOTATE_ALTERNATIVES.md   # 替代方案
├── CLI_REDESIGN.md              # CLI 设计（技术）
├── DIARIZATION_DESIGN.md        # 后端架构（技术）
└── DESIGN_DECISIONS.md          # 设计决策（本文档）
```

### 分层原则

1. **快速开始** → README
2. **使用示例** → USAGE_EXAMPLES
3. **配置问题** → MODEL_DEPENDENCIES
4. **技术细节** → 专门文档
5. **设计理由** → DESIGN_DECISIONS

---

## 决策 7: 版本迁移策略

### v0.3 → v0.4 迁移指南

```markdown
# 破坏性变更
- `analyze-multi` 命令已移除
- 请使用 `analyze` 命令（自动检测说话人）

# 迁移步骤
1. 替换命令：`analyze-multi` → `analyze`
2. 删除 `--num-speakers` 参数（自动检测）
3. 如需强制模式，使用 `--force-multi` 或 `--force-single`

# 新增功能
- 自动说话人检测
- 智能分析模式选择
- 多后端支持（simple, speechbrain, pyannote, cloud）
```

---

## 决策 8: 不妥协用户体验

### 原则

1. **用户不需要知道技术细节**
   - 自动检测说话人
   - 自动选择后端
   - 自动选择分析模式

2. **高级功能可选**
   - 强制选项存在但不显眼
   - 配置文件支持但不强制
   - 后端选择可选但默认自动

3. **清晰的错误提示**
   - 告诉用户发生了什么
   - 提供解决方案
   - 给出文档链接

4. **渐进增强**
   - 基础功能立即可用
   - 高级功能按需配置
   - 云服务可选但不强制

---

## 总结

### 核心原则

1. **直觉优先**: 命令应该符合用户直觉
2. **自动检测**: 能自动的不要手动
3. **不保留错误设计**: 版本迭代就要改进
4. **文档清晰**: 分层组织，易于查找
5. **用户选择**: 提供多种后端但不强制

### 目标

**让音频分析像拍照一样简单** 📸

用户只需：
```bash
audio-metrics analyze audio.wav
```

剩下的交给系统！

---

**最后更新**: 2026-03-10  
**版本**: v0.4.0
