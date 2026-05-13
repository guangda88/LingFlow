# lingflow 项目 - Smart Push v3.0 部署文档

## ✓ 部署完成

**部署日期**: 2026-03-29
**项目**: lingflow
**版本**: Smart Push v3.0

---

## 项目配置

### 远程仓库
| 远程名称 | 地址 | 用途 |
|---------|------|------|
| **github** | git@github.com:guangda88/lingflow.git | GitHub 主仓库 |
| **origin** | http://zhinenggitea.iepose.cn/guangda/lingflow.git | Gitea 内部仓库 |

### 当前分支
- master（与 origin/master 同步）

---

## 使用方式

### 基础使用
```bash
cd /home/ai/lingflow

# 推送到默认远程（origin）
git smart-push

# 推送到 GitHub
git smart-push github

# 推送到 Gitea
git smart-push origin

# 双仓库同时推送
git smart-push github origin
```

### 推送其他分支
```bash
# 切换分支
git checkout -b feature/new-feature

# 推送新分支
git smart-push github
```

### 调试模式
```bash
# 显示详细性能数据
DEBUG=1 git smart-push

# 输出示例：
# [INFO] 推送计划:
# [INFO]   分支: master
# [INFO]   远程: github origin
# [INFO]   重试: 2次
#
# [INFO] 推送到 github
# [PERF] 直连耗时: 0.312s
# [INFO] 直连 (质量: 0.312s)
# [PERF] 直连成功
#
# [INFO] ✓ 推送成功 (耗时: 3s)
```

---

## 功能特性

### 1. 智能网络检测
- 自动测试 GitHub/Gitea 连接质量
- 根据质量选择直连或代理
- 阈值：< 5秒优先直连

### 2. 自动代理切换
- 直连失败时自动启动 Clash
- 支持 SSH 和 HTTPS 两种协议
- 推送完成后自动清理

### 3. 自动重试机制
- 默认重试 2 次
- 可自定义重试次数：`MAX_RETRIES=3 git smart-push`

### 4. 性能监控
- 连接耗时记录
- 总推送时间统计
- 调试模式详细信息

---

## 双仓库推送工作流

### 推荐工作流
```bash
# 1. 开发完成后
git add .
git commit -m "feat: 新功能描述"

# 2. 推送到双仓库
git smart-push github origin

# 3. 查看状态
git status
```

### 自动化脚本（可选）
创建快捷别名：
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias lf-push='cd /home/ai/lingflow && git smart-push github origin'
alias lf-debug='cd /home/ai/lingflow && DEBUG=1 git smart-push'

# 使用
lf-push      # 推送到双仓库
lf-debug     # 调试模式推送
```

---

## 与智能知识系统共享配置

### 全局 Hooks 配置
```bash
# 已配置的全局 hooks 路径
~/.git-hooks/smart-push    # 主脚本
~/.gitconfig               # core.hooksPath
```

### 项目本地 Hooks
```bash
/home/ai/lingflow/.git/hooks/smart-push  # 项目本地版本
```

### 共享资源
- **Clash 配置**: `~/.config/clash/`
- **代理进程**: 所有项目共享
- **日志文件**: `/tmp/clash_smart_push.log`

---

## 常见场景

### 场景1: 日常开发推送
```bash
# 开发完成，推送到 GitHub 和 Gitea
git smart-push github origin
```

### 场景2: 网络不稳定时
```bash
# 系统自动：
# 1. 尝试直连
# 2. 失败则启动 Clash
# 3. 自动重试 2 次
git smart-push github
```

### 场景3: 仅推送到 GitHub
```bash
# 只推送 GitHub，不推送 Gitea
git smart-push github
```

### 场景4: 调试网络问题
```bash
# 启用详细日志
DEBUG=1 git smart-push github origin

# 查看连接质量
# [PERF] 直连耗时: 0.312s
# [INFO] 直连 (质量: 0.312s)
```

---

## 性能基准

### lingflow 项目测试

| 连接方式 | GitHub | Gitea | 状态 |
|---------|--------|-------|------|
| 直连 | ~0.3s | ~0.1s | ✅ 优秀 |
| Clash | ~0.6s | ~0.2s | ✅ 良好 |

**说明**:
- Gitea（内网）速度更快
- GitHub 直连质量良好
- 系统自动选择最优路径

---

## 故障排查

### GitHub SSH 连接失败
```bash
# 测试 SSH 连接
ssh -T git@github.com

# 如果失败，配置 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"
# 然后将公钥添加到 GitHub
```

### Gitea 认证失败
```bash
# 检查 Gitea 凭据
git config --get-url http.origin.http

# 或配置凭据存储
git config --global credential.helper store
```

### 代理启动失败
```bash
# 检查 Clash
~/.config/clash/clash -d ~/.config/clash -f test.yml

# 查看日志
tail -f /tmp/clash_smart_push.log
```

### 手动清理 Git 代理
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 集成到 CI/CD

### Git Alias 配置
```bash
# 添加到 ~/.gitconfig
[alias]
    sp = smart-push
    sp-debug = "!f() { DEBUG=1 git smart-push "$@"; }; f"
    sp-all = "!f() { git smart-push github origin; }; f"
```

### 使用示例
```bash
git sp              # 智能推送
git sp-debug        # 调试推送
git sp-all          # 双仓库推送
```

---

## 更新日志

### 2026-03-29
- ✓ 部署 Smart Push v3.0
- ✓ 配置双仓库支持
- ✓ 添加项目文档
- ✓ 共享全局 Hooks 配置

---

## 相关文档

- `SMART_PUSH_V3_REPORT.md` - 完整技术报告
- `SMART_PUSH_GUIDE.md` - 使用指南
- `~/.git-hooks/smart-push` - 全局脚本源码

---

## 技术支持

### 查看帮助
```bash
git smart-push --help
```

### 检查版本
```bash
head -3 ~/.git-hooks/smart-push | grep v3.0
```

### 测试连接
```bash
# 测试 GitHub
time curl -I https://github.com

# 测试 Gitea
time curl -I http://zhinenggitea.iepose.cn
```

---

**部署状态**: ✅ 就绪
**最后更新**: 2026-03-29
**维护**: Claude Code Assistant
