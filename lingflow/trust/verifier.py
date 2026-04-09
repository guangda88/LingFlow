"""可信输出验证框架 - 核心模块

让 AI 的输出可验证、可质疑、可信。
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List
import subprocess


class VerificationLevel(Enum):
    """验证层级"""
    SYNTAX = 1      # 语法: 能运行吗？
    SEMANTIC = 2    # 语义: 做了说的事吗？
    INTENT = 3      # 意图: 解决了真正的问题吗？
    BOUNDARY = 4    # 边界: 有没有遗漏约束？


@dataclass
class VerificationResult:
    """验证结果"""
    level: VerificationLevel
    passed: bool
    detail: str
    evidence: str = ""  # 支持证据
    confidence: float = 1.0  # 0.0-1.0


@dataclass
class TaskClaim:
    """任务声称 - AI 声称完成了什么"""
    action: str           # "添加数据真实性原则到 AGENTS.md"
    target: str           # "AGENTS.md"
    expected: str         # "文件包含 'Data Truth Principle'"


class Verifier:
    """验证器基类"""
    
    def __init__(self, level: VerificationLevel):
        self.level = level
    
    def verify(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        """验证声称是否成真"""
        raise NotImplementedError


class FileContentVerifier(Verifier):
    """文件内容验证器 - 检查文件是否包含预期内容"""

    def __init__(self):
        super().__init__(VerificationLevel.SEMANTIC)

    def verify(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        try:
            content = Path(claim.target).read_text(encoding="utf-8")
            found = claim.expected in content

            if found:
                return VerificationResult(
                    level=self.level,
                    passed=True,
                    detail=f"在 {claim.target} 中找到 '{claim.expected}'",
                    evidence="grep 通过",
                    confidence=0.95
                )
            else:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"在 {claim.target} 中未找到 '{claim.expected}'",
                    evidence="grep 失败",
                    confidence=0.9
                )
        except Exception as e:
            return VerificationResult(
                level=self.level,
                passed=False,
                detail=f"无法读取文件 {claim.target}: {e}",
                evidence="文件读取失败",
                confidence=0.5
            )


class CommandOutputVerifier(Verifier):
    """命令输出验证器 - 检查命令输出是否包含预期内容"""

    def __init__(self):
        super().__init__(VerificationLevel.SYNTAX)

    def verify(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        try:
            if actual_result is None:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail="No actual_result provided",
                    evidence="Missing output",
                    confidence=0.0
                )

            output = str(actual_result)
            found = claim.expected in output

            if found:
                return VerificationResult(
                    level=self.level,
                    passed=True,
                    detail=f"命令输出包含 '{claim.expected}'",
                    evidence=f"Output length: {len(output)} chars",
                    confidence=0.95
                )
            else:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"命令输出未找到 '{claim.expected}'",
                    evidence=f"Output preview: {output[:100]}",
                    confidence=0.8
                )
        except Exception as e:
            return VerificationResult(
                level=self.level,
                passed=False,
                detail=f"命令输出验证失败: {e}",
                evidence="Exception",
                confidence=0.0
            )


class DirectoryStructureVerifier(Verifier):
    """目录结构验证器 - 检查目录是否存在并包含预期文件/子目录"""

    def __init__(self):
        super().__init__(VerificationLevel.SEMANTIC)

    def verify(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        try:
            path = Path(claim.target)

            if not path.exists():
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"目录不存在: {claim.target}",
                    evidence="Path not found",
                    confidence=1.0
                )

            if not path.is_dir():
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"路径不是目录: {claim.target}",
                    evidence="Not a directory",
                    confidence=1.0
                )

            # Check for expected content
            if claim.expected:
                expected_items = claim.expected.split(",")
                found_items = []
                missing_items = []

                for item in expected_items:
                    item = item.strip()
                    if (path / item).exists():
                        found_items.append(item)
                    else:
                        missing_items.append(item)

                if not missing_items:
                    return VerificationResult(
                        level=self.level,
                        passed=True,
                        detail=f"目录 {claim.target} 包含所有预期项: {found_items}",
                        evidence=f"Found {len(found_items)} items",
                        confidence=0.95
                    )
                else:
                    return VerificationResult(
                        level=self.level,
                        passed=False,
                        detail=f"目录 {claim.target} 缺少项: {missing_items}",
                        evidence=f"Found: {found_items}, Missing: {missing_items}",
                        confidence=0.8
                    )
            else:
                return VerificationResult(
                    level=self.level,
                    passed=True,
                    detail=f"目录存在: {claim.target}",
                    evidence=f"Path exists",
                    confidence=1.0
                )
        except Exception as e:
            return VerificationResult(
                level=self.level,
                passed=False,
                detail=f"目录验证失败: {e}",
                evidence="Exception",
                confidence=0.0
            )


class GitDiffVerifier(Verifier):
    """Git 差异验证器 - 检查 git diff 是否包含预期更改"""

    def __init__(self):
        super().__init__(VerificationLevel.SEMANTIC)

    def verify(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        try:
            # Run git diff
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(claim.target).parent if claim.target else Path.cwd()
            )

            if result.returncode != 0:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"git diff 失败: {result.stderr}",
                    evidence="Git command failed",
                    confidence=0.0
                )

            diff_output = result.stdout

            if not diff_output:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail="工作区干净，无更改",
                    evidence="Empty diff",
                    confidence=1.0
                )

            # Check for expected content in diff
            if claim.expected in diff_output:
                return VerificationResult(
                    level=self.level,
                    passed=True,
                    detail=f"Git diff 包含预期更改: '{claim.expected}'",
                    evidence=f"Diff size: {len(diff_output)} chars",
                    confidence=0.95
                )
            else:
                return VerificationResult(
                    level=self.level,
                    passed=False,
                    detail=f"Git diff 未找到预期更改: '{claim.expected}'",
                    evidence=f"Diff preview: {diff_output[:200]}",
                    confidence=0.8
                )
        except FileNotFoundError:
            return VerificationResult(
                level=self.level,
                passed=False,
                detail="git 命令未找到",
                evidence="git not in PATH",
                confidence=0.0
            )
        except Exception as e:
            return VerificationResult(
                level=self.level,
                passed=False,
                detail=f"Git 验证失败: {e}",
                evidence="Exception",
                confidence=0.0
            )


@dataclass
class AuditReport:
    """质疑者审计报告"""
    questions: List[str]
    challenges: List[str]
    confidence: float  # 0.0-1.0
    summary: str = ""


class Skeptic:
    """质疑者 - 对 AI 输出进行自我挑战"""
    
    QUESTIONS = [
        "I claimed:",
        "Target:",
        "Expected:",
        "Verification passed?",
    ]
    
    def __init__(self):
        self.claim: TaskClaim | None = None
        self.verification_results: List[VerificationResult] = []
        self.result: Any = None
    
    def audit(self, claim: TaskClaim) -> AuditReport:
        """执行质疑者审计，返回完整报告"""
        self.claim = claim
        report = AuditReport(questions=self.QUESTIONS, challenges=[], confidence=0.0)
        
        if not self.verification_results:
            report.challenges.append("No verification performed")
            report.confidence = 0.0
            report.summary = "No verification"
            return report
        
        # 计算置信度
        passed_count = sum(1 for r in self.verification_results if r.passed)
        total = len(self.verification_results)
        report.confidence = passed_count / total if total > 0 else 0.0
        
        # 添加挑战
        for r in self.verification_results:
            if not r.passed:
                report.challenges.append(f"{r.level.name}: {r.detail}")
        
        # 生成摘要
        if report.challenges:
            report.summary = f"Partial completion ({len(report.challenges)} issues)"
        else:
            report.summary = f"Complete (confidence {report.confidence:.0%})"
        
        return report


@dataclass
class VerificationReport:
    """验证报告"""
    claims: List[TaskClaim]
    results: List[VerificationResult]
    overall_confidence: float
    passed: bool = False
    summary: str = ""


class VerificationPipeline:
    """验证管道 - 管理多个验证器"""
    
    def __init__(self):
        self.verifiers: List[Verifier] = []
        self.claim: TaskClaim | None = None
        self.result: Any = None
        self.verification_results: List[VerificationResult] = []
    
    def add_verifier(self, verifier: Verifier) -> None:
        """添加验证器"""
        self.verifiers.append(verifier)
    
    def execute(self, claim: TaskClaim, actual_result: Any = None) -> VerificationResult:
        """执行所有验证器"""
        self.claim = claim
        self.result = actual_result
        self.verification_results = []
        
        if not self.verifiers:
            return VerificationResult(
                level=VerificationLevel.SYNTAX,
                passed=False,
                detail="No verifiers configured",
                evidence="Empty pipeline",
                confidence=0.0
            )
        
        # 执行所有验证器
        for verifier in self.verifiers:
            try:
                result = verifier.verify(claim, actual_result)
                self.verification_results.append(result)
            except Exception as e:
                self.verification_results.append(VerificationResult(
                    level=verifier.level,
                    passed=False,
                    detail=f"Verifier exception: {e}",
                    evidence="Exception",
                    confidence=0.0
                ))
        
        # 计算总体置信度
        passed_count = sum(1 for r in self.verification_results if r.passed)
        total = len(self.verification_results)
        overall_confidence = passed_count / total if total > 0 else 0.0
        
        # 生成报告
        report = VerificationReport(
            claims=[claim] if claim else [],
            results=self.verification_results,
            overall_confidence=overall_confidence
        )
        report.passed = overall_confidence >= 0.8
        
        if report.passed:
            report.summary = f"Complete (confidence {overall_confidence:.0%})"
        else:
            report.summary = f"Partial (confidence {overall_confidence:.0%})"
        
        # 返回第一个结果（为了兼容性）
        return self.verification_results[0] if self.verification_results else VerificationResult(
            level=VerificationLevel.SYNTAX,
            passed=False,
            detail="No results",
            confidence=0.0
        )
    
    def generate_report(self) -> VerificationReport:
        """生成完整报告"""
        passed_count = sum(1 for r in self.verification_results if r.passed)
        total = len(self.verification_results)
        overall_confidence = passed_count / total if total > 0 else 0.0
        
        report = VerificationReport(
            claims=[self.claim] if self.claim else [],
            results=self.verification_results,
            overall_confidence=overall_confidence
        )
        report.passed = overall_confidence >= 0.8
        
        if report.passed:
            report.summary = f"Complete (confidence {overall_confidence:.0%})"
        else:
            report.summary = f"Partial (confidence {overall_confidence:.0%})"
        
        return report
