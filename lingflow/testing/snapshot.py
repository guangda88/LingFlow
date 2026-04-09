#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照测试模式
基于 Chrome DevTools MCP 的快照测试机制
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SnapshotMetadata:
    """快照元数据"""

    test_name: str
    created_at: str
    updated_at: Optional[str] = None
    version: str = "1.0.0"
    description: str = ""


class SnapshotTest:
    """快照测试 - 用于代码分析结果回归检测

    基于 Chrome DevTools MCP 的快照测试模式
    验证输出结果的稳定性和一致性

    特性:
    - JSON 格式快照存储
    - 自动差异检测
    - 支持快照更新
    - 版本控制集成
    - 元数据管理
    """

    def __init__(self, snapshot_dir: Path):
        """初始化快照测试

        Args:
            snapshot_dir: 快照存储目录

        Example:
            >>> snapshot = SnapshotTest(Path("tests/snapshots"))
            >>> result = {"value": 42, "text": "hello"}
            >>> snapshot.assert_match("test_result", result)
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📸 快照测试初始化: {self.snapshot_dir}")

    def _get_snapshot_path(self, test_name: str) -> Path:
        """获取快照文件路径

        Args:
            test_name: 测试名称

        Returns:
            快照文件路径
        """
        return self.snapshot_dir / f"{test_name}.snapshot.json"

    def _normalize_value(self, value: Any) -> Any:
        """规范化值，便于比较

        Args:
            value: 原始值

        Returns:
            规范化后的值
        """
        if isinstance(value, dict):
            return {k: self._normalize_value(v) for k, v in sorted(value.items())}
        elif isinstance(value, list):
            # 列表不排序，保持原始顺序
            return [self._normalize_value(v) for v in value]
        elif isinstance(value, (int, float, str, bool)) or value is None:
            return value
        else:
            return str(value)

    def assert_match(
        self, test_name: str, actual: Dict[str, Any], update: bool = False, metadata: Optional[SnapshotMetadata] = None
    ) -> bool:
        """断言实际结果与快照匹配

        Args:
            test_name: 测试名称
            actual: 实际结果
            update: 是否更新快照
            metadata: 快照元数据

        Returns:
            是否匹配

        Raises:
            AssertionError: 快照不匹配时

        Example:
            >>> snapshot = SnapshotTest(Path("tests/snapshots"))
            >>> result = analyze_code("def foo(): pass")
            >>> snapshot.assert_match("code_analysis", result)
        """
        snapshot_path = self._get_snapshot_path(test_name)

        # 规范化实际结果
        actual_normalized = self._normalize_value(actual)

        # 创建快照元数据
        if metadata is None:
            metadata = SnapshotMetadata(
                test_name=test_name, created_at=datetime.now().isoformat(), description=f"快照测试: {test_name}"
            )

        # 更新模式或快照不存在
        if update or not snapshot_path.exists():
            self._save_snapshot(snapshot_path, actual_normalized, metadata)
            logger.info(f"✓ 快照已更新: {test_name}")
            return True

        # 加载期望快照
        expected = self._load_snapshot(snapshot_path)

        # 比较
        if actual_normalized != expected["data"]:
            self._report_mismatch(test_name, expected["data"], actual_normalized, snapshot_path)
            return False

        logger.debug(f"✓ 快照匹配: {test_name}")
        return True

    def _save_snapshot(self, snapshot_path: Path, data: Dict[str, Any], metadata: SnapshotMetadata):
        """保存快照

        Args:
            snapshot_path: 快照文件路径
            data: 快照数据
            metadata: 快照元数据
        """
        snapshot = {"metadata": asdict(metadata), "data": data}

        snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_snapshot(self, snapshot_path: Path) -> Dict[str, Any]:
        """加载快照

        Args:
            snapshot_path: 快照文件路径

        Returns:
            快照数据

        Raises:
            FileNotFoundError: 快照文件不存在
            json.JSONDecodeError: 快照格式错误
        """
        content = snapshot_path.read_text(encoding="utf-8")
        return json.loads(content)

    def _report_mismatch(self, test_name: str, expected: Dict[str, Any], actual: Dict[str, Any], snapshot_path: Path):
        """报告不匹配

        Args:
            test_name: 测试名称
            expected: 期望值
            actual: 实际值
            snapshot_path: 快照路径

        Raises:
            AssertionError: 包含详细的差异信息
        """
        diff = self._compute_diff(expected, actual)

        error_message = f"\n{'=' * 70}\n"
        error_message += f"❌ 快照不匹配: {test_name}\n"
        error_message += f"{'=' * 70}\n"
        error_message += f"快照路径: {snapshot_path}\n\n"
        error_message += f"期望值:\n{json.dumps(expected, indent=2, ensure_ascii=False)}\n\n"
        error_message += f"实际值:\n{json.dumps(actual, indent=2, ensure_ascii=False)}\n\n"

        if diff:
            error_message += f"差异:\n{diff}\n\n"

        error_message += "要更新快照，运行:\n"
        error_message += f"  snapshot.assert_match('{test_name}', actual, update=True)\n"
        error_message += f"{'=' * 70}\n"

        logger.error(error_message)
        raise AssertionError(error_message)

    def _compute_diff(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> str:
        """计算差异

        Args:
            expected: 期望值
            actual: 实际值

        Returns:
            差异字符串
        """
        diff_lines = []

        # 检查缺失的键
        missing_keys = set(expected.keys()) - set(actual.keys())
        if missing_keys:
            diff_lines.append(f"  缺失键: {', '.join(missing_keys)}")

        # 检查新增的键
        added_keys = set(actual.keys()) - set(expected.keys())
        if added_keys:
            diff_lines.append(f"  新增键: {', '.join(added_keys)}")

        # 检查值差异
        for key in set(expected.keys()) & set(actual.keys()):
            if expected[key] != actual[key]:
                diff_lines.append(f"  键 '{key}' 差异:")
                diff_lines.append(f"    期望: {expected[key]}")
                diff_lines.append(f"    实际: {actual[key]}")

        return "\n".join(diff_lines) if diff_lines else "无明显差异"

    def update_snapshots(self, test_data: Dict[str, Dict[str, Any]]):
        """批量更新快照

        Args:
            test_data: 测试名称到结果的映射

        Example:
            >>> snapshot = SnapshotTest(Path("tests/snapshots"))
            >>> snapshot.update_snapshots({
            ...     "test1": {"result": 1},
            ...     "test2": {"result": 2}
            ... })
        """
        for test_name, result in test_data.items():
            self.assert_match(test_name, result, update=True)

        logger.info(f"✓ 已更新 {len(test_data)} 个快照")

    def list_snapshots(self) -> List[str]:
        """列出所有快照

        Returns:
            快照名称列表
        """
        snapshots = []
        for file_path in self.snapshot_dir.glob("*.snapshot.json"):
            # 移除 .snapshot.json 后缀，只保留测试名称
            name = file_path.name.replace(".snapshot.json", "")
            snapshots.append(name)

        return sorted(snapshots)

    def remove_snapshot(self, test_name: str) -> bool:
        """移除快照

        Args:
            test_name: 测试名称

        Returns:
            是否成功移除
        """
        snapshot_path = self._get_snapshot_path(test_name)

        if snapshot_path.exists():
            snapshot_path.unlink()
            logger.info(f"✓ 已移除快照: {test_name}")
            return True

        return False

    def clear_snapshots(self):
        """清除所有快照

        ⚠️ 警告：此操作不可逆
        """
        for snapshot_path in self.snapshot_dir.glob("*.snapshot.json"):
            snapshot_path.unlink()

        logger.info(f"✓ 已清除所有快照 ({self.snapshot_dir})")


# 示例使用

if __name__ == "__main__":  # pragma: no cover
    import tempfile

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("快照测试示例")
    print("=" * 70)

    # 创建临时快照目录
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_dir = Path(temp_dir) / "snapshots"
        snapshot = SnapshotTest(snapshot_dir)

        # 测试 1: 创建新快照
        print("\n" + "-" * 70)
        print("测试 1: 创建新快照")
        print("-" * 70)

        result1 = {"function": "calculate_sum", "parameters": ["a", "b"], "return_type": "int", "complexity": 1, "lines": 3}

        snapshot.assert_match("test_calculate_sum", result1)
        print("✓ 快照已创建")

        # 测试 2: 验证快照匹配
        print("\n" + "-" * 70)
        print("测试 2: 验证快照匹配")
        print("-" * 70)

        result2 = {"function": "calculate_sum", "parameters": ["a", "b"], "return_type": "int", "complexity": 1, "lines": 3}

        matches = snapshot.assert_match("test_calculate_sum", result2)
        print(f"✓ 快照匹配: {matches}")

        # 测试 3: 检测不匹配
        print("\n" + "-" * 70)
        print("测试 3: 检测不匹配（预期会失败）")
        print("-" * 70)

        result3 = {
            "function": "calculate_sum",
            "parameters": ["a", "b"],
            "return_type": "float",  # 改为 float
            "complexity": 2,  # 改为 2
            "lines": 4,
        }

        try:
            snapshot.assert_match("test_calculate_sum", result3)
            print("❌ 应该失败但没有")
        except AssertionError:
            print("✓ 正确检测到不匹配")

        # 测试 4: 更新快照
        print("\n" + "-" * 70)
        print("测试 4: 更新快照")
        print("-" * 70)

        result4 = {
            "function": "calculate_product",
            "parameters": ["a", "b"],
            "return_type": "int",
            "complexity": 1,
            "lines": 3,
        }

        snapshot.assert_match("test_calculate_product", result4)
        print("✓ 新快照已创建")

        # 测试 5: 批量更新
        print("\n" + "-" * 70)
        print("测试 5: 批量更新快照")
        print("-" * 70)

        batch_data = {
            "test_min": {"value": 1, "desc": "minimum"},
            "test_max": {"value": 100, "desc": "maximum"},
            "test_avg": {"value": 50.5, "desc": "average"},
        }

        snapshot.update_snapshots(batch_data)
        print("✓ 批量更新完成")

        # 测试 6: 列出快照
        print("\n" + "-" * 70)
        print("测试 6: 列出所有快照")
        print("-" * 70)

        snapshots = snapshot.list_snapshots()
        print(f"✓ 找到 {len(snapshots)} 个快照:")
        for name in snapshots:
            print(f"  - {name}")

    print("\n✅ 快照测试示例完成")
