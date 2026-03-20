#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LingFlow 端到端测试引擎
使用Playwright执行真实的端到端测试
"""

import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    test_type: str
    status: str  # passed, failed, skipped
    duration: float
    error_message: Optional[str] = None
    screenshot: Optional[str] = None


class EndToEndTestEngine:
    """端到端测试引擎"""
    
    def __init__(self, base_url: str = "http://localhost:3000", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.results: List[TestResult] = []
        
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright()
            self.browser = None
            self.page = None
            self.available = True
        except ImportError:
            print("⚠️  Playwright未安装，跳过端到端测试")
            self.available = False
    
    def start_browser(self):
        """启动浏览器"""
        if not self.available:
            return None
        
        try:
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = context.new_page()
            self.page.set_default_timeout(30000)  # 30秒超时
            return True
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            return False
    
    def stop_browser(self):
        """停止浏览器"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.page = None
    
    def navigate_to_home(self) -> TestResult:
        """导航到首页"""
        start_time = time.time()
        test_name = "导航到首页"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 访问首页
            self.page.goto(self.base_url)
            
            # 验证页面标题
            assert "中国传统文化知识库" in self.page.title()
            
            # 验证关键元素
            self.page.wait_for_selector("h1", timeout=5000)
            assert self.page.is_visible("h1")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_user_registration(self) -> TestResult:
        """测试用户注册"""
        start_time = time.time()
        test_name = "用户注册"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 点击注册按钮
            self.page.click("text=注册", timeout=5000)
            
            # 填写注册表单
            self.page.fill("input[name='username']", "test_e2e_user")
            self.page.fill("input[name='email']", f"test_e2e_{int(time.time())}@example.com")
            self.page.fill("input[name='password']", "Test123!")
            
            # 提交表单
            self.page.click("button[type='submit']")
            
            # 验证注册成功
            self.page.wait_for_selector("text=注册成功", timeout=5000)
            assert self.page.is_visible("text=注册成功")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_user_login(self) -> TestResult:
        """测试用户登录"""
        start_time = time.time()
        test_name = "用户登录"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 点击登录按钮
            self.page.click("text=登录", timeout=5000)
            
            # 填写登录表单
            self.page.fill("input[name='username']", "test_e2e_user")
            self.page.fill("input[name='password']", "Test123!")
            
            # 提交表单
            self.page.click("button[type='submit']")
            
            # 验证登录成功
            self.page.wait_for_selector("text=欢迎", timeout=5000)
            assert self.page.is_visible("text=欢迎")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_search_functionality(self) -> TestResult:
        """测试搜索功能"""
        start_time = time.time()
        test_name = "搜索功能"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 导航到搜索页面
            self.page.goto(f"{self.base_url}/search")
            
            # 输入搜索关键词
            self.page.fill("input[placeholder*='搜索']", "中医")
            
            # 点击搜索按钮
            self.page.click("button[type='submit']")
            
            # 验证搜索结果
            self.page.wait_for_selector(".result-item", timeout=5000)
            assert self.page.is_visible(".result-item")
            
            # 验证至少有一个结果
            results = self.page.query_selector_all(".result-item")
            assert len(results) > 0
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_document_browsing(self) -> TestResult:
        """测试文献浏览"""
        start_time = time.time()
        test_name = "文献浏览"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 导航到文献库页面
            self.page.goto(f"{self.base_url}/library")
            
            # 验证文献卡片
            self.page.wait_for_selector(".document-card", timeout=5000)
            assert self.page.is_visible(".document-card")
            
            # 点击第一个文献卡片
            self.page.click(".document-card:first-child")
            
            # 验证文献详情页
            self.page.wait_for_selector(".document-detail", timeout=5000)
            assert self.page.is_visible(".document-detail")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_monitoring_page(self) -> TestResult:
        """测试监控页面"""
        start_time = time.time()
        test_name = "监控页面"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 导航到监控页面
            self.page.goto(f"{self.base_url}/monitoring")
            
            # 验证监控指标
            self.page.wait_for_selector(".monitoring-metric", timeout=5000)
            assert self.page.is_visible(".monitoring-metric")
            
            # 验证图表加载
            self.page.wait_for_selector("canvas", timeout=5000)
            assert self.page.is_visible("canvas")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_theme_switch(self) -> TestResult:
        """测试主题切换"""
        start_time = time.time()
        test_name = "主题切换"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 导航到设置页面
            self.page.goto(f"{self.base_url}/settings")
            
            # 点击主题切换按钮
            self.page.click("button[aria-label*='主题']", timeout=5000)
            
            # 验证主题切换
            self.page.wait_for_selector(".dark-mode", timeout=5000)
            assert self.page.is_visible(".dark-mode")
            
            # 再次点击主题切换按钮
            self.page.click("button[aria-label*='主题']")
            
            # 验证主题切换回
            self.page.wait_for_selector(":not(.dark-mode)", timeout=5000)
            assert not self.page.is_visible(".dark-mode")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def test_responsive_design(self) -> TestResult:
        """测试响应式设计"""
        start_time = time.time()
        test_name = "响应式设计"
        
        if not self.available or not self.page:
            return TestResult(test_name, "E2E", "skipped", 0)
        
        try:
            # 导航到首页
            self.page.goto(self.base_url)
            
            # 测试PC布局
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            self.page.wait_for_selector(".sidebar", timeout=5000)
            assert self.page.is_visible(".sidebar")
            
            # 测试平板布局
            self.page.set_viewport_size({"width": 768, "height": 1024})
            self.page.wait_for_selector(".main-content", timeout=5000)
            assert self.page.is_visible(".main-content")
            
            # 测试移动端布局
            self.page.set_viewport_size({"width": 375, "height": 667})
            self.page.wait_for_selector(".mobile-menu", timeout=5000)
            assert self.page.is_visible(".mobile-menu")
            
            duration = time.time() - start_time
            result = TestResult(test_name, "E2E", "passed", duration)
            self.results.append(result)
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            screenshot = self._take_screenshot(f"{test_name}_failed")
            result = TestResult(test_name, "E2E", "failed", duration, str(e), screenshot)
            self.results.append(result)
            return result
    
    def _take_screenshot(self, name: str) -> str:
        """截图"""
        if not self.page:
            return None
        
        try:
            screenshot_dir = Path("test_results/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = screenshot_dir / f"{name}_{timestamp}.png"
            
            self.page.screenshot(path=str(screenshot_path))
            
            return str(screenshot_path)
        except Exception:
            return None
    
    def run_all_tests(self) -> List[TestResult]:
        """运行所有端到端测试"""
        if not self.available:
            print("⚠️  Playwright未安装，跳过所有端到端测试")
            return []
        
        print("🚀 开始端到端测试")
        print(f"📊 测试地址: {self.base_url}")
        print(f"🔧 无头模式: {self.headless}")
        print()
        
        # 启动浏览器
        if not self.start_browser():
            print("❌ 无法启动浏览器，跳过所有端到端测试")
            return []
        
        try:
            # 运行测试
            self.navigate_to_home()
            self.test_user_registration()
            self.test_user_login()
            self.test_search_functionality()
            self.test_document_browsing()
            self.test_monitoring_page()
            self.test_theme_switch()
            self.test_responsive_design()
            
            # 输出结果
            self.print_results()
            
            return self.results
        
        finally:
            # 停止浏览器
            self.stop_browser()
            if self.playwright:
                self.playwright.stop()
    
    def print_results(self):
        """打印测试结果"""
        print("📊 端到端测试结果:")
        print()
        
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        total = len(self.results)
        
        print(f"  总测试数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  跳过: {skipped}")
        print()
        
        # 打印失败的测试
        if failed > 0:
            print("❌ 失败的测试:")
            for result in self.results:
                if result.status == "failed":
                    print(f"  - {result.test_name}")
                    if result.error_message:
                        print(f"    错误: {result.error_message}")
                    if result.screenshot:
                        print(f"    截图: {result.screenshot}")
            print()
        
        # 打印最快的3个测试
        if self.results:
            fastest = sorted(self.results, key=lambda x: x.duration)[:3]
            print("🏃 最快的3个测试:")
            for result in fastest:
                print(f"  - {result.test_name}: {result.duration*1000:.2f}ms")
            print()
        
        # 打印最慢的3个测试
        if self.results:
            slowest = sorted(self.results, key=lambda x: -x.duration)[:3]
            print("🐢 最慢的3个测试:")
            for result in slowest:
                print(f"  - {result.test_name}: {result.duration*1000:.2f}ms")
            print()
        
        # 打印总耗时
        total_duration = sum(r.duration for r in self.results)
        print(f"⏱️  总耗时: {total_duration:.2f}秒")
    
    def save_results(self, output_dir: Path):
        """保存测试结果"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / f"e2e_test_results_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([{
                "test_name": r.test_name,
                "test_type": r.test_type,
                "status": r.status,
                "duration": r.duration,
                "error_message": r.error_message,
                "screenshot": r.screenshot
            } for r in self.results], f, ensure_ascii=False, indent=2)
        
        print(f"✅ 测试结果已保存到: {json_file}")


# 主函数
def main():
    """主函数"""
    # 创建端到端测试引擎
    engine = EndToEndTestEngine(headless=True)
    
    # 运行所有测试
    results = engine.run_all_tests()
    
    # 保存测试结果
    if results:
        engine.save_results(Path("test_results"))


if __name__ == "__main__":
    main()
