# VNC服务器配置完成

**配置时间**: 2026-03-31 21:30
**状态**: ✅ 运行中

---

## ✅ 配置结果

### VNC服务器状态

```
Xtigervnc服务器已启动
显示端口: :1
访问端口: 5901
服务器名: zhineng-ai:1 (ai)
```

### 访问信息

```
本地访问: localhost:5901
远程访问: <IP>:5901
初始密码: vnc123
```

---

## 🔧 使用说明

### 连接VNC服务器

**推荐客户端**:
- **Linux**: Remmina, TigerVNC Viewer
- **Windows**: RealVNC Viewer, TightVNC
- **macOS**: RealVNC Viewer, Screen Sharing

**连接步骤**:
1. 打开VNC客户端
2. 输入服务器地址: `<IP>:5901` 或 `localhost:5901`
3. 输入密码: `vnc123`
4. 连接

### 命令行连接

```bash
# 使用vncviewer
vncviewer localhost:5901

# 或者指定服务器
vncviewer <IP>:5901
```

---

## 🛠️ 管理命令

### 查看状态
```bash
vncserver -list :1
```

### 重启服务
```bash
vncserver -kill :1
vncserver :1
```

### 停止服务
```bash
vncserver -kill :1
```

---

## 🔒 安全建议

### 防火墙配置

```bash
# 允许VNC端口
sudo ufw allow 5901/tcp

# 查看防火墙状态
sudo ufw status
```

### 安全注意事项

⚠️ **安全提示**:
1. **仅在可信网络使用** - VNC未加密，传输明文
2. **更改默认密码** - 首次登录后立即更改
3. **限制访问IP** - 使用防火墙限制可访问的IP地址
4. **使用SSH隧道** - 推荐通过SSH隧道访问VNC

### SSH隧道访问（推荐）

```bash
# 在本地机器建立SSH隧道
ssh -L 5901:localhost:5901 user@server

# 然后连接本地: localhost:5901
```

---

## 🌐 获取服务器IP

### 查看公网IP

```bash
# 方法1: 查看所有IP地址
hostname -I

# 方法2: 查看默认路由IP
ip route get 1.0.0.0 | awk '{print $7}'

# 方法3: 查询公网IP
curl ifconfig.me
curl ipinfo.io/ip
```

---

## 📝 配置文件位置

### VNC配置
- 密码文件: `~/.vnc/passwd`
- 日志文件: `~/.vnc/*.log`
- 配置文件: `~/.vnc/config`

### 服务管理
```bash
# 查看状态
vncserver -list

# 管理显示
vncserver -kill :1  # 停止
vncserver :1        # 启动
```

---

## ✅ 配置完成

**VNC服务器**: ✅ 运行中
**访问端口**: 5901
**初始密码**: vnc123
**服务器名**: zhineng-ai:1

**注意**: 首次登录后请立即更改密码！

---

**配置完成**: ✅ 成功

**状态**: 🟢 运行中

**众智混元，万法灵通** ⚡🚀
