# Phase 4-5 端到端集成测试设计

## 概述

本文档定义了Phase 4（参数优化）和Phase 5（AI工具学习）系统的端到端集成测试方案。

## 测试范围

### Phase 4: 参数优化系统
- 贝叶斯优化器工作流
- 参数存储和检索
- 缓存机制
- 多目标优化
- 敏感性分析

### Phase 5: AI工具学习系统
- AI工具适配器
- 规则提取
- 模式识别
- 知识库

### 集成场景
- Phase 4 + Phase 5 协同工作
- 与现有系统集成（Semgrep, Ruff等）

## 测试架构

```
tests/integration/
├── fixtures/
│   ├── __init__.py           # 共享测试数据和fixtures
│   ├── code_samples.py       # 示例代码
│   ├── feedback_data.py      # 模拟工具反馈数据
│   └── mock_tools.py         # Mock外部工具
├── conftest.py               # 集成测试配置
├── test_phase4_e2e.py        # Phase 4端到端测试
├── test_phase5_e2e.py        # Phase 5端到端测试
├── test_integration_e2e.py   # Phase 4+5集成测试
└── test_edge_cases.py        # 边界条件和错误处理
```

## 测试场景

### 1. 正常工作流

#### Phase 4 正常工作流
```
1. 初始化优化引擎
2. 定义搜索空间
3. 运行贝叶斯优化
4. 验证最佳参数
5. 生成报告
6. 缓存结果
```

#### Phase 5 正常工作流
```
1. 接收工具反馈
2. 提取规则
3. 去重和验证
4. 存储到知识库
5. 应用规则到新代码
```

#### 集成工作流
```
1. Phase 5 学习规则
2. Phase 4 使用规则优化参数
3. 验证改进效果
4. 持续学习循环
```

### 2. 错误处理

- 无效的搜索空间
- 工具执行失败
- 缓存损坏
- 知识库连接失败
- 超时处理

### 3. 边界条件

- 空输入
- 大量输入
- 极端参数值
- 并发访问
- 资源限制

## 测试工具选择

### 核心测试框架
- **pytest**: 主测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 覆盖率报告

### Mock和Fixture
- **unittest.mock**: Mock外部依赖
- **pytest fixtures**: 共享测试数据
- **tmp_path**: 临时文件/目录

### 测试数据
- **fixtures/code_samples**: 示例代码片段
- **fixtures/feedback_data**: 模拟工具反馈
- **fixtures/mock_tools**: Mock工具实现

## 测试模板

### Phase 4 端到端测试模板

```python
class TestPhase4E2E:
    def test_full_optimization_workflow(self):
        """测试完整的优化工作流"""

    def test_bayesian_vs_grid_search(self):
        """对比贝叶斯和网格搜索"""

    def test_caching_mechanism(self):
        """测试缓存机制"""

    def test_multi_objective_optimization(self):
        """测试多目标优化"""

    def test_sensitivity_analysis(self):
        """测试敏感性分析"""
```

### Phase 5 端到端测试模板

```python
class TestPhase5E2E:
    def test_learning_pipeline(self):
        """测试完整学习流水线"""

    def test_tool_integration(self):
        """测试工具集成"""

    def test_knowledge_base_crud(self):
        """测试知识库CRUD操作"""

    def test_pattern_recognition(self):
        """测试模式识别"""

    def test_rule_application(self):
        """测试规则应用"""
```

### 集成测试模板

```python
class TestPhase4Phase5Integration:
    def test_learning_to_optimization(self):
        """测试从学习到优化的流程"""

    def test_feedback_loop(self):
        """测试反馈循环"""

    def test_continuous_improvement(self):
        """测试持续改进"""
```

## 运行测试

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/integration/test_phase4_e2e.py -v

# 运行特定测试类
pytest tests/integration/test_phase4_e2e.py::TestPhase4E2E -v

# 运行特定测试
pytest tests/integration/test_phase4_e2e.py::TestPhase4E2E::test_full_optimization_workflow -v

# 生成覆盖率报告
pytest tests/integration/ --cov=lingflow.self_optimizer --cov-report=html

# 运行并生成详细报告
pytest tests/integration/ -v --tb=short --html=report.html
```

## 测试数据管理

### 示例代码
位于 `fixtures/code_samples/`:
- `simple_function.py`: 简单函数
- `complex_class.py`: 复杂类
- `security_issues.py`: 安全问题示例
- `performance_issues.py`: 性能问题示例

### 反馈数据
位于 `fixtures/feedback_data.py`:
- `SEMGREP_FEEDBACK`: Semgrep反馈样本
- `RUFF_FEEDBACK`: Ruff反馈样本
- `BANDIT_FEEDBACK`: Bandit反馈样本
- `MIXED_FEEDBACK`: 混合反馈样本

### Mock工具
位于 `fixtures/mock_tools.py`:
- `MockSemgrep`: Mock Semgrep工具
- `MockRuff`: Mock Ruff工具
- `MockBandit`: Mock Bandit工具

## 持续集成

### CI配置
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run E2E tests
        run: pytest tests/integration/ -v --cov
```

## 预期结果

### 成功标准
1. 所有测试通过
2. 代码覆盖率 > 80%
3. 测试执行时间 < 5分钟
4. 无内存泄漏
5. 无资源泄漏

### 质量指标
- 测试可维护性
- 测试可读性
- 测试隔离性
- 测试可重复性

## 维护指南

### 添加新测试
1. 确定测试场景
2. 选择合适的测试文件
3. 实现测试函数
4. 添加测试数据
5. 更新文档

### 调试测试
1. 使用 `-v` 标志获取详细输出
2. 使用 `-s` 标志显示print输出
3. 使用 `--pdb` 进入调试模式
4. 查看日志文件

### 更新测试
1. 审查失败的测试
2. 确定失败原因
3. 更新测试或实现
4. 验证修复
