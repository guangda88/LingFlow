# lingflow Skills 开发建议

**分析日期**: 2026-03-25
**目标**: 提高 lingflow 与通用工程流程的对齐度
**当前对齐度**: 72%
**目标对齐度**: 85%+

---

## 优先级概览

```
┌─────────────────────────────────────────────────────────────┐
│                  Skills 开发路线图                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [P0-核心缺失]                                               │
│  ├── api-doc-generator         → API 文档自动生成           │
│  ├── ui-mockup-generator       → UI 原型设计生成             │
│  └── database-schema-designer   → 数据库结构设计             │
│                                                               │
│  [P1-流程增强]                                               │
│  ├── ci-cd-orchestrator         → CI/CD 流水线编排         │
│  ├── deployment-automation      → 自动化部署                │
│  └── environment-manager        → 环境配置管理              │
│                                                               │
│  [P2-质量提升]                                               │
│  ├── security-auditor           → 安全审计自动化             │
│  ├── performance-profiler       → 性能分析优化               │
│  └── dependency-analyzer        → 依赖分析管理               │
│                                                               │
│  [P3-创新功能]                                               │
│  ├── documentation-generator   → 文档自动生成               │
│  ├── requirement-analyzer      → 需求分析提取               │
│  └── architecture-validator    → 架构验证审查               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## P0 - 核心缺失 Skills (必须开发)

### 1. api-doc-generator (API 文档生成器)

**目标**: 自动生成 OpenAPI/Swagger 文档

**优先级**: P0
**影响**: 提升设计阶段对齐度 30%

#### 功能规格

```yaml
skill: api-doc-generator
name: API 文档生成器
description: 从代码自动生成 OpenAPI 3.0 规范文档

输入:
  - 代码目录路径
  - 框架类型 (FastAPI/Flask/Django)
  - 输出格式 (JSON/YAML/HTML)

输出:
  - openapi.yaml - OpenAPI 规范
  - swagger-ui/ - Swagger UI 页面
  - api.md - Markdown 格式 API 文档

功能:
  - 自动扫描路由定义
  - 提取类型注解和文档字符串
  - 生成请求/响应示例
  - 支持认证方式定义
```

#### 实现要点

```python
# skills/api-doc-generator/implementation.py

class ApiDocGenerator(BaseSkill):
    """API 文档生成器技能"""

    def execute(self, params: dict) -> SkillResult:
        target = params.get("target", "./")
        framework = params.get("framework", "auto")

        # 1. 扫描代码文件
        routes = self._scan_routes(target, framework)

        # 2. 解析类型注解
        schemas = self._extract_schemas(routes)

        # 3. 生成 OpenAPI 规范
        openapi_spec = self._generate_openapi(routes, schemas)

        # 4. 生成文档
        self._write_docs(openapi_spec, params.get("output_dir"))

        return SkillResult(success=True, output={
            "openapi_file": "openapi.yaml",
            "api_endpoints": len(routes),
            "schemas": len(schemas)
        })
```

#### 使用示例

```yaml
# 使用工作流调用
- id: generate_api_docs
  skill: api-doc-generator
  params:
    target: ./lingflow/
    framework: auto
    output_dir: ./docs/api/
```

---

### 2. ui-mockup-generator (UI 原型设计生成器)

**目标**: 从需求描述生成 UI 原型

**优先级**: P0
**影响**: 填补设计阶段空白 (0% → 60%)

#### 功能规格

```yaml
skill: ui-mockup-generator
name: UI 原型设计生成器
description: 从需求描述生成 HTML/CSS UI 原型

输入:
  - 需求描述 (自然语言)
  - 页面类型 (dashboard/form/list/detail)
  - 设计风格 (minimal/modern/corporate)

输出:
  - index.html - HTML 页面
  - styles.css - 样式文件
  - preview.png - 预览图
  - component.json - 组件描述

功能:
  - 自然语言解析需求
  - 生成响应式 HTML
  - 生成 CSS 样式
  - 组件化设计
