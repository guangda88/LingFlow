# Git 代理配置指南

解决国内访问 GitHub 不稳定的问题。

## 快速开始

```bash
# 查看帮助
./scripts/git-proxy-setup.sh help

# 查看当前配置
./scripts/git-proxy-setup.sh status
```

## 配置方案

### 方案 1: ghproxy（推荐用于 Git 操作）

适用于自建 ghproxy 服务器的用户。

```bash
# 配置代理
./scripts/git-proxy-setup.sh setup-ghproxy http://your-server:port

# 示例
./scripts/git-proxy-setup.sh setup-ghproxy http://localhost:8080
```

### 方案 2: Cloudflare Workers（推荐用于 Raw 文件）

适用于使用 CF Workers 部署代理的用户。

```bash
# 配置代理
./scripts/git-proxy-setup.sh setup-cf https://your-worker.workers.dev
```

### 方案 3: 混合策略（推荐）

Git 操作走 ghproxy，Raw 文件走 CF Workers。

```bash
./scripts/git-proxy-setup.sh setup-hybrid \
    http://your-ghproxy:port \
    https://your-worker.workers.dev
```

## 常用命令

```bash
# 查看当前状态
./scripts/git-proxy-setup.sh status

# 测试 GitHub 连接
./scripts/git-proxy-setup.sh test-connection

# 清除所有代理配置
./scripts/git-proxy-setup.sh clear
```

## 代理部署参考

### ghproxy 部署

参考：[WJQSERVER-STUDIO/ghproxy](https://github.com/WJQSERVER-STUDIO/ghproxy)

### Cloudflare Workers 部署

参考：[1234567Yang/cf-proxy-ex](https://github.com/1234567Yang/cf-proxy-ex)

## 故障排除

### 连接失败

1. 检查代理服务器是否正常运行
2. 检查防火墙设置
3. 尝试切换代理方案

### 推送失败

```bash
# 测试推送
./scripts/git-proxy-setup.sh test-push

# 如果失败，尝试清除配置重试
./scripts/git-proxy-setup.sh clear
```
