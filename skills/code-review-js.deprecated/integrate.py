#!/usr/bin/env python3
"""
集成 code-review-js 技能到 LingFlow
"""

import sys
import os
import json
from pathlib import Path

# 添加 LingFlow 路径
lingflow_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(lingflow_path))


def register_skill():
    """注册 code-review-js 技能到 LingFlow"""
    print("=" * 70)
    print("🔧 集成 code-review-js 技能到 LingFlow")
    print("=" * 70)
    print()
    
    # 1. 检查技能目录
    skill_dir = lingflow_path / "skills" / "code-review-js"
    
    if not skill_dir.exists():
        print(f"❌ 技能目录不存在: {skill_dir}")
        return False
    
    print(f"✅ 技能目录存在: {skill_dir}")
    print()
    
    # 2. 检查必要文件
    required_files = [
        "SKILL.md",
        "implementation.py",
        "skill_config.json",
        "__init__.py"
    ]
    
    print("📋 检查必要文件:")
    all_files_exist = True
    
    for file in required_files:
        file_path = skill_dir / file
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  ✅ {file} ({file_size} bytes)")
        else:
            print(f"  ❌ {file}")
            all_files_exist = False
    
    print()
    
    if not all_files_exist:
        print("❌ 缺少必要文件")
        return False
    
    # 3. 读取技能配置
    config_file = skill_dir / "skill_config.json"
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print("📋 技能配置:")
    print(f"  名称: {config['name']}")
    print(f"  版本: {config['version']}")
    print(f"  描述: {config['description']}")
    print(f"  分类: {config['category']}")
    print()
    
    print("📋 支持的语言:")
    for lang in config['languages']:
        print(f"  ✅ {lang}")
    print()
    
    print("📋 工具:")
    for tool_name, tool_config in config['tools'].items():
        required = "必需" if tool_config['required'] else "可选"
        print(f"  {tool_name}: {tool_config['name']} ({required})")
    print()
    
    # 4. 检查技能是否能导入
    print("📋 测试技能导入:")
    try:
        from skills.code_review_js import JavaScriptCodeReviewSkill
        print("  ✅ JavaScriptCodeReviewSkill")
    except Exception as e:
        print(f"  ❌ JavaScriptCodeReviewSkill: {e}")
        return False
    
    try:
        from skills.code_review_js import review_javascript
        print("  ✅ review_javascript")
    except Exception as e:
        print(f"  ❌ review_javascript: {e}")
        return False
    
    try:
        from skills.code_review_js import review_typescript
        print("  ✅ review_typescript")
    except Exception as e:
        print(f"  ❌ review_typescript: {e}")
        return False
    
    print()
    
    # 5. 测试基本功能
    print("📋 测试基本功能:")
    try:
        # 创建测试报告
        test_dir = "/tmp/code_review_js_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # 创建测试文件
        test_file = test_dir / "test.js"
        test_file.write_text("""
const test = 'hello';
console.log(test);
""")
        
        # 运行审查
        reviewer = JavaScriptCodeReviewSkill(str(test_dir), "javascript")
        report = reviewer.analyze()
        
        print(f"  ✅ 基本审查功能")
        print(f"  📊 测试结果: {report['overall_score']}")
        
        # 清理
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        print(f"  ❌ 基本功能测试: {e}")
        return False
    
    print()
    
    # 6. 注册技能
    print("📋 注册技能到 LingFlow:")
    
    # 更新技能列表
    skills_list_file = lingflow_path / "skills" / "SKILLS.md"
    
    if skills_list_file.exists():
        with open(skills_list_file, 'r') as f:
            content = f.read()
        
        # 检查是否已注册
        if "code-review-js" not in content.lower():
            # 添加到技能列表
            new_entry = f"""
## code-review-js

- **名称**: {config['name']}
- **版本**: {config['version']}
- **描述**: {config['description']}
- **支持的语言**: {', '.join(config['languages'])}
- **文件**: skills/code-review-js/
"""
            with open(skills_list_file, 'a') as f:
                f.write(new_entry)
            
            print(f"  ✅ 已添加到 SKILLS.md")
        else:
            print(f"  ℹ️  已存在于 SKILLS.md")
    
    print()
    
    # 7. 创建启动脚本
    print("📋 创建启动脚本:")
    
    launcher_script = lingflow_path / "run_code_review_js.py"
    
    with open(launcher_script, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
快速运行 code-review-js 技能
"""

import sys
from pathlib import Path

# 添加 LingFlow 路径
lingflow_path = Path(__file__).parent
sys.path.insert(0, str(lingflow_path))

from skills.code_review_js import review_javascript


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python run_code_review_js.py <target_dir> [language]")
        print("示例:")
        print("  python run_code_review_js.py /home/ai/myproject javascript")
        print("  python run_code_review_js.py /home/ai/myproject typescript")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "javascript"
    
    print(f"开始 {language} 代码审查...")
    print(f"目标目录: {target_dir}")
    print()
    
    # 执行审查
    report = review_javascript(target_dir, language)
    
    # 输出报告
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
''')
    
    launcher_script.chmod(0o755)
    print(f"  ✅ 启动脚本: {launcher_script}")
    
    print()
    
    # 8. 完成
    print("=" * 70)
    print("✅ code-review-js 技能集成完成")
    print("=" * 70)
    print()
    print("📊 集成摘要:")
    print(f"  技能名称: {config['name']}")
    print(f"  技能版本: {config['version']}")
    print(f"  技能路径: {skill_dir}")
    print(f"  启动脚本: {launcher_script}")
    print()
    print("🚀 使用方法:")
    print(f"  cd {lingflow_path}")
    print(f"  python run_code_review_js.py <target_dir> [language]")
    print()
    print("📋 示例:")
    print(f"  python run_code_review_js.py /home/ai/zhineng-bridge javascript")
    print(f"  python run_code_review_js.py /home/ai/zhineng-bridge typescript")
    print()
    print("=" * 70)
    
    return True


def main():
    """主函数"""
    print()
    success = register_skill()
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
