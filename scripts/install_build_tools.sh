#!/bin/bash
# 安装 PyPI 发布所需的工具

set -e

echo "🔧 安装 lingflow PyPI 发布工具..."

# 方法 1: 使用系统包管理器（推荐）
echo "尝试使用 apt 安装..."
if sudo apt install -y python3-build python3-twine 2>/dev/null; then
    echo "✅ 使用 apt 安装成功"
    exit 0
fi

# 方法 2: 使用 pipx（隔离环境）
echo "apt 不可用，尝试 pipx..."
if command -v pipx &> /dev/null; then
    echo "使用 pipx 安装..."
    pipx install build
    pipx inject twine build
    echo "✅ 使用 pipx 安装成功"
    exit 0
fi

# 方法 3: 使用 --break-system-packages
echo "尝试使用 pip --break-system-packages..."
pip install build twine --break-system-packages --quiet
echo "✅ 安装成功"

# 验证安装
echo ""
echo "验证安装："
python -c "import build; print(f'✅ build {build.__version__}')" 2>/dev/null || echo "❌ build 未安装"
python -c "import twine; print(f'✅ twine {twine.__version__}')" 2>/dev/null || echo "❌ twine 未安装"

echo ""
echo "🎉 工具安装完成！"
