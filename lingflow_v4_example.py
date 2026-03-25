"""LingFlow V4.0 核心代码示例

这是一个可执行的核心代码示例，展示了 V4.0 优化方案的核心功能。

使用方法：
    python lingflow_v4_example.py

运行此文件将演示：
    - Result 类型的所有功能
    - 配置构建器
    - 基础服务实现
    - 插件系统
    - 缓存系统
    - 监控系统
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from functools import wraps
import time
import json
import hashlib
import threading
import asyncio
from collections import defaultdict, OrderedDict


# =============================================================================
# 1. Result 类型（增强版）
# =============================================================================

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """统一的执行结果封装（增强版）"""

    data: Optional[T] = None
    error: Optional[str] = None
    code: str = "OK"
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    # ==================== 工厂方法 ====================

    @classmethod
    def ok(cls, data: T, **details) -> "Result[T]":
        """创建成功结果"""
        return cls(data=data, code="OK", details=details)

    @classmethod
    def fail(cls, error: str, code: str = "ERROR", **details) -> "Result[T]":
        """创建失败结果"""
        return cls(data=None, error=error, code=code, details=details)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Result[T]":
        """从字典反序列化"""
        try:
            if data.get("code") == "OK":
                return cls.ok(data.get("data"), **data.get("details", {}))
            else:
                return cls.fail(
                    data.get("error", "Unknown error"),
                    code=data.get("code", "ERROR"),
                    **data.get("details", {})
                )
        except Exception as e:
            return cls.fail(f"Failed to deserialize: {e}")

    # ==================== 属性 ====================

    @property
    def is_ok(self) -> bool:
        """是否成功"""
        return self.code == "OK" and self.error is None

    @property
    def is_error(self) -> bool:
        """是否失败"""
        return not self.is_ok

    # ==================== 基础操作 ====================

    def unwrap(self) -> T:
        """获取数据，失败时抛出异常"""
        if self.is_error:
            raise LingFlowError(self.error or "Unknown error", code=self.code)
        return self.data

    def unwrap_or(self, default: T) -> T:
        """获取数据，失败时返回默认值"""
        return self.data if self.is_ok else default

    def unwrap_or_else(self, func: Callable[[], T]) -> T:
        """获取数据，失败时调用函数"""
        return self.data if self.is_ok else func()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "ok": self.is_ok,
            "data": self.data,
            "error": self.error,
            "code": self.code,
            "details": self.details,
            "execution_time": self.execution_time,
        }

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    # ==================== 链式操作 ====================

    def map(self, func: Callable[[T], Any]) -> "Result[Any]":
        """链式转换（同步）"""
        if self.is_ok:
            try:
                start_time = time.time()
                result = func(self.data)
                return Result.ok(result, **self.details, execution_time=time.time() - start_time)
            except Exception as e:
                return Result.fail(str(e), code="MAP_ERROR")
        return self

    def and_then(self, func: Callable[[T], "Result[T]"]) -> "Result[T]":
        """链式调用（同步）"""
        if self.is_ok:
            return func(self.data)
        return self

    def or_else(self, func: Callable[[str], "Result[T]"]) -> "Result[T]":
        """错误处理链"""
        if self.is_error:
            return func(self.error)
        return self

    def inspect(self, func: Callable[["Result[T]"], None]) -> "Result[T]":
        """检查结果并返回自身"""
        func(self)
        return self

    # ==================== 组合操作 ====================

    @staticmethod
    def zip(*results: "Result[T]") -> "Result[List[T]]":
        """组合多个结果（全部成功才成功）"""
        data = []
        errors = []

        for result in results:
            if result.is_ok:
                data.append(result.data)
            else:
                errors.append(result.error)

        if errors:
            return Result.fail(
                f"Some results failed: {', '.join(errors)}",
                code="ZIP_ERROR",
                failed_results=len(errors)
            )

        return Result.ok(data)

    @staticmethod
    def first_ok(*results: "Result[T]") -> "Result[T]":
        """返回第一个成功的结果"""
        for result in results:
            if result.is_ok:
                return result

        return Result.fail(
            "All results failed",
            code="ALL_FAILED",
            errors=[r.error for r in results if r.is_error]
        )


# =============================================================================
# 2. 统一异常体系
# =============================================================================

class LingFlowError(Exception):
    """LingFlow 基础异常"""

    def __init__(
        self,
        message: str,
        *,
        code: str = "LF000",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return self.message


class ConfigurationError(LingFlowError):
    """配置相关异常"""
    pass


class SkillError(LingFlowError):
    """技能相关异常"""
    pass


class ValidationError(LingFlowError):
    """验证相关异常"""
    pass


# =============================================================================
# 3. 配置系统
# =============================================================================

@dataclass
class LingFlowConfig:
    """LingFlow 配置类（支持热重载）"""

    # 工作流配置
    max_parallel: int = 2
    max_iterations: int = 100
    workflow_timeout: float = 600.0

    # 技能配置
    skills_path: str = "skills"
    skill_timeout: float = 30.0
    skill_cache_enabled: bool = True

    # 代理配置
    agent_timeout: float = 300.0
    agent_context_limit: int = 8000

    # 压缩配置
    compression_enabled: bool = True
    compression_target_tokens: int = 4000

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 1000

    # 日志配置
    log_level: str = "INFO"

    @classmethod
    def builder(cls) -> "LingFlowConfigBuilder":
        """创建构建器"""
        return LingFlowConfigBuilder(cls())

    def validate(self) -> Result[None]:
        """验证配置"""
        errors = []

        if self.max_parallel < 1:
            errors.append("max_parallel must be >= 1")
        if self.skill_timeout < 0:
            errors.append("skill_timeout must be >= 0")
        if self.agent_timeout < 0:
            errors.append("agent_timeout must be >= 0")

        if errors:
            return Result.fail(
                f"Configuration validation failed: {'; '.join(errors)}",
                code="CONFIG_VALIDATION_FAILED",
                errors=errors
            )

        return Result.ok(None)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_parallel": self.max_parallel,
            "max_iterations": self.max_iterations,
            "workflow_timeout": self.workflow_timeout,
            "skills_path": self.skills_path,
            "skill_timeout": self.skill_timeout,
            "agent_timeout": self.agent_timeout,
            "agent_context_limit": self.agent_context_limit,
            "compression_enabled": self.compression_enabled,
            "compression_target_tokens": self.compression_target_tokens,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "log_level": self.log_level,
        }

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class LingFlowConfigBuilder:
    """配置构建器"""

    def __init__(self, config: LingFlowConfig):
        self._config = config

    def max_parallel(self, value: int) -> "LingFlowConfigBuilder":
        self._config.max_parallel = value
        return self

    def timeout(self, value: float) -> "LingFlowConfigBuilder":
        self._config.agent_timeout = value
        self._config.skill_timeout = value
        return self

    def compression(
        self,
        enabled: bool,
        target_tokens: int = 4000
    ) -> "LingFlowConfigBuilder":
        self._config.compression_enabled = enabled
        self._config.compression_target_tokens = target_tokens
        return self

    def cache(
        self,
        enabled: bool,
        ttl: int = 3600
    ) -> "LingFlowConfigBuilder":
        self._config.cache_enabled = enabled
        self._config.cache_ttl = ttl
        return self

    def performance(self, mode: str = "balanced") -> "LingFlowConfigBuilder":
        """性能预设"""
        if mode == "fast":
            self._config.max_parallel = 8
            self._config.compression_enabled = False
        elif mode == "balanced":
            self._config.max_parallel = 2
            self._config.compression_enabled = True
        elif mode == "conservative":
            self._config.max_parallel = 1
            self._config.compression_enabled = True
        return self

    def build(self) -> LingFlowConfig:
        """构建配置"""
        result = self._config.validate()
        if result.is_error:
            raise ConfigurationError(result.error, code=result.code)
        return self._config


# =============================================================================
# 4. 技能基类
# =============================================================================

@dataclass
class SkillContext:
    """技能执行上下文"""
    skill_name: str
    params: Dict[str, Any]
    working_dir: Path
    temp_dir: Path
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 新增字段
    execution_id: str = ""
    cache_key: Optional[str] = None


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 新增字段
    cached: bool = False
    execution_id: str = ""

    @classmethod
    def ok(cls, data: Any = None, **metadata) -> "SkillResult":
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "SkillResult":
        return cls(success=False, error=error, metadata=metadata)

    def to_result(self) -> Result[Any]:
        """转换为 Result 类型"""
        if self.success:
            return Result.ok(self.data, **self.metadata)
        else:
            return Result.fail(self.error or "Unknown error", details=self.metadata)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "cached": self.cached,
            "execution_id": self.execution_id,
            "metadata": self.metadata,
        }


class BaseSkill(ABC):
    """技能基类 - 所有技能应继承此类"""

    # 元数据
    name: str = "base-skill"
    description: str = "Base skill class"
    version: str = "1.0.0"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)

    @classmethod
    @abstractmethod
    def validate_params(cls, params: Dict[str, Any]) -> Result[None]:
        """验证参数"""
        return Result.ok(None)

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        """执行技能"""
        return SkillResult.ok()

    def pre_execute(self, context: SkillContext) -> SkillResult:
        """执行前钩子"""
        return SkillResult.ok()

    def post_execute(self, context: SkillContext, result: SkillResult) -> SkillResult:
        """执行后钩子"""
        return result

    def on_error(self, context: SkillContext, error: Exception) -> SkillResult:
        """错误处理钩子"""
        return SkillResult.fail(str(error))


# =============================================================================
# 5. 缓存系统
# =============================================================================

class CacheManager:
    """缓存管理器（支持 TTL 和 LRU）"""

    def __init__(self, config: LingFlowConfig):
        self._config = config
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0,
        }
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # 检查 TTL
            if time.time() - entry["timestamp"] > self._config.cache_ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                self._stats["total_size"] -= entry.get("size", 0)
                return None

            # 更新访问时间（LRU）
            self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry["data"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        with self._lock:
            # 计算大小
            value_str = json.dumps(value, default=str)
            size = len(value_str.encode('utf-8'))

            # 检查缓存大小限制
            if len(self._cache) >= self._config.cache_max_size:
                self._evict()

            entry = {
                "data": value,
                "timestamp": time.time(),
                "ttl": ttl or self._config.cache_ttl,
                "size": size,
            }

            self._cache[key] = entry
            self._stats["total_size"] += size

            return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                size = self._cache[key].get("size", 0)
                del self._cache[key]
                self._stats["total_size"] -= size
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats["total_size"] = 0

    def _evict(self):
        """淘汰最旧的缓存项"""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            size = entry.get("size", 0)
            self._stats["total_size"] -= size
            self._stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            hit_rate = (
                self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                if (self._stats["hits"] + self._stats["misses"]) > 0
                else 0.0
            )

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": hit_rate,
                "total_size": self._stats["total_size"],
                "total_entries": len(self._cache),
            }

    def update_config(self, new_config: LingFlowConfig):
        """更新配置"""
        self._config = new_config

        # 如果缓存大小限制减小，淘汰多余的缓存
        while len(self._cache) > self._config.cache_max_size:
            self._evict()


# =============================================================================
# 6. 监控系统
# =============================================================================

class Monitor:
    """性能监控器"""

    def __init__(self, config: LingFlowConfig):
        self._config = config
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        with self._lock:
            self._counters[name] += value

    def record_time(self, name: str, duration: float):
        """记录时间"""
        with self._lock:
            self._timers[name].append(duration)

            # 保留最近的100条记录
            if len(self._timers[name]) > 100:
                self._timers[name] = self._timers[name][-100:]

            # 检查性能阈值
            if duration > 1.0:
                pass  # 可以添加警告逻辑

    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        with self._lock:
            stats = {
                "counters": dict(self._counters),
                "timers": {},
            }

            # 计算计时器统计
            for name, times in self._timers.items():
                if times:
                    stats["timers"][name] = {
                        "count": len(times),
                        "min": min(times),
                        "max": max(times),
                        "avg": sum(times) / len(times),
                        "sum": sum(times),
                    }

            return stats

    def clear_metrics(self):
        """清除所有指标"""
        with self._lock:
            self._counters.clear()
            self._timers.clear()

    def update_config(self, new_config: LingFlowConfig):
        """更新配置"""
        self._config = new_config


# =============================================================================
# 7. 简单技能服务实现
# =============================================================================

class SimpleSkillService:
    """简单的技能服务（示例实现）"""

    def __init__(self, config: LingFlowConfig, cache_manager: Optional[CacheManager] = None):
        self._config = config
        self._cache_manager = cache_manager
        self._skills: Dict[str, BaseSkill] = {}

    def register_skill(self, skill: BaseSkill):
        """注册技能"""
        self._skills[skill.name] = skill
        print(f"✓ Registered skill: {skill.name}")

    def list(self) -> List[str]:
        """列出所有可用技能"""
        return list(self._skills.keys())

    def get_info(self, name: str) -> Result[Dict[str, Any]]:
        """获取技能信息"""
        if name not in self._skills:
            return Result.fail(f"Skill not found: {name}", code="SKILL_NOT_FOUND")

        skill = self._skills[name]
        return Result.ok({
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "author": skill.author,
            "dependencies": skill.dependencies,
        })

    def execute(self, name: str, params: Dict[str, Any]) -> SkillResult:
        """执行技能"""
        if name not in self._skills:
            return SkillResult.fail(f"Skill not found: {name}")

        skill = self._skills[name]

        # 验证参数
        validation = skill.validate_params(params)
        if validation.is_error:
            return SkillResult.fail(validation.error)

        # 检查缓存
        if self._cache_manager:
            cache_key = self._compute_cache_key(name, params)
            cached_result = self._cache_manager.get(cache_key)
            if cached_result:
                result = SkillResult(**cached_result)
                result.cached = True
                return result

        # 创建上下文
        import uuid
        context = SkillContext(
            skill_name=name,
            params=params,
            working_dir=Path.cwd(),
            temp_dir=Path.cwd() / ".lingflow" / "temp",
            execution_id=str(uuid.uuid4()),
            cache_key=self._compute_cache_key(name, params) if self._cache_manager else None,
        )

        # 执行
        try:
            start_time = time.time()

            pre_result = skill.pre_execute(context)
            if not pre_result.success:
                return pre_result

            result = skill.execute(context)
            result.execution_time = time.time() - start_time
            result.execution_id = context.execution_id

            result = skill.post_execute(context, result)

            # 缓存结果
            if self._cache_manager and result.success and context.cache_key:
                self._cache_manager.set(context.cache_key, result.to_dict())

            return result

        except Exception as e:
            error_result = skill.on_error(context, e)
            error_result.execution_time = time.time() - start_time
            return error_result

    def _compute_cache_key(self, skill_name: str, params: Dict[str, Any]) -> str:
        """计算缓存键"""
        key_str = f"{skill_name}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_str.encode()).hexdigest()


# =============================================================================
# 8. 示例技能
# =============================================================================

class EchoSkill(BaseSkill):
    """回声技能（示例）"""

    name = "echo"
    description = "Echo back the input parameters"
    version = "1.0.0"
    author = "LingFlow"

    @classmethod
    def validate_params(cls, params):
        if "message" not in params:
            return Result.fail("Missing 'message' parameter")
        if not isinstance(params["message"], str):
            return Result.fail("'message' must be a string")
        return Result.ok(None)

    def execute(self, context):
        message = context.params["message"]
        return SkillResult.ok(data={
            "echo": message,
            "timestamp": time.time(),
        })


class CalculatorSkill(BaseSkill):
    """计算器技能（示例）"""

    name = "calculator"
    description = "Simple calculator for basic operations"
    version = "1.0.0"
    author = "LingFlow"

    @classmethod
    def validate_params(cls, params):
        if "operation" not in params:
            return Result.fail("Missing 'operation' parameter")
        if "a" not in params or "b" not in params:
            return Result.fail("Missing operands 'a' and/or 'b'")
        return Result.ok(None)

    def execute(self, context):
        operation = context.params["operation"]
        a = context.params["a"]
        b = context.params["b"]

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a / b
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return SkillResult.ok(data={
                "operation": operation,
                "a": a,
                "b": b,
                "result": result,
            })

        except Exception as e:
            raise ValueError(f"Calculation error: {e}")


# =============================================================================
# 9. 测试和演示函数
# =============================================================================

def test_result_type():
    """测试 Result 类型"""
    print("\n" + "=" * 70)
    print("  测试 Result 类型")
    print("=" * 70)

    # 1. 基础创建
    print("\n1. 基础创建:")
    success = Result.ok(data={"key": "value"})
    failure = Result.fail("Something went wrong", code="ERR001")
    print(f"   Success: {success.is_ok}, Data: {success.data}")
    print(f"   Failure: {failure.is_error}, Error: {failure.error}")

    # 2. 链式调用
    print("\n2. 链式调用:")
    result = (Result.ok("  hello  ")
              .map(str.strip)
              .map(str.upper)
              .and_then(lambda x: Result.ok(x + "!"))
              .inspect(lambda r: print(f"   Current: {r.data}")))
    print(f"   Final: {result.data}")

    # 3. 组合操作
    print("\n3. 组合操作:")
    r1 = Result.ok(1)
    r2 = Result.ok(2)
    r3 = Result.ok(3)
    combined = Result.zip(r1, r2, r3)
    print(f"   Combined: {combined.data}")

    # 4. 错误处理
    print("\n4. 错误处理:")
    result = Result.fail("Error occurred").or_else(
        lambda error: Result.ok(f"Recovered from: {error}")
    )
    print(f"   Recovered: {result.data}")

    # 5. 序列化
    print("\n5. 序列化:")
    json_str = result.to_json()
    print(f"   JSON:\n{json_str}")


def test_config_builder():
    """测试配置构建器"""
    print("\n" + "=" * 70)
    print("  测试配置构建器")
    print("=" * 70)

    # 1. 基础构建
    print("\n1. 基础构建:")
    config = (LingFlowConfig.builder()
              .max_parallel(4)
              .timeout(600)
              .compression(True, 8000)
              .build())
    print(f"   Config: {config.to_dict()}")

    # 2. 性能预设
    print("\n2. 性能预设:")
    fast_config = LingFlowConfig.builder().performance("fast").build()
    balanced_config = LingFlowConfig.builder().performance("balanced").build()
    print(f"   Fast max_parallel: {fast_config.max_parallel}")
    print(f"   Balanced max_parallel: {balanced_config.max_parallel}")

    # 3. 配置验证
    print("\n3. 配置验证:")
    valid_config = LingFlowConfig()
    print(f"   Valid: {valid_config.validate().is_ok}")

    try:
        invalid_config = (LingFlowConfig.builder()
                          .max_parallel(0)
                          .build())
        print(f"   Invalid: {invalid_config.validate().is_error}")
    except ConfigurationError as e:
        print(f"   Invalid config rejected: {e.message}")


def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "=" * 70)
    print("  测试缓存管理器")
    print("=" * 70)

    config = LingFlowConfig(cache_enabled=True, cache_ttl=60, cache_max_size=3)
    cache = CacheManager(config)

    # 1. 基础操作
    print("\n1. 基础操作:")
    cache.set("key1", {"data": "value1"})
    result = cache.get("key1")
    print(f"   Get result: {result}")

    # 2. 缓存未命中
    print("\n2. 缓存未命中:")
    result = cache.get("key_not_exist")
    print(f"   Result: {result}")

    # 3. LRU 淘汰
    print("\n3. LRU 淘汰（max_size=3）:")
    cache.set("key2", {"data": "value2"})
    cache.set("key3", {"data": "value3"})
    cache.set("key4", {"data": "value4"})  # 应该淘汰 key1
    print(f"   Key1 exists: {cache.get('key1') is not None}")
    print(f"   Key2 exists: {cache.get('key2') is not None}")
    print(f"   Key4 exists: {cache.get('key4') is not None}")

    # 4. 缓存统计
    print("\n4. 缓存统计:")
    stats = cache.get_stats()
    print(f"   Stats: {json.dumps(stats, indent=4)}")


def test_monitor():
    """测试监控系统"""
    print("\n" + "=" * 70)
    print("  测试监控系统")
    print("=" * 70)

    config = LingFlowConfig()
    monitor = Monitor(config)

    # 1. 计数器
    print("\n1. 计数器:")
    monitor.increment_counter("api_calls")
    monitor.increment_counter("api_calls", 5)
    monitor.increment_counter("errors")
    print(f"   Counters: {monitor.get_stats()['counters']}")

    # 2. 计时器
    print("\n2. 计时器:")
    for i in range(5):
        start = time.time()
        time.sleep(0.01 * i)
        duration = time.time() - start
        monitor.record_time("operation_time", duration)

    print(f"   Timers: {monitor.get_stats()['timers']}")


def test_skill_service():
    """测试技能服务"""
    print("\n" + "=" * 70)
    print("  测试技能服务")
    print("=" * 70)

    config = LingFlowConfig(skill_cache_enabled=True)
    cache = CacheManager(config)
    skill_service = SimpleSkillService(config, cache)

    # 1. 注册技能
    print("\n1. 注册技能:")
    skill_service.register_skill(EchoSkill())
    skill_service.register_skill(CalculatorSkill())
    print(f"   Available skills: {skill_service.list()}")

    # 2. 获取技能信息
    print("\n2. 获取技能信息:")
    info = skill_service.get_info("echo")
    print(f"   Info: {info.data}")

    # 3. 执行技能
    print("\n3. 执行 Echo 技能:")
    result = skill_service.execute("echo", {"message": "Hello LingFlow!"})
    print(f"   Result: {result.data}")
    print(f"   Execution time: {result.execution_time:.4f}s")

    # 4. 执行计算器技能
    print("\n4. 执行 Calculator 技能:")
    result = skill_service.execute("calculator", {"operation": "add", "a": 10, "b": 20})
    print(f"   Result: {result.data}")

    # 5. 缓存测试
    print("\n5. 缓存测试:")
    result1 = skill_service.execute("echo", {"message": "cached"})
    print(f"   First call (cached={result1.cached}): {result1.data}")

    result2 = skill_service.execute("echo", {"message": "cached"})
    print(f"   Second call (cached={result2.cached}): {result2.data}")

    # 6. 参数验证
    print("\n6. 参数验证:")
    result = skill_service.execute("echo", {})
    print(f"   Missing param: {result.error}")

    # 7. 错误处理
    print("\n7. 错误处理:")
    result = skill_service.execute("calculator", {"operation": "divide", "a": 10, "b": 0})
    print(f"   Division by zero: {result.error}")


def main():
    """主函数 - 运行所有测试"""
    print("\n" + "=" * 70)
    print("  LingFlow V4.0 核心代码示例")
    print("=" * 70)

    try:
        # 运行所有测试
        test_result_type()
        test_config_builder()
        test_cache_manager()
        test_monitor()
        test_skill_service()

        # 总结
        print("\n" + "=" * 70)
        print("  ✓ 所有测试完成！")
        print("=" * 70)
        print("\n核心功能:")
        print("  ✓ Result 类型 - 统一结果封装")
        print("  ✓ 配置构建器 - 链式配置")
        print("  ✓ 缓存管理器 - LRU + TTL")
        print("  ✓ 监控系统 - 性能追踪")
        print("  ✓ 技能服务 - 技能执行")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
