"""
代码审查测试共享 fixtures 和配置
"""

import ast
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_code_file():
    """创建示例代码文件"""
    content = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        result = ""
        for item in self.data:
            result += str(item)
        return result
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # 清理
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_code_with_issues():
    """包含各种问题的示例代码"""
    return """
# 安全问题
password = "hardcoded123"
x = eval(user_input)

# 性能问题
result = ""
for i in range(1000):
    result += str(i)

# 嵌套循环
matrix = [[1, 2], [3, 4]]
for row in matrix:
    for item in row:
        for x in range(10):
            for y in range(10):
                pass

# 命名问题
class badClassName:
    def BadMethod(self):
        pass
"""


@pytest.fixture
def sample_ast():
    """示例 AST"""
    code = """
def hello():
    print("Hello, world!")
"""
    return ast.parse(code)


@pytest.fixture
def temp_file_path():
    """临时文件路径"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        temp_path = Path(f.name)

    yield temp_path

    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def clean_code():
    """无问题的代码示例"""
    return """
import os
from typing import List, Optional

class DataProcessor:
    '''数据处理器类'''

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def process_items(self, items: List[str]) -> List[str]:
        '''处理项目列表'''
        return [item.upper() for item in items]

def main():
    processor = DataProcessor()
    items = ['a', 'b', 'c']
    return processor.process_items(items)
"""
