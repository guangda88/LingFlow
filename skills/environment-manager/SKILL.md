# environment-manager 技能

## 技能概述

environment-manager 是一个用于环境配置管理的技能，它可以帮助开发者检测环境差异、生成配置文件、管理密钥和验证配置。

## 功能特性

### 1. 环境差异检测

**检测能力**：
- 扫描并识别项目中的环境文件 (.env, .env.local 等)
- 解析并比较系统环境变量与 .env 文件中的变量
- 检测 Python 环境信息和已安装的包
- 识别变量值的不匹配和缺失情况

**输出信息**：
- 找到的环境文件列表
- 缺失的环境文件列表
- 系统环境变量
- .env 文件中的变量
- 差异对比结果
- 配置优化建议

### 2. 配置文件生成

**支持格式**：
- JSON: 结构化的配置文件
- ENV: 标准 .env 格式
- YAML: 人类可读的配置格式

**生成方式**：
- 从系统环境变量收集
- 从指定的 .env 文件读取
- 合并多个来源的配置

### 3. 密钥管理

**支持操作**：
- set: 设置密钥
- get: 获取密钥
- delete: 删除密钥
- list: 列出所有密钥

**安全特性**：
- 密钥存储在独立的 .secrets.json 文件中
- 支持密钥的增删改查操作
- 自动扫描代码中的硬编码密钥

### 4. 配置验证

**支持类型**：
- database: 数据库配置验证
- api: API 配置验证
- logging: 日志配置验证

**验证内容**：
- 必需字段检查
- 字段值格式验证
- 生成详细的验证报告

### 5. 安全审计

**扫描能力**：
- 扫描多种文件类型 (.py, .js, .ts, .json, .yml, .yaml, .env, .sh, .bash)
- 识别潜在的敏感信息泄露
- 检测硬编码的密码、密钥和凭证
- 计算整体风险等级

**风险等级**：
- critical: 发现私钥或高度敏感凭证
- high: 发现密码或密钥
- medium: 发现疑似敏感信息
- low: 未发现明显风险

## 使用场景

- 当你需要检查项目环境配置是否完整时
- 当你需要在不同环境间同步配置时
- 当你需要验证配置文件格式是否正确时
- 当你需要审计代码中的安全风险时
- 当你需要管理项目密钥时
- 当你需要生成标准化的配置文件时

## 触发条件

### 通用触发
- `environment`
- `env config`
- `env setup`
- `config environment`

### 特定操作触发
- `环境检测` / `detect environment`
- `生成配置` / `generate config`
- `验证配置` / `validate config`
- `安全审计` / `security audit`
- `管理密钥` / `manage secrets`

## 依赖关系

- 无直接依赖关系
- 可选依赖:
  - PyYAML: 用于 YAML 格式配置生成

## 使用方法

### 1. 环境差异检测

```bash
# 检测当前项目环境
lingflow run environment-manager --params '{"action": "detect", "project_dir": "/path/to/project"}'

# 使用默认目录（当前目录）
lingflow run environment-manager --params '{"action": "detect"}'
```

### 2. 生成配置文件

```bash
# 生成 JSON 格式配置
lingflow run environment-manager --params '{"action": "generate", "output_format": "json"}'

# 生成 .env 格式配置
lingflow run environment-manager --params '{"action": "generate", "output_format": "env"}'

# 从指定 .env 文件生成配置
lingflow run environment-manager --params '{"action": "generate", "env_file": ".env.production"}'
```

### 3. 验证配置

```bash
# 验证数据库配置
lingflow run environment-manager --params '{"action": "validate", "config_type": "database"}'

# 验证 API 配置
lingflow run environment-manager --params '{"action": "validate", "config_type": "api"}'

# 验证日志配置
lingflow run environment-manager --params '{"action": "validate", "config_type": "logging"}'
```

### 4. 安全审计

```bash
# 审计项目安全风险
lingflow run environment-manager --params '{"action": "audit", "project_dir": "/path/to/project"}'
```

## 技能结构

```
skills/environment-manager/
├── SKILL.md           # 技能描述文件
├── __init__.py        # 技能初始化文件
└── implementation.py  # 技能实现文件
```

## 环境变量检测

技能会自动检测以下环境文件：
- `.env`
- `.env.local`
- `.env.production`
- `.env.development`
- `.env.test`
- `.env.example`
- `config/.env`

## 敏感信息检测

技能会扫描以下敏感信息模式：
- password / passwd
- api_key / apikey
- secret
- token
- private_key
- auth_token
- access_token
- aws_access_key / aws_secret_key
- database_url
- redis_password

## 最佳实践

1. **使用 .env.example**: 创建模板文件，说明需要哪些环境变量
2. **版本控制**: 将 .env 添加到 .gitignore，只提交 .env.example
3. **分离配置**: 为不同环境使用不同的配置文件
4. **定期审计**: 定期运行安全审计，检查代码中的敏感信息
5. **验证配置**: 在部署前验证配置的完整性

## 故障排除

- **检测失败**: 检查目录路径是否正确，以及是否有读取权限
- **解析错误**: 检查 .env 文件格式是否正确 (KEY=VALUE 格式)
- **验证失败**: 检查环境变量命名是否符合规范 (CONFIG_TYPE_FIELD)
- **审计超时**: 对于大型项目，可以限制扫描的文件类型或目录

## 相关技能

- `code-review` - 用于代码审查，包括安全检查
- `config-validator` - 用于配置文件验证 (如果存在)
- `secrets-manager` - 用于更高级的密钥管理 (如果存在)
