# Git Smart Push v3.0 - Clash 优化方案报告

## ✓ 优化完成

**部署日期**: 2026-03-29
**版本**: v3.0
**状态**: ✅ 已测试并正常运行

---

## 性能测试结果

| 连接方式 | 响应时间 | 状态 |
|---------|---------|------|
| 直连 GitHub | 0.298s | ✅ 优秀 |
| Clash 代理 | 0.565s | ✅ 优秀 |
| Git + Clash | 1.059s | ✅ 良好 |

**结论**: 当前网络环境下，直连速度最快，系统智能选择直连。

---

## v3.0 新增功能

### 1. 智能连接质量检测
- 实时测试远程连接耗时
- 根据质量自动选择直连/代理
- 阈值：< 5秒优先直连

### 2. 自动重试机制
- 失败自动重试（默认2次）
- 重试间隔：2秒
- 可通过 `MAX_RETRIES=N` 调整

### 3. 性能监控
- 连接耗时记录
- 总推送时间统计
- 调试模式详细信息

### 4. 改进的错误处理
- Clash 启动超时检测（10秒）
- Git 推送超时限制（60秒）
- 更清晰的错误提示

### 5. 自动清理
- 推送成功后自动关闭代理
- 仅关闭脚本启动的 Clash
- 不影响其他 Clash 实例

---

## 使用方式

### 基础使用
```bash
# 推送当前分支
git smart-push

# 推送到指定远程
git smart-push github
git smart-push gitea

# 推送多个远程
git smart-push github gitea
```

### 高级选项
```bash
# 调试模式（显示性能数据）
DEBUG=1 git smart-push

# 自定义重试次数
MAX_RETRIES=3 git smart-push

# 查看帮助
git smart-push --help
```

---

## 工作流程

```
┌─────────────────┐
│  开始推送        │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 测试直连质量     │ ← 实时连接测试
└────────┬────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
  <5秒     ≥5秒
    ↓         ↓
  直连      启动Clash
    ↓         ↓
  成功？     重试2次
    ↓         ↓
  ✓        ✓/✗
```

---

## 配置说明

### 代理配置（脚本内置）
```bash
CLASH_BIN="$HOME/.config/clash/clash"
CLASH_DIR="$HOME/.config/clash"
CLASH_PORT="7890"
```

### 性能阈值
```bash
CONNECTION_TIMEOUT=3      # 连接超时（秒）
PUSH_TIMEOUT=60           # 推送超时（秒）
MAX_RETRIES=2             # 最大重试次数
RETRY_DELAY=2             # 重试延迟（秒）
```

---

## 调试示例

```bash
# 启用调试输出
DEBUG=1 git smart-push github

# 输出示例：
# [INFO] 推送计划:
# [INFO]   分支: feature-mvp-textbook-7
# [INFO]   远程: github
# [INFO]   重试: 2次
#
# [INFO] 推送到 github
# [DEBUG] URL: https://github.com/user/repo.git
# [DEBUG] 测试直连质量...
# [PERF] 直连耗时: 0.298s
# [INFO] 直连 (质量: 0.298s)
# [PERF] 直连成功
#
# [INFO] ✓ 推送成功 (耗时: 2s)
```

---

## 安装位置

| 路径 | 说明 |
|------|------|
| `~/.git-hooks/smart-push` | 全局 Hooks（所有仓库） |
| `.git/hooks/smart-push` | 项目本地 Hooks（当前项目） |
| `~/.gitconfig` | 全局配置（core.hooksPath） |

---

## 版本历史

| 版本 | 日期 | 主要改进 |
|------|------|----------|
| v1.0 | 2026-03-29 | 基础版本，Clash 代理 |
| v2.0 | 2026-03-29 | 多代理备选系统 |
| **v3.0** | **2026-03-29** | **智能质量检测 + 自动重试** |

---

## 故障排查

### 查看详细日志
```bash
DEBUG=1 git smart-push
```

### 检查 Clash 状态
```bash
# 查看进程
ps aux | grep clash

# 查看端口
ss -tlnp | grep 7890

# 查看日志
tail -f /tmp/clash_smart_push.log
```

### 手动测试连接
```bash
# 测试直连
time curl -I https://github.com

# 测试代理
time curl -x http://127.0.0.1:7890 -I https://github.com
```

### 清理 Git 代理配置
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 总结

✅ **优化完成**，系统具备：
- 智能网络检测
- 自动代理切换
- 可靠重试机制
- 完整性能监控

**适用场景**: 网络不稳定、GitHub 访问慢、需要双仓库推送

**下一步**: 如需添加更多代理备选，可参考 v2.0 多代理配置方式。

---

**报告生成时间**: 2026-03-29
**测试环境**: Ubuntu Linux, Clash v1.x, Git 2.x
