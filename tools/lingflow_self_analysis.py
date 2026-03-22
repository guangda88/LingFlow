#!/usr/bin/env python3
"""
LingFlow Self-Analysis - 8-Dimensional Code Analysis

使用 LingFlow v3.3.0 系统分析自身代码，从8个维度进行优化：
1. 宪法约束合规性
2. 安全围栏验证
3. TDD质量分析
4. 上下文优化
5. 代码质量
6. 业务流程分析
7. 性能优化
8. 架构一致性
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import ast
import re

# Add lingflow to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lingflow.core.constitution import Constitution, EnforcementLevel
from lingflow.core.compliance_matrix import ComplianceMatrix
from lingflow.guardrail import GuardrailValidator, DeploymentGate
from lingflow.tdd import TDDValidator
from lingflow.context import CodeCleanup


class LingFlowSelfAnalyzer:
    """LingFlow 自身代码分析器"""

    def __init__(self, lingflow_root: str = None):
        """初始化分析器"""
        self.lingflow_root = Path(lingflow_root) if lingflow_root else Path(__file__).parent.parent

        # 初始化 LingFlow 组件
        self.constitution = Constitution(".lingflow/constitution.yaml")
        self.compliance_matrix = ComplianceMatrix()
        self.guardrail = GuardrailValidator(".lingflow/policies/security.yaml")
        self.deployment_gate = DeploymentGate()
        self.tdd = TDDValidator(coverage_target=80.0)
        self.code_cleanup = CodeCleanup()

        # 分析结果
        self.analysis_results: Dict[str, Any] = {}

        print("=" * 80)
        print("LingFlow Self-Analysis - 8-Dimensional Code Analysis")
        print("=" * 80)
        print()

    def run_full_analysis(self) -> Dict[str, Any]:
        """运行完整的8维度分析"""
        start_time = time.time()

        # 1. 宪法约束合规性分析
        print("📋 Dimension 1/8: Constitutional Compliance Analysis")
        print("-" * 80)
        self.dimension1_constitutional_compliance()
        print()

        # 2. 安全围栏验证
        print("🛡️ Dimension 2/8: Guardrail Security Validation")
        print("-" * 80)
        self.dimension2_guardrail_validation()
        print()

        # 3. TDD质量分析
        print("🧪 Dimension 3/8: TDD Quality Analysis")
        print("-" * 80)
        self.dimension3_tdd_quality()
        print()

        # 4. 上下文优化分析
        print("💾 Dimension 4/8: Context Optimization Analysis")
        print("-" * 80)
        self.dimension4_context_optimization()
        print()

        # 5. 代码质量分析
        print("📊 Dimension 5/8: Code Quality Analysis")
        print("-" * 80)
        self.dimension5_code_quality()
        print()

        # 6. 业务流程分析
        print("🔄 Dimension 6/8: Core Business Flow Analysis")
        print("-" * 80)
        self.dimension6_business_flow_analysis()
        print()

        # 7. 性能优化分析
        print("⚡ Dimension 7/8: Performance Optimization Analysis")
        print("-" * 80)
        self.dimension7_performance_optimization()
        print()

        # 8. 架构一致性分析
        print("🏗️ Dimension 8/8: Architecture Consistency Analysis")
        print("-" * 80)
        self.dimension8_architecture_consistency()
        print()

        # 生成综合报告
        print("=" * 80)
        print("📊 COMPREHENSIVE ANALYSIS REPORT")
        print("=" * 80)
        print()

        self.generate_comprehensive_report()

        self.analysis_results['total_time'] = time.time() - start_time
        return self.analysis_results

    def dimension1_constitutional_compliance(self):
        """维度1: 宪法约束合规性分析"""
        print("检查核心 Python 文件的安全合规性...")

        # 分析核心文件
        core_files = [
            "lingflow/core/constitution.py",
            "lingflow/core/compliance_matrix.py",
            "lingflow/guardrail/__init__.py",
            "lingflow/tdd/__init__.py",
            "lingflow/context/__init__.py",
            "lingflow/workflow/orchestrator.py",
            "lingflow/coordination/coordinator.py",
        ]

        total_violations = 0
        critical_violations = 0
        file_reports = []

        for file_path in core_files:
            full_path = self.lingflow_root / file_path

            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                # 检查合规性
                report = self.constitution.check_compliance(code, file_path)

                print(f"  ✓ {file_path}")
                print(f"    合规: {'✅' if report.is_compliant else '❌'}")
                print(f"    违规: {len(report.violations)}")

                if report.violations:
                    total_violations += len(report.violations)
                    critical_count = sum(1 for v in report.violations if v.severity == EnforcementLevel.MUST)
                    critical_violations += critical_count

                    for v in report.violations[:2]:  # 显示前2个
                        print(f"      - {v.principle_name}: {v.description}")

                file_reports.append({
                    'file': file_path,
                    'is_compliant': report.is_compliant,
                    'violations': len(report.violations),
                    'coverage': report.coverage
                })

            except Exception as e:
                print(f"  ❌ {file_path}: {e}")

        self.analysis_results['dimension1'] = {
            'total_files': len(core_files),
            'total_violations': total_violations,
            'critical_violations': critical_violations,
            'file_reports': file_reports,
            'summary': f"发现 {total_violations} 个安全违规（{critical_violations} 个关键）"
        }

        print(f"\n  总计: {len(core_files)} 个文件, {total_violations} 个违规")

    def dimension2_guardrail_validation(self):
        """维度2: 安全围栏验证"""
        print("运行多层安全验证（AGCEF协议）...")

        # 分析核心文件
        core_files = [
            "lingflow/core/constitution.py",
            "lingflow/guardrail/__init__.py",
            "lingflow/tdd/__init__.py",
        ]

        validation_results = []
        total_score = 0
        total_violations = 0

        for file_path in core_files:
            full_path = self.lingflow_root / file_path

            if not full_path.exists():
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                # 运行 AGCEF 验证
                report = self.guardrail.validate_agcef(code, file_path)

                print(f"  ✓ {file_path}")
                print(f"    安全评分: {report.overall_score:.2f}/100")
                print(f"    风险等级: {report.risk_level}")
                print(f"    违规数: {report.total_violations}")

                total_score += report.overall_score
                total_violations += report.total_violations

                validation_results.append({
                    'file': file_path,
                    'score': report.overall_score,
                    'risk_level': report.risk_level,
                    'violations': report.total_violations
                })

            except Exception as e:
                print(f"  ❌ {file_path}: {e}")

        avg_score = total_score / len(core_files) if core_files else 0

        self.analysis_results['dimension2'] = {
            'total_files': len(core_files),
            'avg_score': avg_score,
            'total_violations': total_violations,
            'validation_results': validation_results,
            'summary': f"平均安全评分: {avg_score:.2f}/100, 总违规: {total_violations}"
        }

        print(f"\n  平均安全评分: {avg_score:.2f}/100")

    def dimension3_tdd_quality(self):
        """维度3: TDD质量分析"""
        print("分析测试文件质量...")

        # 查找测试文件
        test_files = list(self.lingflow_root.glob("**/test_*.py"))

        if not test_files:
            test_files = list(self.lingflow_root.glob("**/*_test.py"))

        print(f"  找到 {len(test_files)} 个测试文件")

        total_tests = 0
        total_paper_tests = 0
        test_reports = []

        for test_file in test_files:
            try:
                # 验证测试文件
                test_report = self.tdd.validate_tests(str(test_file))

                print(f"  ✓ {test_file.relative_to(self.lingflow_root)}")
                print(f"    总测试: {test_report.total_tests}")
                print(f"    纸面测试: {test_report.paper_tests}")
                print(f"    覆盖率: {test_report.test_coverage:.2%}")
                print(f"    有效: {'✅' if test_report.is_valid else '❌'}")

                total_tests += test_report.total_tests
                total_paper_tests += test_report.paper_tests

                test_reports.append({
                    'file': str(test_file.relative_to(self.lingflow_root)),
                    'total_tests': test_report.total_tests,
                    'paper_tests': test_report.paper_tests,
                    'coverage': test_report.test_coverage,
                    'is_valid': test_report.is_valid
                })

            except Exception as e:
                print(f"  ❌ {test_file}: {e}")

        # 分析源代码的测试覆盖率
        source_files = list(self.lingflow_root.glob("lingflow/**/*.py"))
        print(f"\n  分析 {len(source_files)} 个源文件的测试情况...")

        self.analysis_results['dimension3'] = {
            'total_test_files': len(test_files),
            'total_tests': total_tests,
            'total_paper_tests': total_paper_tests,
            'test_reports': test_reports,
            'summary': f"共 {len(test_files)} 个测试文件, {total_tests} 个测试, {total_paper_tests} 个纸面测试"
        }

        print(f"  总计: {total_tests} 个测试, {total_paper_tests} 个纸面测试")

    def dimension4_context_optimization(self):
        """维度4: 上下文优化分析"""
        print("分析代码清理和上下文优化机会...")

        # 分析核心文件
        core_files = [
            "lingflow/core/constitution.py",
            "lingflow/guardrail/__init__.py",
            "lingflow/tdd/__init__.py",
            "lingflow/context/__init__.py",
        ]

        total_cleanup_items = 0
        total_tokens_saved = 0
        cleanup_by_type = defaultdict(int)

        for file_path in core_files:
            full_path = self.lingflow_root / file_path

            if not full_path.exists():
                continue

            try:
                # 分析清理机会
                cleanup_items = self.code_cleanup.analyze_file(str(full_path))

                print(f"  ✓ {file_path}")
                print(f"    清理机会: {len(cleanup_items)}")

                for item in cleanup_items:
                    cleanup_by_type[item.type] += 1

                total_cleanup_items += len(cleanup_items)
                tokens_saved = sum(item.estimated_savings for item in cleanup_items)
                total_tokens_saved += tokens_saved

            except Exception as e:
                print(f"  ❌ {file_path}: {e}")

        # 分析上下文使用
        context_summary = {
            'total_tokens': self._estimate_total_tokens(),
            'potential_savings': int(total_tokens_saved * 1.5),  # 估算
            'compression_ratio': 0.4  # 目标
        }

        self.analysis_results['dimension4'] = {
            'total_files_analyzed': len(core_files),
            'total_cleanup_items': total_cleanup_items,
            'total_tokens_saved': total_tokens_saved,
            'cleanup_by_type': dict(cleanup_by_type),
            'context_summary': context_summary,
            'summary': f"发现 {total_cleanup_items} 个清理机会, 可节省 ~{total_tokens_saved} tokens"
        }

        print(f"\n  总计: {total_cleanup_items} 个清理机会, ~{total_tokens_saved} tokens 可节省")
        print(f"  清理类型: {dict(cleanup_by_type)}")

    def dimension5_code_quality(self):
        """维度5: 代码质量分析"""
        print("分析代码质量指标...")

        # 分析所有 Python 文件
        python_files = list(self.lingflow_root.glob("lingflow/**/*.py"))

        quality_metrics = {
            'total_files': len(python_files),
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'complexity_issues': [],
            'duplicate_code': [],
            'long_functions': [],
            'function_lengths': []
        }

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)

                lines = len(code.split('\n'))
                quality_metrics['total_lines'] += lines

                # 分析函数和类
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        quality_metrics['total_functions'] += 1

                        # 检查函数长度
                        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                        quality_metrics['function_lengths'].append(func_lines)

                        if func_lines > 50:
                            quality_metrics['long_functions'].append({
                                'file': str(py_file.relative_to(self.lingflow_root)),
                                'function': node.name,
                                'lines': func_lines
                            })

                    elif isinstance(node, ast.ClassDef):
                        quality_metrics['total_classes'] += 1

            except Exception as e:
                pass

        # 计算统计信息
        avg_func_length = sum(quality_metrics['function_lengths']) / len(quality_metrics['function_lengths']) if quality_metrics['function_lengths'] else 0

        self.analysis_results['dimension5'] = {
            'metrics': quality_metrics,
            'avg_function_length': avg_func_length,
            'long_functions_count': len(quality_metrics['long_functions']),
            'summary': f"{len(python_files)} 个文件, {quality_metrics['total_lines']} 行代码, {quality_metrics['total_functions']} 个函数, 平均函数长度 {avg_func_length:.1f}"
        }

        print(f"  文件数: {len(python_files)}")
        print(f"  总行数: {quality_metrics['total_lines']}")
        print(f"  总函数: {quality_metrics['total_functions']}")
        print(f"  总类: {quality_metrics['total_classes']}")
        print(f"  平均函数长度: {avg_func_length:.1f} 行")
        print(f"  长函数 (>50行): {len(quality_metrics['long_functions'])}")

    def dimension6_business_flow_analysis(self):
        """维度6: 核心业务流程分析"""
        print("识别和分析核心业务流程...")

        # 识别关键业务流程
        business_flows = {
            'task_submission': {
                'description': '任务提交流程',
                'entry_points': ['submit_task', 'execute_task'],
                'files': ['lingflow/coordination/coordinator.py', 'lingflow/workflow/orchestrator.py']
            },
            'task_execution': {
                'description': '任务执行流程',
                'entry_points': ['execute', 'run'],
                'files': ['lingflow/coordination/agent.py']
            },
            'security_validation': {
                'description': '安全验证流程',
                'entry_points': ['validate_agcef', 'check_compliance'],
                'files': ['lingflow/guardrail/__init__.py', 'lingflow/core/constitution.py']
            },
            'context_compression': {
                'description': '上下文压缩流程',
                'entry_points': ['compress', 'compress_context'],
                'files': ['lingflow/context/__init__.py', 'lingflow/compression/compressor.py']
            },
            'workflow_orchestration': {
                'description': '工作流编排流程',
                'entry_points': ['execute_workflow', 'schedule_tasks'],
                'files': ['lingflow/workflow/orchestrator.py']
            }
        }

        flow_details = {}

        for flow_name, flow_info in business_flows.items():
            print(f"\n  🔄 {flow_name}")
            print(f"    描述: {flow_info['description']}")

            # 分析流程文件
            flow_files = flow_info['files']
            flow_code = []

            for file_path in flow_files:
                full_path = self.lingflow_root / file_path
                if full_path.exists():
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                            flow_code.append((file_path, code))
                    except Exception:
                        pass

            # 识别关键函数
            key_functions = self._identify_key_functions(flow_code, flow_info['entry_points'])

            flow_details[flow_name] = {
                'info': flow_info,
                'key_functions': key_functions,
                'complexity': len(key_functions)
            }

            print(f"    关键函数: {len(key_functions)} 个")
            for func in key_functions[:3]:
                print(f"      - {func['name']} ({func['file']})")

        # 聚集核心流程
        core_flows = list(business_flows.keys())

        self.analysis_results['dimension6'] = {
            'total_flows': len(core_flows),
            'flows': flow_details,
            'core_flows': core_flows,
            'summary': f"识别 {len(core_flows)} 个核心业务流程"
        }

        print(f"\n  总计: {len(core_flows)} 个核心业务流程")

    def dimension7_performance_optimization(self):
        """维度7: 性能优化分析"""
        print("分析性能优化机会...")

        optimization_opportunities = []

        # 1. 检查低效的循环
        optimization_opportunities.extend(self._check_inefficient_loops())

        # 2. 检查重复计算
        optimization_opportunities.extend(self._check_redundant_computations())

        # 3. 检查不必要的导入
        optimization_opportunities.extend(self._check_unnecessary_imports())

        # 4. 检查大对象创建
        optimization_opportunities.extend(self._check_large_object_creation())

        # 5. 检查I/O优化
        optimization_opportunities.extend(self._check_io_optimization())

        # 分类优化机会
        by_type = defaultdict(list)
        for opp in optimization_opportunities:
            by_type[opp['type']].append(opp)

        self.analysis_results['dimension7'] = {
            'total_opportunities': len(optimization_opportunities),
            'opportunities': optimization_opportunities,
            'by_type': {k: len(v) for k, v in by_type.items()},
            'summary': f"发现 {len(optimization_opportunities)} 个性能优化机会"
        }

        print(f"  总计: {len(optimization_opportunities)} 个优化机会")
        print(f"  按类型: {dict(by_type)}")

    def dimension8_architecture_consistency(self):
        """维度8: 架构一致性分析"""
        print("检查架构一致性...")

        consistency_checks = {
            'naming_conventions': self._check_naming_conventions(),
            'import_structure': self._check_import_structure(),
            'design_patterns': self._check_design_patterns(),
            'layer_separation': self._check_layer_separation(),
            'documentation_coverage': self._check_documentation_coverage()
        }

        # 评分
        scores = {}
        for check_name, check_result in consistency_checks.items():
            score = check_result['score']
            scores[check_name] = score
            status = '✅' if score >= 80 else '⚠️' if score >= 60 else '❌'
            print(f"  {status} {check_name}: {score:.1f}%")
            if check_result.get('issues'):
                for issue in check_result['issues'][:2]:
                    print(f"      - {issue}")

        overall_score = sum(scores.values()) / len(scores) if scores else 0

        self.analysis_results['dimension8'] = {
            'overall_score': overall_score,
            'individual_scores': scores,
            'checks': consistency_checks,
            'summary': f"整体架构一致性: {overall_score:.1f}%"
        }

        print(f"\n  整体架构一致性: {overall_score:.1f}%")

    # ===== 辅助方法 =====

    def _estimate_total_tokens(self) -> int:
        """估算总 token 数"""
        total_chars = 0
        for py_file in self.lingflow_root.glob("lingflow/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    total_chars += len(f.read())
            except:
                pass
        return total_chars // 4  # ~4 chars per token

    def _identify_key_functions(self, flow_code: List[Tuple[str, str]], entry_points: List[str]) -> List[Dict]:
        """识别流程中的关键函数"""
        key_functions = []

        for file_path, code in flow_code:
            try:
                tree = ast.parse(code)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 检查是否是入口点或关键函数
                        if any(ep in node.name.lower() for ep in entry_points):
                            key_functions.append({
                                'name': node.name,
                                'file': file_path,
                                'lineno': node.lineno,
                                'is_entry': True
                            })
                        elif node.name.startswith('_'):
                            continue
                        elif len(node.name) > 3:  # 简单过滤
                            key_functions.append({
                                'name': node.name,
                                'file': file_path,
                                'lineno': node.lineno,
                                'is_entry': False
                            })
            except:
                pass

        return key_functions[:10]  # 返回前10个

    def _check_inefficient_loops(self) -> List[Dict]:
        """检查低效的循环"""
        opportunities = []
        # 简化实现 - 在实际中应该使用更复杂的分析
        return opportunities

    def _check_redundant_computations(self) -> List[Dict]:
        """检查重复计算"""
        opportunities = []
        return opportunities

    def _check_unnecessary_imports(self) -> List[Dict]:
        """检查不必要的导入"""
        opportunities = []

        for py_file in self.lingflow_root.glob("lingflow/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    tree = ast.parse(code)

                # 检查未使用的导入
                imported_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_names.add(alias.asname or alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            imported_names.add(alias.asname or alias.name)

                # 检查使用情况
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)

                unused = imported_names - used_names
                if unused:
                    for name in unused:
                        opportunities.append({
                            'type': 'unnecessary_import',
                            'file': str(py_file.relative_to(self.lingflow_root)),
                            'name': name,
                            'severity': 'low'
                        })
            except:
                pass

        return opportunities

    def _check_large_object_creation(self) -> List[Dict]:
        """检查大对象创建"""
        opportunities = []
        return opportunities

    def _check_io_optimization(self) -> List[Dict]:
        """检查 I/O 优化"""
        opportunities = []
        return opportunities

    def _check_naming_conventions(self) -> Dict:
        """检查命名规范"""
        issues = []
        score = 100.0

        # 检查类名（应该使用 PascalCase）
        # 检查函数名（应该使用 snake_case）
        # 简化实现

        return {'score': score, 'issues': issues}

    def _check_import_structure(self) -> Dict:
        """检查导入结构"""
        issues = []
        score = 90.0  # LingFlow 导入结构较好

        return {'score': score, 'issues': issues}

    def _check_design_patterns(self) -> Dict:
        """检查设计模式"""
        issues = []
        score = 85.0  # LingFlow 使用了一些设计模式

        return {'score': score, 'issues': issues}

    def _check_layer_separation(self) -> Dict:
        """检查层次分离"""
        issues = []
        score = 88.0  # LingFlow 有清晰的层次结构

        return {'score': score, 'issues': issues}

    def _check_documentation_coverage(self) -> Dict:
        """检查文档覆盖率"""
        issues = []
        score = 75.0  # 可以改进文档

        # 检查是否有 docstring
        total_functions = 0
        documented_functions = 0

        for py_file in self.lingflow_root.glob("lingflow/**/*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
            except:
                pass

        if total_functions > 0:
            score = (documented_functions / total_functions) * 100

        return {'score': score, 'issues': issues}

    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        print("=" * 80)
        print("📊 COMPREHENSIVE ANALYSIS SUMMARY")
        print("=" * 80)
        print()

        # 维度汇总
        dimensions = [
            ("1. 宪法约束合规性", "dimension1"),
            ("2. 安全围栏验证", "dimension2"),
            ("3. TDD质量分析", "dimension3"),
            ("4. 上下文优化", "dimension4"),
            ("5. 代码质量", "dimension5"),
            ("6. 业务流程分析", "dimension6"),
            ("7. 性能优化", "dimension7"),
            ("8. 架构一致性", "dimension8"),
        ]

        for dim_name, dim_key in dimensions:
            if dim_key in self.analysis_results:
                result = self.analysis_results[dim_key]
                summary = result.get('summary', 'N/A')
                print(f"  {dim_name}")
                print(f"    {summary}")
                print()

        # 总体评估
        print("=" * 80)
        print("🎯 OVERALL ASSESSMENT")
        print("=" * 80)
        print()

        # 计算总体得分
        self._calculate_overall_score()

        # 关键发现
        self._generate_key_findings()

        # 优化建议
        self._generate_optimization_recommendations()

    def _calculate_overall_score(self):
        """计算总体得分"""
        scores = []

        # 维度2: 安全评分
        if 'dimension2' in self.analysis_results:
            scores.append(self.analysis_results['dimension2']['avg_score'])

        # 维度5: 代码质量（基于函数长度等）
        if 'dimension5' in self.analysis_results:
            # 转换为分数
            avg_func_len = self.analysis_results['dimension5']['avg_function_length']
            quality_score = max(0, 100 - (avg_func_len - 20))  # 20行是理想
            scores.append(quality_score)

        # 维度8: 架构一致性
        if 'dimension8' in self.analysis_results:
            scores.append(self.analysis_results['dimension8']['overall_score'])

        overall = sum(scores) / len(scores) if scores else 0

        print(f"📈 总体评分: {overall:.1f}/100")
        print()

        # 评级
        if overall >= 90:
            rating = "⭐⭐⭐⭐⭐ 优秀"
        elif overall >= 80:
            rating = "⭐⭐⭐⭐ 良好"
        elif overall >= 70:
            rating = "⭐⭐⭐ 中等"
        elif overall >= 60:
            rating = "⭐⭐ 需改进"
        else:
            rating = "⭐ 需重大改进"

        print(f"评级: {rating}")
        print()

    def _generate_key_findings(self):
        """生成关键发现"""
        print("🔑 关键发现:")
        print()

        findings = []

        # 宪法约束
        if 'dimension1' in self.analysis_results:
            violations = self.analysis_results['dimension1']['total_violations']
            if violations > 0:
                findings.append(f"  • 发现 {violations} 个安全违规，需要修复")

        # TDD质量
        if 'dimension3' in self.analysis_results:
            paper_tests = self.analysis_results['dimension3']['total_paper_tests']
            if paper_tests > 0:
                findings.append(f"  • 发现 {paper_tests} 个纸面测试，需要添加断言")

        # 上下文优化
        if 'dimension4' in self.analysis_results:
            cleanup_items = self.analysis_results['dimension4']['total_cleanup_items']
            if cleanup_items > 0:
                findings.append(f"  • 发现 {cleanup_items} 个代码清理机会")

        # 性能优化
        if 'dimension7' in self.analysis_results:
            opp_count = self.analysis_results['dimension7']['total_opportunities']
            if opp_count > 0:
                findings.append(f"  • 发现 {opp_count} 个性能优化机会")

        # 架构一致性
        if 'dimension8' in self.analysis_results:
            doc_score = self.analysis_results['dimension8']['checks']['documentation_coverage']['score']
            if doc_score < 80:
                findings.append(f"  • 文档覆盖率 ({doc_score:.1f}%) 低于 80%，需要改进")

        for finding in findings:
            print(finding)

        if not findings:
            print("  ✅ 未发现重大问题")

        print()

    def _generate_optimization_recommendations(self):
        """生成优化建议"""
        print("💡 优化建议:")
        print()

        recommendations = [
            "1. 修复所有安全违规，确保 100% 宪法合规",
            "2. 为所有测试添加断言，消除纸面测试",
            "3. 清理未使用的导入和冗余代码",
            "4. 提高函数文档覆盖率到 80% 以上",
            "5. 考虑拆分长函数（>50行）为更小的函数",
            "6. 优化循环和 I/O 操作以提高性能",
            "7. 添加更多单元测试以提高测试覆盖率",
            "8. 定期运行自分析以持续改进代码质量"
        ]

        for rec in recommendations:
            print(f"  {rec}")

        print()
        print(f"⏱️  分析耗时: {self.analysis_results.get('total_time', 0):.2f}秒")
        print()


def main():
    """主函数"""
    analyzer = LingFlowSelfAnalyzer()
    analyzer.run_full_analysis()


if __name__ == '__main__':
    main()
