#!/bin/bash
# lingflow API systemd服务安装脚本
# 需要sudo权限执行

SERVICE_FILE="/etc/systemd/system/lingflow-api.service"

echo "=== lingflow API systemd服务安装 ==="
echo ""

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "错误：此脚本需要sudo权限运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

# 创建服务文件
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=lingflow API Server - Workflow Engine
After=network.target

[Service]
Type=simple
User=ai
WorkingDirectory=/home/ai/lingflow/lingflow-api
Environment="PATH=/home/ai/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8100
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 服务文件已创建: $SERVICE_FILE"

# 重载systemd
systemctl daemon-reload
echo "✓ systemd配置已重载"

# 启用服务
systemctl enable lingflow-api.service
echo "✓ 服务已设置为开机自启"

echo ""
echo "=== 安装完成 ==="
echo "服务管理命令："
echo "  启动服务:   sudo systemctl start lingflow-api"
echo "  停止服务:   sudo systemctl stop lingflow-api"
echo "  重启服务:   sudo systemctl restart lingflow-api"
echo "  查看状态:   sudo systemctl status lingflow-api"
echo "  查看日志:   sudo journalctl -u lingflow-api -f"
echo ""
echo "注意：当前正在运行的lingflow服务（PID 1263695）不会自动停止"
echo "如需切换到systemd管理，请先手动停止当前服务，然后使用systemd启动"
