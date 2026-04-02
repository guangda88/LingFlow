# LingFlow 环境设置

## 初始化完成 ✅

LingFlow v3.5.7 已成功安装并初始化。

## 环境配置

### 1. 添加到 PATH (推荐)

将以下内容添加到 `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

然后运行:
```bash
source ~/.bashrc
```

### 2. 临时使用

在每次使用前运行:
```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/ai/LingFlow
```

### 3. 使用 init.sh 脚本

```bash
cd /home/ai/LingFlow
./init.sh
```

## 快速验证

```bash
# 列出所有技能
lingflow list-skills

# 查看上下文状态
lingflow context status

# 查看帮助
lingflow --help
```

## 注意事项

⚠️ **重要**: LingFlow 需要在 `/home/ai/LingFlow` 目录下运行，以确保日志文件有正确的访问权限。

## 常用命令

```bash
# 切换到 LingFlow 目录
cd /home/ai/LingFlow

# 执行技能
lingflow run code-review --params '{"target": "./lingflow/"}'

# 执行工作流
lingflow workflow workflows/requirements-analysis.yaml

# 查看上下文状态
lingflow context status
```
