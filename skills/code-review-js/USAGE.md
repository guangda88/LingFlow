# 🚀 code-review-js 使用指南

## 目录

1. [简介](#简介)
2. [安装](#安装)
3. [基本使用](#基本使用)
4. [高级功能](#高级功能)
5. [配置选项](#配置选项)
6. [输出格式](#输出格式)
7. [最佳实践](#最佳实践)
8. [故障排除](#故障排除)
9. [示例](#示例)

---

## 📖 简介

### 什么是 code-review-js？

**code-review-js** 是 LingFlow 的一个技能，用于审查 JavaScript/TypeScript 代码。

### 支持的语言

- ✅ JavaScript (ES6+)
- ✅ TypeScript
- ✅ JSX (React)
- ✅ TSX (React TypeScript)
- ✅ Node.js

### 8-Dimension 代码审查框架

1. **代码质量** - ESLint 检查、代码风格、复杂度
2. **架构设计** - 模块化、依赖管理、package.json 验证
3. **性能分析** - V8 优化、异步处理、内存管理
4. **安全性** - npm audit、XSS/CSRF 防护、危险函数检测
5. **可维护性** - JSDoc 文档、测试覆盖、代码组织
6. **最佳实践** - ES6+ 特性、错误处理、编码标准
7. **autoresearch理念一致性** - 符合核心理念的程度
8. **潜在Bug分析** - 运行时错误、类型错误、边界条件

---

## 🔧 安装

### 1. 确保已安装 Node.js 和 npm

```bash
# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version
```

### 2. 安装 ESLint（推荐）

```bash
# 全局安装
npm install -g eslint

# 或在项目中安装
npm install --save-dev eslint

# TypeScript 支持
npm install --save-dev typescript @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

### 3. 验证技能

```bash
cd /home/ai/LingFlow
python3 skills/code-review-js/test.py
```

---

## 🚀 基本使用

### 方法1: 使用 Python 脚本

```bash
cd /home/ai/LingFlow
python3 run_code_review_js.py /home/ai/zhineng-bridge javascript
```

### 方法2: 使用便捷函数

```python
from skills.code_review_js import review_javascript

# 审查 JavaScript 项目
report = review_javascript("/home/ai/zhineng-bridge", "javascript")

# 审查 TypeScript 项目
report = review_javascript("/home/ai/zhineng-bridge", "typescript")

# 输出报告
import json
print(json.dumps(report, indent=2))
```

### 方法3: 使用 JavaScriptCodeReviewSkill 类

```python
from skills.code_review_js import JavaScriptCodeReviewSkill

# 创建审查器
reviewer = JavaScriptCodeReviewSkill("/home/ai/zhineng-bridge", "javascript")

# 执行审查
report = reviewer.analyze()

# 访问结果
for issue in report['results']['code_quality']:
    print(f"[{issue['severity']}] {issue['message']}")
```

---

## ⚙️ 高级功能

### 1. 指定语言

```bash
# JavaScript
python3 run_code_review_js.py /home/ai/project javascript

# TypeScript
python3 run_code_review_js.py /home/ai/project typescript

# JSX (React)
python3 run_code_review_js.py /home/ai/project jsx
```

### 2. 自定义配置

```python
from skills.code_review_js import JavaScriptCodeReviewSkill

# 创建审查器
reviewer = JavaScriptCodeReviewSkill("/home/ai/project")

# 自定义排除目录
reviewer.exclude_dirs = ['node_modules', 'dist', 'build']

# 自定义文件扩展名
reviewer.js_extensions = ['.js', '.jsx', '.ts', '.tsx']

# 执行审查
report = reviewer.analyze()
```

### 3. 过滤严重程度

```python
from skills.code_review_js import JavaScriptCodeReviewSkill, SeverityLevel

# 创建审查器
reviewer = JavaScriptCodeReviewSkill("/home/ai/project")

# 执行审查
report = reviewer.analyze()

# 只显示 Critical 和 High 问题
for dimension, issues in report['results'].items():
    for issue in issues:
        if issue['severity'] in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            print(f"[{dimension}] [{issue['severity']}] {issue['message']}")
```

### 4. 分析特定维度

```python
from skills.code_review_js import JavaScriptCodeReviewSkill

# 创建审查器
reviewer = JavaScriptCodeReviewSkill("/home/ai/project")

# 执行审查
report = reviewer.analyze()

# 只分析安全问题
security_issues = report['results']['security']
for issue in security_issues:
    print(f"[{issue['severity']}] {issue['message']}")
```

---

## 📝 配置选项

### ESLint 配置

创建 `.eslintrc.json`:

```json
{
  "extends": "eslint:recommended",
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn",
    "semi": ["error", "always"]
  },
  "env": {
    "browser": true,
    "node": true
  }
}
```

### TypeScript 配置

创建 `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES6",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

### package.json 配置

```json
{
  "name": "my-project",
  "version": "1.0.0",
  "scripts": {
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "audit": "npm audit",
    "test": "npm test"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "typescript": "^4.0.0",
    "@typescript-eslint/parser": "^5.0.0",
    "@typescript-eslint/eslint-plugin": "^5.0.0"
  }
}
```

---

## 📊 输出格式

### Markdown 格式（默认）

```markdown
# JavaScript 代码审查报告

## 📊 审查摘要

- 文件数: 10
- 代码行数: 1000
- 问题数: 5
- 安全漏洞: 2

## 🔴 Critical Issues

1. npm: Found 2 high severity vulnerabilities

## 🟠 High Issues

1. ESLint: no-unused-vars (test.js:10)

## 🟡 Medium Issues

1. ESLint: no-console (test.js:15)
```

### JSON 格式

```json
{
  "summary": {
    "files": 10,
    "issues": 5,
    "vulnerabilities": 2
  },
  "overall_score": "Good",
  "results": {
    "code_quality": [...],
    "architecture": [...],
    "security": [...],
    ...
  }
}
```

---

## 💡 最佳实践

### 1. 定期运行审查

```bash
# 在 CI/CD 中集成
npm run lint
npm audit
npm test

# 使用 code-review-js
python3 /home/ai/LingFlow/run_code_review_js.py . javascript
```

### 2. 自动修复问题

```bash
# ESLint 自动修复
npx eslint --fix .

# Prettier 格式化
npx prettier --write "**/*.{js,jsx,ts,tsx}"
```

### 3. 持续改进

- ✅ 每次提交前运行审查
- ✅ 定期更新依赖
- ✅ 及时修复安全漏洞
- ✅ 保持代码风格一致

---

## 🔧 故障排除

### 问题1: ESLint 未找到

```bash
# 解决方案：全局安装 ESLint
npm install -g eslint

# 或在项目中安装
npm install --save-dev eslint
```

### 问题2: npm audit 失败

```bash
# 解决方案：更新 npm
npm install -g npm@latest

# 或跳过 npm audit（不推荐）
```

### 问题3: TypeScript 编译错误

```bash
# 解决方案：检查 tsconfig.json
npx tsc --showConfig

# 或修复类型错误
npx tsc --noEmit
```

### 问题4: 权限错误

```bash
# 解决方案：检查文件权限
chmod -R 755 /home/ai/project

# 或使用 sudo
sudo python3 run_code_review_js.py /home/ai/project
```

---

## 📋 示例

### 示例1: 审查简单项目

```bash
# 创建测试项目
mkdir -p /tmp/test-project
cd /tmp/test-project

# 创建 package.json
cat > package.json << 'EOF'
{
  "name": "test-project",
  "version": "1.0.0"
}
EOF

# 创建测试文件
cat > index.js << 'EOF'
const test = 'hello';
console.log(test);
EOF

# 运行审查
python3 /home/ai/LingFlow/run_code_review_js.py /tmp/test-project javascript
```

### 示例2: 审查 TypeScript 项目

```bash
# 创建 TypeScript 项目
mkdir -p /tmp/ts-project
cd /tmp/ts-project

# 创建 package.json
cat > package.json << 'EOF'
{
  "name": "ts-project",
  "version": "1.0.0",
  "devDependencies": {
    "typescript": "^4.0.0"
  }
}
EOF

# 创建 tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES6",
    "module": "commonjs",
    "strict": true
  }
}
EOF

# 创建测试文件
cat > index.ts << 'EOF'
const test: string = 'hello';
console.log(test);
EOF

# 运行审查
python3 /home/ai/LingFlow/run_code_review_js.py /tmp/ts-project typescript
```

### 示例3: 审查 React 项目

```bash
# 审查 React 项目
python3 /home/ai/LingFlow/run_code_review_js.py /home/ai/my-react-app javascript

# 审查 React TypeScript 项目
python3 /home/ai/LingFlow/run_code_review_js.py /home/ai/my-react-app typescript
```

---

## 📞 支持

如有问题，请查看：

- LingFlow 文档：`/home/ai/LingFlow/docs/`
- Code Review 技能：`/home/ai/LingFlow/skills/code-review-js/`
- ESLint 文档：https://eslint.org/
- TypeScript 文档：https://www.typescriptlang.org/

---

**版本：** 1.0.0
**最后更新：** 2026-03-23