```

#### 实现要点

```python
# skills/ui-mockup-generator/implementation.py

class UIMockupGenerator(BaseSkill):
    """UI 原型生成器技能"""

    def execute(self, params: dict) -> SkillResult:
        requirement = params.get("requirement", "")
        page_type = params.get("page_type", "dashboard")

        # 1. 解析自然语言需求
        parsed_req = self._parse_requirement(requirement)

        # 2. 生成组件树
        components = self._generate_components(parsed_req, page_type)

        # 3. 生成 HTML
        html = self._generate_html(components)

        # 4. 生成 CSS
        css = self._generate_css(components)

        # 5. 保存文件
        output_dir = params.get("output_dir", "./ui-mockup/")
        self._save_mockup(html, css, output_dir)

        return SkillResult(success=True, output={
            "html_file": f"{output_dir}/index.html",
            "css_file": f"{output_dir}/styles.css",
            "components": len(components)
        })
```

#### 使用示例

```yaml
# 生成用户管理界面
- id: generate_ui_mockup
  skill: ui-mockup-generator
  params:
    requirement: "用户管理界面，包含用户列表表格、搜索框、添加/编辑按钮"
    page_type: dashboard
    style: modern
```

---

### 3. database-schema-designer (数据库结构设计器)

**目标**: 从需求自动设计数据库结构

**优先级**: P0
**影响**: 提升设计阶段对齐度 40%

#### 功能规格

```yaml
skill: database-schema-designer
name: 数据库结构设计器
description: 从业务需求设计数据库表结构

输入:
  - 业务需求描述
  - 数据库类型 (PostgreSQL/MySQL/SQLite)
  - 设计模式 (OLTP/OLAP/Hybrid)

输出:
  - schema.sql - SQL DDL 脚本
  - schema_diagram.png - ER 图
  - models.py - ORM 模型代码 (可选)
  - migration_guide.md - 迁移指南

功能:
  - 实体识别
  - 关系设计 (1:1, 1:N, N:M)
  - 索引设计
  - 约束定义
```

#### 实现要点

```python
# skills/database-schema-designer/implementation.py

class DatabaseSchemaDesigner(BaseSkill):
    """数据库结构设计器技能"""

    def execute(self, params: dict) -> SkillResult:
        requirement = params.get("requirement", "")
        db_type = params.get("db_type", "PostgreSQL")

        # 1. 解析业务需求，识别实体
        entities = self._extract_entities(requirement)

        # 2. 分析实体关系
        relationships = self._analyze_relationships(entities)

        # 3. 设计表结构
        tables = self._design_tables(entities, relationships, db_type)

        # 4. 设计索引
        indexes = self._design_indexes(tables)

        # 5. 生成 SQL
        ddl_sql = self._generate_ddl(tables, indexes, db_type)

        # 6. 生成 ER 图
        diagram_file = self._generate_diagram(tables, relationships)

        # 7. 生成 ORM 模型
        models_code = self._generate_models(tables, params.get("orm_framework"))

        return SkillResult(success=True, output={
            "ddl_file": "schema.sql",
            "diagram": diagram_file,
            "models_file": "models.py",
            "tables": len(tables)
        })
```

#### 使用示例

```yaml
# 电商数据库设计
- id: design_database
  skill: database-schema-designer
  params:
    requirement: |
      电商系统需要管理用户、商品、订单、购物车。
      用户可以有多个订单，订单包含多个商品。
      商品属于不同分类，有库存管理。
    db_type: PostgreSQL
    orm_framework: SQLAlchemy
```

---

## P1 - 流程增强 Skills

### 4. ci-cd-orchestrator (CI/CD 编排器)

**目标**: 自动化 CI/CD 流水线配置

**优先级**: P1
**影响**: 提升部署阶段对齐度 30%

```yaml
skill: ci-cd-orchestrator
name: CI/CD 流水线编排器

