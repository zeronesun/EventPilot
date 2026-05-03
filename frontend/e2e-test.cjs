const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';
const OUTPUT_DIR = path.join(__dirname, 'e2e-test-output');
const HEADLESS = process.env.HEADLESS !== 'false';
const SLOW_MO = parseInt(process.env.SLOW_MO || '100');

const TEST_USER = {
  username: process.env.TEST_USERNAME || 'admin',
  password: process.env.TEST_PASSWORD || 'admin123'
};

class UserPerspectiveTester {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.results = {
      passed: [],
      failed: [],
      warnings: [],
      screenshots: [],
      consoleErrors: [],
      apiErrors: [],
      networkLogs: []
    };
    this.testStartTime = null;
  }

  async init() {
    console.log('\n');
    console.log('='.repeat(70));
    console.log('🧪 EventPilot 用户视角端到端测试');
    console.log('='.repeat(70));
    console.log(`📅 测试时间: ${new Date().toLocaleString('zh-CN')}`);
    console.log(`🌐 前端地址: ${BASE_URL}`);
    console.log(`🔗 API地址: ${API_URL}`);
    console.log(`👤 测试用户: ${TEST_USER.username}`);
    console.log(`🖥️  无头模式: ${HEADLESS}`);
    console.log('');

    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    this.browser = await chromium.launch({
      headless: HEADLESS,
      slowMo: SLOW_MO,
      args: ['--start-maximized']
    });

    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      locale: 'zh-CN',
      timezoneId: 'Asia/Shanghai'
    });

    this.page = await this.context.newPage();

    this.setupEventListeners();
    this.testStartTime = Date.now();
  }

  setupEventListeners() {
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        this.results.consoleErrors.push({
          url: this.page.url(),
          message: text
        });
        console.log('   🔴 Console Error:', text.substring(0, 100));
      }
    });

    this.page.on('response', async response => {
      const url = response.url();
      const status = response.status();

      if (url.includes('/api/')) {
        if (status >= 400) {
          this.results.apiErrors.push({
            url: url,
            status: status,
            method: response.request().method()
          });
          console.log(`   🌐 API Error [${status}]: ${url.substring(0, 60)}`);
        }
      }
    });

    this.page.on('pageerror', error => {
      this.results.consoleErrors.push({
        url: this.page.url(),
        message: error.message,
        type: 'pageerror'
      });
    });
  }

  async login() {
    console.log('\n📍 测试: 用户登录');
    console.log('-'.repeat(50));

    try {
      await this.page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
      await this.page.waitForSelector('input[placeholder="用户名"]', { timeout: 10000 });

      await this.page.fill('input[placeholder="用户名"]', TEST_USER.username);
      await this.page.waitForTimeout(200);

      await this.page.fill('input[type="password"]', TEST_USER.password);
      await this.page.waitForTimeout(200);

      await this.page.click('button[type="button"]');
      await this.page.waitForTimeout(3000);

      const currentUrl = this.page.url();
      if (currentUrl.includes('/login')) {
        const errorVisible = await this.page.$('.el-message--error, .el-alert--error');
        if (errorVisible) {
          const errorText = await errorVisible.textContent();
          throw new Error(`登录失败: ${errorText}`);
        }
        throw new Error('登录后未跳转，可能认证失败');
      }

      console.log('   ✅ 登录成功');
      this.results.passed.push({ test: '用户登录', message: '成功登录并跳转' });
      return true;
    } catch (error) {
      console.log(`   ❌ 登录失败: ${error.message}`);
      this.results.failed.push({ test: '用户登录', error: error.message });
      return false;
    }
  }

  async testPageLoad(pageName, pagePath) {
    console.log(`\n📍 测试页面: ${pageName}`);
    console.log('-'.repeat(50));

    const testResult = {
      page: pageName,
      path: pagePath,
      status: 'PASS',
      issues: [],
      interactions: []
    };

    try {
      await this.page.goto(`${BASE_URL}${pagePath}`, { waitUntil: 'networkidle', timeout: 15000 });
      await this.page.waitForTimeout(1500);

      const errorMessages = await this.checkForErrors();
      if (errorMessages.length > 0) {
        testResult.status = 'WARNING';
        testResult.issues.push(...errorMessages);
        errorMessages.forEach(msg => console.log(`   ⚠️  ${msg}`));
      }

      const screenshotPath = path.join(OUTPUT_DIR, `${pageName.replace(/\s+/g, '-')}.png`);
      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      this.results.screenshots.push({ page: pageName, path: screenshotPath });

      console.log(`   ✅ 页面加载完成`);
      this.results.passed.push({ test: `页面加载: ${pageName}`, message: '成功加载' });

    } catch (error) {
      testResult.status = 'FAIL';
      testResult.issues.push(error.message);
      console.log(`   ❌ 页面加载失败: ${error.message}`);
      this.results.failed.push({ test: `页面加载: ${pageName}`, error: error.message });
    }

    return testResult;
  }

  async checkForErrors() {
    const errors = [];

    try {
      const errorElements = await this.page.evaluate(() => {
        const results = [];
        const selectors = [
          '.el-message--error',
          '.el-message.error',
          '.el-alert--error',
          '[role="alert"]',
          '.error-message',
          '.error-info'
        ];

        selectors.forEach(selector => {
          document.querySelectorAll(selector).forEach(el => {
            const text = el.textContent?.trim();
            if (text && text.length > 0 && text.length < 500) {
              results.push(text);
            }
          });
        });

        return [...new Set(results)];
      });

      errors.push(...errorElements);
    } catch (e) {
      // Ignore evaluation errors
    }

    return errors;
  }

  async testInputField(selector, value, description) {
    console.log(`   🔤 测试输入框: ${description}`);

    try {
      const input = await this.page.$(selector);
      if (!input) {
        console.log(`      ⚠️  输入框未找到: ${selector}`);
        return { success: false, reason: 'not_found' };
      }

      await input.click();
      await this.page.waitForTimeout(100);
      await input.fill(value);
      await this.page.waitForTimeout(200);

      const actualValue = await input.inputValue();
      if (actualValue === value) {
        console.log(`      ✅ 输入成功`);
        return { success: true };
      } else {
        console.log(`      ⚠️  输入值不匹配`);
        return { success: false, reason: 'value_mismatch' };
      }
    } catch (error) {
      console.log(`      ❌ 输入失败: ${error.message}`);
      return { success: false, reason: error.message };
    }
  }

  async testButton(selector, description, options = {}) {
    console.log(`   🔘 测试按钮: ${description}`);

    try {
      const button = await this.page.$(selector);
      if (!button) {
        console.log(`      ⚠️  按钮未找到: ${selector}`);
        return { success: false, reason: 'not_found' };
      }

      const isVisible = await button.isVisible();
      const isEnabled = await button.isEnabled();

      if (!isVisible) {
        console.log(`      ⚠️  按钮不可见`);
        return { success: false, reason: 'not_visible' };
      }

      if (!isEnabled) {
        console.log(`      ⚠️  按钮被禁用`);
        return { success: false, reason: 'disabled' };
      }

      if (!options.dryRun) {
        await button.click();
        await this.page.waitForTimeout(options.waitAfter || 1000);
      }

      console.log(`      ✅ 按钮可点击`);
      return { success: true };
    } catch (error) {
      console.log(`      ❌ 点击失败: ${error.message}`);
      return { success: false, reason: error.message };
    }
  }

  async testSelect(selector, description) {
    console.log(`   📋 测试下拉选择: ${description}`);

    try {
      const select = await this.page.$(selector);
      if (!select) {
        console.log(`      ⚠️  下拉框未找到: ${selector}`);
        return { success: false, reason: 'not_found' };
      }

      await select.click();
      await this.page.waitForTimeout(500);

      const options = await this.page.$$('.el-select-dropdown__item, .el-select-dropdown li');
      if (options.length > 0) {
        console.log(`      ✅ 下拉框可展开，共 ${options.length} 个选项`);

        await this.page.keyboard.press('Escape');
        await this.page.waitForTimeout(200);
        return { success: true, optionCount: options.length };
      } else {
        console.log(`      ⚠️  下拉框无选项`);
        return { success: false, reason: 'no_options' };
      }
    } catch (error) {
      console.log(`      ❌ 测试失败: ${error.message}`);
      return { success: false, reason: error.message };
    }
  }

  async testTable(description) {
    console.log(`   📊 测试表格: ${description}`);

    try {
      const table = await this.page.$('.el-table');
      if (!table) {
        console.log(`      ⚠️  表格未找到`);
        return { success: false, reason: 'not_found' };
      }

      const rows = await this.page.$$('.el-table__row');
      const headers = await this.page.$$('.el-table__header th');

      console.log(`      ✅ 表格存在，${headers.length} 列，${rows.length} 行数据`);
      return { success: true, rows: rows.length, columns: headers.length };
    } catch (error) {
      console.log(`      ❌ 测试失败: ${error.message}`);
      return { success: false, reason: error.message };
    }
  }

  async testNavigation() {
    console.log('\n📍 测试: 侧边栏导航');
    console.log('-'.repeat(50));

    const menuItems = [
      { selector: '.menu-item:has-text("工作台")', name: '工作台', expectedPath: '/dashboard' },
      { selector: '.menu-item:has-text("活动管理")', name: '活动管理', expectedPath: '/events' },
      { selector: '.menu-item:has-text("任务管理")', name: '任务管理', expectedPath: '/tasks' },
      { selector: '.menu-item:has-text("用户管理")', name: '用户管理', expectedPath: '/users' },
    ];

    for (const item of menuItems) {
      try {
        const menuItem = await this.page.$(item.selector);
        if (menuItem) {
          await menuItem.click();
          await this.page.waitForTimeout(1500);

          const currentPath = new URL(this.page.url()).pathname;
          if (currentPath === item.expectedPath || currentPath.includes(item.expectedPath)) {
            console.log(`   ✅ ${item.name} 导航正确`);
            this.results.passed.push({ test: `导航: ${item.name}`, message: '导航正确' });
          } else {
            console.log(`   ⚠️  ${item.name} 导航路径不匹配: ${currentPath}`);
            this.results.warnings.push({ test: `导航: ${item.name}`, message: `路径不匹配: ${currentPath}` });
          }
        } else {
          console.log(`   ⚠️  ${item.name} 菜单项未找到`);
        }
      } catch (error) {
        console.log(`   ❌ ${item.name} 导航失败: ${error.message}`);
        this.results.failed.push({ test: `导航: ${item.name}`, error: error.message });
      }
    }
  }

  async testEventsPage() {
    console.log('\n📍 深度测试: 活动管理页面');
    console.log('-'.repeat(50));

    await this.page.goto(`${BASE_URL}/events`, { waitUntil: 'networkidle' });
    await this.page.waitForTimeout(1500);

    await this.testInputField('input[placeholder*="搜索"]', '测试活动', '活动搜索框');
    await this.page.keyboard.press('Enter');
    await this.page.waitForTimeout(1000);

    await this.testSelect('.el-select', '活动状态筛选');

    await this.testButton('button:has-text("新建活动")', '新建活动按钮', { dryRun: true });

    await this.testTable('活动列表');
  }

  async testTasksPage() {
    console.log('\n📍 深度测试: 任务管理页面');
    console.log('-'.repeat(50));

    await this.page.goto(`${BASE_URL}/tasks`, { waitUntil: 'networkidle' });
    await this.page.waitForTimeout(1500);

    const kanbanColumns = await this.page.$$('.kanban-column');
    if (kanbanColumns.length > 0) {
      console.log(`   ✅ 看板视图存在，共 ${kanbanColumns.length} 列`);
      this.results.passed.push({ test: '任务看板', message: `看板视图正常，${kanbanColumns.length} 列` });
    }

    await this.testButton('button:has-text("新建任务")', '新建任务按钮', { dryRun: true });
  }

  async testUsersPage() {
    console.log('\n📍 深度测试: 用户管理页面');
    console.log('-'.repeat(50));

    await this.page.goto(`${BASE_URL}/users`, { waitUntil: 'networkidle' });
    await this.page.waitForTimeout(1500);

    await this.testTable('用户列表');

    await this.testInputField('input[placeholder*="搜索"]', 'admin', '用户搜索框');

    await this.testButton('button:has-text("新增用户")', '新增用户按钮', { dryRun: true });
  }

  async testChecklistsPage() {
    console.log('\n📍 深度测试: 清单管理页面');
    console.log('-'.repeat(50));

    await this.page.goto(`${BASE_URL}/checklists`, { waitUntil: 'networkidle' });
    await this.page.waitForTimeout(1500);

    await this.testTable('清单列表');

    await this.testButton('button:has-text("新建")', '新建按钮', { dryRun: true });
  }

  async testFilesPage() {
    console.log('\n📍 深度测试: 文件管理页面');
    console.log('-'.repeat(50));

    await this.page.goto(`${BASE_URL}/files`, { waitUntil: 'networkidle' });
    await this.page.waitForTimeout(1500);

    const uploadArea = await this.page.$('[class*="upload"]');
    if (uploadArea) {
      console.log('   ✅ 上传区域存在');
    }

    await this.testInputField('input[placeholder*="搜索"]', '测试文件', '文件搜索框');
  }

  async testLogout() {
    console.log('\n📍 测试: 用户登出');
    console.log('-'.repeat(50));

    try {
      await this.page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle' });
      await this.page.waitForTimeout(1000);

      const userAvatar = await this.page.$('.user-avatar, .el-avatar');
      if (userAvatar) {
        await userAvatar.click();
        await this.page.waitForTimeout(500);

        const logoutBtn = await this.page.$('text=退出登录, text=登出, text=注销');
        if (logoutBtn) {
          await logoutBtn.click();
          await this.page.waitForTimeout(2000);

          const currentUrl = this.page.url();
          if (currentUrl.includes('/login')) {
            console.log('   ✅ 登出成功，跳转到登录页');
            this.results.passed.push({ test: '用户登出', message: '成功登出' });
            return true;
          }
        }
      }

      console.log('   ⚠️  登出流程不完整');
      this.results.warnings.push({ test: '用户登出', message: '登出流程不完整' });
      return false;
    } catch (error) {
      console.log(`   ❌ 登出失败: ${error.message}`);
      this.results.failed.push({ test: '用户登出', error: error.message });
      return false;
    }
  }

  generateReport() {
    const duration = ((Date.now() - this.testStartTime) / 1000).toFixed(2);

    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('📊 测试结果汇总');
    console.log('='.repeat(70));

    console.log(`\n⏱️  测试耗时: ${duration} 秒`);
    console.log(`📸 截图数量: ${this.results.screenshots.length}`);
    console.log(`✅ 通过测试: ${this.results.passed.length}`);
    console.log(`❌ 失败测试: ${this.results.failed.length}`);
    console.log(`⚠️  警告数量: ${this.results.warnings.length}`);
    console.log(`🔴 Console错误: ${this.results.consoleErrors.length}`);
    console.log(`🌐 API错误: ${this.results.apiErrors.length}`);

    if (this.results.failed.length > 0) {
      console.log('\n❌ 失败的测试:');
      this.results.failed.forEach((item, i) => {
        console.log(`   ${i + 1}. ${item.test}: ${item.error}`);
      });
    }

    if (this.results.warnings.length > 0) {
      console.log('\n⚠️  警告:');
      this.results.warnings.forEach((item, i) => {
        console.log(`   ${i + 1}. ${item.test}: ${item.message}`);
      });
    }

    const report = {
      timestamp: new Date().toISOString(),
      duration: `${duration}s`,
      summary: {
        passed: this.results.passed.length,
        failed: this.results.failed.length,
        warnings: this.results.warnings.length,
        consoleErrors: this.results.consoleErrors.length,
        apiErrors: this.results.apiErrors.length
      },
      details: {
        passed: this.results.passed,
        failed: this.results.failed,
        warnings: this.results.warnings,
        consoleErrors: this.results.consoleErrors,
        apiErrors: this.results.apiErrors
      }
    };

    const reportPath = path.join(OUTPUT_DIR, 'e2e-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');

    const mdReportPath = path.join(OUTPUT_DIR, 'e2e-test-report.md');
    const mdContent = this.generateMarkdownReport(report);
    fs.writeFileSync(mdReportPath, mdContent, 'utf-8');

    console.log(`\n📄 JSON报告: ${reportPath}`);
    console.log(`📄 Markdown报告: ${mdReportPath}`);

    return report;
  }

  generateMarkdownReport(report) {
    return `# EventPilot 用户视角端到端测试报告

**测试时间**: ${report.timestamp}
**测试耗时**: ${report.duration}

## 测试概要

| 指标 | 数量 |
|------|------|
| ✅ 通过 | ${report.summary.passed} |
| ❌ 失败 | ${report.summary.failed} |
| ⚠️ 警告 | ${report.summary.warnings} |
| 🔴 Console错误 | ${report.summary.consoleErrors} |
| 🌐 API错误 | ${report.summary.apiErrors} |

## 通过的测试

${report.details.passed.map(item => `- ✅ ${item.test}: ${item.message}`).join('\n') || '无'}

## 失败的测试

${report.details.failed.map(item => `- ❌ ${item.test}: ${item.error}`).join('\n') || '无'}

## 警告

${report.details.warnings.map(item => `- ⚠️ ${item.test}: ${item.message}`).join('\n') || '无'}

## Console错误

${report.details.consoleErrors.map(item => `- 🔴 [${new URL(item.url).pathname}] ${item.message.substring(0, 200)}`).join('\n') || '无'}

## API错误

${report.details.apiErrors.map(item => `- 🌐 [${item.status}] ${item.method} ${item.url}`).join('\n') || '无'}

---
*报告由 EventPilot E2E 测试框架自动生成*
`;
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
    console.log('\n✅ 测试完成');
    console.log('='.repeat(70));
  }
}

