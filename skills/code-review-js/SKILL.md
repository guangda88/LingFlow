# code-review-js 技能

## 技能概述

code-review-js 是一个用于审查 JavaScript/TypeScript 代码的技能，它可以分析代码质量、识别安全问题并提供改进建议。

## 支持的语言

- JavaScript (ES6+)
- TypeScript
- JSX/TSX (React)
- Node.js

## 功能特性

### 8维代码审查框架

本技能基于8个关键维度进行全面的代码审查：

1. **代码质量** - ESLint 检查、代码风格、复杂度
2. **架构设计** - 模块化、依赖管理、package.json 验证
3. **性能分析** - V8 优化、异步处理、内存管理
4. **安全性** - npm audit、XSS/CSRF 防护、危险函数检测
5. **可维护性** - JSDoc 文档、测试覆盖、代码组织
6. **最佳实践** - ES6+ 特性、错误处理、编码标准
7. **autoresearch理念一致性** - 符合核心理念的程度
8. **潜在Bug分析** - 运行时错误、类型错误、边界条件

## 工具集成

### 主要工具

1. **ESLint** ⭐⭐⭐⭐⭐
   - JavaScript 代码检查
   - 可配置的规则
   - 支持 TypeScript

2. **npm audit** ⭐⭐⭐⭐⭐
   - 安全漏洞检测
   - 依赖安全审计
   - 自动化安全检查

3. **TypeScript Compiler** ⭐⭐⭐⭐
   - 类型检查
   - 编译时错误检测
   - 增量编译

4. **JSDoc** ⭐⭐⭐
   - 文档生成
   - 类型注释
   - API 文档

## 使用方法

### 基本使用

```bash
# 审查 JavaScript 项目
python3 main.py --task "code-review-js" --target /path/to/project

# 审查 TypeScript 项目
python3 main.py --task "code-review-js" --target /path/to/project --language typescript

# 指定配置文件
python3 main.py --task "code-review-js" --target /path/to/project --config .eslintrc.json
```

### 高级选项

```bash
# 排除目录
python3 main.py --task "code-review-js" --target /path/to/project --exclude node_modules,dist,build

# 严重程度过滤
python3 main.py --task "code-review-js" --target /path/to/project --severity high,critical

# 输出格式
python3 main.py --task "code-review-js" --target /path/to/project --format json
```

## 检查维度

### 1. 代码质量

- ESLint 规则检查
- 代码风格一致性
- 复杂度分析
- 未使用变量检测
- 未使用导入检测

### 2. 架构设计

- package.json 验证
- 依赖关系分析
- 循环依赖检测
- 模块组织检查
- 文件结构验证

### 3. 性能分析

- 异步代码优化
- 内存泄漏检测
- 性能瓶颈识别
- V8 优化建议
- 缓存策略检查

### 4. 安全性

- npm audit 漏洞检测
- 危险函数检测（eval, innerHTML）
- XSS 攻击防护
- CSRF 攻击防护
- 敏感信息泄露检查

### 5. 可维护性

- JSDoc 文档完整性
- 代码注释质量
- 函数命名规范
- 变量命名规范
- 代码组织结构

### 6. 最佳实践

- ES6+ 特性使用
- 错误处理最佳实践
- 异步处理最佳实践
- Promise/async-await 使用
- 模块化最佳实践

### 7. autoresearch理念一致性

- 代码风格一致性
- 命名规范一致性
- 错误处理一致性
- 文档格式一致性
- 架构设计一致性

### 8. 潜在Bug分析

- 运行时错误检测
- 类型错误检测
- 空值引用检测
- 边界条件检查
- 未处理的异常

## 配置选项

### ESLint 配置

```javascript
// .eslintrc.json
{
  "extends": "eslint:recommended",
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn"
  }
}
```

### TypeScript 配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

## 输出格式

### Markdown 报告

```markdown
# JavaScript 代码审查报告

## 📊 审查摘要
- 文件数: 10
- 问题数: 5
- 安全漏洞: 2

## 🔴 Critical Issues
1. npm: Found 2 high severity vulnerabilities
```

### JSON 报告

```json
{
  "summary": {
    "files": 10,
    "issues": 5,
    "vulnerabilities": 2
  },
  "issues": [
    {
      "severity": "critical",
      "type": "security",
      "message": "Found 2 high severity vulnerabilities"
    }
  ]
}
```

## 最佳实践

### 1. 定期运行审查

```bash
# CI/CD 中集成
npm run lint
npm audit
npm test
```

### 2. 自动修复

```bash
# ESLint 自动修复
npx eslint --fix .

# Prettier 格式化
npx prettier --write "**/*.{js,jsx,ts,tsx}"
```

### 3. 持续改进

- 每次提交前运行审查
- 定期更新依赖
- 及时修复安全漏洞
- 保持代码风格一致

## 限制

### 当前限制

- 仅支持 JavaScript/TypeScript
- 需要安装 ESLint
- 需要 package.json

### 未来计划

- 支持 Flow
- 支持 CoffeeScript
- 支持更多 linter
- 支持 IDE 集成

## 参考资料

- [ESLint 官方文档](https://eslint.org/)
- [npm audit 官方文档](https://docs.npmjs.com/cli/audit)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [JSDoc 官方文档](https://jsdoc.app/)

## 版本历史

### 1.0.0 (2026-03-23)

- ✅ 初始版本
- ✅ 支持 JavaScript/TypeScript
- ✅ ESLint 集成
- ✅ npm audit 集成
- ✅ TypeScript 集成
- ✅ 8维代码审查框架

---

**技能版本:** 1.0.0
**最后更新:** 2026-03-23
**维护者:** LingFlow Team
