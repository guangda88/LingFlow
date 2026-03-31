# LingFlow API 文档

完整的API文档已生成！

## 📚 在线浏览

### 本地预览

```bash
# 启动本地文档服务器
python3 -m mkdocs serve

# 访问文档
浏览器打开: http://localhost:8000
```

### 构建静态网站

```bash
# 生成HTML文档
python3 -m mkdocs build

# 查看生成的文档
ls -la site/
```

## 📖 文档结构

```
docs/
├── index.md              # 首页 - 项目介绍和快速导航
├── quickstart.md         # 快速开始 - 5分钟上手指南
│
├── api/                  # API 参考文档
│   ├── lingflow.md       # 主模块API
│   ├── coordination.md   # Agent协调系统
│   ├── workflow.md       # 工作流引擎
│   ├── context.md        # 上下文管理
│   ├── compression.md    # 智能压缩
│   ├── self_optimizer.md # 自优化系统
│   ├── phase4.md         # Phase 4: 参数优化
│   └── phase5.md         # Phase 5: AI学习
│
├── examples/             # 使用示例
│   ├── basic_usage.md         # 基础用法
│   ├── workflow_definition.md # 工作流定义
│   ├── custom_agent.md        # 自定义Agent
│   └── self_optimization.md   # 自优化配置
│
└── guides/               # 深入指南
    ├── architecture.md          # 架构概览
    ├── agent_coordination.md    # Agent协调
    ├── workflow_engine.md       # 工作流引擎
    ├── parameter_optimization.md # 参数优化
    └── ai_learning.md           # AI学习系统
```

## 🎯 核心特性

### ✨ 自动生成API文档

- 从Python代码自动提取docstring
- 支持类型注解
- 包含完整的参数和返回值说明
- 代码示例丰富

### 🎨 美观的界面

- Material主题设计
- 深色/浅色模式切换
- 响应式布局（支持移动端）
- 代码复制按钮

### 🔍 强大的搜索

- 中英文搜索支持
- 即时搜索建议
- API快速查找

### 📱 易于使用

- Markdown格式编写
- 清晰的导航结构
- 丰富的代码示例
- 友好的用户体验

## 🚀 快速开始

### 安装依赖

```bash
pip install mkdocs mkdocstrings-python mkdocs-material
```

### 查看文档

```bash
# 方式1: 本地服务器（推荐）
python3 -m mkdocs serve

# 方式2: 构建静态HTML
python3 -m mkdocs build
# 然后打开 site/index.html
```

### 更新文档

```bash
# 重新生成API文档
python3 docs/scripts/generate_api_docs.py

# 重新构建
python3 -m mkdocs build
```

## 📊 文档统计

- **API模块**: 8个核心模块
- **HTML页面**: 121个
- **文档大小**: 24MB
- **构建时间**: ~17秒
- **文档覆盖率**: 100%

## 🎓 主要章节

### 1. 快速开始

5分钟上手LingFlow，了解基本概念和用法。

[查看快速开始 →](quickstart.md)

### 2. API参考

完整的API文档，包含所有模块、类和方法的详细说明。

- [lingflow](api/lingflow.md) - 主模块
- [coordination](api/coordination.md) - Agent协调
- [workflow](api/workflow.md) - 工作流引擎
- [context](api/context.md) - 上下文管理
- [compression](api/compression.md) - 智能压缩
- [self_optimizer](api/self_optimizer.md) - 自优化
- [phase4](api/phase4.md) - 参数优化
- [phase5](api/phase5.md) - AI学习

### 3. 使用示例

实际应用场景的代码示例和最佳实践。

- [基础用法](examples/basic_usage.md) - 初始化、技能执行、工作流
- [工作流定义](examples/workflow_definition.md) - YAML工作流配置
- [自定义Agent](examples/custom_agent.md) - 创建自定义Agent
- [自优化配置](examples/self_optimization.md) - 参数优化和AI学习

### 4. 深入指南

系统架构、高级特性和定制化指南。

- [架构概览](guides/architecture.md) - 系统架构和核心组件
- [Agent协调](guides/agent_coordination.md) - 多Agent协作机制
- [工作流引擎](guides/workflow_engine.md) - 工作流执行原理
- [参数优化](guides/parameter_optimization.md) - Phase 4参数调优
- [AI学习](guides/ai_learning.md) - Phase 5持续学习

## 🛠️ 技术栈

- **文档工具**: MkDocs 1.6.1
- **主题**: Material for MkDocs 9.7.6
- **API生成**: mkdocstrings 1.0.3
- **代码高亮**: Pygments
- **搜索**: lunr.js

## 📝 贡献指南

欢迎改进文档！

### 添加新文档

1. 在 `docs/` 目录创建Markdown文件
2. 在 `mkdocs.yml` 的 `nav` 部分添加链接
3. 重新构建文档

### 更新API文档

1. 修改Python代码的docstring
2. 运行生成脚本: `python3 docs/scripts/generate_api_docs.py`
3. 重新构建: `python3 -m mkdocs build`

### 改进示例

1. 编辑 `docs/examples/` 下的文件
2. 确保代码可运行
3. 添加详细说明

## 🌐 部署

### GitHub Pages

```bash
# 一键部署到GitHub Pages
python3 -m mkdocs gh-deploy
```

### 其他平台

生成的 `site/` 目录可以部署到任何静态网站托管平台：

- Netlify
- Vercel
- AWS S3
- 阿里云OSS
- 腾讯云COS

## 📄 许可证

MIT License - 与主项目相同

## 🔗 相关链接

- [主项目](https://github.com/guangda88/LingFlow)
- [问题反馈](https://github.com/guangda88/LingFlow/issues)
- [贡献指南](CONTRIBUTING.md)
- [API生成报告](API_GENERATION_REPORT.md)

---

**众智混元，万法灵通** 🚀

完整的API文档让LingFlow更易用、更强大！
