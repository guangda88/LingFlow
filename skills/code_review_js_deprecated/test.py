#!/usr/bin/env python3
"""
测试 code-review-js 技能
"""

import sys
import json
import os
from pathlib import Path

# 添加 lingflow 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.code_review_js import JavaScriptCodeReviewSkill, review_javascript


def test_basic_review():
    """基本测试"""
    print("=" * 70)
    print("🧪 测试 1: 基本 JavaScript 审查")
    print("=" * 70)
    print()
    
    # 测试目录
    target_dir = "/home/ai"
    
    # 创建审查器
    reviewer = JavaScriptCodeReviewSkill(target_dir, "javascript")
    
    # 执行审查
    report = reviewer.analyze()
    
    # 输出结果
    print(f"📊 审查摘要:")
    print(f"  文件数: {report['stats']['files_count']}")
    print(f"  代码行数: {report['stats']['lines_count']}")
    print(f"  问题数: {report['stats']['issues_count']}")
    print(f"  安全漏洞: {report['stats']['vulnerabilities_count']}")
    print()
    
    print(f"📋 总体评分: {report['overall_score']}")
    print()
    
    # 输出各维度的问题
    for dimension, issues in report['results'].items():
        if issues:
            print(f"🔹 {dimension}: {len(issues)} 个问题")
            for issue in issues[:3]:  # 只显示前3个
                print(f"  - [{issue['severity']}] {issue['message']}")
            if len(issues) > 3:
                print(f"  ... 还有 {len(issues) - 3} 个问题")
            print()
    
    print("=" * 70)
    print("✅ 测试 1 完成")
    print("=" * 70)
    print()
    
    return report


def test_typescript_review():
    """TypeScript 审查测试"""
    print("=" * 70)
    print("🧪 测试 2: TypeScript 审查")
    print("=" * 70)
    print()
    
    # 测试目录
    target_dir = "/home/ai"
    
    # 创建审查器
    reviewer = JavaScriptCodeReviewSkill(target_dir, "typescript")
    
    # 执行审查
    report = reviewer.analyze()
    
    # 输出结果
    print(f"📊 审查摘要:")
    print(f"  语言: {report['language']}")
    print(f"  文件数: {report['stats']['files_count']}")
    print(f"  代码行数: {report['stats']['lines_count']}")
    print(f"  问题数: {report['stats']['issues_count']}")
    print(f"  安全漏洞: {report['stats']['vulnerabilities_count']}")
    print()
    
    print(f"📋 总体评分: {report['overall_score']}")
    print()
    
    print("=" * 70)
    print("✅ 测试 2 完成")
    print("=" * 70)
    print()
    
    return report


def test_convenience_function():
    """便捷函数测试"""
    print("=" * 70)
    print("🧪 测试 3: 便捷函数")
    print("=" * 70)
    print()
    
    # 测试目录
    target_dir = "/home/ai"
    
    # 使用便捷函数
    report = review_javascript(target_dir, "javascript")
    
    # 输出结果
    print(f"📊 审查结果:")
    print(f"  文件数: {report['stats']['files_count']}")
    print(f"  问题数: {report['stats']['issues_count']}")
    print()
    
    print("=" * 70)
    print("✅ 测试 3 完成")
    print("=" * 70)
    print()
    
    return report


def test_json_output():
    """JSON 输出测试"""
    print("=" * 70)
    print("🧪 测试 4: JSON 输出")
    print("=" * 70)
    print()
    
    # 测试目录
    target_dir = "/home/ai"
    
    # 执行审查
    report = review_javascript(target_dir)
    
    # 输出 JSON
    json_output = json.dumps(report, indent=2)
    
    print("📋 JSON 输出（前500字符）:")
    print(json_output[:500] + "...")
    print()
    
    # 保存到文件
    output_file = "/tmp/code_review_js_test.json"
    with open(output_file, 'w') as f:
        f.write(json_output)
    
    print(f"✅ JSON 输出已保存到: {output_file}")
    print()
    
    print("=" * 70)
    print("✅ 测试 4 完成")
    print("=" * 70)
    print()


def test_specific_project():
    """特定项目测试"""
    print("=" * 70)
    print("🧪 测试 5: 特定项目（zhineng-bridge）")
    print("=" * 70)
    print()
    
    # 检查 zhineng-bridge 是否存在
    target_dir = "/home/ai/zhibridge"
    
    if not os.path.exists(target_dir):
        print(f"❌ 项目不存在: {target_dir}")
        print()
        print("=" * 70)
        print("✅ 测试 5 跳过")
        print("=" * 70)
        print()
        return None
    
    # 检查 package.json
    package_json = os.path.join(target_dir, "package.json")
    
    if not os.path.exists(package_json):
        print(f"❌ package.json 不存在: {package_json}")
        print()
        print("=" * 70)
        print("✅ 测试 5 跳过")
        print("=" * 70)
        print()
        return None
    
    print(f"✅ 项目存在: {target_dir}")
    print(f"✅ package.json 存在: {package_json}")
    print()
    
    # 执行审查
    reviewer = JavaScriptCodeReviewSkill(target_dir, "javascript")
    report = reviewer.analyze()
    
    # 输出结果
    print(f"📊 审查摘要:")
    print(f"  项目: zhineng-bridge")
    print(f"  文件数: {report['stats']['files_count']}")
    print(f"  代码行数: {report['stats']['lines_count']}")
    print(f"  问题数: {report['stats']['issues_count']}")
    print(f"  安全漏洞: {report['stats']['vulnerabilities_count']}")
    print()
    
    print(f"📋 总体评分: {report['overall_score']}")
    print()
    
    # 输出各维度的问题
    print("📋 各维度问题:")
    for dimension, issues in report['results'].items():
        if issues:
            print(f"  {dimension}: {len(issues)} 个问题")
    
    print()
    
    print("=" * 70)
    print("✅ 测试 5 完成")
    print("=" * 70)
    print()
    
    return report


def main():
    """主函数"""
    print()
    print("=" * 70)
    print("🚀 code-review-js 技能测试")
    print("=" * 70)
    print()
    
    # 运行所有测试
    tests = [
        ("基本 JavaScript 审查", test_basic_review),
        ("TypeScript 审查", test_typescript_review),
        ("便捷函数", test_convenience_function),
        ("JSON 输出", test_json_output),
        ("特定项目（zhineng-bridge）", test_specific_project),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append({
                'name': test_name,
                'status': 'pass',
                'result': result
            })
        except Exception as e:
            print(f"❌ 测试失败: {test_name}")
            print(f"错误: {e}")
            print()
            results.append({
                'name': test_name,
                'status': 'fail',
                'error': str(e)
            })
    
    # 输出测试摘要
    print("=" * 70)
    print("📊 测试摘要")
    print("=" * 70)
    print()
    
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    
    print(f"总测试数: {len(results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print()
    
    print("测试结果:")
    for result in results:
        status_icon = "✅" if result['status'] == 'pass' else "❌"
        print(f"  {status_icon} {result['name']}")
    
    print()
    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
    print()
    
    # 返回退出码
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
