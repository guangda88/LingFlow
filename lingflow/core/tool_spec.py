"""LingFlow Tool Interface Standard (ToolSpec v1.0)

灵字辈统一的工具描述协议。所有灵字辈成员（灵依、灵克、灵知）的工具
都应通过 ToolSpec 注册，实现跨项目互操作。

核心设计：
- ToolSpec 是工具的元数据描述（name, description, parameters schema, required）
- ToolRegistry 管理 ToolSpec 的注册和查找
- 每个工具通过 callback_name 关联到具体实现
- 路由标记: primary (function calling) / fallback (关键词降级)

使用方式：
    from lingflow.core.tool_spec import ToolSpec, ToolRegistry

    spec = ToolSpec(
        name="schedule_today",
        description="查看今日日程",
        parameters={
            "type": "object",
            "properties": {},
        },
        required=[],
        callback_name="schedule_today",
        source="lingyi",
    )
    ToolRegistry.global_instance().register(spec)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolSpec:
    """统一工具描述协议。

    所有灵字辈工具必须通过此协议注册，确保跨项目互操作。

    Attributes:
        name: 工具唯一标识（snake_case，如 schedule_today）
        description: 功能描述（中文，用于 function calling 的 description 字段）
        parameters: JSON Schema 格式的参数描述
        required: 必填参数名列表
        callback_name: 关联到具体实现的回调名
        source: 来源项目（lingyi / lingclaude / lingzhi / lingflow）
        route: 路由类型（primary=主路由, fallback=降级路由）
        tags: 分类标签
        version: 工具版本
    """

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    callback_name: str = ""
    source: str = ""
    route: str = "primary"
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI function calling 格式。

        Returns:
            OpenAI tools 格式的字典
        """
        schema = dict(self.parameters)
        if self.required:
            schema["required"] = self.required
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "required": self.required,
            "callback_name": self.callback_name,
            "source": self.source,
            "route": self.route,
            "tags": self.tags,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolSpec":
        """从字典反序列化。"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            required=data.get("required", []),
            callback_name=data.get("callback_name", data["name"]),
            source=data.get("source", ""),
            route=data.get("route", "primary"),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
        )


class ToolRegistry:
    """工具注册表。

    管理所有 ToolSpec 的注册、查找和列表。

    Design:
        - 支持全局单例和独立实例
        - 按名称、来源、标签查找
        - 生成 OpenAI function calling 格式的工具列表
    """

    _global: Optional["ToolRegistry"] = None

    def __init__(self) -> None:
        self._specs: Dict[str, ToolSpec] = {}

    @classmethod
    def global_instance(cls) -> "ToolRegistry":
        """获取全局注册表实例。"""
        if cls._global is None:
            cls._global = cls()
        return cls._global

    def register(self, spec: ToolSpec) -> None:
        """注册一个工具。"""
        self._specs[spec.name] = spec

    def register_simple(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        required: Optional[List[str]] = None,
        callback_name: str = "",
        source: str = "",
    ) -> ToolSpec:
        """快捷注册一个工具。

        Args:
            name: 工具名
            description: 描述
            parameters: 参数 schema
            required: 必填参数
            callback_name: 回调名（默认等于 name）
            source: 来源项目

        Returns:
            注册的 ToolSpec
        """
        spec = ToolSpec(
            name=name,
            description=description,
            parameters=parameters or {"type": "object", "properties": {}},
            required=required or [],
            callback_name=callback_name or name,
            source=source,
        )
        self.register(spec)
        return spec

    def get(self, name: str) -> Optional[ToolSpec]:
        """按名称查找工具。"""
        return self._specs.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否已注册。"""
        return name in self._specs

    def remove(self, name: str) -> bool:
        """移除工具。"""
        if name in self._specs:
            del self._specs[name]
            return True
        return False

    def list_names(self) -> List[str]:
        """列出所有工具名称。"""
        return list(self._specs.keys())

    def list_by_source(self, source: str) -> List[ToolSpec]:
        """按来源过滤工具。"""
        return [s for s in self._specs.values() if s.source == source]

    def list_by_tag(self, tag: str) -> List[ToolSpec]:
        """按标签过滤工具。"""
        return [s for s in self._specs.values() if tag in s.tags]

    def list_primary(self) -> List[ToolSpec]:
        """列出所有主路由工具。"""
        return [s for s in self._specs.values() if s.route == "primary"]

    def list_fallback(self) -> List[ToolSpec]:
        """列出所有降级路由工具。"""
        return [s for s in self._specs.values() if s.route == "fallback"]

    def to_openai_tools(self, source: str = "") -> List[Dict[str, Any]]:
        """生成 OpenAI function calling 格式的工具列表。

        Args:
            source: 可选，只输出指定来源的工具

        Returns:
            OpenAI tools 格式列表
        """
        specs = self.list_by_source(source) if source else list(self._specs.values())
        return [s.to_openai_format() for s in specs if s.route == "primary"]

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """序列化所有工具为字典列表。"""
        return [s.to_dict() for s in self._specs.values()]

    def count(self) -> int:
        """返回注册工具数量。"""
        return len(self._specs)

    def clear(self) -> None:
        """清空注册表。"""
        self._specs.clear()