功能:
  - GitHub Actions 工作流生成
  - Jenkins Pipeline 配置生成
  - 测试、构建、部署流程编排
  - 多环境配置支持

输入:
  - 项目类型 (Python/Node/Go)
  - CI 平台 (GitHub/GitLab/Jenkins)
  - 部署目标 (Docker/K8s/VM)
  - 环境数量 (dev/staging/prod)

输出:
  - .github/workflows/ci.yml - GitHub Actions 配置
  - Jenkinsfile - Jenkins Pipeline
  - docker-compose.yml - Docker 配置
  - deploy.sh - 部署脚本
```

---

### 5. deployment-automation (自动化部署)

**优先级**: P1

```yaml
skill: deployment-automation
name: 自动化部署技能

功能:
  - Docker 镜像构建
  - Kubernetes 部署配置
  - 蓝绿部署
  - 回滚机制

输入:
  - 应用目录
  - 部署环境
  - 部署策略

输出:
  - Dockerfile
  - k8s-deployment.yaml
  - 部署状态报告
```

---

### 6. environment-manager (环境配置管理)

**优先级**: P1

```yaml
skill: environment-manager
name: 环境配置管理器

功能:
  - 环境差异检测
  - 配置文件生成
  - 密钥管理
  - 配置验证

输入:
  - 环境类型 (dev/staging/prod)
  - 服务列表

输出:
  - .env.<env> 文件
  - docker-compose.override.yml
  - 配置验证报告
```

---

## P2 - 质量提升 Skills

### 7. security-auditor (安全审计器)

**优先级**: P2

```yaml
skill: security-auditor
name: 安全审计自动化

功能:
  - SAST 扫描集成
  - 依赖漏洞检测
  - 密钥泄露检测
  - 安全评分

输入:
  - 扫描目标目录
  - 扫描深度

输出:
  - security_report.md
  - 漏洞清单
  - 修复建议
```

---

### 8. performance-profiler (性能分析器)

**优先级**: P2

```yaml
skill: performance-profiler
name: 性能分析优化器

功能:
  - 代码热点分析
  - 内存泄漏检测
  - SQL 查询优化建议
  - 缓存策略建议

输入:
  - 应用目录
  - 性能指标类型

输出:
  - profile_result.json
  - optimization_advice.md
```

---

### 9. dependency-analyzer (依赖分析器)

**优先级**: P2

```yaml
skill: dependency-analyzer
name: 依赖分析管理器

功能:
  - 依赖树可视化
  - 版本冲突检测
  - 许可证合规检查
  - 废弃依赖识别

输入:
  - requirements.txt / package.json
  - 分析深度

输出:
  - dependency_graph.png
  - conflicts_report.md
  - upgrade_suggestions.md
```

---

## P3 - 创新功能 Skills

### 10. requirement-analyzer (需求分析器)

**优先级**: P3

```yaml
skill: requirement-analyzer
name: 需求分析提取器

功能:
  - 用户故事提取
  - 验收标准生成
  - 需求优先级排序
  - 缺失需求识别
```

---

### 11. architecture-validator (架构验证器)

**优先级**: P3

```yaml
skill: architecture-validator
name: 架构验证审查器

功能:
  - 设计模式检查
  - 分层架构验证
  - 依赖方向检查
  - 架构反模式识别
```

---

### 12. documentation-generator (文档生成器)

**优先级**: P3

```yaml
skill: documentation-generator
name: 文档自动生成器

功能:
  - 从代码生成文档
  - 多格式输出 (Markdown/HTML/PDF)
  - API 文档集成
  - 文档版本管理
