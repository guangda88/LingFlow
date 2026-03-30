"""
LingFlow AI 友好接口改进

基于 VibeCoding 原则，提供更简洁、更直观的 API，
让 AI 更容易理解和使用 LingFlow。

核心改进:
1. 智能默认值 - 减少必需参数
2. 便捷方法 - 常见操作的一行调用
3. 上下文感知 - 自动推断意图
4. 智能重试 - 容错和恢复
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass

from lingflow import LingFlow
from lingflow.coordination.coordinator import Task, TaskResult


class AIFriendlyLingFlow(LingFlow):
    """AI 友好的 LingFlow 接口

    设计原则:
    - 意图明确: 方法名清晰表达意图
    - 智能默认: 自动处理常见情况
    - 容错设计: 自动重试和降级
    - 简洁易用: 一行代码完成常见操作
    """

    def __init__(self):
        super().__init__()
        self._max_retries = 3
        self._fallback_strategy = "skip"

    # ==================== 常见操作的便捷方法 ====================

    def review(
        self,
        path: str = ".",
        rules: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """代码审查 - 最常用的操作

        智能默认:
        - 自动扫描指定目录（默认当前目录）
        - 使用默认审查规则
        - 自动生成报告

        Args:
            path: 要审查的路径（默认当前目录）
            rules: 自定义规则列表（可选）
            **kwargs: 其他参数

        Returns:
            审查结果字典

        Examples:
            >>> lingflow.review()  # 审查当前目录
            >>> lingflow.review("src/")  # 审查 src 目录
            >>> lingflow.review(".", rules=["security", "performance"])  # 指定规则
        """
        params = {
            "path": str(path),
            "rules": rules or ["security", "bugs", "code_quality"],
            **kwargs
        }
        return self.run_skill("code-review", params)

    def test(
        self,
        path: str = ".",
        verbose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """运行测试 - 另一个常用操作

        Args:
            path: 测试路径（默认当前目录）
            verbose: 是否显示详细输出
            **kwargs: 其他参数

        Returns:
            测试结果字典

        Examples:
            >>> lingflow.test()  # 运行所有测试
            >>> lingflow.test("tests/test_core.py")  # 运行特定测试
        """
        params = {
            "path": str(path),
            "verbose": verbose,
            **kwargs
        }
        return self.run_skill("test-runner", params)

    def refactor(
        self,
        path: str = ".",
        style: str = "clean",
        **kwargs
    ) -> Dict[str, Any]:
        """代码重构

        Args:
            path: 重构路径
            style: 重构风格（clean/optimized/modern）
            **kwargs: 其他参数

        Returns:
            重构结果字典
        """
        params = {
            "path": str(path),
            "style": style,
            **kwargs
        }
        return self.run_skill("code-refactor", params)

    def debug(
        self,
        error: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """智能调试

        Args:
            error: 错误信息或堆栈跟踪
            context: 额外上下文信息
            **kwargs: 其他参数

        Returns:
            调试分析结果
        """
        params = {
            "error": error,
            "context": context or {},
            **kwargs
        }
        return self.run_skill("systematic-debugging", params)

    # ==================== 工作流便捷方法 ====================

    def workflow(self, name: str, **kwargs) -> Dict[str, Any]:
        """执行工作流（自动查找）

        智能特性:
        - 自动在工作流目录中查找
        - 支持 YAML 和 JSON 格式
        - 自动验证参数

        Args:
            name: 工作流名称（不含扩展名）
            **kwargs: 工作流参数

        Returns:
            执行结果

        Examples:
            >>> lingflow.workflow("code-review")
            >>> lingflow.workflow("full-ci", branch="main")
        """
        # 自动查找工作流文件
        workflows_dir = Path("workflows")
        possible_paths = [
            workflows_dir / f"{name}.yaml",
            workflows_dir / f"{name}.yml",
            workflows_dir / f"{name}.json",
        ]

        workflow_path = None
        for path in possible_paths:
            if path.exists():
                workflow_path = str(path)
                break

        if workflow_path is None:
            raise ValueError(f"工作流未找到: {name}")

        return self.run_workflow_file(workflow_path, **kwargs)

    # ==================== 智能执行（带重试） ====================

    async def execute_with_retry(
        self,
        skill_name: str,
        params: Dict[str, Any],
        max_retries: int = 3,
        on_retry: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """带智能重试的技能执行

        Args:
            skill_name: 技能名称
            params: 参数字典
            max_retries: 最大重试次数
            on_retry: 重试时的回调函数

        Returns:
            执行结果

        Examples:
            >>> result = await lingflow.execute_with_retry(
            ...     "code-review",
            ...     {"path": "src/"},
            ...     max_retries=2
            ... )
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                result = self.run_skill(skill_name, params)
                # 检查结果是否成功
                if result.get("success", True):
                    return result
            except Exception as e:
                last_error = e
                if on_retry:
                    on_retry(attempt, e)

        # 所有重试都失败，返回错误结果
        return {
            "success": False,
            "error": str(last_error),
            "attempts": max_retries
        }

    async def execute_tasks_with_fallback(
        self,
        tasks: List[Task],
        max_parallel: int = 2,
        fallback_strategy: str = "skip"
    ) -> Dict[str, TaskResult]:
        """带回退机制的并行任务执行

        Args:
            tasks: 任务列表
            max_parallel: 最大并行数
            fallback_strategy: 失败时的策略
                - "skip": 跳过失败的任务
                - "continue": 继续执行其他任务
                - "abort": 中止所有任务

        Returns:
            任务结果字典
        """
        semaphore = asyncio.Semaphore(max_parallel)
        results = {}

        async def execute_one(task: Task) -> tuple:
            """执行单个任务（带回退）"""
            try:
                async with semaphore:
                    result = await self._coordinator.execute_skill_async(
                        task.skill_name,
                        task.params
                    )
                    return (task.id, result)
            except Exception as e:
                if fallback_strategy == "abort":
                    raise
                # 其他策略：记录错误但继续
                return (task.id, TaskResult.error(str(e)))

        # 并行执行所有任务
        executed = await asyncio.gather(
            *[execute_one(task) for task in tasks],
            return_exceptions=(fallback_strategy != "abort")
        )

        # 收集结果
        for item in executed:
            if isinstance(item, Exception):
                continue
            task_id, result = item
            results[task_id] = result

        return results

    # ==================== 上下文感知 ====================

    def suggest_next_action(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """基于上下文建议下一步操作

        Args:
            context: 当前上下文信息

        Returns:
            建议的操作列表

        Examples:
            >>> context = {"stage": "development", "tests": "failing"}
            >>> suggestions = lingflow.suggest_next_action(context)
            >>> # ['debug', 'run_tests', 'fix_issues']
        """
        suggestions = []

        # 分析上下文并提供建议
        if context.get("tests") == "failing":
            suggestions.extend(["debug", "fix_issues"])
        if context.get("stage") == "development":
            suggestions.extend(["test", "review"])
        if context.get("coverage", 0) < 80:
            suggestions.append("improve_coverage")

        return suggestions

    # ==================== 批量操作 ====================

    def batch_review(
        self,
        paths: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """批量代码审查

        Args:
            paths: 路径列表
            **kwargs: 传递给 review 的参数

        Returns:
            审查结果列表
        """
        results = []
        for path in paths:
            result = self.review(path, **kwargs)
            results.append(result)
        return results

    def batch_test(
        self,
        paths: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """批量测试

        Args:
            paths: 测试路径列表
            **kwargs: 传递给 test 的参数

        Returns:
            测试结果列表
        """
        results = []
        for path in paths:
            result = self.test(path, **kwargs)
            results.append(result)
        return results


# ==================== 全局便捷函数 ====================

def create_ai_friendly() -> AIFriendlyLingFlow:
    """创建 AI 友好的 LingFlow 实例"""
    return AIFriendlyLingFlow()


# 单例实例
_ai_friendly_instance: Optional[AIFriendlyLingFlow] = None


def get_ai_friendly() -> AIFriendlyLingFlow:
    """获取全局 AI 友好实例（单例模式）"""
    global _ai_friendly_instance
    if _ai_friendly_instance is None:
        _ai_friendly_instance = create_ai_friendly()
    return _ai_friendly_instance


# ==================== 使用示例 ====================

if __name__ == "__main__":
    import asyncio

    # 创建 AI 友好实例
    lingflow = create_ai_friendly()

    # 示例 1: 简单的代码审查
    print("示例 1: 代码审查")
    result = lingflow.review()
    print(f"审查完成: {result.get('success')}")

    # 示例 2: 带重试的执行
    print("\n示例 2: 带重试的执行")
    async def with_retry():
        result = await lingflow.execute_with_retry(
            "code-review",
            {"path": "src/"},
            max_retries=2
        )
        print(f"执行完成: {result}")

    asyncio.run(with_retry())

    # 示例 3: 工作流执行
    print("\n示例 3: 工作流执行")
    result = lingflow.workflow("code-review")
    print(f"工作流完成: {result.get('success')}")

    # 示例 4: 批量操作
    print("\n示例 4: 批量审查")
    results = lingflow.batch_review(["src/", "tests/"])
    print(f"批量审查完成: {len(results)} 个目录")

    # 示例 5: 智能建议
    print("\n示例 5: 智能建议")
    suggestions = lingflow.suggest_next_action({
        "stage": "development",
        "tests": "failing"
    })
    print(f"建议操作: {suggestions}")
