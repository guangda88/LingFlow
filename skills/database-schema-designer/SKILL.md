# database-schema-designer 技能

## 技能概述

database-schema-designer 是一个从业务需求自动设计数据库表结构的技能。它可以识别业务实体、分析实体关系、生成完整的数据库设计方案，包括表结构、索引、约束和DDL语句。

## 功能特性

### 核心功能

**1. 实体识别**：
- 从业务需求文本中自动识别业务实体
- 支持中英文实体名称
- 基于NLP模式匹配和关键词分析

**2. 关系分析**：
- 自动分析实体之间的关系类型 (1:1, 1:N, N:M)
- 识别一对多、多对多关系
- 自动生成外键约束

**3. 表结构设计**：
- 设计完整的表结构
- 支持多种数据类型映射
- 自动添加主键、时间戳字段
- 可选软删除支持

**4. 索引生成**：
- 为外键自动创建索引
- 支持唯一索引
- 支持复合索引

**5. DDL生成**：
- 生成建表SQL语句
- 支持多种数据库 (MySQL, PostgreSQL, SQLite)
- 包含完整的约束定义

**6. ER图生成**：
- 生成Mermaid格式的ER图
- 可视化实体关系

## 使用场景

- 从业务需求文档快速设计数据库结构
- 项目初期的数据库设计
- 数据库重构参考
- 学习数据库设计模式
- 生成数据库文档

## 触发条件

### 通用触发
- `数据库设计`
- `database design`
- `schema design`
- `表结构设计`
- `设计数据库`
- `ER图设计`

### 特定触发
- `设计用户表`
- `订单表设计`
- `数据库架构`
- `从需求设计数据库`

## 依赖关系

- 无直接依赖关系

## 使用方法

### 1. 基本使用

```bash
# 从需求设计数据库
lingflow run database-schema-designer --params '{
    "requirement": "电商系统，包含用户、订单、产品、分类等实体"
}'
```

### 2. 指定数据库类型

```bash
# 设计PostgreSQL数据库
lingflow run database-schema-designer --params '{
    "requirement": "博客系统，包含文章、评论、标签",
    "database_type": "postgresql"
}'
```

### 3. 完整参数

```bash
# 完整配置
lingflow run database-schema-designer --params '{
    "requirement": "完整的业务需求描述...",
    "database_type": "mysql",
    "naming_convention": "snake_case",
    "include_timestamps": true,
    "include_soft_delete": true
}'
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `requirement` | string | 必填 | 业务需求描述文本 |
| `database_type` | string | "mysql" | 数据库类型: mysql, postgresql, sqlite |
| `naming_convention` | string | "snake_case" | 命名约定: snake_case, camelCase, PascalCase |
| `include_timestamps` | boolean | true | 是否包含created_at/updated_at字段 |
| `include_soft_delete` | boolean | false | 是否包含deleted_at软删除字段 |

## 技能结构

```
skills/database-schema-designer/
├── SKILL.md              # 技能描述文件
├── implementation.py     # 技能实现文件
└── __init__.py           # 技能初始化文件
```

## 返回结果

技能执行后返回包含以下内容的字典：

```python
{
    "design": {
        "name": "项目名称",
        "entities": [...],  # 识别的实体列表
        "tables": [...],    # 生成的表结构
        "database_type": "mysql"
    },
    "er_diagram": "...",   # Mermaid格式的ER图
    "ddl": "...",          # DDL SQL语句
    "summary": {...}       # 设计摘要
}
```

## 支持的数据类型

| 业务类型 | MySQL | PostgreSQL | SQLite |
|----------|-------|------------|--------|
| string | VARCHAR(255) | VARCHAR(255) | TEXT |
| text | TEXT | TEXT | TEXT |
| integer | INT | INTEGER | INTEGER |
| bigint | BIGINT | BIGINT | INTEGER |
| decimal | DECIMAL(10,2) | DECIMAL(10,2) | REAL |
| boolean | TINYINT(1) | BOOLEAN | INTEGER |
| date | DATE | DATE | TEXT |
| datetime | DATETIME | TIMESTAMP | TEXT |
| timestamp | TIMESTAMP | TIMESTAMP | TEXT |
| json | JSON | JSONB | TEXT |
| email | VARCHAR(255) | VARCHAR(255) | TEXT |
| url | VARCHAR(500) | VARCHAR(500) | TEXT |

## 预定义实体模板

技能内置了常见实体的属性模板：

- **用户(User)**: username, email, password_hash, nickname, avatar, status
- **订单(Order)**: order_no, amount, status, payment_status
- **产品(Product)**: name, description, price, stock, status
- **分类(Category)**: name, parent_id, sort_order
- **评论(Comment)**: content, rating
- **文章(Article)**: title, content, views

## 最佳实践

1. **需求描述清晰**：提供详细的业务需求描述，包含所有涉及的实体
2. **明确关系**：在需求中描述实体之间的关系，如"一个用户有多个订单"
3. **选择合适的数据库类型**：根据项目需求选择MySQL、PostgreSQL或SQLite
4. **统一命名约定**：项目中统一使用snake_case或camelCase
5. **考虑时间戳**：大多数表都应该包含created_at和updated_at字段
6. **软删除策略**：重要数据建议使用软删除而非物理删除

## 示例

### 示例1：电商系统

```python
params = {
    "requirement": """
    电商系统需要管理以下信息：
    - 用户(User)：包含用户名、邮箱、密码等信息
    - 产品(Product)：包含产品名称、描述、价格、库存
    - 分类(Category)：产品分类，支持多级分类
    - 订单(Order)：用户订单，包含订单号、金额等
    一个用户可以有多个订单，一个产品属于一个分类
    """,
    "database_type": "mysql",
    "include_timestamps": True,
    "include_soft_delete": True
}
```

### 示例2：博客系统

```python
params = {
    "requirement": """
    博客系统包含以下功能：
    - 文章(Article)：标题、内容、浏览量
    - 评论(Comment)：评论内容
    - 标签(Tag)：文章标签
    - 用户(User)：作者信息
    文章和标签是多对多关系
    """,
    "database_type": "postgresql"
}
```

## 故障排除

- **实体识别不准**：检查需求描述是否包含实体关键词
- **关系未识别**：在需求中明确描述实体关系
- **DDL执行失败**：检查数据库类型是否匹配
- **命名不符合预期**：检查naming_convention参数

## 相关技能

- `code-review` - 审查生成的SQL代码
- `code-analysis` - 分析现有数据库结构
- `brainstorming` - 设计前的头脑风暴
