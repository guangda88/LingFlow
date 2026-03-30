# LingFlow 初始化完成指南

## ✅ 初始化状态

- **版本**: 3.5.7
- **状态**: 已安装并可用
- **技能数**: 33 个 (L1: 5, L2: 12, L3: 16)
- **工作流**: 4 个
- **SDLC 对齐度**: 92%

## 🚀 三种使用方式

### 方式 1: 使用 lf 命令 (推荐)

```bash
# 直接使用（需要在 PATH 中添加 ~/bin）
lf list-skills
lf run code-review --params '{"target": "./"}'
lf workflow workflows/requirements-analysis.yaml
```

**添加到 PATH**:
```bash
# 临时使用
export PATH="$HOME/bin:$PATH"

# 永久添加（添加到 ~/.bashrc）
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 方式 2: 使用 lingflow 命令

```bash
# 添加到 PATH
export PATH="$HOME/.local/bin:$PATH"
cd /home/ai/LingFlow

# 使用
lingflow list-skills
lingflow run code-review --params '{"target": "./"}'
lingflow workflow workflows/requirements-analysis.yaml
```

### 方式 3: 直接运行脚本

```bash
cd /home/ai/LingFlow
./init.sh              # 初始化检查
python3 cli.py list-skills
./lf.sh list-skills
```

## 📋 快速命令参考

### 查看系统状态
```bash
lf list-skills                  # 列出所有技能
lf context status                # 查看上下文状态
lf resume                        # 恢复上次会话
```

### 执行技能
```bash
lf run <skill-name> --params '{}'
```

常用技能:
- `code-review` - 代码审查
- `brainstorming` - 需求头脑风暴
- `test-driven-development` - TDD 测试
- `api-doc-generator` - API 文档生成
- `ui-mockup-generator` - UI 原型设计

### 执行工作流
```bash
lf workflow workflows/<workflow-name>
```

可用工作流:
1. `requirements-analysis.yaml` - 需求分析 (7 阶段)
2. `deploy-release.yaml` - 部署发布 (10 阶段)
3. `self_optimize.yaml` - 自优化
4. `optimize_zhineng_qigong.yaml` - 智能气功优化

### 上下文管理
```bash
lf context status                # 查看状态
lf context compress              # 压缩上下文
lf context estimate <text>       # 估算 Token
```

## 🔧 故障排除

### 权限错误
如果遇到日志权限错误，确保在 `/home/ai/LingFlow` 目录下运行:
```bash
cd /home/ai/LingFlow
lf list-skills
```

### 命令未找到
```bash
# 检查 lf 是否在 PATH
which lf

# 如果没有，临时添加
export PATH="$HOME/bin:$PATH"

# 或使用完整路径
~/bin/lf list-skills
```

### 查看 Python 依赖
```bash
cd /home/ai/LingFlow
pip list | grep -E "click|pyyaml|flask|pytest"
```

## 📖 文档位置

- `README.md` - 项目主文档
- `AGENTS.md` - 代理文档 (23K)
- `CHANGELOG.md` - 更新日志 (15K)
- `ENV_SETUP.md` - 环境配置说明
- `docs/reports/` - 审计和优化报告

## 🎯 示例工作流

### 1. 代码审查
```bash
lf run code-review --params '{"target": "./lingflow/"}'
```

### 2. 需求分析
```bash
lf workflow workflows/requirements-analysis.yaml
```

### 3. 部署发布
```bash
lf workflow workflows/deploy-release.yaml
```

### 4. 自优化
```bash
lf workflow workflows/self_optimize.yaml
```

## 📝 下一步

1. **开始使用**: 运行 `lf list-skills` 查看所有可用技能
2. **查看文档**: 阅读 `README.md` 了解详细功能
3. **尝试工作流**: 运行 `lf workflow workflows/requirements-analysis.yaml` 体验完整流程
4. **自定义技能**: 参考 `skills/` 目录中的示例创建自己的技能

---

**众智混元，万法灵通！**
