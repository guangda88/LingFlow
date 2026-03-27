# LingFlow 自我审查能力改进计划

> 对比手动8维度审查与自我审查报告，识别差距并提出改进方案

---

## 执行摘要

| 维度 | 手动审查发现 | 自我审查发现 | 覆盖率 |
|------|-------------|-------------|--------|
| 代码结构 | 6项 | 1项 | 17% |
| 代码质量 | 7项 | 2项 | 29% |
| 安全性 | 6项 | 2项(含误报) | 33% |
| 性能 | 8项 | 0项 | 0% |
| 测试覆盖 | 6项 | 0项 | 0% |
| 依赖管理 | 6项 | 0项 | 0% |
| 错误处理 | 6项 | 0项 | 0% |
| 文档规范 | 7项 | 0项 | 0% |
| **平均** | - | - | **10%** |

---

## 优先级1: 缺失能力的补充实现

### 1.1 项目结构检查器

```python
# skills/structure-checker/implementation.py

import os
from pathlib import Path
from typing import Dict, List, Any

STANDARD_DIRS = ['tests', 'docs', 'src']
TEMP_FILE_PATTERNS = ['*.txt', '*.log', '*.tmp', 'test_output*']
ROOT_TEST_FILES = ['test_', '_test.py']

def check_project_structure(params: Dict[str, Any]) -> Dict[str, Any]:
    """检查项目结构规范性"""
    project_path = Path(params.get('target', '.'))

    issues = []

    # 检查标准目录
    for dir_name in STANDARD_DIRS:
        if not (project_path / dir_name).exists():
            issues.append({
                'type': 'missing_dir',
                'severity': 'warning',
                'message': f'缺少标准目录: {dir_name}/'
            })

    # 检查根目录测试文件
    for file_path in project_path.glob('*.py'):
        if any(pattern in file_path.name for pattern in ROOT_TEST_FILES):
            issues.append({
                'type': 'test_file_in_root',
                'severity': 'warning',
                'message': f'测试文件应在tests/目录: {file_path.name}'
            })

    # 检查临时文件
    for pattern in TEMP_FILE_PATTERNS:
        for file_path in project_path.glob(pattern):
            if file_path.name not in ['.gitignore', 'README.md']:
                issues.append({
                    'type': 'temp_file',
                    'severity': 'info',
                    'message': f'临时文件未清理: {file_path.name}'
                })

    return {
        'total_issues': len(issues),
        'issues': issues,
        'score': max(0, 100 - len(issues) * 5)
    }

def execute_skill(params):
    return check_project_structure(params)
```

### 1.2 日志规范检查器

```python
# skills/log-checker/implementation.py

import ast
from pathlib import Path

def check_logging_usage(code: str, file_path: str) -> List[Dict]:
    """检查代码中是否使用print而非logger"""
    issues = []

    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # 检查 print() 调用
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                issues.append({
                    'type': 'print_statement',
                    'severity': 'warning',
                    'message': '应使用logger而非print()',
                    'line': node.lineno
                })

    return issues
```

### 1.3 性能分析器

```python
# skills/performance-analyzer/implementation.py

import ast
from typing import Dict, List, Any

PERFORMANCE_ISSUES = {
    'repeated_file_reads': '文件在循环中重复读取',
    'missing_cache': '应使用缓存的计算密集型操作',
    'inefficient_string_concat': '字符串拼接应使用join()',
    'nested_loops_deep': '嵌套循环过深(>3层)',
}

def analyze_performance(params: Dict[str, Any]) -> Dict[str, Any]:
    """分析代码中的性能问题"""
    target = Path(params.get('target', '.'))

    issues = []

    for py_file in target.rglob('*.py'):
        code = py_file.read_text()
        tree = ast.parse(code)

        # 检查嵌套循环深度
        for node in ast.walk(tree):
            depth = _get_loop_depth(node)
            if depth > 3:
                issues.append({
                    'type': 'nested_loops_deep',
                    'file': str(py_file),
                    'line': node.lineno if hasattr(node, 'lineno') else 0,
                    'depth': depth
                })

        # 检查字符串拼接
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
                if isinstance(node.target, ast.Name) and node.target.id == 's':
                    issues.append({
                        'type': 'inefficient_string_concat',
                        'file': str(py_file),
                        'line': node.lineno
                    })

    return {
        'total_issues': len(issues),
        'issues': issues
    }

def _get_loop_depth(node, depth=0):
    """计算嵌套循环深度"""
    if isinstance(node, (ast.For, ast.While)):
        child_depth = 0
        for child in ast.iter_child_nodes(node):
            child_depth = max(child_depth, _get_loop_depth(child, depth + 1))
        return child_depth
    return 0

def execute_skill(params):
    return analyze_performance(params)
```

