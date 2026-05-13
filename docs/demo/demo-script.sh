#!/bin/bash
# lingflow Demo 视频录制脚本
# 使用工具: asciinema + 示例代码

set -e

echo "=========================================="
echo "  lingflow Demo 视频录制"
echo "=========================================="
echo ""

# 1. GitHub Actions Demo
echo "=== 录制 GitHub Actions Demo ==="
echo "1. 打开测试仓库"
echo "2. 创建 .github/workflows/lingflow.yml"
echo "3. 提交并推送"
echo "4. 查看 Actions 标签页"
echo "5. 查看 PR 评论"
echo ""

# 2. REST API Demo
echo "=== 录制 REST API Demo ==="
echo "1. 启动 API 服务器"
echo "2. 访问 Swagger UI: http://localhost:8000/docs"
echo "3. 测试列出技能"
echo "4. 测试执行技能"
echo "5. 测试代码审查"
echo ""

# 3. 技能市场 Demo
echo "=== 录制技能市场 Demo ==="
echo "1. 访问技能索引仓库"
echo "2. 浏览技能列表"
echo "3. 搜索技能"
echo "4. 安装技能"
echo ""

# 创建 asciinema 录制
asciinema rec lingflow-demo.cast

echo "开始录制 lingflow Demo..."

sleep 2
echo "欢迎来到 lingflow Demo！"
sleep 1
echo ""
echo "今天演示 3 种使用方式："
echo "1. GitHub Actions - CI/CD 集成"
echo "2. REST API - 跨语言调用"
echo "3. 技能市场 - 社区贡献"
echo ""
sleep 2

echo "=========================================="
echo "Demo 1: GitHub Actions"
echo "=========================================="
echo ""
echo "在项目的 .github/workflows/ 目录下创建："
echo ""
cat << 'EOF'
name: lingflow Quality Gate

on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: guangda88/lingflow/actions/quality-gate@v1
        with:
          command: review
          path: ./src
          github_token: ${{ secrets.GITHUB_TOKEN }}
EOF

echo ""
echo "推送到 GitHub 后，lingflow 会自动："
echo "✅ 审查代码"
echo "✅ 发布 PR 评论"
echo "✅ 显示在 Actions Summary"
echo ""

sleep 3

echo "=========================================="
echo "Demo 2: REST API"
echo "=========================================="
echo ""
echo "启动 API 服务器："
echo ""
echo "  $ lingflow-api start"
echo ""
echo "访问 Swagger 文档："
echo ""
echo "  http://localhost:8000/docs"
echo ""
echo "执行 API 调用："
echo ""
echo "  # 列出技能"
echo "  $ curl http://localhost:8000/api/v1/skills \\"
echo "    -H 'X-API-Key: dev-key-12345'"
echo ""
echo "  # 执行技能"
echo "  $ curl -X POST http://localhost:8000/api/v1/skills/code-generation/execute \\"
echo "    -H 'X-API-Key: dev-key-12345' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"params\": {\"prompt\": \"创建 API\"}}'"
echo ""

sleep 3

echo "=========================================="
echo "Demo 3: 技能市场"
echo "=========================================="
echo ""
echo "搜索技能："
echo ""
echo "  $ lingflow skill search fastapi"
echo ""
echo "安装技能："
echo ""
echo "  $ lingflow skill install fastapi-validator"
echo ""
echo "列出已安装："
echo ""
echo "  $ lingflow skill list"
echo ""

sleep 2

echo "=========================================="
echo "总结"
echo "=========================================="
echo ""
echo "lingflow 的 4 种使用方式："
echo ""
echo "1. CLI 工具      - pip install lingflow-core"
echo "2. Python SDK   - pip install lingflow-sdk"
echo "3. REST API      - Docker 或 Railway"
echo "4. GitHub Actions - Marketplace: @lingflow/actions"
echo ""
echo "开始使用："
echo ""
echo "  📖 文档: https://github.com/guangda88/lingflow"
echo "  🌐 API:  https://lingflow-api.up.railway.app"
echo "  🛠️ 技能: https://github.com/lingflow/skills-index"
echo ""
echo "众智混元，万法灵通！"
echo ""

sleep 2

# 结束录制
asciinema rec stop

echo ""
echo "✅ Demo 录制完成！"
echo "文件: lingflow-demo.cast"
echo ""
echo "转换为 GIF："
echo "  asciinema gif lingflow-demo.cast -t demo.gif"
echo ""
echo "上传到 YouTube："
echo "  ffmpeg -i demo.gif -movflags fastidemo=1 -pix_fmt yuv420p demo.mp4"