async function main() {
  const tester = new UserPerspectiveTester();

  try {
    await tester.init();

    const loginSuccess = await tester.login();
    if (!loginSuccess) {
      console.log('\n❌ 登录失败，无法继续测试');
      tester.generateReport();
      await tester.cleanup();
      process.exit(1);
    }

    const pages = [
      { name: '工作台', path: '/dashboard' },
      { name: '活动管理', path: '/events' },
      { name: '任务管理', path: '/tasks' },
      { name: '用户管理', path: '/users' },
      { name: '清单管理', path: '/checklists' },
      { name: '文件管理', path: '/files' },
      { name: '预算管理', path: '/budget' },
      { name: '关联方档案', path: '/profiles' },
      { name: '知识库', path: '/knowledge' },
      { name: '活动复盘', path: '/reviews' },
      { name: '数据分析', path: '/analytics' },
    ];

    for (const pageInfo of pages) {
      await tester.testPageLoad(pageInfo.name, pageInfo.path);
    }

    await tester.testNavigation();

    await tester.testEventsPage();
    await tester.testTasksPage();
    await tester.testUsersPage();
    await tester.testChecklistsPage();
    await tester.testFilesPage();

    await tester.testLogout();

    const report = tester.generateReport();

    await tester.cleanup();

    process.exit(report.summary.failed > 0 ? 1 : 0);

  } catch (error) {
    console.error('\n❌ 测试异常:', error);
    await tester.cleanup();
    process.exit(1);
  }
}

main();
