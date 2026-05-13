# 自定义Agent示例

本文档展示如何创建和定制lingflow Agent。

## 目录

- [基础Agent](#基础agent)
- [添加技能](#添加技能)
- [状态管理](#状态管理)
- [Agent通信](#agent通信)
- [高级特性](#高级特性)

## 基础Agent

### 简单Agent

```python
from lingflow.coordination import BaseAgent

class SimpleAgent(BaseAgent):
    """简单的自定义Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.logger.info(f"初始化 {self.name}")

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        """执行技能"""
        self.logger.info(f"执行技能: {skill_name}")

        if skill_name == "hello":
            return self._hello(params)
        else:
            return {
                "status": "error",
                "message": f"未知技能: {skill_name}"
            }

    def _hello(self, params: dict) -> dict:
        """打招呼技能"""
        name = params.get("name", "世界")
        return {
            "status": "success",
            "message": f"你好，{name}！"
        }
```

### 使用自定义Agent

```python
from lingflow.coordination import AgentRegistry
from lingflow import lingflow

# 注册自定义Agent
registry = AgentRegistry()
registry.register("simple", SimpleAgent)

# 使用自定义Agent
lf = lingflow()
result = lf.run_skill("hello", {"name": "用户"})
print(result)  # {'status': 'success', 'message': '你好，用户！'}
```

## 添加技能

### 单一技能Agent

```python
from lingflow.coordination import BaseAgent
import subprocess

class GitAgent(BaseAgent):
    """Git操作Agent"""

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if skill_name == "status":
            return self._git_status(params)
        elif skill_name == "commit":
            return self._git_commit(params)
        elif skill_name == "push":
            return self._git_push(params)
        else:
            return super().execute_skill(skill_name, params)

    def _git_status(self, params: dict) -> dict:
        """检查Git状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []

            return {
                "status": "success",
                "changed_files": len(files),
                "files": files
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _git_commit(self, params: dict) -> dict:
        """提交代码"""
        message = params.get("message", "自动提交")
        files = params.get("files", ".")

        try:
            # 添加文件
            subprocess.run(["git", "add", files], check=True)

            # 提交
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True
            )

            return {
                "status": "success",
                "message": f"提交成功: {message}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _git_push(self, params: dict) -> dict:
        """推送到远程"""
        remote = params.get("remote", "origin")
        branch = params.get("branch", "main")

        try:
            subprocess.run(
                ["git", "push", remote, branch],
                check=True,
                capture_output=True
            )

            return {
                "status": "success",
                "message": f"推送到 {remote}/{branch}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": str(e)
            }
```

### 多技能Agent

```python
from lingflow.coordination import BaseAgent
import requests
import json

class DevOpsAgent(BaseAgent):
    """DevOps自动化Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.api_base = config.get("api_base") if config else None

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        skills = {
            "deploy": self._deploy,
            "rollback": self._rollback,
            "scale": self._scale,
            "monitor": self._monitor,
            "health_check": self._health_check
        }

        handler = skills.get(skill_name)
        if handler:
            return handler(params)
        else:
            return {
                "status": "error",
                "message": f"未知技能: {skill_name}"
            }

    def _deploy(self, params: dict) -> dict:
        """部署服务"""
        service = params.get("service")
        version = params.get("version")
        environment = params.get("environment", "production")

        self.logger.info(f"部署 {service}:{version} 到 {environment}")

        # 实际部署逻辑
        # ...

        return {
            "status": "success",
            "service": service,
            "version": version,
            "environment": environment,
            "deployment_id": "deploy-12345"
        }

    def _rollback(self, params: dict) -> dict:
        """回滚部署"""
        deployment_id = params.get("deployment_id")

        self.logger.info(f"回滚部署 {deployment_id}")

        # 回滚逻辑
        # ...

        return {
            "status": "success",
            "message": f"已回滚到 {deployment_id}"
        }

    def _scale(self, params: dict) -> dict:
        """扩缩容"""
        service = params.get("service")
        replicas = params.get("replicas", 1)

        self.logger.info(f"扩容 {service} 到 {replicas} 个实例")

        # 扩缩容逻辑
        # ...

        return {
            "status": "success",
            "service": service,
            "replicas": replicas
        }

    def _monitor(self, params: dict) -> dict:
        """监控服务"""
        service = params.get("service")
        duration = params.get("duration", 300)

        # 监控逻辑
        # ...

        return {
            "status": "success",
            "metrics": {
                "cpu_usage": 65.5,
                "memory_usage": 72.3,
                "request_count": 15234,
                "error_rate": 0.02
            }
        }

    def _health_check(self, params: dict) -> dict:
        """健康检查"""
        service = params.get("service")

        # 健康检查逻辑
        # ...

        return {
            "status": "success",
            "healthy": True,
            "checks": {
                "api": "healthy",
                "database": "healthy",
                "cache": "healthy"
            }
        }
```

## 状态管理

### 带状态的Agent

```python
from lingflow.coordination import BaseAgent
from typing import Dict, Any
import json
from pathlib import Path

class StatefulAgent(BaseAgent):
    """带状态的Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.state_file = Path(f".agent_state_{name}.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_state(self):
        """保存状态"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if skill_name == "set_state":
            return self._set_state(params)
        elif skill_name == "get_state":
            return self._get_state(params)
        elif skill_name == "clear_state":
            return self._clear_state(params)
        else:
            return super().execute_skill(skill_name, params)

    def _set_state(self, params: dict) -> dict:
        """设置状态"""
        key = params.get("key")
        value = params.get("value")

        self.state[key] = value
        self._save_state()

        return {
            "status": "success",
            "key": key,
            "value": value
        }

    def _get_state(self, params: dict) -> dict:
        """获取状态"""
        key = params.get("key")

        if key:
            value = self.state.get(key)
            return {
                "status": "success",
                "key": key,
                "value": value
            }
        else:
            return {
                "status": "success",
                "state": self.state
            }

    def _clear_state(self, params: dict) -> dict:
        """清除状态"""
        self.state.clear()
        self._save_state()

        return {
            "status": "success",
            "message": "状态已清除"
        }
```

## Agent通信

### Agent间通信

```python
from lingflow.coordination import BaseAgent, AgentCoordinator
from typing import List, Dict

class CommunicatingAgent(BaseAgent):
    """可通信的Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.coordinator = None  # 将在运行时设置

    def set_coordinator(self, coordinator: AgentCoordinator):
        """设置协调器"""
        self.coordinator = coordinator

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if skill_name == "delegate":
            return self._delegate(params)
        elif skill_name == "broadcast":
            return self._broadcast(params)
        elif skill_name == "collaborate":
            return self._collaborate(params)
        else:
            return super().execute_skill(skill_name, params)

    def _delegate(self, params: dict) -> dict:
        """委托任务给其他Agent"""
        target_agent = params.get("agent")
        target_skill = params.get("skill")
        target_params = params.get("params", {})

        if not self.coordinator:
            return {
                "status": "error",
                "message": "未设置协调器"
            }

        # 通过协调器执行
        result = self.coordinator.execute_agent_skill(
            target_agent,
            target_skill,
            target_params
        )

        return {
            "status": "success",
            "delegated_to": target_agent,
            "result": result
        }

    def _broadcast(self, params: dict) -> dict:
        """广播消息给所有Agent"""
        message = params.get("message")
        skill = params.get("skill")
        skill_params = params.get("params", {})

        if not self.coordinator:
            return {
                "status": "error",
                "message": "未设置协调器"
            }

        # 获取所有Agent
        agents = self.coordinator.list_agents()

        results = {}
        for agent_name in agents:
            try:
                result = self.coordinator.execute_agent_skill(
                    agent_name,
                    skill,
                    skill_params
                )
                results[agent_name] = result
            except Exception as e:
                results[agent_name] = {
                    "status": "error",
                    "message": str(e)
                }

        return {
            "status": "success",
            "broadcast_results": results
        }

    def _collaborate(self, params: dict) -> dict:
        """协作完成任务"""
        workflow = params.get("workflow")

        # 定义协作工作流
        steps = [
            {"agent": "analyzer", "skill": "analyze", "params": params},
            {"agent": "planner", "skill": "plan", "params": params},
            {"agent": "executor", "skill": "execute", "params": params},
        ]

        results = []
        for step in steps:
            result = self.coordinator.execute_agent_skill(
                step["agent"],
                step["skill"],
                step["params"]
            )
            results.append(result)

            # 如果某步失败，停止协作
            if result.get("status") == "error":
                break

        return {
            "status": "success",
            "collaboration_results": results
        }
```

## 高级特性

### 异步Agent

```python
from lingflow.coordination import BaseAgent
import asyncio
from typing import Coroutine

class AsyncAgent(BaseAgent):
    """异步Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.loop = asyncio.get_event_loop()

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if skill_name == "parallel_tasks":
            return self._run_parallel(params)
        elif skill_name == "batch_process":
            return self._batch_process(params)
        else:
            return super().execute_skill(skill_name, params)

    def _run_parallel(self, params: dict) -> dict:
        """并行执行多个任务"""
        tasks = params.get("tasks", [])

        async def run_all():
            coroutines = [self._async_task(task) for task in tasks]
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            return results

        results = self.loop.run_until_complete(run_all())

        return {
            "status": "success",
            "results": results
        }

    async def _async_task(self, task: dict) -> dict:
        """异步任务"""
        # 模拟异步操作
        await asyncio.sleep(0.1)
        return {
            "task": task,
            "status": "completed"
        }

    def _batch_process(self, params: dict) -> dict:
        """批量处理"""
        items = params.get("items", [])
        batch_size = params.get("batch_size", 10)

        async def process_batches():
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_result = await self._process_batch(batch)
                results.extend(batch_result)
            return results

        results = self.loop.run_until_complete(process_batches())

        return {
            "status": "success",
            "processed": len(results),
            "results": results
        }

    async def _process_batch(self, batch: list) -> list:
        """处理批次"""
        # 模拟批量处理
        await asyncio.sleep(0.05)
        return [{"item": item, "status": "processed"} for item in batch]
```

### 带缓存的Agent

```python
from lingflow.coordination import BaseAgent
from functools import lru_cache
from typing import Any
import hashlib
import json

class CachedAgent(BaseAgent):
    """带缓存的Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.cache_enabled = config.get("cache_enabled", True) if config else True
        self._cache = {}

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if self.cache_enabled:
            cache_key = self._get_cache_key(skill_name, params)

            if cache_key in self._cache:
                self.logger.info(f"缓存命中: {skill_name}")
                return self._cache[cache_key]

        result = super().execute_skill(skill_name, params)

        if self.cache_enabled and result.get("status") == "success":
            self._cache[cache_key] = result

        return result

    def _get_cache_key(self, skill_name: str, params: dict) -> str:
        """生成缓存键"""
        params_str = json.dumps(params, sort_keys=True)
        key_str = f"{skill_name}:{params_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self.logger.info("缓存已清除")

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }
```

## 完整示例

### 数据分析Agent

```python
from lingflow.coordination import BaseAgent
import pandas as pd
import numpy as np
from pathlib import Path

class DataAnalysisAgent(BaseAgent):
    """数据分析Agent"""

    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.data = None

    def execute_skill(self, skill_name: str, params: dict) -> dict:
        skills = {
            "load_data": self._load_data,
            "summary": self._summary,
            "analyze": self._analyze,
            "visualize": self._visualize,
            "export": self._export
        }

        handler = skills.get(skill_name)
        if handler:
            return handler(params)
        else:
            return {
                "status": "error",
                "message": f"未知技能: {skill_name}"
            }

    def _load_data(self, params: dict) -> dict:
        """加载数据"""
        file_path = params.get("file_path")
        file_type = params.get("type", "csv")

        try:
            if file_type == "csv":
                self.data = pd.read_csv(file_path)
            elif file_type == "excel":
                self.data = pd.read_excel(file_path)
            elif file_type == "json":
                self.data = pd.read_json(file_path)
            else:
                return {
                    "status": "error",
                    "message": f"不支持的文件类型: {file_type}"
                }

            return {
                "status": "success",
                "rows": len(self.data),
                "columns": len(self.data.columns),
                "column_names": list(self.data.columns)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _summary(self, params: dict) -> dict:
        """生成数据摘要"""
        if self.data is None:
            return {
                "status": "error",
                "message": "未加载数据"
            }

        summary = {
            "shape": self.data.shape,
            "dtypes": self.data.dtypes.astype(str).to_dict(),
            "missing_values": self.data.isnull().sum().to_dict(),
            "numeric_summary": self.data.describe().to_dict()
        }

        return {
            "status": "success",
            "summary": summary
        }

    def _analyze(self, params: dict) -> dict:
        """执行分析"""
        analysis_type = params.get("type", "correlation")

        if self.data is None:
            return {
                "status": "error",
                "message": "未加载数据"
            }

        if analysis_type == "correlation":
            result = self.data.corr().to_dict()
        elif analysis_type == "distribution":
            result = self.data.describe().to_dict()
        else:
            return {
                "status": "error",
                "message": f"未知分析类型: {analysis_type}"
            }

        return {
            "status": "success",
            "analysis_type": analysis_type,
            "result": result
        }

    def _visualize(self, params: dict) -> dict:
        """生成可视化"""
        chart_type = params.get("type", "histogram")
        columns = params.get("columns", [])

        if self.data is None:
            return {
                "status": "error",
                "message": "未加载数据"
            }

        # 可视化逻辑
        # 这里可以集成matplotlib、plotly等

        return {
            "status": "success",
            "chart_type": chart_type,
            "message": "可视化已生成"
        }

    def _export(self, params: dict) -> dict:
        """导出结果"""
        output_path = params.get("output_path")
        output_format = params.get("format", "csv")

        if self.data is None:
            return {
                "status": "error",
                "message": "未加载数据"
            }

        try:
            if output_format == "csv":
                self.data.to_csv(output_path, index=False)
            elif output_format == "excel":
                self.data.to_excel(output_path, index=False)
            elif output_format == "json":
                self.data.to_json(output_path, orient='records')
            else:
                return {
                    "status": "error",
                    "message": f"不支持的输出格式: {output_format}"
                }

            return {
                "status": "success",
                "output_path": output_path
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
```

### 使用自定义Agent

```python
from lingflow import lingflow
from lingflow.coordination import AgentRegistry

# 注册自定义Agent
registry = AgentRegistry()
registry.register("data_analyst", DataAnalysisAgent)

# 使用Agent
lf = lingflow()

# 加载数据
result = lf.run_skill("load_data", {
    "file_path": "data/sales.csv",
    "type": "csv"
})

# 生成摘要
result = lf.run_skill("summary", {})

# 执行分析
result = lf.run_skill("analyze", {
    "type": "correlation"
})

# 导出结果
result = lf.run_skill("export", {
    "output_path": "output/analysis.csv",
    "format": "csv"
})
```

## 最佳实践

1. **单一职责** - 每个Agent专注于特定领域
2. **错误处理** - 妥善处理异常情况
3. **日志记录** - 记录关键操作和决策
4. **参数验证** - 验证输入参数
5. **状态管理** - 合理使用状态
6. **性能优化** - 使用缓存和批处理

## 相关文档

- [基础用法示例](basic_usage.md)
- [工作流定义示例](workflow_definition.md)
- [Agent协调指南](../guides/agent_coordination.md)