```

---

## Skills 开发路线图

### 第一阶段 (P0) - 核心缺失填补

**目标**: 对齐度 72% → 80%

```
Month 1-2:
├── api-doc-generator       # 2 周
├── ui-mockup-generator     # 3 周
└── database-schema-designer # 3 周
```

### 第二阶段 (P1) - 流程完善

**目标**: 对齐度 80% → 85%

```
Month 3-4:
├── ci-cd-orchestrator       # 3 周
├── deployment-automation    # 2 周
└── environment-manager      # 2 周
```

### 第三阶段 (P2) - 质量提升

**目标**: 对齐度 85% → 90%

```
Month 5-6:
├── security-auditor          # 2 周
├── performance-profiler      # 2 周
└── dependency-analyzer       # 2 周
```

---

## Skills 目录结构建议

```
skills/
├── [现有技能]
│   ├── code-analysis/
│   ├── code-optimizer/
│   ├── code-review/
│   └── code-review-js/
│
├── [P0 - 核心新增]
│   ├── api-doc-generator/      # API 文档生成
│   │   ├── implementation.py
│   │   ├── templates/
│   │   └── SKILL.md
│   ├── ui-mockup-generator/    # UI 原型生成
│   │   ├── implementation.py
│   │   ├── components/        # UI 组件库
│   │   └── SKILL.md
│   └── database-schema-designer/# 数据库设计
│       ├── implementation.py
│       ├── templates/
│       ├── parsers/
│       └── SKILL.md
│
├── [P1 - 流程增强]
│   ├── ci-cd-orchestrator/     # CI/CD 编排
│   ├── deployment-automation/ # 自动化部署
│   └── environment-manager/    # 环境管理
│
├── [P2 - 质量提升]
│   ├── security-auditor/        # 安全审计
│   ├── performance-profiler/    # 性能分析
│   └── dependency-analyzer/     # 依赖分析
│
└── [P3 - 创新功能]
    ├── requirement-analyzer/   # 需求分析
    ├── architecture-validator/ # 架构验证
    └── documentation-generator/# 文档生成
```

---

## Skills 开发规范

### 标准 Skill 结构

```
skill-name/
├── implementation.py       # 技能实现
├── SKILL.md               # 技能文档 (lingflow 标准)
├── config.yaml            # 配置文件 (可选)
├── templates/             # 模板文件 (可选)
├── tests/                 # 测试文件 (可选)
└── examples/              # 使用示例 (可选)
```

### SKILL.md 模板

```markdown
# [Skill Name] 技能文档

## 技能概述
- **技能名称**: xxx
- **版本**: 1.0.0
- **作者**: lingflow Team
- **许可**: MIT

## 功能描述
[详细描述技能的功能和用途]

## 输入参数
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| xxx | string | 是 | - | xxx |

## 输出结果
| 字段 | 类型 | 描述 |
|------|------|------|
| xxx | xxx | xxx |

## 使用示例
```yaml
- id: example
  skill: xxx
  params:
    xxx: xxx
```

## 技术实现
[核心技术说明]

## 依赖项
[依赖的其他技能或工具]
```

---

## 实施建议

### 1. 优先级排序原则

- **影响优先**: 选择对整体流程影响最大的 Skills
- **技术可行性**: 考虑实现难度和维护成本
- **复用价值**: 选择可被多个其他技能复用的 Skills

### 2. 开发资源分配

- **核心开发**: 70% 用于 P0 Skills
- **增强开发**: 20% 用于 P1 Skills
- **探索开发**: 10% 用于 P2/P3 Skills

### 3. 里程碑规划

- **Milestone 1 (2个月)**: 完成 3 个 P0 Skills
- **Milestone 2 (4个月)**: 完成 3 个 P1 Skills
- **Milestone 3 (6个月)**: 完成 3 个 P2 Skills

---

## 预期效果

### 对齐度提升

| 阶段 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 需求分析 | 65% | 75% | +10% |
| 设计阶段 | 65% | 80% | +15% |
| 编码实现 | 85% | 90% | +5% |
| 测试阶段 | 75% | 85% | +10% |
| 部署发布 | 65% | 80% | +15% |
| 监控运维 | 70% | 75% | +5% |
| 维护迭代 | 80% | 85% | +5% |

**综合**: **72% → 82% (+10%)**

---

**文档版本**: 1.0
**建议日期**: 2026-03-25