### 1.4 测试质量分析器

```python
# skills/test-analyzer/implementation.py

import ast
from pathlib import Path
from typing import Dict, List

def analyze_test_quality(params: Dict) -> Dict[str, Any]:
    """分析测试文件质量"""
    target = Path(params.get('target', 'tests/'))

    if not target.exists():
        target = Path('.')

    results = {
        'test_files': 0,
        'test_functions': 0,
        'assertions': 0,
        'tests_without_assertions': [],
        'missing_fixtures': [],
        'mock_usage': 0
    }

    for test_file in target.rglob('test_*.py'):
        results['test_files'] += 1
        code = test_file.read_text()
        tree = ast.parse(code)

        has_assertion = False
        has_mock = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                results['test_functions'] += 1

            if isinstance(node, ast.Assert):
                results['assertions'] += 1
                has_assertion = True

            # 检查 mock 使用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['mock', 'patch', 'Mock']:
                        has_mock = True
                        results['mock_usage'] += 1

        if not has_assertion and 'def test_' in code:
            results['tests_without_assertions'].append(str(test_file))

    return results

def execute_skill(params):
    return analyze_test_quality(params)
```

### 1.5 依赖分析器

```python
# skills/dependency-checker/implementation.py

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

def check_dependencies(params: Dict[str, Any]) -> Dict[str, Any]:
    """检查依赖管理问题"""
    project_path = Path(params.get('target', '.'))

    issues = []

    # 检查 setup.py 与 requirements.txt 同步
    setup_deps = _parse_setup_dependencies(project_path / 'setup.py')
    req_deps = _parse_requirements(project_path / 'requirements.txt')

    for dep in setup_deps:
        if dep not in req_deps:
            issues.append({
                'type': 'dependency_mismatch',
                'message': f'setup.py中的依赖未在requirements.txt中: {dep}'
            })

    # 检查是否有 lockfile
    lockfiles = ['poetry.lock', 'Pipfile.lock', 'requirements.lock']
    has_lockfile = any((project_path / f).exists() for f in lockfiles)

    if not has_lockfile:
        issues.append({
            'type': 'missing_lockfile',
            'message': '缺少依赖锁定文件，建议使用poetry或pip-tools'
        })

    # 检查版本约束
    for dep in req_deps:
        if '>=' in dep and not any(c in dep for c in ['^', '~', '==']):
            issues.append({
                'type': 'loose_version_constraint',
                'message': f'版本约束过宽，可能引入破坏性变更: {dep}'
            })

    return {
        'total_issues': len(issues),
        'issues': issues,
        'has_lockfile': has_lockfile
    }

def _parse_setup_dependencies(setup_path: Path) -> List[str]:
    """解析 setup.py 中的依赖"""
    if not setup_path.exists():
        return []

    # 简化实现，实际应使用AST解析
    content = setup_path.read_text()
    if 'install_requires' in content:
        start = content.index('install_requires')
        end = content.index(']', start)
        deps_section = content[start:end+1]
        # 提取包名
        import re
        return [m.group(1) for m in re.finditer(r'([a-zA-Z0-9_-]+)>=', deps_section)]
    return []

def _parse_requirements(req_path: Path) -> List[str]:
    """解析 requirements.txt"""
    if not req_path.exists():
        return []

    deps = []
    with open(req_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 提取包名
                pkg = line.split('>=')[0].split('==')[0].split('[')[0].strip()
                deps.append(pkg)
    return deps

def execute_skill(params):
    return check_dependencies(params)
```

