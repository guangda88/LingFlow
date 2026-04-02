#!/usr/bin/env python3
"""
快速运行 code-review-js 技能
"""

import sys
import json
import os
from pathlib import Path

# 添加技能路径
skills_path = Path(__file__).parent / "skills"
sys.path.insert(0, str(skills_path))

# 添加 code-review-js 路径
code_review_js_path = skills_path / "code-review-js"
sys.path.insert(0, str(code_review_js_path))

# 导入技能
import importlib.util
spec = importlib.util.spec_from_file_location("code_review_js", str(code_review_js_path / "implementation.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["code_review_js"] = module
spec.loader.exec_module(module)

JavaScriptCodeReviewSkill = module.JavaScriptCodeReviewSkill
review_javascript = module.review_javascript


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 70)
        print("🚀 LingFlow - code-review-js 技能")
        print("=" * 70)
        print()
        print("使用方法:")
        print("  python run_code_review_js.py <target_dir> [language]")
        print()
        print("参数:")
        print("  <target_dir>  - 项目目录（必需）")
        print("  [language]    - 语言类型（可选：javascript/typescript）")
        print()
        print("示例:")
        print("  python run_code_review_js.py /home/ai/myproject")
        print("  python run_code_review_js.py /home/ai/myproject javascript")
        print("  python run_code_review_js.py /home/ai/myproject typescript")
        print()
        print("=" * 70)
        sys.exit(1)
    
    target_dir = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "javascript"
    
    print("=" * 70)
    print("🚀 LingFlow - code-review-js 技能")
    print("=" * 70)
    print()
    print(f"目标目录: {target_dir}")
    print(f"语言类型: {language}")
    print()
    
    # 检查目标目录
    if not os.path.exists(target_dir):
        print(f"❌ 目标目录不存在: {target_dir}")
        sys.exit(1)
    
    # 检查 package.json
    package_json = os.path.join(target_dir, "package.json")
    if not os.path.exists(package_json):
        print(f"⚠️  package.json 不存在: {package_json}")
        print("⚠️  部分功能可能无法使用")
        print()
    
    # 执行审查
    print("开始代码审查...")
    print()
    
    try:
        report = review_javascript(target_dir, language)
        
        # 输出摘要
        print("=" * 70)
        print("📊 审查摘要")
        print("=" * 70)
        print()
        print(f"文件数: {report['stats']['files_count']}")
        print(f"代码行数: {report['stats']['lines_count']}")
        print(f"问题数: {report['stats']['issues_count']}")
        print(f"安全漏洞: {report['stats']['vulnerabilities_count']}")
        print()
        print(f"总体评分: {report['overall_score']}")
        print()
        
        # 输出各维度的问题
        print("=" * 70)
        print("📋 各维度问题")
        print("=" * 70)
        print()
        
        for dimension, issues in report['results'].items():
            if issues:
                severity_icons = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢',
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌'
                }
                
                print(f"{dimension}: {len(issues)} 个问题")
                
                # 统计各严重程度
                severity_counts = {}
                for issue in issues:
                    severity = issue['severity']
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    icon = severity_icons.get(severity, '•')
                    print(f"  {icon} {severity}: {count}")
                
                print()
        
        # 保存报告
        output_file = "/tmp/code_review_js_report.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("=" * 70)
        print("✅ 审查完成")
        print("=" * 70)
        print()
        print(f"📋 报告已保存到: {output_file}")
        print()
        print("查看报告:")
        print(f"  cat {output_file}")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 审查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
