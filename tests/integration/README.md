# Phase 4-5 集成测试

Phase 4（参数优化）和Phase 5（AI工具学习）的端到端集成测试套件。

## 目录结构

```
tests/integration/
├── fixtures/                    # 测试数据和工具
│   └── __init__.py             # 共享fixtures
├── conftest.py                  # pytest配置
├── test_phase4_e2e.py          # Phase 4端到端测试
├── test_phase5_e2e.py          # Phase 5端到端测试
├── test_integration_e2e.py     # Phase 4+5集成测试
├── test_edge_cases.py          # 边界条件测试
├── run_e2e_tests.sh            # 测试运行脚本
└── README.md                   # 本文件
```

## 快速开始

### 运行所有测试

```bash
./tests/integration/run_e2e_tests.sh
```

### 运行特定测试

```bash
# 仅Phase 4测试
./tests/integration/run_e2e_tests.sh --phase4

# 仅Phase 5测试
./tests/integration/run_e2e_tests.sh --phase5

# 仅集成测试
./tests/integration/run_e2e_tests.sh --integration

# 边界条件测试
./tests/integration/run_e2e_tests.sh --edge
```

### 使用pytest直接运行

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定文件
pytest tests/integration/test_phase4_e2e.py -v

# 运行特定测试类
pytest tests/integration/test_phase4_e2e.py::TestBayesianOptimizer -v

# 运行特定测试
pytest tests/integration/test_phase4_e2e.py::TestBayesianOptimizer::test_initialization -v

# 带覆盖率报告
pytest tests/integration/ --cov=lingflow.self_optimizer --cov-report=html

# 详细输出
pytest tests/integration/ -v -s
```

## 测试覆盖

### Phase 4 测试 (test_phase4_e2e.py)

- **BayesianOptimizer**: 贝叶斯优化器测试
  - 初始化
  - 参数建议
  - 结果观察
  - 优化收敛
  - 停止条件

- **GridSearchOptimizer**: 网格搜索测试
  - 降级方案
  - 参数生成

- **ParameterStorage**: 参数存储测试
  - 存储和检索
  - 持久化
  - 键管理

- **OptimizationCache**: 缓存测试
  - 缓存命中/未命中
  - 大小限制
  - 统计

- **OptimizationEngine**: 优化引擎测试
  - 单目标优化
  - 多目标优化
  - 敏感性分析
  - 历史管理

### Phase 5 测试 (test_phase5_e2e.py)

- **ToolAdapters**: 工具适配器测试
  - Semgrep适配器
  - Ruff适配器
  - Bandit适配器
  - 结果标准化

- **RuleExtraction**: 规则提取测试
  - 基本提取
  - 安全规则提取
  - 类别过滤
  - 质量评分

- **RuleDeduplication**: 去重测试
  - 基本去重
  - 相似度检测

- **RuleValidation**: 验证测试
  - 有效规则
  - 无效规则
  - 批量验证

- **PatternRecognition**: 模式识别测试
  - 长方法检测
  - 硬编码密钥检测
  - 多模式检测

- **KnowledgeBase**: 知识库测试
  - CRUD操作
  - 搜索
  - 统计

### 集成测试 (test_integration_e2e.py)

- **Phase4Phase5Integration**: Phase 4+5集成
  - 学习到优化流程
  - 反馈驱动优化
  - 持续改进循环
  - 知识库指导优化

- **ToolIntegration**: 工具集成
  - Semgrep集成
  - Ruff集成
  - 多工具协作

- **SystemWorkflows**: 系统工作流
  - 完整分析流程
  - 自适应优化
  - 错误恢复

### 边界条件测试 (test_edge_cases.py)

- **EmptyInputs**: 空输入处理
- **LargeInputs**: 大量输入处理
- **ExtremeParameters**: 极端参数值
- **ConcurrentAccess**: 并发访问
- **ResourceLimits**: 资源限制
- **ErrorRecovery**: 错误恢复
- **BoundaryConditions**: 边界条件

## Fixtures

测试使用以下共享fixtures（定义在 `fixtures/__init__.py` 和 `conftest.py`）：

- `temp_project`: 临时测试项目
- `sample_code`: 示例代码
- `security_issues_code`: 安全问题代码
- `mock_feedback_data`: 模拟反馈数据
- `mock_semgrep`, `mock_ruff`, `mock_bandit`: Mock工具
- `optimization_config`: 优化配置
- `sample_search_space`: 示例搜索空间
- `sample_objective`: 示例目标函数

## 标记

测试使用pytest标记：

- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.phase4`: Phase 4测试
- `@pytest.mark.phase5`: Phase 5测试

运行特定标记的测试：

```bash
pytest tests/integration/ -m phase4
pytest tests/integration/ -m "not slow"
```

## 覆盖率

生成覆盖率报告：

```bash
pytest tests/integration/ --cov=lingflow.self_optimizer --cov-report=html
```

报告将生成在 `htmlcov/index.html`。

## 故障排除

### 测试失败

1. 查看详细输出：
   ```bash
   pytest tests/integration/test_file.py -v -s
   ```

2. 运行特定测试：
   ```bash
   pytest tests/integration/test_file.py::TestClass::test_method -v
   ```

3. 使用pdb调试：
   ```bash
   pytest tests/integration/test_file.py --pdb
   ```

### 依赖问题

确保安装了所有依赖：

```bash
pip install pytest pytest-cov pytest-asyncio
```

### 权限问题

确保测试脚本有执行权限：

```bash
chmod +x tests/integration/run_e2e_tests.sh
```

## 持续集成

测试设计用于在CI环境中运行：

```yaml
# GitHub Actions示例
- name: Run E2E tests
  run: |
    pip install pytest pytest-cov
    pytest tests/integration/ -v --cov
```

## 贡献

添加新测试时：

1. 确定测试场景和位置
2. 使用适当的fixtures
3. 添加必要的标记
4. 更新文档
5. 确保测试独立且可重复

## 相关文档

- [E2E_TEST_DESIGN.md](../../E2E_TEST_DESIGN.md) - 详细测试设计
- [Phase 4文档](../../docs/phase4.md) - Phase 4功能文档
- [Phase 5文档](../../docs/phase5.md) - Phase 5功能文档
