#!/bin/bash
# 快速验证集成测试框架

echo "=== Phase 4-5 集成测试框架验证 ==="
echo ""

# 验证目录结构
echo "1. 检查测试目录结构..."
test -d tests/integration && echo "✓ tests/integration 存在" || echo "✗ 缺少 tests/integration"
test -f tests/integration/conftest.py && echo "✓ conftest.py 存在" || echo "✗ 缺少 conftest.py"
test -f tests/integration/fixtures/__init__.py && echo "✓ fixtures 存在" || echo "✗ 缺少 fixtures"
test -f tests/integration/test_phase4_e2e.py && echo "✓ Phase 4 测试存在" || echo "✗ 缺少 Phase 4 测试"
test -f tests/integration/test_phase5_e2e.py && echo "✓ Phase 5 测试存在" || echo "✗ 缺少 Phase 5 测试"
test -f tests/integration/test_integration_e2e.py && echo "✓ 集成测试存在" || echo "✗ 缺少集成测试"
test -f tests/integration/test_edge_cases.py && echo "✓ 边界条件测试存在" || echo "✗ 缺少边界条件测试"
test -f tests/integration/run_e2e_tests.sh && echo "✓ 运行脚本存在" || echo "✗ 缺少运行脚本"

echo ""
echo "2. 验证测试导入..."
python -m pytest tests/integration/test_phase4_e2e.py --collect-only -q 2>&1 | head -1
python -m pytest tests/integration/test_phase5_e2e.py --collect-only -q 2>&1 | head -1
python -m pytest tests/integration/test_integration_e2e.py --collect-only -q 2>&1 | head -1
python -m pytest tests/integration/test_edge_cases.py --collect-only -q 2>&1 | head -1

echo ""
echo "3. 运行示例测试..."
python -m pytest tests/integration/test_phase4_e2e.py::TestBayesianOptimizer::test_initialization -v 2>&1 | grep -E "PASSED|FAILED|ERROR"

echo ""
echo "4. 统计测试数量..."
echo -n "Phase 4 测试: "
python -m pytest tests/integration/test_phase4_e2e.py --collect-only -q 2>&1 | grep -o "[0-9]* collected" | grep -o "[0-9]*"

echo -n "Phase 5 测试: "
python -m pytest tests/integration/test_phase5_e2e.py --collect-only -q 2>&1 | grep -o "[0-9]* collected" | grep -o "[0-9]*"

echo -n "集成测试: "
python -m pytest tests/integration/test_integration_e2e.py --collect-only -q 2>&1 | grep -o "[0-9]* collected" | grep -o "[0-9]*"

echo -n "边界条件测试: "
python -m pytest tests/integration/test_edge_cases.py --collect-only -q 2>&1 | grep -o "[0-9]* collected" | grep -o "[0-9]*"

echo ""
echo "=== 验证完成 ==="
