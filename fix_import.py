import sys

# 读取文件
file_path = '/home/ai/zhineng-knowledge-system/lingflow/comprehensive_test_runner.py'
with open(file_path, 'r') as f:
    content = f.read()

# 在import语句后添加dataclass导入
import_line = "from typing import Dict, List, Any, Optional\n"
new_import = import_line + "from dataclasses import dataclass\n"

content = content.replace(import_line, new_import)

# 写回文件
with open(file_path, 'w') as f:
    f.write(content)

print("✅ 修复导入问题完成")
