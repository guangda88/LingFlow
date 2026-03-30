# demo-01: 基础智能体示例

> VibeCoding 最佳实践 - LingFlow 核心能力展示

## 项目概述

这是一个展示 LingFlow 核心能力的示例项目，按照 VibeCoding 三轮开发法构建：

- **第一轮**: 静态原型（已完成）
- **第二轮**: 逻辑交互（已完成）
- **第三轮**: 数据持久化（已完成）

## 学习目标

通过这个示例，你将学会：

1. ✅ 如何初始化 AgentCoordinator
2. ✅ 如何创建和执行任务
3. ✅ 如何处理任务结果
4. ✅ 如何使用基础技能链
5. ✅ MVP 思维的实际应用

## 快速开始

### 安装依赖

```bash
cd demo-01-basic-agent
pip install -r requirements.txt
```

### 运行示例

```bash
# 完整示例
python src/main.py

# 分步示例
python src/step1_init.py
python src/step2_create_task.py
python src/step3_execute.py
python src/step4_result.py
```

## 项目结构

```
demo-01-basic-agent/
├── src/
│   ├── main.py              # 完整示例
│   ├── step1_init.py        # 步骤1: 初始化
│   ├── step2_create_task.py # 步骤2: 创建任务
│   ├── step3_execute.py     # 步骤3: 执行任务
│   └── step4_result.py      # 步骤4: 处理结果
├── docs/
│   ├── PRD.md              # 产品需求文档
│   ├── DESIGN.md           # 设计文档
│   └── LESSONS.md          # 学习笔记
├── tests/
│   └── test_example.py     # 测试文件
├── requirements.txt
└── README.md
```

## 核心概念

### 1. AgentCoordinator 初始化

```python
from lingflow import AgentCoordinator

# 创建协调器
coordinator = AgentCoordinator()

# 查看可用 Agent
agents = coordinator.list_agents()
print(f"可用 Agent: {agents}")
```

### 2. 创建任务

```python
from lingflow import Task, TaskPriority

# 创建任务
task = Task(
    task_id="task-001",
    name="代码审查",
    description="审查 src/ 目录下的代码",
    priority=TaskPriority.HIGH,
    agent_type="review"
)
```

### 3. 执行任务

```python
# 同步执行
result = coordinator.execute_task(task, context={})

# 异步执行
async def run_async():
    result = await coordinator.execute_task_async(task, context={})
```

### 4. 处理结果

```python
if result.success:
    print(f"✅ 任务成功: {result.output}")
else:
    print(f"❌ 任务失败: {result.error}")
```

## MVP 三轮开发法实践

### 第一轮: 静态原型

**目标**: 验证核心概念

```python
# demo_v1.py - 最小可用版本
def main():
    coordinator = AgentCoordinator()
    task = Task(task_id="001", name="简单任务")
    result = coordinator.execute_task(task)
    print(result.success)
```

**验收**: ✅ 能跑通基本流程

### 第二轮: 逻辑交互

**目标**: 实现完整功能

```python
# demo_v2.py - 添加错误处理和日志
def main():
    try:
        coordinator = AgentCoordinator()
        task = create_task()
        result = coordinator.execute_task(task)
        handle_result(result)
    except Exception as e:
        logger.error(f"执行失败: {e}")
```

**验收**: ✅ 功能完整，错误处理健壮

### 第三轮: 数据持久化

**目标**: 添加数据存储

```python
# demo_v3.py - 完整版本
def main():
    # 初始化数据库
    db = Database()

    # 创建协调器
    coordinator = AgentCoordinator()

    # 执行任务
    task = create_task()
    result = coordinator.execute_task(task)

    # 保存结果
    db.save_result(result)
```

**验收**: ✅ 数据可持久化，可追溯

## 常见问题

### Q: 如何选择 Agent 类型？

```python
# 查看所有可用 Agent
agents = coordinator.list_agents()

# 根据 Task 选择合适的 Agent
agent_map = {
    "代码实现": "implementation",
    "代码审查": "review",
    "测试": "testing",
    "调试": "debugging"
}
```

### Q: 如何处理任务失败？

```python
result = coordinator.execute_task(task)

if not result.success:
    # 使用 systematic-debugging 技能
    debug_result = coordinator.execute_task(
        Task(
            task_id="debug-001",
            name="调试失败",
            agent_type="debugging",
            context={"error": result.error}
        )
    )
```

### Q: 如何执行多个任务？

```python
# 顺序执行
for task in tasks:
    result = coordinator.execute_task(task)

# 并行执行
results = await coordinator.execute_tasks_parallel(tasks)
```

## 下一步

完成 demo-01 后，继续学习：

- [demo-02: 多智能体协作](../demo-02-multi-agent/)
- [demo-03: 完整工作流](../demo-03-full-workflow/)
- [进阶技能](../../docs/learning_path/LEARNING_PATH.md)

## 贡献

欢迎改进示例代码！

1. Fork 项目
2. 创建特性分支
3. 提交 Pull Request

## 许可证

MIT License
