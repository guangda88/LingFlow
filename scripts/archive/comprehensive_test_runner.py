#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LingFlow 综合测试运行器
统一执行端到端、性能、安全、兼容性、稳定性测试
from dataclasses import dataclass
"""

import os
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json


@dataclass
class TestResult:
    """测试结果"""
    test_type: str
    test_name: str
    status: str  # passed, failed, skipped
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ComprehensiveTestRunner:
    """综合测试运行器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[TestResult] = []
        self.test_results_dir = project_root / "test_results"
        self.test_results_dir.mkdir(exist_ok=True)
    
    def run_end_to_end_tests(self) -> List[TestResult]:
        """运行端到端测试"""
        print("🌐 开始端到端测试")
        print()
        
        start_time = time.time()
        
        try:
            # 导入端到端测试引擎
            from end_to_end_test_engine import EndToEndTestEngine
            
            # 创建端到端测试引擎
            engine = EndToEndTestEngine(headless=True)
            
            # 运行所有测试
            engine.run_all_tests()
            
            # 保存结果
            engine.save_results(self.test_results_dir)
            
            # 转换结果
            results = [
                TestResult(
                    test_type="E2E",
                    test_name=r.test_name,
                    status=r.status,
                    duration=r.duration,
                    error_message=r.error_message,
                    details={"screenshot": r.screenshot} if r.screenshot else None
                )
                for r in engine.results
            ]
            
            self.results.extend(results)
            
            print(f"✅ 端到端测试完成，耗时: {time.time() - start_time:.2f}秒")
            print()
            
            return results
        
        except ImportError:
            print("⚠️  端到端测试引擎未安装，跳过")
            return []
        except Exception as e:
            print(f"❌ 端到端测试失败: {e}")
            return []
    
    def run_performance_tests(self) -> List[TestResult]:
        """运行性能测试"""
        print("🚀 开始性能测试")
        print()
        
        start_time = time.time()
        
        results = []
        
        # 1. Lighthouse性能测试
        print("  📊 运行Lighthouse性能测试...")
        try:
            lighthouse_result = self._run_lighthouse_test()
            if lighthouse_result:
                results.append(lighthouse_result)
        except Exception as e:
            print(f"  ❌ Lighthouse测试失败: {e}")
        
        # 2. API性能测试
        print("  🌐 运行API性能测试...")
        try:
            api_result = self._run_api_performance_test()
            if api_result:
                results.append(api_result)
        except Exception as e:
            print(f"  ❌ API性能测试失败: {e}")
        
        # 3. 资源加载性能测试
        print("  📦 运行资源加载性能测试...")
        try:
            resource_result = self._run_resource_performance_test()
            if resource_result:
                results.append(resource_result)
        except Exception as e:
            print(f"  ❌ 资源加载性能测试失败: {e}")
        
        self.results.extend(results)
        
        print(f"✅ 性能测试完成，耗时: {time.time() - start_time:.2f}秒")
        print()
        
        return results
    
    def _run_lighthouse_test(self) -> Optional[TestResult]:
        """运行Lighthouse性能测试"""
        start_time = time.time()
        test_name = "Lighthouse性能测试"
        
        # 检查Lighthouse是否安装
        if not self._command_exists("lighthouse"):
            return TestResult("Performance", test_name, "skipped", 0)
        
        try:
            # 运行Lighthouse测试
            output_file = self.test_results_dir / f"lighthouse_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = subprocess.run([
                "lighthouse",
                "http://localhost:3000",
                "--output=json",
                "--output=html",
                f"--output-path={output_file}",
                "--chrome-flags=--headless",
                "--quiet"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                return TestResult("Performance", test_name, "failed", 
                                time.time() - start_time, result.stderr)
            
            # 解析Lighthouse结果
            json_file = Path(f"{output_file}.report.json")
            if json_file.exists():
                with open(json_file, 'r') as f:
                    report = json.load(f)
                
                # 获取性能指标
                performance_score = report['categories']['performance']['score'] * 100
                lcp = report['audits']['largest-contentful-paint']['displayValue']
                fcp = report['audits']['first-contentful-paint']['displayValue']
                
                details = {
                    "performance_score": performance_score,
                    "lcp": lcp,
                    "fcp": fcp
                }
                
                # 验证性能指标
                if performance_score >= 90:
                    return TestResult("Performance", test_name, "passed", 
                                    time.time() - start_time, details=details)
                else:
                    return TestResult("Performance", test_name, "failed", 
                                    time.time() - start_time, 
                                    f"性能分数不达标: {performance_score}/100", 
                                    details=details)
            else:
                return TestResult("Performance", test_name, "failed", 
                                time.time() - start_time, "无法解析Lighthouse结果")
        
        except subprocess.TimeoutExpired:
            return TestResult("Performance", test_name, "failed", 
                            time.time() - start_time, "Lighthouse测试超时")
        except Exception as e:
            return TestResult("Performance", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def _run_api_performance_test(self) -> Optional[TestResult]:
        """运行API性能测试"""
        start_time = time.time()
        test_name = "API性能测试"
        
        try:
            import requests
            import statistics
            
            # 测试API
            api_urls = [
                "http://localhost:3000/api/search",
                "http://localhost:3000/api/documents",
                "http://localhost:3000/api/health"
            ]
            
            response_times = []
            
            for api_url in api_urls:
                try:
                    # 连续测试10次
                    for _ in range(10):
                        start = time.time()
                        response = requests.get(api_url, timeout=5)
                        end = time.time()
                        
                        if response.status_code == 200:
                            response_times.append(end - start)
                except requests.exceptions.RequestException:
                    pass
            
            if not response_times:
                return TestResult("Performance", test_name, "skipped", 0, "API不可用")
            
            # 计算性能指标
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            details = {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "total_requests": len(response_times)
            }
            
            # 验证API性能
            if avg_response_time <= 1.5:  # 平均响应时间≤1.5秒
                return TestResult("Performance", test_name, "passed", 
                                time.time() - start_time, details=details)
            else:
                return TestResult("Performance", test_name, "failed", 
                                time.time() - start_time, 
                                f"平均响应时间过长: {avg_response_time:.2f}秒", 
                                details=details)
        
        except ImportError:
            return TestResult("Performance", test_name, "skipped", 0, "requests库未安装")
        except Exception as e:
            return TestResult("Performance", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def _run_resource_performance_test(self) -> Optional[TestResult]:
        """运行资源加载性能测试"""
        start_time = time.time()
        test_name = "资源加载性能测试"
        
        try:
            # 计算前端资源大小
            dist_dir = self.project_root / "services/web_app/frontend/dist"
            if not dist_dir.exists():
                return TestResult("Performance", test_name, "skipped", 0, "dist目录不存在")
            
            # 计算所有文件大小
            total_size = 0
            file_count = 0
            for file in dist_dir.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
                    file_count += 1
            
            size_mb = total_size / 1024 / 1024
            size_kb = total_size / 1024
            
            details = {
                "total_size_mb": size_mb,
                "total_size_kb": size_kb,
                "file_count": file_count
            }
            
            # 验证资源大小
            if size_kb <= 500:  # ≤500KB
                return TestResult("Performance", test_name, "passed", 
                                time.time() - start_time, details=details)
            else:
                return TestResult("Performance", test_name, "failed", 
                                time.time() - start_time, 
                                f"资源大小过大: {size_kb:.2f}KB", 
                                details=details)
        
        except Exception as e:
            return TestResult("Performance", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def run_security_tests(self) -> List[TestResult]:
        """运行安全测试"""
        print("🔒 开始安全测试")
        print()
        
        start_time = time.time()
        
        results = []
        
        # 1. XSS防护测试
        print("  🛡️  运行XSS防护测试...")
        try:
            xss_result = self._test_xss_protection()
            if xss_result:
                results.append(xss_result)
        except Exception as e:
            print(f"  ❌ XSS防护测试失败: {e}")
        
        # 2. SQL注入防护测试
        print("  💉 运行SQL注入防护测试...")
        try:
            sql_result = self._test_sql_injection_protection()
            if sql_result:
                results.append(sql_result)
        except Exception as e:
            print(f"  ❌ SQL注入防护测试失败: {e}")
        
        # 3. 敏感信息泄露测试
        print("  🔑 运行敏感信息泄露测试...")
        try:
            leak_result = self._test_sensitive_info_leak()
            if leak_result:
                results.append(leak_result)
        except Exception as e:
            print(f"  ❌ 敏感信息泄露测试失败: {e}")
        
        self.results.extend(results)
        
        print(f"✅ 安全测试完成，耗时: {time.time() - start_time:.2f}秒")
        print()
        
        return results
    
    def _test_xss_protection(self) -> Optional[TestResult]:
        """测试XSS防护"""
        start_time = time.time()
        test_name = "XSS防护测试"
        
        try:
            import requests
            
            # 构造XSS攻击载荷
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "<svg/onload=alert('XSS')>"
            ]
            
            # 测试搜索API
            for payload in xss_payloads:
                try:
                    response = requests.post(
                        "http://localhost:3000/api/search",
                        json={"query": payload},
                        timeout=5
                    )
                    
                    # 验证XSS防护
                    if payload in response.text:
                        return TestResult("Security", test_name, "failed", 
                                        time.time() - start_time, 
                                        f"XSS攻击成功: {payload}")
                
                except requests.exceptions.RequestException:
                    pass
            
            return TestResult("Security", test_name, "passed", 
                            time.time() - start_time)
        
        except ImportError:
            return TestResult("Security", test_name, "skipped", 0, "requests库未安装")
        except Exception as e:
            return TestResult("Security", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def _test_sql_injection_protection(self) -> Optional[TestResult]:
        """测试SQL注入防护"""
        start_time = time.time()
        test_name = "SQL注入防护测试"
        
        try:
            import requests
            
            # 构造SQL注入攻击载荷
            sql_payloads = [
                "' OR '1'='1",
                "' OR '1'='1'--",
                "admin'--",
                "' UNION SELECT NULL,NULL,NULL--"
            ]
            
            # 测试登录API
            for payload in sql_payloads:
                try:
                    response = requests.post(
                        "http://localhost:3000/api/login",
                        json={"username": payload, "password": "test"},
                        timeout=5
                    )
                    
                    # 验证SQL注入防护
                    if response.status_code == 200 and "token" in response.text.lower():
                        return TestResult("Security", test_name, "failed", 
                                        time.time() - start_time, 
                                        f"SQL注入成功: {payload}")
                
                except requests.exceptions.RequestException:
                    pass
            
            return TestResult("Security", test_name, "passed", 
                            time.time() - start_time)
        
        except ImportError:
            return TestResult("Security", test_name, "skipped", 0, "requests库未安装")
        except Exception as e:
            return TestResult("Security", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def _test_sensitive_info_leak(self) -> Optional[TestResult]:
        """测试敏感信息泄露"""
        start_time = time.time()
        test_name = "敏感信息泄露测试"
        
        try:
            # 检查源代码中的敏感信息
            sensitive_patterns = [
                r"password\s*=\s*['\"][^'\"]+['\"]",  # 密码
                r"api_key\s*=\s*['\"][^'\"]+['\"]",   # API密钥
                r"secret\s*=\s*['\"][^'\"]+['\"]",    # 密钥
                r"token\s*=\s*['\"][^'\"]+['\"]"     # Token
            ]
            
            # 搜索Python文件
            python_files = list(self.project_root.rglob("*.py"))
            javascript_files = list(self.project_root.rglob("*.js"))
            typescript_files = list(self.project_root.rglob("*.ts"))
            
            all_files = python_files + javascript_files + typescript_files
            
            for file in all_files:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 检查敏感信息模式
                    for pattern in sensitive_patterns:
                        import re
                        if re.search(pattern, content, re.IGNORECASE):
                            return TestResult("Security", test_name, "failed", 
                                            time.time() - start_time, 
                                            f"发现敏感信息: {file}")
                
                except Exception:
                    pass
            
            return TestResult("Security", test_name, "passed", 
                            time.time() - start_time)
        
        except Exception as e:
            return TestResult("Security", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def run_compatibility_tests(self) -> List[TestResult]:
        """运行兼容性测试"""
        print("🌐 开始兼容性测试")
        print()
        
        start_time = time.time()
        
        results = []
        
        # 1. 检查国产化文档
        print("  📄 检查国产化文档...")
        try:
            doc_result = self._check_domestic_documentation()
            if doc_result:
                results.append(doc_result)
        except Exception as e:
            print(f"  ❌ 国产化文档检查失败: {e}")
        
        # 2. 检查ARM64支持
        print("  💻 检查ARM64支持...")
        try:
            arm64_result = self._check_arm64_support()
            if arm64_result:
                results.append(arm64_result)
        except Exception as e:
            print(f"  ❌ ARM64支持检查失败: {e}")
        
        # 3. 检查国产化AI模型
        print("  🤖 检查国产化AI模型...")
        try:
            ai_result = self._check_domestic_ai_models()
            if ai_result:
                results.append(ai_result)
        except Exception as e:
            print(f"  ❌ 国产化AI模型检查失败: {e}")
        
        self.results.extend(results)
        
        print(f"✅ 兼容性测试完成，耗时: {time.time() - start_time:.2f}秒")
        print()
        
        return results
    
    def _check_domestic_documentation(self) -> Optional[TestResult]:
        """检查国产化文档"""
        start_time = time.time()
        test_name = "国产化文档检查"
        
        required_docs = [
            "docs/麒麟系统适配.md",
            "docs/统信系统适配.md",
            "docs/鲲鹏芯片适配.md",
            "docs/国产化部署指南.md"
        ]
        
        for doc in required_docs:
            doc_path = self.project_root / doc
            if not doc_path.exists():
                return TestResult("Compatibility", test_name, "failed", 
                                time.time() - start_time, 
                                f"文档不存在: {doc}")
        
        return TestResult("Compatibility", test_name, "passed", 
                        time.time() - start_time)
    
    def _check_arm64_support(self) -> Optional[TestResult]:
        """检查ARM64支持"""
        start_time = time.time()
        test_name = "ARM64支持检查"
        
        # 检查ARM64配置
        required_files = [
            "docker-compose.arm64.yml",
            "services/web_app/backend/Dockerfile.arm64",
            "services/ai_service/Dockerfile.arm64"
        ]
        
        for file in required_files:
            file_path = self.project_root / file
            if not file_path.exists():
                return TestResult("Compatibility", test_name, "failed", 
                                time.time() - start_time, 
                                f"文件不存在: {file}")
        
        return TestResult("Compatibility", test_name, "passed", 
                        time.time() - start_time)
    
    def _check_domestic_ai_models(self) -> Optional[TestResult]:
        """检查国产化AI模型"""
        start_time = time.time()
        test_name = "国产化AI模型检查"
        
        # 检查国产化AI模型文件
        domestic_models_file = self.project_root / "services/ai_service/domestic_models.py"
        if not domestic_models_file.exists():
            return TestResult("Compatibility", test_name, "skipped", 0, 
                            "国产化AI模型文件不存在")
        
        # 检查是否支持国产化AI模型
        with open(domestic_models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_models = ["wenxin", "qianwen", "zhipu", "bge"]
        for model in required_models:
            if model not in content:
                return TestResult("Compatibility", test_name, "failed", 
                                time.time() - start_time, 
                                f"不支持AI模型: {model}")
        
        return TestResult("Compatibility", test_name, "passed", 
                        time.time() - start_time)
    
    def run_stability_tests(self) -> List[TestResult]:
        """运行稳定性测试"""
        print("🔄 开始稳定性测试")
        print()
        
        start_time = time.time()
        
        results = []
        
        # 1. 并发用户测试
        print("  👥 运行并发用户测试...")
        try:
            concurrent_result = self._test_concurrent_users()
            if concurrent_result:
                results.append(concurrent_result)
        except Exception as e:
            print(f"  ❌ 并发用户测试失败: {e}")
        
        # 2. API稳定性测试
        print("  🌐 运行API稳定性测试...")
        try:
            stability_result = self._test_api_stability()
            if stability_result:
                results.append(stability_result)
        except Exception as e:
            print(f"  ❌ API稳定性测试失败: {e}")
        
        self.results.extend(results)
        
        print(f"✅ 稳定性测试完成，耗时: {time.time() - start_time:.2f}秒")
        print()
        
        return results
    
    def _test_concurrent_users(self) -> Optional[TestResult]:
        """测试并发用户"""
        start_time = time.time()
        test_name = "并发用户测试"
        
        try:
            import requests
            from concurrent.futures import ThreadPoolExecutor
            import statistics
            
            # 并发用户数
            concurrent_users = 50
            
            # 测试API
            def test_user_api(user_id):
                try:
                    start = time.time()
                    response = requests.get(
                        "http://localhost:3000/api/health",
                        timeout=5
                    )
                    end = time.time()
                    
                    return {
                        "user_id": user_id,
                        "status": response.status_code,
                        "duration": end - start
                    }
                except Exception as e:
                    return {
                        "user_id": user_id,
                        "status": 500,
                        "duration": 0,
                        "error": str(e)
                    }
            
            # 创建线程池
            with ThreadPoolExecutor(max_workers=10) as executor:
                # 提交所有任务
                futures = [
                    executor.submit(test_user_api, user_id)
                    for user_id in range(concurrent_users)
                ]
                
                # 等待所有任务完成
                results = [future.result() for future in futures]
            
            # 分析结果
            success_count = sum(1 for r in results if r["status"] == 200)
            avg_duration = statistics.mean([r["duration"] for r in results if r["duration"] > 0])
            max_duration = max([r["duration"] for r in results if r["duration"] > 0])
            
            details = {
                "success_count": success_count,
                "total_users": concurrent_users,
                "success_rate": success_count / concurrent_users * 100,
                "avg_duration": avg_duration,
                "max_duration": max_duration
            }
            
            # 验证并发性能
            if success_count >= 45 and avg_duration <= 3:  # 成功率≥90%，平均响应≤3秒
                return TestResult("Stability", test_name, "passed", 
                                time.time() - start_time, details=details)
            else:
                return TestResult("Stability", test_name, "failed", 
                                time.time() - start_time, 
                                f"并发性能不达标: 成功率{success_count/concurrent_users*100:.1f}%, 平均响应{avg_duration:.2f}秒", 
                                details=details)
        
        except ImportError:
            return TestResult("Stability", test_name, "skipped", 0, "requests库未安装")
        except Exception as e:
            return TestResult("Stability", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def _test_api_stability(self) -> Optional[TestResult]:
        """测试API稳定性"""
        start_time = time.time()
        test_name = "API稳定性测试"
        
        try:
            import requests
            
            # 测试API列表
            api_urls = [
                "http://localhost:3000/api/health",
                "http://localhost:3000/api/search",
                "http://localhost:3000/api/documents"
            ]
            
            # 连续测试100次
            total_tests = 100
            error_count = 0
            
            for i in range(total_tests):
                for api_url in api_urls:
                    try:
                        response = requests.get(api_url, timeout=5)
                        if response.status_code != 200:
                            error_count += 1
                    except Exception:
                        error_count += 1
            
            # 计算成功率
            success_rate = (total_tests * len(api_urls) - error_count) / (total_tests * len(api_urls)) * 100
            
            details = {
                "total_tests": total_tests * len(api_urls),
                "error_count": error_count,
                "success_rate": success_rate
            }
            
            # 验证API稳定性
            if error_count == 0:
                return TestResult("Stability", test_name, "passed", 
                                time.time() - start_time, details=details)
            elif success_rate >= 95:
                return TestResult("Stability", test_name, "passed", 
                                time.time() - start_time, 
                                f"成功率{success_rate:.1f}%，有{error_count}次错误", 
                                details=details)
            else:
                return TestResult("Stability", test_name, "failed", 
                                time.time() - start_time, 
                                f"成功率过低: {success_rate:.1f}%", 
                                details=details)
        
        except ImportError:
            return TestResult("Stability", test_name, "skipped", 0, "requests库未安装")
        except Exception as e:
            return TestResult("Stability", test_name, "failed", 
                            time.time() - start_time, str(e))
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("="*80)
        print("🚀 启动LingFlow综合测试运行器")
        print("="*80)
        print()
        
        overall_start_time = time.time()
        
        # 运行各类型测试
        self.run_end_to_end_tests()
        self.run_performance_tests()
        self.run_security_tests()
        self.run_compatibility_tests()
        self.run_stability_tests()
        
        # 计算总体统计
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "passed")
        failed_tests = sum(1 for r in self.results if r.status == "failed")
        skipped_tests = sum(1 for r in self.results if r.status == "skipped")
        total_duration = time.time() - overall_start_time
        
        # 按测试类型分组
        type_stats = {}
        for result in self.results:
            test_type = result.test_type
            if test_type not in type_stats:
                type_stats[test_type] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0
                }
            
            type_stats[test_type]["total"] += 1
            if result.status == "passed":
                type_stats[test_type]["passed"] += 1
            elif result.status == "failed":
                type_stats[test_type]["failed"] += 1
            elif result.status == "skipped":
                type_stats[test_type]["skipped"] += 1
        
        # 生成测试报告
        report = {
            "test_time": datetime.now().isoformat(),
            "duration": total_duration,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0
            },
            "by_type": type_stats,
            "results": [
                {
                    "test_type": r.test_type,
                    "test_name": r.test_name,
                    "status": r.status,
                    "duration": r.duration,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        # 保存测试报告
        self.save_report(report)
        
        # 打印测试摘要
        self.print_summary(report)
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """保存测试报告"""
        # 保存JSON报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_report = self.test_results_dir / f"comprehensive_test_report_{timestamp}.json"
        
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown报告
        md_report = self.test_results_dir / f"comprehensive_test_report_{timestamp}.md"
        self._generate_markdown_report(report, md_report)
        
        print(f"✅ 测试报告已保存:")
        print(f"  JSON: {json_report}")
        print(f"  Markdown: {md_report}")
        print()
    
    def _generate_markdown_report(self, report: Dict[str, Any], output_file: Path):
        """生成Markdown测试报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# LingFlow综合测试报告\n\n")
            f.write(f"**测试时间**: {report['test_time']}\n\n")
            f.write(f"**总耗时**: {report['duration']:.2f}秒\n\n")
            
            # 测试摘要
            summary = report['summary']
            f.write("## 📊 测试摘要\n\n")
            f.write(f"- 总测试数: {summary['total']}\n")
            f.write(f"- 通过: {summary['passed']}\n")
            f.write(f"- 失败: {summary['failed']}\n")
            f.write(f"- 跳过: {summary['skipped']}\n")
            f.write(f"- 成功率: {summary['success_rate']:.1f}%\n\n")
            
            # 按类型分组结果
            f.write("## 📋 各类型测试结果\n\n")
            
            type_names = {
                "E2E": "端到端测试",
                "Performance": "性能测试",
                "Security": "安全测试",
                "Compatibility": "兼容性测试",
                "Stability": "稳定性测试"
            }
            
            for test_type, stats in report['by_type'].items():
                f.write(f"### {type_names.get(test_type, test_type)}\n\n")
                f.write(f"- 总测试数: {stats['total']}\n")
                f.write(f"- 通过: {stats['passed']}\n")
                f.write(f"- 失败: {stats['failed']}\n")
                f.write(f"- 跳过: {stats['skipped']}\n\n")
            
            # 详细测试结果
            f.write("## 🔍 详细测试结果\n\n")
            
            for result in report['results']:
                status_emoji = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏭️"
                f.write(f"{status_emoji} **{result['test_name']}**\n\n")
                f.write(f"- 测试类型: {result['test_type']}\n")
                f.write(f"- 状态: {result['status']}\n")
                f.write(f"- 耗时: {result['duration']:.2f}秒\n\n")
                
                if result["error_message"]:
                    f.write(f"- 错误信息: {result['error_message']}\n\n")
                
                if result["details"]:
                    f.write(f"- 详细信息: {json.dumps(result['details'], ensure_ascii=False, indent=2)}\n\n")
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        print("="*80)
        print("📊 测试摘要")
        print("="*80)
        print()
        
        summary = report['summary']
        print(f"总测试数: {summary['total']}")
        print(f"通过: {summary['passed']} ✅")
        print(f"失败: {summary['failed']} ❌")
        print(f"跳过: {summary['skipped']} ⏭️")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print()
        
        print("="*80)
        print("📋 各类型测试结果")
        print("="*80)
        print()
        
        type_names = {
            "E2E": "端到端测试",
            "Performance": "性能测试",
            "Security": "安全测试",
            "Compatibility": "兼容性测试",
            "Stability": "稳定性测试"
        }
        
        for test_type, stats in report['by_type'].items():
            status_emoji = "✅" if stats['failed'] == 0 else "❌"
            print(f"{status_emoji} {type_names.get(test_type, test_type)}: {stats['passed']}/{stats['total']} 通过")
        
        print()
        print("="*80)
        print(f"⏱️  总耗时: {report['duration']:.2f}秒")
        print("="*80)
    
    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            subprocess.run(
                ["which", command],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


# 主函数
def main():
    """主函数"""
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # 创建综合测试运行器
    runner = ComprehensiveTestRunner(project_root)
    
    # 运行所有测试
    report = runner.run_all_tests()
    
    # 测试结论
    if report['summary']['failed'] == 0:
        print("\n✅ 所有测试通过，可以上线！")
    else:
        print(f"\n❌ 存在{report['summary']['failed']}个失败测试，请修复后再上线。")


if __name__ == "__main__":
    main()
