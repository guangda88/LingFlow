#!/usr/bin/env python3
"""API文档生成脚本 - 为MkDocs生成API参考文档"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def generate_module_doc(module_path, module_name):
    """生成模块文档"""
    return f"""# {module_name}

::: {module_path}
    options:
      show_source: true
      show_root_heading: true
      show_root_members_full_path: false
      show_object_full_path: false
      show_category_heading: true
      heading_level: 2
      inherited_members: true
      members_order: source
      separate_signature: true
      show_signature: true
      annotations_path: brief
"""

def main():
    """生成所有API文档"""
    api_dir = Path(__file__).parent.parent / "api"
    api_dir.mkdir(exist_ok=True)

    # 核心模块
    modules = {
        "lingflow.md": "lingflow",
        "coordination.md": "lingflow.coordination",
        "workflow.md": "lingflow.workflow",
        "context.md": "lingflow.context",
        "compression.md": "lingflow.compression",
        "self_optimizer.md": "lingflow.self_optimizer",
        "phase4.md": "lingflow.self_optimizer.phase4",
        "phase5.md": "lingflow.self_optimizer.phase5",
    }

    # 生成文档
    for filename, module_name in modules.items():
        output_path = api_dir / filename
        content = generate_module_doc(module_name, module_name)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Generated {filename}")

    print(f"\n✓ API documentation generated in {api_dir}")

if __name__ == "__main__":
    main()
