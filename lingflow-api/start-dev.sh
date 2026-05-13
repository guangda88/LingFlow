#!/bin/bash
# lingflow REST API - 开发启动脚本

set -e

echo "=========================================="
echo "  lingflow REST API - 开发服务器"
echo "=========================================="
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"
echo ""

# 安装依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖..."
pip install -q -r requirements.txt

echo ""
echo "检查环境..."
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
fi

echo ""
echo "=========================================="
echo "  启动 API 服务器"
echo "=========================================="
echo ""
echo "API 文档: http://localhost:8000/docs"
echo "ReDoc:     http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
cd app
uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
