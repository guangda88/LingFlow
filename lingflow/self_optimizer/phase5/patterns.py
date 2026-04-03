"""
模式识别引擎

识别代码中的反模式、安全漏洞和最佳实践违规。
YOLO模式：基于原型快速生产化
"""

import ast
import re
from typing import Dict, List, Any, Optional


class PatternRecognizer:
    """模式识别器 - 协调多个检测器"""

    def __init__(self, detectors: Optional[List["PatternDetector"]] = None):
        self.detectors = detectors or self._default_detectors()
        self._detected_count = 0

    def _default_detectors(self) -> List["PatternDetector"]:
        """默认检测器列表"""
        return [
            LongMethodDetector(),
            UnusedVariableDetector(),
            HardcodedSecretDetector(),
            DuplicateCodeDetector(),
            EmptyBlockDetector(),
        ]

    def register_detector(self, detector: "PatternDetector") -> None:
        """注册自定义检测器"""
        self.detectors.append(detector)

    def recognize_patterns(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """识别代码中的模式

        Args:
            source_code: 源代码内容
            file_path: 文件路径

        Returns:
            检测到的模式列表
        """
        patterns = []

        for detector in self.detectors:
            try:
                detected = detector.detect(source_code, file_path)
                patterns.extend(detected)
                self._detected_count += len(detected)
            except Exception:
                # 单个检测器失败不影响其他
                continue

        return patterns

    def recognize_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """从文件识别模式"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            return self.recognize_patterns(source_code, file_path)
        except Exception:
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_detectors": len(self.detectors),
            "total_detections": self._detected_count,
        }


class PatternDetector:
    """模式检测器基类"""

    def __init__(self, name: str, pattern_type: str, severity: str = "MEDIUM"):
        self.name = name
        self.pattern_type = pattern_type
        self.severity = severity
        self._detection_count = 0

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测模式

        Args:
            source_code: 源代码
            file_path: 文件路径

        Returns:
            检测结果列表
        """
        raise NotImplementedError

    def _create_finding(
        self, file_path: str, line: int, message: str, confidence: float = 0.8, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建标准化的发现结果"""
        finding = {
            "type": self.pattern_type,
            "name": self.name,
            "file": file_path,
            "line": line,
            "message": message,
            "severity": self.severity,
            "confidence": confidence,
        }

        if extra:
            finding.update(extra)

        self._detection_count += 1
        return finding


class LongMethodDetector(PatternDetector):
    """长方法检测器"""

    def __init__(self, threshold: int = 50):
        super().__init__(name="Long Method", pattern_type="anti_pattern", severity="MEDIUM")
        self.threshold = threshold

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测过长的方法"""
        patterns = []

        try:
            # 使用AST解析
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 计算函数行数
                    line_count = node.end_lineno - node.lineno if node.end_lineno else 0

                    if line_count > self.threshold:
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=node.lineno,
                                message=f"Function '{node.name}' is too long ({line_count} lines)",
                                confidence=0.9,
                                extra={"function_name": node.name, "line_count": line_count},
                            )
                        )
        except Exception:
            # AST解析失败，使用简单方法
            patterns.extend(self._simple_detection(source_code, file_path))

        return patterns

    def _simple_detection(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """简单的行数检测"""
        patterns = []
        lines = source_code.split("\n")
        current_function = None
        function_lines = 0
        function_start = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("async def "):
                # 保存上一个函数
                if current_function and function_lines > self.threshold:
                    patterns.append(
                        self._create_finding(
                            file_path=file_path,
                            line=function_start,
                            message=f"Function '{current_function}' is too long ({function_lines} lines)",
                            confidence=0.7,
                        )
                    )

                # 开始新函数
                func_def = stripped.replace("async def ", "def ")
                current_function = func_def.split("(")[0].replace("def ", "").strip()
                function_lines = 0
                function_start = i
            elif current_function and stripped:
                function_lines += 1

        # 检查最后一个函数
        if current_function and function_lines > self.threshold:
            patterns.append(
                self._create_finding(
                    file_path=file_path,
                    line=function_start,
                    message=f"Function '{current_function}' is too long ({function_lines} lines)",
                    confidence=0.7,
                )
            )

        return patterns


class UnusedVariableDetector(PatternDetector):
    """未使用变量检测器"""

    def __init__(self):
        super().__init__(name="Unused Variable", pattern_type="code_quality", severity="LOW")

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测未使用的变量"""
        patterns = []

        try:
            tree = ast.parse(source_code)

            # 收集所有赋值
            assignments: Dict[str, List[int]] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            line = node.lineno
                            if var_name not in assignments:
                                assignments[var_name] = []
                            assignments[var_name].append(line)

                # 处理for循环变量
                elif isinstance(node, ast.For):
                    if isinstance(node.target, ast.Name):
                        var_name = node.target.id
                        line = node.lineno
                        if var_name not in assignments:
                            assignments[var_name] = []
                        assignments[var_name].append(line)

            # 检查使用情况
            used_vars = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        used_vars.add(node.id)

            # 找出未使用的变量
            for var_name, lines in assignments.items():
                if var_name not in used_vars and not var_name.startswith("_"):
                    # 排除常见模式
                    if var_name not in ["self", "cls"]:
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=lines[0],
                                message=f"Variable '{var_name}' is assigned but never used",
                                confidence=0.85,
                                extra={"variable_name": var_name},
                            )
                        )

        except Exception:
            # AST解析失败，跳过
            pass

        return patterns[:10]  # 限制返回数量


class HardcodedSecretDetector(PatternDetector):
    """硬编码密钥检测器"""

    def __init__(self):
        super().__init__(name="Hardcoded Secret", pattern_type="security", severity="HIGH")
        self.secret_patterns = {
            "password": r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',
            "api_key": r'(?:api[_-]?key|apikey)\s*=\s*["\'][^"\']{10,}["\']',
            "secret": r'(?:secret|token)\s*=\s*["\'][^"\']{10,}["\']',
            "private_key": r'private[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
        }

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测硬编码密钥"""
        patterns = []

        for secret_name, pattern in self.secret_patterns.items():
            matches = re.finditer(pattern, source_code, re.IGNORECASE)
            for match in matches:
                line_num = source_code[: match.start()].count("\n") + 1
                patterns.append(
                    self._create_finding(
                        file_path=file_path,
                        line=line_num,
                        message=f"Hardcoded {secret_name.replace('_', ' ')} detected",
                        confidence=0.9,
                        extra={"secret_type": secret_name},
                    )
                )

        return patterns


class DuplicateCodeDetector(PatternDetector):
    """重复代码检测器"""

    def __init__(self, min_lines: int = 3):
        super().__init__(name="Duplicate Code", pattern_type="code_quality", severity="LOW")
        self.min_lines = min_lines

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测重复代码"""
        patterns = []

        # 提取代码块
        lines = source_code.split("\n")
        code_blocks: Dict[str, List[int]] = {}

        for i in range(len(lines) - self.min_lines + 1):
            # 提取连续的代码行
            block = []
            for j in range(self.min_lines):
                if i + j < len(lines):
                    line = lines[i + j].strip()
                    if line and not line.startswith("#"):
                        block.append(line)

            if len(block) >= self.min_lines:
                # 标准化代码块
                normalized = self._normalize_block(block)
                if normalized:
                    if normalized not in code_blocks:
                        code_blocks[normalized] = []
                    code_blocks[normalized].append(i + 1)

        # 找出重复的代码块
        for block, locations in code_blocks.items():
            if len(locations) > 1:
                for location in locations[1:]:
                    patterns.append(
                        self._create_finding(
                            file_path=file_path,
                            line=location,
                            message=f"Duplicate code block found (also at line {locations[0]})",
                            confidence=0.75,
                            extra={"duplicate_of": locations[0]},
                        )
                    )

        return patterns[:5]  # 限制返回数量

    def _normalize_block(self, block: List[str]) -> Optional[str]:
        """标准化代码块"""
        try:
            # 移除字符串字面量
            normalized = []
            for line in block:
                line = re.sub(r'["\'][^"\']*["\']', '""', line)
                line = re.sub(r"\b\d+\b", "0", line)
                normalized.append(line)

            return " ".join(normalized)
        except Exception:
            return None


class EmptyBlockDetector(PatternDetector):
    """空代码块检测器"""

    def __init__(self):
        super().__init__(name="Empty Block", pattern_type="code_quality", severity="INFO")

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测空代码块"""
        patterns = []

        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                # 检查空函数
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.body:
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=node.lineno,
                                message=f"Function '{node.name}' has empty body",
                                confidence=1.0,
                                extra={"function_name": node.name},
                            )
                        )
                    elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=node.lineno,
                                message=f"Function '{node.name}' only contains 'pass' statement",
                                confidence=1.0,
                                extra={"function_name": node.name},
                            )
                        )

                # 检查空if/for/while块
                elif isinstance(node, (ast.If, ast.For, ast.While)):
                    if not node.body:
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=node.lineno,
                                message=f"Empty {'if' if isinstance(node, ast.If) else 'loop'} block detected",
                                confidence=1.0,
                            )
                        )

        except Exception:
            # AST解析失败，使用简单方法
            patterns.extend(self._simple_detection(source_code, file_path))

        return patterns

    def _simple_detection(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """简单的空块检测"""
        patterns = []
        lines = source_code.split("\n")

        empty_pattern = re.compile(r"(def |if |for |while |class )[^:]+:\s*pass\s*$")

        for i, line in enumerate(lines, 1):
            if empty_pattern.search(line):
                patterns.append(
                    self._create_finding(
                        file_path=file_path, line=i, message="Empty block with only 'pass' statement", confidence=0.8
                    )
                )

        return patterns


class ComplexityDetector(PatternDetector):
    """圈复杂度检测器"""

    def __init__(self, threshold: int = 10):
        super().__init__(name="High Complexity", pattern_type="complexity", severity="MEDIUM")
        self.threshold = threshold

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测高复杂度函数"""
        patterns = []

        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)

                    if complexity > self.threshold:
                        patterns.append(
                            self._create_finding(
                                file_path=file_path,
                                line=node.lineno,
                                message=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                                confidence=0.9,
                                extra={"function_name": node.name, "complexity": complexity},
                            )
                        )

        except Exception:
            pass

        return patterns

    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity


# 导出
__all__ = [
    "PatternRecognizer",
    "PatternDetector",
    "LongMethodDetector",
    "UnusedVariableDetector",
    "HardcodedSecretDetector",
    "DuplicateCodeDetector",
    "EmptyBlockDetector",
    "ComplexityDetector",
]
