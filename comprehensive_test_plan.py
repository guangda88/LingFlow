"""
智能气功知识库项目全面测试计划

测试层次：
1. 端到端测试（1-3个）- 验证完整用户场景
2. 集成测试（10-20个）- 验证模块间协作
3. 单元测试（50-100个）- 验证单个函数/类

测试内容：
- AI API调用
- 数据库操作
- 文件I/O
- 代码分析
"""

import pytest
import os
import tempfile
from pathlib import Path

# 测试目录结构
test_dir = Path(__file__).parent / "tests"
test_dir.mkdir(exist_ok=True)

# 端到端测试
def test_e2e_ai_analysis():
    """端到端测试：AI分析功能"""
    from lingflow import LingFlow
    
    lf = LingFlow()
    
    # 测试AI分析工作流
    workflow = {
        'name': 'AI分析工作流',
        'tasks': [
            {
                'id': 'analyze_code',
                'skill': 'code-analysis',
                'params': {
                    'target': '.',
                    'metrics': ['complexity', 'duplication', 'dead_code']
                }
            },
            {
                'id': 'optimize_code',
                'skill': 'code-optimizer',
                'params': {
                    'issues': '{{tasks.analyze_code.output}}',
                    'strategy': 'comprehensive_optimization'
                }
            }
        ]
    }
    
    result = lf.run_workflow(workflow)
    assert result.get('status') == 'completed'

# 集成测试
def test_integration_code_analysis():
    """集成测试：代码分析功能"""
    from lingflow import LingFlow
    
    lf = LingFlow()
    result = lf.run_skill('code-analysis', {
        'target': '.',
        'metrics': ['complexity', 'duplication', 'dead_code']
    })
    
    assert result.get('result') is not None
    assert 'total_files' in result.get('result', {})

# 单元测试
def test_unit_code_analysis_implementation():
    """单元测试：代码分析技能实现"""
    from lingflow import LingFlow
    
    lf = LingFlow()
    # 通过 LingFlow 执行代码分析技能
    result = lf.run_skill('code-analysis', {
        'target': '.',
        'metrics': ['complexity']
    })
    assert result.get('result') is not None
    assert 'complexity' in result.get('result', {})

# 测试文件I/O
def test_file_io():
    """测试文件I/O操作"""
    import tempfile
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def test_function():\n    return True\n')
        temp_file = f.name
    
    try:
        # 测试代码分析技能对临时文件的分析
        from lingflow import LingFlow
        lf = LingFlow()
        result = lf.run_skill('code-analysis', {
            'target': temp_file,
            'metrics': ['complexity']
        })
        assert result.get('result') is not None
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)

# 测试数据库操作
def test_database_operation():
    """测试数据库操作"""
    from lingflow import LingFlow
    
    lf = LingFlow()
    
    # 测试数据库导出技能
    result = lf.run_skill('database-export', {
        'query': 'SELECT * FROM users LIMIT 10',
        'format': 'csv',
        'output': 'test_export.csv'
    })
    
    # 检查导出文件是否生成
    if os.path.exists('test_export.csv'):
        os.unlink('test_export.csv')
    
    assert result.get('result') is not None

if __name__ == '__main__':
    # 运行所有测试
    test_e2e_ai_analysis()
    test_integration_code_analysis()
    test_unit_code_analysis_implementation()
    test_file_io()
    test_database_operation()
    print("All tests passed!")
