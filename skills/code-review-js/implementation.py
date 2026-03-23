#!/usr/bin/env python3
"""
code-review-js 技能实现

JavaScript/TypeScript 代码审查技能，支持 8-Dimension 代码审查框架。
"""

import os
import subprocess
import json
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class SeverityLevel:
    """严重程度等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class JavaScriptCodeReviewSkill:
    """JavaScript/TypeScript 代码审查技能"""
    
    def __init__(self, target_dir: str, language: str = "javascript"):
        self.target_dir = Path(target_dir)
        self.language = language.lower()
        self.results = {
            'code_quality': [],
            'architecture': [],
            'performance': [],
            'security': [],
            'maintainability': [],
            'best_practices': [],
            'autoresearch_consistency': [],
            'bugs': []
        }
        
        # 统计信息
        self.stats = {
            'files_count': 0,
            'lines_count': 0,
            'issues_count': 0,
            'vulnerabilities_count': 0
        }
        
        # 配置
        self.exclude_dirs = ['node_modules', 'dist', 'build', '.git', '__pycache__']
        self.js_extensions = ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']
    
    def analyze(self) -> Dict[str, Any]:
        """执行完整的代码分析"""
        print(f"开始 {self.language} 代码审查...")
        
        # 1. 检查 package.json
        self._check_package_json()
        
        # 2. 运行 ESLint
        self._run_eslint()
        
        # 3. 运行 npm audit
        self._run_npm_audit()
        
        # 4. TypeScript 检查
        if self.language in ['typescript', 'ts']:
            self._run_typescript_check()
        
        # 5. 分析代码结构
        self._analyze_code_structure()
        
        # 6. 检查安全性
        self._check_security()
        
        # 7. 检查性能
        self._check_performance()
        
        # 8. 检查可维护性
        self._check_maintainability()
        
        # 9. 检查最佳实践
        self._check_best_practices()
        
        # 10. 检查 Bug
        self._check_bugs()
        
        # 11. 检查 autoresearch 一致性
        self._check_autoresearch_consistency()
        
        return self._generate_report()
    
    def _check_package_json(self):
        """检查 package.json"""
        package_json = self.target_dir / 'package.json'
        
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                
                # 检查依赖
                dependencies = pkg.get('dependencies', {})
                dev_dependencies = pkg.get('devDependencies', {})
                
                self.results['architecture'].append({
                    'severity': SeverityLevel.INFO,
                    'category': 'architecture',
                    'message': f"Found {len(dependencies)} production dependencies",
                    'file': str(package_json)
                })
                
                self.results['architecture'].append({
                    'severity': SeverityLevel.INFO,
                    'category': 'architecture',
                    'message': f"Found {len(dev_dependencies)} development dependencies",
                    'file': str(package_json)
                })
                
                # 检查脚本
                scripts = pkg.get('scripts', {})
                if scripts:
                    self.results['best_practices'].append({
                        'severity': SeverityLevel.INFO,
                        'category': 'best_practices',
                        'message': f"Found {len(scripts)} npm scripts",
                        'file': str(package_json)
                    })
                
                # 检查 ESLint 配置
                if 'eslintConfig' in pkg:
                    self.results['best_practices'].append({
                        'severity': SeverityLevel.INFO,
                        'category': 'best_practices',
                        'message': "ESLint configuration found in package.json",
                        'file': str(package_json)
                    })
                
                # 检查 engines
                if 'engines' in pkg:
                    engines = pkg['engines']
                    if 'node' in engines:
                        self.results['best_practices'].append({
                            'severity': SeverityLevel.INFO,
                            'category': 'best_practices',
                            'message': f"Node.js version specified: {engines['node']}",
                            'file': str(package_json)
                        })
            
            except json.JSONDecodeError as e:
                self.results['bugs'].append({
                    'severity': SeverityLevel.ERROR,
                    'category': 'bugs',
                    'message': f"Invalid JSON in package.json: {e}",
                    'file': str(package_json)
                })
    
    def _run_eslint(self):
        """运行 ESLint"""
        try:
            # 检查 ESLint 是否已安装
            result = subprocess.run(
                ['npx', 'eslint', '--version'],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"ESLint 未安装或配置错误: {result.stderr}")
                return
            
            # 运行 ESLint
            result = subprocess.run(
                ['npx', 'eslint', '--format', 'json', str(self.target_dir)],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    
                    for file_issues in issues:
                        file_path = file_issues.get('filePath', '')
                        messages = file_issues.get('messages', [])
                        
                        for issue in messages:
                            severity = self._eslint_severity_to_severity(issue.get('severity'))
                            
                            self.results['code_quality'].append({
                                'severity': severity,
                                'category': 'code_quality',
                                'file': file_path,
                                'line': issue.get('line'),
                                'column': issue.get('column'),
                                'message': issue.get('message'),
                                'rule': issue.get('ruleId'),
                                'source': 'eslint'
                            })
                            
                            self.stats['issues_count'] += 1
                
                except json.JSONDecodeError:
                    self.results['bugs'].append({
                        'severity': SeverityLevel.ERROR,
                        'category': 'bugs',
                        'message': "Failed to parse ESLint output",
                        'source': 'eslint'
                    })
        
        except subprocess.TimeoutExpired:
            self.results['bugs'].append({
                'severity': SeverityLevel.ERROR,
                'category': 'bugs',
                'message': "ESLint execution timeout",
                'source': 'eslint'
            })
        except Exception as e:
            print(f"ESLint check failed: {e}")
    
    def _run_npm_audit(self):
        """运行 npm audit"""
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                try:
                    audit = json.loads(result.stdout)
                    vulnerabilities = audit.get('vulnerabilities', {})
                    
                    for vuln_type, vuln_info in vulnerabilities.items():
                        if vuln_info:
                            self.results['security'].append({
                                'severity': SeverityLevel.CRITICAL,
                                'category': 'security',
                                'type': vuln_type,
                                'count': len(vuln_info),
                                'message': f"Found {len(vuln_info)} {vuln_type} vulnerabilities",
                                'source': 'npm_audit'
                            })
                            
                            self.stats['vulnerabilities_count'] += len(vuln_info)
                    
                    # 检查审计摘要
                    advisories = audit.get('advisories', {})
                    if advisories:
                        self.results['security'].append({
                            'severity': SeverityLevel.INFO,
                            'category': 'security',
                            'message': f"Found {len(advisories)} security advisories",
                            'source': 'npm_audit'
                        })
                
                except json.JSONDecodeError:
                    pass
        
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"npm audit check failed: {e}")
    
    def _run_typescript_check(self):
        """运行 TypeScript 检查"""
        try:
            # 检查 TypeScript 是否已安装
            result = subprocess.run(
                ['npx', 'tsc', '--version'],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return
            
            # 运行 TypeScript 编译器
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit'],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout or result.stderr:
                output = result.stdout + result.stderr
                
                for line in output.split('\n'):
                    if line.strip():
                        # 解析 TypeScript 错误
                        # 格式: file.ts(line,column): error TSxxxx: message
                        match = re.match(r'^(.+?)\((\d+),(\d+)\):\s+error\s+TS\d+:\s+(.+)$', line)
                        if match:
                            file_path = match.group(1)
                            line_num = match.group(2)
                            column_num = match.group(3)
                            message = match.group(4)
                            
                            self.results['bugs'].append({
                                'severity': SeverityLevel.HIGH,
                                'category': 'bugs',
                                'file': file_path,
                                'line': int(line_num),
                                'column': int(column_num),
                                'message': message,
                                'source': 'typescript'
                            })
                            
                            self.stats['issues_count'] += 1
        
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"TypeScript check failed: {e}")
    
    def _analyze_code_structure(self):
        """分析代码结构"""
        js_files = []
        total_lines = 0
        
        for root, dirs, files in os.walk(self.target_dir):
            # 跳过排除的目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    js_files.append(file_path)
                    
                    # 统计行数
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            total_lines += len(lines)
                    except:
                        pass
        
        self.stats['files_count'] = len(js_files)
        self.stats['lines_count'] = total_lines
        
        self.results['architecture'].append({
            'severity': SeverityLevel.INFO,
            'category': 'architecture',
            'message': f"Found {len(js_files)} JavaScript/TypeScript files",
            'file': str(self.target_dir)
        })
        
        self.results['architecture'].append({
            'severity': SeverityLevel.INFO,
            'category': 'architecture',
            'message': f"Total lines of code: {total_lines}",
            'file': str(self.target_dir)
        })
    
    def _check_security(self):
        """检查安全性"""
        dangerous_patterns = [
            (r'\beval\s*\(', 'eval() is dangerous', SeverityLevel.CRITICAL),
            (r'\bFunction\s*\(\s*[\'"]', 'Function() is dangerous', SeverityLevel.CRITICAL),
            (r'\bdocument\.write\s*\(', 'document.write() is dangerous', SeverityLevel.HIGH),
            (r'\binnerHTML\s*=', 'innerHTML can lead to XSS', SeverityLevel.HIGH),
            (r'\bdangerouslySetInnerHTML', 'dangerouslySetInnerHTML is dangerous', SeverityLevel.HIGH),
            (r'\bexec\s*\(', 'exec() is dangerous', SeverityLevel.CRITICAL),
            (r'process\.env\.([A-Z_]+)', 'Environment variable check', SeverityLevel.INFO),
        ]
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for pattern, message, severity in dangerous_patterns:
                                matches = re.finditer(pattern, content)
                                for match in matches:
                                    self.results['security'].append({
                                        'severity': severity,
                                        'category': 'security',
                                        'file': file_path,
                                        'message': message,
                                        'pattern': pattern,
                                        'source': 'security_check'
                                    })
                    
                    except:
                        pass
    
    def _check_performance(self):
        """检查性能"""
        performance_patterns = [
            (r'\bfor\s*\(\s*\w+\s+in\s+\.keys\(\)', 'Use for...of for better performance', SeverityLevel.MEDIUM),
            (r'\bJSON\.parse\s*\(\s*JSON\.stringify', 'Deep clone is expensive', SeverityLevel.MEDIUM),
            (r'\bArray\.prototype\.concat\.apply', 'Potential stack overflow', SeverityLevel.MEDIUM),
            (r'\bsetTimeout\s*\(\s*[\'"]\s*[^\'\"]+[\'\"]\s*,\s*0\s*\)', 'setTimeout(..., 0) is inefficient', SeverityLevel.LOW),
        ]
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            
                            for line_num, line in enumerate(lines, 1):
                                for pattern, message, severity in performance_patterns:
                                    if re.search(pattern, line):
                                        self.results['performance'].append({
                                            'severity': severity,
                                            'category': 'performance',
                                            'file': file_path,
                                            'line': line_num,
                                            'message': message,
                                            'source': 'performance_check'
                                        })
                    
                    except:
                        pass
    
    def _check_maintainability(self):
        """检查可维护性"""
        # 检查文件大小
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        # 文件大小超过 10KB
                        if file_size > 10240:
                            self.results['maintainability'].append({
                                'severity': SeverityLevel.MEDIUM,
                                'category': 'maintainability',
                                'file': file_path,
                                'message': f"Large file: {file_size} bytes",
                                'source': 'maintainability_check'
                            })
                    
                    except:
                        pass
    
    def _check_best_practices(self):
        """检查最佳实践"""
        # 检查 ES6+ 特性使用
        modern_js_features = [
            (r'\bconst\s+', 'Using const', SeverityLevel.INFO),
            (r'\blet\s+', 'Using let', SeverityLevel.INFO),
            (r'\b=>\s*', 'Using arrow functions', SeverityLevel.INFO),
            (r'\`\`', 'Using template literals', SeverityLevel.INFO),
            (r'\.\.\.', 'Using spread operator', SeverityLevel.INFO),
            (r'import\s+.*from', 'Using ES6 modules', SeverityLevel.INFO),
            (r'\bclass\s+', 'Using class syntax', SeverityLevel.INFO),
            (r'\basync\s+', 'Using async/await', SeverityLevel.INFO),
        ]
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for pattern, message, severity in modern_js_features:
                                if re.search(pattern, content):
                                    self.results['best_practices'].append({
                                        'severity': severity,
                                        'category': 'best_practices',
                                        'file': file_path,
                                        'message': message,
                                        'source': 'best_practices_check'
                                    })
                                    break  # 每个文件只报告一次
                    
                    except:
                        pass
    
    def _check_bugs(self):
        """检查 Bug"""
        common_bugs = [
            (r'==\s*null', 'Potential null reference', SeverityLevel.HIGH),
            (r'==\s*undefined', 'Potential undefined reference', SeverityLevel.HIGH),
            (r'\!\w+\s*==\s*\w+\s*\!', 'Double negation is confusing', SeverityLevel.MEDIUM),
            (r'\bconsole\.(log|warn|error)\s*\(', 'Console statement found', SeverityLevel.LOW),
            (r'\bdebugger\s*;', 'Debugger statement found', SeverityLevel.HIGH),
        ]
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            
                            for line_num, line in enumerate(lines, 1):
                                for pattern, message, severity in common_bugs:
                                    if re.search(pattern, line):
                                        self.results['bugs'].append({
                                            'severity': severity,
                                            'category': 'bugs',
                                            'file': file_path,
                                            'line': line_num,
                                            'message': message,
                                            'source': 'bug_check'
                                        })
                    
                    except:
                        pass
    
    def _check_autoresearch_consistency(self):
        """检查 AutoResearch 一致性"""
        # 检查代码风格一致性
        consistency_checks = [
            (r'\bconst\s+', 'Using const', SeverityLevel.INFO),
            (r'\blet\s+', 'Using let', SeverityLevel.INFO),
            (r'\bvar\s+', 'Using var (should use const/let)', SeverityLevel.MEDIUM),
        ]
        
        const_count = 0
        let_count = 0
        var_count = 0
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.js_extensions):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            const_count += len(re.findall(r'\bconst\s+', content))
                            let_count += len(re.findall(r'\blet\s+', content))
                            var_count += len(re.findall(r'\bvar\s+', content))
                    
                    except:
                        pass
        
        self.results['autoresearch_consistency'].append({
            'severity': SeverityLevel.INFO,
            'category': 'autoresearch_consistency',
            'message': f"const usage: {const_count}, let usage: {let_count}, var usage: {var_count}",
            'source': 'consistency_check'
        })
        
        if var_count > 0:
            self.results['autoresearch_consistency'].append({
                'severity': SeverityLevel.MEDIUM,
                'category': 'autoresearch_consistency',
                'message': f"Found {var_count} var declarations (consider using const/let)",
                'source': 'consistency_check'
            })
    
    def _eslint_severity_to_severity(self, eslint_severity: int) -> str:
        """转换 ESLint 严重程度到标准严重程度"""
        if eslint_severity == 2:
            return SeverityLevel.ERROR
        elif eslint_severity == 1:
            return SeverityLevel.WARNING
        else:
            return SeverityLevel.INFO
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成审查报告"""
        # 统计各维度的问题数
        summary = {}
        for dimension, issues in self.results.items():
            summary[dimension] = len(issues)
        
        # 计算总体评分
        total_issues = sum(summary.values())
        if total_issues == 0:
            overall_score = "Excellent"
        elif total_issues < 10:
            overall_score = "Good"
        elif total_issues < 50:
            overall_score = "Fair"
        else:
            overall_score = "Poor"
        
        return {
            'summary': summary,
            'overall_score': overall_score,
            'stats': self.stats,
            'results': self.results,
            'timestamp': datetime.now().isoformat(),
            'language': self.language,
            'target_dir': str(self.target_dir)
        }


# 便捷函数
def review_javascript(target_dir: str, language: str = "javascript") -> Dict[str, Any]:
    """审查 JavaScript 代码"""
    reviewer = JavaScriptCodeReviewSkill(target_dir, language)
    return reviewer.analyze()


def review_typescript(target_dir: str) -> Dict[str, Any]:
    """审查 TypeScript 代码"""
    return review_javascript(target_dir, "typescript")


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else "javascript"
        
        report = review_javascript(target_dir, language)
        print(json.dumps(report, indent=2))
    else:
        print("Usage: python implementation.py <target_dir> [language]")
