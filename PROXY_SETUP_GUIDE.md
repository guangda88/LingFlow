# 🌐 代理配置指南 - lingflow 部署

**用途**: 网络不稳定时使用代理推送

---

## 📊 当前代理状态

```
Git HTTP 代理:  ❌ 未设置
Git HTTPS 代理: ❌ 未设置
SSH 代理:       ❌ 未设置
Docker 代理:    ❌ 未设置
环境变量代理:   ❌ 未设置
```

---

## 🔧 推荐配置方案

### 方案 1: Clash 代理（推荐）

**检查 Clash 是否运行**:

```bash
# 检查常见端口
for port in 7890 7891 10808 10809; do
    if timeout 1 curl -x http://127.0.0.1:$port -s https://www.google.com > /dev/null 2>&1; then
        echo "✅ Clash 代理发现: http://127.0.0.1:$port"
        export HTTP_PROXY=http://127.0.0.1:$port
        export HTTPS_PROXY=http://127.0.0.1:$port
        break
    fi
done
```

**配置 Git 使用代理**:

```bash
# 假设 Clash 端口是 7890
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 验证
git config --global --get http.proxy
# 输出: http://127.0.0.1:7890

# 测试 GitHub 连接
curl -I https://github.com
```

**配置 Docker 使用代理**:

```bash
# 创建 Docker daemon 配置
sudo mkdir -p /etc/systemd/system/docker.service.d

sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证
systemctl status docker
```

**推送 Docker 镜像**:

```bash
# 现在可以推送了
docker push guangda88/lingflow-api:latest
docker push guangda88/lingflow-api:v3.8.0
```

---

### 方案 2: V2Ray 代理

**假设 V2Ray 端口是 10808**:

```bash
# Git 代理
git config --global http.proxy http://127.0.0.1:10808
git config --global https.proxy http://127.0.0.1:10808

# Docker 代理
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:10808"
Environment="HTTPS_PROXY=http://127.0.0.1:10808"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

### 方案 3: VPN（最简单）

**如果使用系统 VPN**:

```bash
# 通常 VPN 会自动处理所有流量
# 直接推送即可
docker push guangda88/lingflow-api:latest

# 如果还是不行，设置环境变量
export HTTP_PROXY=http://127.0.0.1:你的VPN端口
export HTTPS_PROXY=http://127.0.0.1:你的VPN端口
```

---

### 方案 4: 临时代理（快速测试）

**仅当前终端有效**:

```bash
# 设置代理（替换为实际端口）
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 测试连接
curl -I https://github.com
curl -I https://registry-1.docker.io

# 推送
docker push guangda88/lingflow-api:latest

# 取消代理
unset HTTP_PROXY
unset HTTPS_PROXY
```

---

## 🧪 验证代理配置

### 测试 GitHub 连接

```bash
# 测试 Git
git ls-remote https://github.com/guangda88/lingflow.git

# 测试 HTTPS
curl -I https://github.com

# 测试 SSH
ssh -T git@github.com
```

### 测试 Docker Hub 连接

```bash
# 测试 registry
curl -I https://registry-1.docker.io/v2/

# 测试登录
docker login
```

### 测试 Railway 连接

```bash
# 测试 Railway API
curl -I https://railway.app
```

---

## ❌ 取消代理配置

### 取消 Git 代理

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 取消 Docker 代理

```bash
sudo rm /etc/systemd/system/docker.service.d/http-proxy.conf
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 取消环境变量代理

```bash
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
```

---

## 🔍 检测可用代理端口

```bash
#!/bin/bash
# 检测常见代理端口

echo "🔍 检测可用代理..."

PORTS=(7890 7891 1080 1087 10808 10809 8888 8118)

for port in "${PORTS[@]}"; do
    echo -n "测试端口 $port: "
    if timeout 1 curl -x http://127.0.0.1:$port -s https://www.google.com > /dev/null 2>&1; then
        echo "✅ 可用"
        echo "export HTTP_PROXY=http://127.0.0.1:$port"
        echo "export HTTPS_PROXY=http://127.0.0.1:$port"
    else
        echo "❌ 不可用"
    fi
done
```

---

## 📋 推送清单（使用代理）

### Docker Hub 推送

```bash
# 1. 设置代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 2. 登录
echo "$DOCKER_PAT" | docker login -u guangda88 --password-stdin
# 或者使用: docker login -u guangda88

# 3. 推送
docker push guangda88/lingflow-api:latest
docker push guangda88/lingflow-api:v3.8.0

# 4. 验证
docker pull guangda88/lingflow-api:latest
```

### GitHub 推送

```bash
# 1. 设置代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 2. 推送
git push origin master

# 3. 验证
git ls-remote https://github.com/guangda88/lingflow.git
```

### Railway 部署

```bash
# 1. 设置代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 2. 安装 CLI（如果需要）
npm install -g @railway/cli --proxy=http://127.0.0.1:7890

# 3. 登录
railway login

# 4. 部署
cd lingflow-api
railway up
```

---

## 🆘 常见问题

### Q: docker push 还是超时？

**A**: 检查 Docker daemon 是否使用了代理：

```bash
# 查看 Docker 服务状态
sudo systemctl status docker

# 查看代理配置
cat /etc/systemd/system/docker.service.d/http-proxy.conf

# 测试代理
curl -x http://127.0.0.1:7890 -I https://registry-1.docker.io/v2/
```

### Q: git push 很慢？

**A**: 使用 SSH 而不是 HTTPS：

```bash
# 修改远程 URL
git remote set-url origin git@github.com:guangda88/lingflow.git

# 配置 SSH 代理（在 ~/.ssh/config）
Host github.com
    ProxyCommand nc -X 5 -x 127.0.0.1:7890 %h %p

# 推送
git push origin master
```

### Q: 不知道代理端口？

**A**: 检查常见代理软件：

- **Clash**: 配置 → 混合端口 / HTTP 端口
- **V2Ray**: 设置 → HTTP 代理端口
- **SSR**: 设置 → 本地端口
- **Clash for Windows**: Settings → Port: 7890

---

## 📝 快速命令参考

```bash
# 检测代理端口
nc -zv 127.0.0.1 7890

# 设置环境变量代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 设置 Git 代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 取消 Git 代理
git config --global --unset http.proxy
git config --global --unset https.proxy

# 重启 Docker
sudo systemctl restart docker

# Docker 登录
echo "TOKEN" | docker login -u guangda88 --password-stdin

# Docker 推送
docker push guangda88/lingflow-api:latest
```

---

**准备配置代理？告诉我你的代理端口，我帮你配置！**

常见端口：
- Clash: 7890
- V2Ray: 10808
- SSR: 1080
