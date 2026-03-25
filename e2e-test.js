#!/usr/bin/env node

/**
 * Chrome DevTools MCP - End-to-End Test Suite
 *
 * Tests:
 * 1. Browser startup
 * 2. Page navigation
 * 3. Screenshot capture
 * 4. Console message capture
 * 5. JavaScript execution
 * 6. Network monitoring
 * 7. Performance metrics
 * 8. Device emulation
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test configuration
const CONFIG = {
  executablePath: process.env.PUPPETEER_EXECUTABLE_PATH ||
    '/home/ai/.cache/puppeteer/chrome/linux-146.0.7680.76/chrome-linux64/chrome',
  headless: true,
  outputDir: '/tmp/chrome-devtools-mcp-test',
  testUrl: 'https://example.com',
  testTimeout: 30000,
  chromeArgs: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu'
  ]
};

// Test results storage
const results = {
  total: 0,
  passed: 0,
  failed: 0,
  tests: []
};

// Color codes for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function printHeader(title) {
  console.log('\n' + '='.repeat(70));
  log(`  ${title}`, 'cyan');
  console.log('='.repeat(70));
}

function printTestResult(testName, passed, message = '') {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  const color = passed ? 'green' : 'red';

  results.total++;
  if (passed) results.passed++;
  else results.failed++;

  results.tests.push({
    name: testName,
    passed,
    message
  });

  log(`  ${status} ${testName}`, color);
  if (message) log(`    ${message}`, 'yellow');
}

function createOutputDir() {
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Test 1: Browser Startup
async function testBrowserStartup() {
  printHeader('Test 1: Browser Startup');

  try {
    log(`Starting browser with executable: ${CONFIG.executablePath}`, 'blue');

    const browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const version = await browser.version();
    log(`Browser version: ${version}`, 'blue');

    const pages = await browser.pages();
    log(`Initial pages: ${pages.length}`, 'blue');

    printTestResult('Browser Launch', true, version);

    await browser.close();
    return true;
  } catch (error) {
    printTestResult('Browser Launch', false, error.message);
    return false;
  }
}

// Test 2: Page Navigation
async function testPageNavigation() {
  printHeader('Test 2: Page Navigation');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();
    log(`Navigating to: ${CONFIG.testUrl}`, 'blue');

    const startTime = Date.now();
    const response = await page.goto(CONFIG.testUrl, {
      waitUntil: 'networkidle2',
      timeout: CONFIG.testTimeout
    });
    const loadTime = Date.now() - startTime;

    const title = await page.title();
    const url = page.url();
    const status = response ? response.status() : 'unknown';

    log(`Page title: ${title}`, 'blue');
    log(`Final URL: ${url}`, 'blue');
    log(`HTTP Status: ${status}`, 'blue');
    log(`Load time: ${loadTime}ms`, 'blue');

    const testsPassed = [
      url === CONFIG.testUrl,
      status === 200 || status === '200',
      loadTime < 10000,
      title.length > 0
    ];

    printTestResult('Navigate to URL', testsPassed[0], `URL: ${url}`);
    printTestResult('HTTP Status OK', testsPassed[1], `Status: ${status}`);
    printTestResult('Load Time', testsPassed[2], `${loadTime}ms`);
    printTestResult('Page Title Loaded', testsPassed[3], `Title: ${title}`);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Page Navigation', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 3: Screenshot Capture
async function testScreenshotCapture() {
  printHeader('Test 3: Screenshot Capture');

  let browser;
  try {
    createOutputDir();

    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();
    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });

    // Capture full page screenshot
    const screenshotPath = path.join(CONFIG.outputDir, 'screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });

    // Verify screenshot was created
    const stats = fs.statSync(screenshotPath);
    const sizeKB = (stats.size / 1024).toFixed(2);

    log(`Screenshot saved: ${screenshotPath}`, 'blue');
    log(`File size: ${sizeKB} KB`, 'blue');

    const testsPassed = [
      fs.existsSync(screenshotPath),
      stats.size > 1000, // At least 1KB
      stats.size < 5000000 // Less than 5MB
    ];

    printTestResult('Screenshot Created', testsPassed[0], screenshotPath);
    printTestResult('Screenshot Size Valid', testsPassed[1], `${sizeKB} KB`);
    printTestResult('Screenshot Not Too Large', testsPassed[2], `${sizeKB} KB`);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Screenshot Capture', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 4: Console Message Capture
async function testConsoleCapture() {
  printHeader('Test 4: Console Message Capture');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();

    // Capture console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text()
      });
    });

    // Navigate to page
    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });

    // Execute JavaScript to generate console output
    await page.evaluate(() => {
      console.log('Test log message');
      console.warn('Test warning message');
      console.error('Test error message');
      console.info('Test info message');
    });

    await sleep(1000);

    log(`Console messages captured: ${consoleMessages.length}`, 'blue');

    // Save console messages to file
    const consoleLogPath = path.join(CONFIG.outputDir, 'console-messages.json');
    fs.writeFileSync(consoleLogPath, JSON.stringify(consoleMessages, null, 2));
    log(`Console log saved: ${consoleLogPath}`, 'blue');

    const testsPassed = [
      consoleMessages.length >= 4,
      consoleMessages.some(m => m.type === 'log'),
      consoleMessages.some(m => m.type === 'warn'),
      consoleMessages.some(m => m.type === 'error')
    ];

    printTestResult('Console Messages Captured', testsPassed[0], `${consoleMessages.length} messages`);
    printTestResult('Log Messages Found', testsPassed[1]);
    printTestResult('Warning Messages Found', testsPassed[2]);
    printTestResult('Error Messages Found', testsPassed[3]);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Console Capture', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 5: JavaScript Execution
async function testJavaScriptExecution() {
  printHeader('Test 5: JavaScript Execution');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();
    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });

    // Test basic evaluation
    const result1 = await page.evaluate(() => {
      return 1 + 1;
    });

    // Test complex evaluation
    const result2 = await page.evaluate(() => {
      const obj = { name: 'test', value: 42 };
      return JSON.stringify(obj);
    });

    // Test DOM manipulation
    const result3 = await page.evaluate(() => {
      document.body.style.backgroundColor = 'lightblue';
      return window.getComputedStyle(document.body).backgroundColor;
    });

    // Test async evaluation
    const result4 = await page.evaluate(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
      return 'async result';
    });

    log(`Basic evaluation: ${result1}`, 'blue');
    log(`Complex evaluation: ${result2}`, 'blue');
    log(`DOM manipulation: ${result3}`, 'blue');
    log(`Async evaluation: ${result4}`, 'blue');

    const testsPassed = [
      result1 === 2,
      result2.includes('test') && result2.includes('42'),
      result3.includes('lightblue'),
      result4 === 'async result'
    ];

    printTestResult('Basic Evaluation', testsPassed[0], `Result: ${result1}`);
    printTestResult('Complex Evaluation', testsPassed[1]);
    printTestResult('DOM Manipulation', testsPassed[2]);
    printTestResult('Async Evaluation', testsPassed[3]);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('JavaScript Execution', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 6: Network Monitoring
async function testNetworkMonitoring() {
  printHeader('Test 6: Network Monitoring');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();

    // Capture network requests
    const requests = [];
    const responses = [];

    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType()
      });
    });

    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        headers: response.headers()
      });
    });

    // Navigate to page
    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });

    log(`Requests captured: ${requests.length}`, 'blue');
    log(`Responses captured: ${responses.length}`, 'blue');

    // Save network data
    const networkLogPath = path.join(CONFIG.outputDir, 'network-log.json');
    fs.writeFileSync(networkLogPath, JSON.stringify({ requests, responses }, null, 2));
    log(`Network log saved: ${networkLogPath}`, 'blue');

    const testsPassed = [
      requests.length > 0,
      responses.length > 0,
      requests.some(r => r.resourceType === 'document'),
      responses.every(r => r.status >= 100 && r.status < 600)
    ];

    printTestResult('Network Requests Captured', testsPassed[0], `${requests.length} requests`);
    printTestResult('Network Responses Captured', testsPassed[1], `${responses.length} responses`);
    printTestResult('Document Request Found', testsPassed[2]);
    printTestResult('Valid HTTP Status Codes', testsPassed[3]);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Network Monitoring', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 7: Performance Metrics
async function testPerformanceMetrics() {
  printHeader('Test 7: Performance Metrics');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();

    const startTime = Date.now();
    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });
    const loadTime = Date.now() - startTime;

    // Get performance metrics
    const metrics = await page.metrics();

    log(`Page load time: ${loadTime}ms`, 'blue');
    log(`Timestamp: ${metrics.Timestamp}`, 'blue');
    log(`Documents: ${metrics.Documents}`, 'blue');
    log(`Frames: ${metrics.Frames}`, 'blue');
    log(`JSEventListeners: ${metrics.JSEventListeners}`, 'blue');

    // Get navigation timing
    const navigationTiming = JSON.parse(
      await page.evaluate(() => JSON.stringify(window.performance.timing))
    );

    const domContentLoaded = navigationTiming.domContentLoadedEventEnd - navigationTiming.navigationStart;
    const pageLoadTime = navigationTiming.loadEventEnd - navigationTiming.navigationStart;

    log(`DOM Content Loaded: ${domContentLoaded}ms`, 'blue');
    log(`Page Load Time: ${pageLoadTime}ms`, 'blue');

    // Save performance data
    const perfLogPath = path.join(CONFIG.outputDir, 'performance-metrics.json');
    fs.writeFileSync(perfLogPath, JSON.stringify({ metrics, navigationTiming }, null, 2));
    log(`Performance log saved: ${perfLogPath}`, 'blue');

    const testsPassed = [
      loadTime < 10000,
      domContentLoaded > 0,
      pageLoadTime > 0,
      metrics.Documents >= 1
    ];

    printTestResult('Load Time', testsPassed[0], `${loadTime}ms`);
    printTestResult('DOM Content Loaded', testsPassed[1], `${domContentLoaded}ms`);
    printTestResult('Page Load Complete', testsPassed[2], `${pageLoadTime}ms`);
    printTestResult('Documents Count', testsPassed[3], `${metrics.Documents} documents`);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Performance Metrics', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Test 8: Device Emulation
async function testDeviceEmulation() {
  printHeader('Test 8: Device Emulation');

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: CONFIG.executablePath,
      headless: CONFIG.headless,
      args: CONFIG.chromeArgs
    });

    const page = await browser.newPage();

    // Emulate iPhone
    await page.emulate(puppeteer.devices['iPhone 12']);

    const viewport = page.viewport();
    log(`Viewport width: ${viewport.width}`, 'blue');
    log(`Viewport height: ${viewport.height}`, 'blue');
    log(`Device scale factor: ${viewport.deviceScaleFactor}`, 'blue');
    log(`Is mobile: ${viewport.isMobile}`, 'blue');

    await page.goto(CONFIG.testUrl, { waitUntil: 'networkidle2' });

    // Capture mobile screenshot
    const mobileScreenshotPath = path.join(CONFIG.outputDir, 'mobile-screenshot.png');
    await page.screenshot({ path: mobileScreenshotPath, fullPage: true });
    log(`Mobile screenshot saved: ${mobileScreenshotPath}`, 'blue');

    const testsPassed = [
      viewport.width === 390,
      viewport.height === 844,
      viewport.deviceScaleFactor === 3,
      viewport.isMobile === true
    ];

    printTestResult('Viewport Width', testsPassed[0], `${viewport.width}px`);
    printTestResult('Viewport Height', testsPassed[1], `${viewport.height}px`);
    printTestResult('Device Scale Factor', testsPassed[2], `${viewport.deviceScaleFactor}x`);
    printTestResult('Mobile Flag', testsPassed[3]);

    await browser.close();
    return testsPassed.every(t => t);
  } catch (error) {
    printTestResult('Device Emulation', false, error.message);
    if (browser) await browser.close();
    return false;
  }
}

// Main test runner
async function runAllTests() {
  printHeader('Chrome DevTools MCP - E2E Test Suite');
  log(`Test URL: ${CONFIG.testUrl}`, 'blue');
  log(`Output Directory: ${CONFIG.outputDir}`, 'blue');
  log(`Browser: ${CONFIG.executablePath}`, 'blue');

  createOutputDir();

  // Run all tests
  await testBrowserStartup();
  await testPageNavigation();
  await testScreenshotCapture();
  await testConsoleCapture();
  await testJavaScriptExecution();
  await testNetworkMonitoring();
  await testPerformanceMetrics();
  await testDeviceEmulation();

  // Print summary
  printHeader('Test Summary');
  log(`Total Tests: ${results.total}`, 'cyan');
  log(`Passed: ${results.passed}`, 'green');
  log(`Failed: ${results.failed}`, results.failed > 0 ? 'red' : 'green');
  log(`Success Rate: ${((results.passed / results.total) * 100).toFixed(1)}%`, 'cyan');

  // Save test results
  const resultsPath = path.join(CONFIG.outputDir, 'test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  log(`\nTest results saved: ${resultsPath}`, 'blue');

  // Exit with appropriate code
  process.exit(results.failed > 0 ? 1 : 0);
}

// Run tests
runAllTests().catch(error => {
  log(`Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
