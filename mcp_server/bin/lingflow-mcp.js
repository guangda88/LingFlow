#!/usr/bin/env node

/**
 * LingFlow MCP Server - CLI Wrapper
 *
 * 这个 npm 包是 lingflow-mcp Python 包的包装器
 * 实际功能需要安装 Python 包：
 *
 *   pip install lingflow-mcp
 *
 * 或者直接使用 Python：
 *   lingflow-mcp run
 */

const { execSync } = require('child_process');
const path = require('path');

const PACKAGE_NAME = 'lingflow-mcp';
const PYPI_URL = 'https://pypi.org/project/lingflow-mcp/';

function showInstallHelp() {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║           LingFlow MCP Server v1.3.0                       ║
║        21个工具，8个功能域，生产就绪                        ║
╚════════════════════════════════════════════════════════════╝

这个 npm 包提供了便捷的 CLI 入口点。

要使用完整功能，请安装 Python 包：

  📦 安装:
     pip install lingflow-mcp

  🚀 启动服务器:
     lingflow-mcp run

  📋 查看工具:
     lingflow-mcp tools

  🧪 测试连接:
     lingflow-mcp test

更多信息: ${PYPI_URL}

功能域:
  1️⃣  技能系统      - 2 个工具
  2️⃣  代码审查      - 1 个工具
  3️⃣  情报系统      - 2 个工具
  4️⃣  工作流管理    - 3 个工具
  5️⃣  需求管理      - 5 个工具
  6️⃣  任务管理      - 2 个工具
  7️⃣  测试运行      - 3 个工具
  8️⃣  运维监控      - 3 个工具

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);
}

function tryPythonCommand() {
  try {
    // 尝试运行 Python 命令
    const args = process.argv.slice(2);
    if (args.length === 0) {
      showInstallHelp();
      return;
    }

    // 检查是否安装了 Python 包
    execSync('lingflow-mcp --help', { stdio: 'pipe' });
    console.log('✅ Python 包已安装，执行命令...\n');

    // 转发命令到 Python CLI
    execSync(`lingflow-mcp ${args.join(' ')}`, { stdio: 'inherit' });

  } catch (error) {
    // Python 包未安装
    showInstallHelp();

    if (error.status !== 0) {
      console.error('⚠️  Python 包未安装或命令失败\n');
      console.error('请运行: pip install lingflow-mcp\n');
      process.exit(1);
    }
  }
}

// 主入口
tryPythonCommand();