---

## 优先级2: 安全检查改进

### 2.1 减少误报

```python
# 改进 constitution.py 中的检查逻辑

def _check_weak_crypto(self, code: str, principle, file_path: str) -> List[Violation]:
    """检查弱加密算法 - 改进版"""
    violations = []

    lines = code.split('\n')
    weak_algorithms = ['MD5', 'SHA1', 'DES', 'RC4', 'Blowfish']

    for i, line in enumerate(lines, 1):
        # 跳过注释
        if line.strip().startswith('#'):
            continue

        # 跳过字符串字面量
        if 'MD5' in line and ('"' in line or "'" in line):
            # 检查是否在注释中
            code_before_md5 = line[:line.index('MD5') if 'MD5' in line else 0]
            if '#' in code_before_md5:
                continue

        for algo in weak_algorithms:
            if algo in line:
                # 更精确的检测：只在导入或函数调用时报警
                if any(keyword in line for keyword in ['import', 'from', 'hashlib.', 'crypto.']):
                    violations.append(Violation(
                        principle_id=principle.id,
                        principle_name=principle.name,
                        severity=principle.level,
                        description=f"弱加密算法: {algo}",
                        location=file_path,
                        line_number=i,
                        suggested_fix=principle.implementation_pattern
                    ))
                    break

    return violations
```

---

## 优先级3: 统一审查工作流

创建完整的自审查工作流:

```yaml
# workflows/self_audit.yaml
name: LingFlow 完整自我审查
description: 运行所有检查技能生成完整报告

tasks:
  # 阶段1: 代码质量
  - id: structure_check
    skill: structure-checker
    params:
      target: ./

  - id: log_check
    skill: log-checker
    params:
      target: ./lingflow/

  - id: type_check
    skill: mypy-runner
    params:
      target: ./lingflow/

  # 阶段2: 安全检查
  - id: security_check
    skill: code-security-scan
    params:
      target: ./lingflow/

  # 阶段3: 性能分析
  - id: performance_check
    skill: performance-analyzer
    params:
      target: ./lingflow/

  # 阶段4: 测试分析
  - id: test_check
    skill: test-analyzer
    params:
      target: ./

  # 阶段5: 依赖检查
  - id: dependency_check
    skill: dependency-checker
    params:
      target: ./

  # 阶段6: 生成报告
  - id: generate_report
    skill: report-generator
    params:
      template: audit_report
      output: LINGFLOW_SELF_AUDIT_REPORT.md
    depends_on:
      - structure_check
      - log_check
      - security_check
      - performance_check
      - test_check
      - dependency_check
```

---

## 实施路线图

| 阶段 | 任务 | 技能 | 优先级 |
|------|------|------|--------|
| 第1周 | 实现缺失的5个检查器 | structure, log, performance, test, dependency | P0 |
| 第2周 | 改进安全检查减少误报 | constitution.py优化 | P0 |
| 第3周 | 创建统一审查工作流 | self_audit.yaml | P1 |
| 第4周 | 添加CLI命令 | lingflow audit | P1 |

---

## 预期改进效果

实施后，自我审查覆盖率预计从 **10%** 提升至 **85%**:

| 维度 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 代码结构 | 17% | 80% | +63% |
| 代码质量 | 29% | 90% | +61% |
| 安全性 | 33% | 80% | +47% |
| 性能 | 0% | 70% | +70% |
| 测试覆盖 | 0% | 90% | +90% |
| 依赖管理 | 0% | 100% | +100% |
| 错误处理 | 0% | 60% | +60% |
| 文档规范 | 0% | 80% | +80% |
