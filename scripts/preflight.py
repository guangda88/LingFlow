"""
灵通 行动前置调查框架

核心原则：对不了解的系统做操作之前，必须先调查。
泛化到：数据库、API、文件系统、网络服务、代码库——一切外部系统。

使用方式：
    from preflight import investigate
    report = investigate(target="数据库表", context="要往 documents 写数据")

机制：不是靠意愿，是靠导入。在任何操作脚本开头 import 并调用。
"""

import inspect
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class Investigation:
    def __init__(self, target: str, context: str = ""):
        self.target = target
        self.context = context
        self.findings: Dict[str, Any] = {}
        self.gaps: List[str] = []
        self.safe = True
        self.report_lines: List[str] = []

    def add(self, key: str, value: Any):
        self.findings[key] = value
        self.report_lines.append(f"  {key}: {value}")

    def add_gap(self, description: str):
        self.gaps.append(description)
        self.report_lines.append(f"  ⚠ GAP: {description}")
        self.safe = False

    def block(self, reason: str):
        self.safe = False
        self.report_lines.append(f"  ✗ BLOCKED: {reason}")

    def report(self) -> str:
        header = f"=== Investigation: {self.target} ==="
        if self.context:
            header += f"\n  Context: {self.context}"
        return header + "\n" + "\n".join(self.report_lines)

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "context": self.context,
            "findings": self.findings,
            "gaps": self.gaps,
            "safe": self.safe,
        }


def investigate(target: str, context: str = "") -> Investigation:
    inv = Investigation(target, context)

    target_lower = target.lower()

    # 数据库相关
    if any(kw in target_lower for kw in ["数据库", "database", "表", "table", "postgres", "sqlite", "db"]):
        _investigate_database(inv)

    # API 相关
    if any(kw in target_lower for kw in ["api", "接口", "服务", "service", "endpoint", "http"]):
        _investigate_api(inv)

    # 文件系统相关
    if any(kw in target_lower for kw in ["文件", "file", "目录", "directory", "路径", "path"]):
        _investigate_filesystem(inv)

    # 代码相关
    if any(kw in target_lower for kw in ["代码", "code", "模块", "module", "函数", "function", "类", "class"]):
        _investigate_code(inv)

    # 如果没有匹配任何模式，提醒做手动调查
    if not inv.findings and not inv.gaps:
        inv.add_gap(f"未识别目标类型 '{target}'，需要手动调查")

    return inv


def _investigate_database(inv: Investigation):
    inv.add("type", "database")
    inv.add_gap("需要检查: 表结构、约束、外键、序列状态、合法值范围")
    inv.add_gap("需要确认: 目标系统实际读取哪张表（不是看表名，看代码）")
    inv.add_gap("需要确认: 写入的数据是否会被使用（用途追问）")


def _investigate_api(inv: Investigation):
    inv.add("type", "api")
    inv.add_gap("需要检查: 接口文档、请求格式、响应格式、错误码")
    inv.add_gap("需要确认: 速率限制（429策略）、超时设置、重试策略")
    inv.add_gap("需要确认: 认证方式、权限要求")


def _investigate_filesystem(inv: Investigation):
    inv.add("type", "filesystem")
    inv.add_gap("需要检查: 路径是否存在、权限、磁盘空间")
    inv.add_gap("需要确认: 文件编码、格式规范、命名约定")


def _investigate_code(inv: Investigation):
    inv.add("type", "code")
    inv.add_gap("需要检查: 依赖关系、接口约定、副作用")
    inv.add_gap("需要确认: 调用方是谁、修改影响范围")


if __name__ == "__main__":
    # 示例
    inv = investigate("数据库表 documents", "要往里面写入教材数据")
    print(inv.report())
    print(f"\nSafe to proceed: {inv.safe}")
    print(f"Gaps: {len(inv.gaps)}")
