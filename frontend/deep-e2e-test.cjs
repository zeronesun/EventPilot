const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const OUTPUT_DIR = path.join(__dirname, 'deep-test-output');
const HEADLESS = process.env.HEADLESS !== 'false';
const SLOW_MO = parseInt(process.env.SLOW_MO || '100');

const TEST_USER = {
  username: process.env.TEST_USERNAME || 'admin',
  password: process.env.TEST_PASSWORD || 'admin123'
};

class DeepE2ETester {
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
      buttonTests: [],
      dialogTests: [],
      formTests: []
    };
    this.testStartTime = null;
  }

  async init() {
    console.log('\n');
    console.log('='.repeat(70));
    console.log('🧪 EventPilot 深度用户视角端到端测试');
    console.log('='.repeat(70));
    console.log(`📅 测试时间: ${new Date().toLocaleString('zh-CN')}`);
    console.log(`🌐 前端地址: ${BASE_URL}`);
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
        this.results.consoleErrors.push({ url: this.page.url(), message: text });
      }
    });

    this.page.on('response', async response => {
      const url = response.url();
      const status = response.status();
      if (url.includes('/api/') && status >= 400) {
        this.results.apiErrors.push({ url, status, method: response.request().method() });
      }
    });
  }

  async login() {
    console.log('\n📍 登录系统');
    console.log('-'.repeat(50));

    try {
      await this.page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
      await this.page.waitForSelector('input[placeholder="用户名"]', { timeout: 10000 });
      await this.page.fill('input[placeholder="用户名"]', TEST_USER.username);
      await this.page.fill('input[type="password"]', TEST_USER.password);
      await this.page.click('button[type="button"]');
      await this.page.waitForTimeout(3000);

      const currentUrl = this.page.url();
      if (!currentUrl.includes('/login')) {
        console.log('   ✅ 登录成功');
        this.results.passed.push({ test: '用户登录', message: '成功' });
        return true;
      }
      throw new Error('登录后未跳转');
    } catch (error) {
      console.log(`   ❌ 登录失败: ${error.message}`);
      this.results.failed.push({ test: '用户登录', error: error.message });
      return false;
    }
  }

  async testAllButtonsOnPage(pageName, pagePath) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`📍 深度测试页面: ${pageName}`);
    console.log('='.repeat(70));

    try {
      await this.page.goto(`${BASE_URL}${pagePath}`, { waitUntil: 'networkidle' });
      await this.page.waitForTimeout(2000);
    } catch (error) {
      console.log(`   ❌ 页面加载失败: ${error.message}`);
      return;
    }

    const screenshotPath = path.join(OUTPUT_DIR, `${pageName.replace(/\s+/g, '-')}-main.png`);
    await this.page.screenshot({ path: screenshotPath, fullPage: true });

    await this.testToolbarButtons(pageName);
    await this.testTableRowButtons(pageName);
    await this.testFilterAndSearch(pageName);
    await this.testDialogsAndForms(pageName);
  }

  async testToolbarButtons(pageName) {
    console.log(`\n   📌 测试工具栏按钮`);

    const toolbarSelectors = [
      { selector: 'button:has-text("新建")', name: '新建按钮' },
      { selector: 'button:has-text("添加")', name: '添加按钮' },
      { selector: 'button:has-text("新增")', name: '新增按钮' },
      { selector: 'button:has-text("导出")', name: '导出按钮' },
      { selector: 'button:has-text("导入")', name: '导入按钮' },
      { selector: 'button:has-text("批量")', name: '批量操作按钮' },
      { selector: 'button:has-text("删除")', name: '删除按钮' },
      { selector: 'button:has-text("刷新")', name: '刷新按钮' },
      { selector: 'button .el-icon:has-text("Refresh"), button:has([class*="refresh"])', name: '刷新图标按钮' },
      { selector: 'button:has-text("筛选")', name: '筛选按钮' },
    ];

    for (const btn of toolbarSelectors) {
      try {
        const button = await this.page.$(btn.selector);
        if (button) {
          const isVisible = await button.isVisible();
          const isEnabled = await button.isEnabled();
          
          if (isVisible && isEnabled) {
            console.log(`      ✅ ${btn.name} - 可见且可点击`);
            this.results.buttonTests.push({ page: pageName, button: btn.name, status: 'PASS' });
          } else if (isVisible && !isEnabled) {
            console.log(`      ⚠️  ${btn.name} - 可见但被禁用`);
            this.results.buttonTests.push({ page: pageName, button: btn.name, status: 'DISABLED' });
          }
        }
      } catch (e) {
        // Button not found, skip
      }
    }
  }

  async testTableRowButtons(pageName) {
    console.log(`\n   📌 测试表格行操作按钮`);

    const rows = await this.page.$$('.el-table__row');
    if (rows.length === 0) {
      console.log('      ⚠️  表格无数据行');
      return;
    }

    console.log(`      发现 ${rows.length} 行数据`);

    const firstRow = rows[0];
    if (!firstRow) return;

    const rowButtonSelectors = [
      { selector: 'button:has-text("查看")', name: '查看按钮' },
      { selector: 'button:has-text("详情")', name: '详情按钮' },
      { selector: 'button:has-text("编辑")', name: '编辑按钮' },
      { selector: 'button:has-text("删除")', name: '删除按钮' },
      { selector: 'button:has-text("复制")', name: '复制按钮' },
      { selector: 'button:has-text("导出")', name: '导出按钮' },
      { selector: 'button:has-text("核验")', name: '核验按钮' },
      { selector: 'button:has-text("实例化")', name: '实例化按钮' },
      { selector: 'button:has-text("更多")', name: '更多按钮' },
      { selector: 'button .el-icon:has-text("More"), button:has([class*="more"])', name: '更多操作按钮' },
      { selector: '.el-dropdown button', name: '下拉菜单按钮' },
      { selector: 'button.is-circle', name: '圆形操作按钮' },
      { selector: 'button.is-link', name: '链接样式按钮' },
    ];

    for (const btn of rowButtonSelectors) {
      try {
        const button = await firstRow.$(btn.selector);
        if (button) {
          const isVisible = await button.isVisible();
          const isEnabled = await button.isEnabled();
          
          if (isVisible && isEnabled) {
            console.log(`      ✅ ${btn.name} - 存在且可点击`);
            this.results.buttonTests.push({ page: pageName, button: `行内${btn.name}`, status: 'PASS' });
          } else if (isVisible) {
            console.log(`      ⚠️  ${btn.name} - 存在但被禁用`);
            this.results.buttonTests.push({ page: pageName, button: `行内${btn.name}`, status: 'DISABLED' });
          }
        }
      } catch (e) {
        // Skip
      }
    }

    await this.testRowClickAndDetailDialog(firstRow, pageName);
  }

  async testRowClickAndDetailDialog(row, pageName) {
    console.log(`\n   📌 测试行点击和详情弹窗`);

    try {
      await row.click();
      await this.page.waitForTimeout(1500);

      const dialog = await this.page.$('.el-dialog, .el-drawer, [role="dialog"]');
      if (dialog) {
        const isVisible = await dialog.isVisible();
        if (isVisible) {
          console.log('      ✅ 点击行打开详情弹窗/抽屉');
          this.results.dialogTests.push({ page: pageName, dialog: '详情弹窗', status: 'OPENED' });

          await this.testDialogContent(dialog, pageName);

          const closeBtn = await this.page.$('.el-dialog__close, .el-drawer__close-btn, button:has-text("关闭"), button:has-text("取消")');
          if (closeBtn) {
            await closeBtn.click();
            await this.page.waitForTimeout(500);
            console.log('      ✅ 关闭弹窗');
          }
        }
      } else {
        const currentUrl = this.page.url();
        if (currentUrl.includes('/events/') || currentUrl.includes('/tasks/')) {
          console.log('      ✅ 点击行跳转到详情页');
          await this.page.goBack();
          await this.page.waitForTimeout(1000);
        }
      }
    } catch (e) {
      console.log(`      ⚠️  行点击测试: ${e.message}`);
    }
  }

  async testDialogContent(dialog, pageName) {
    console.log(`      📌 测试弹窗内容`);

    const formItems = await dialog.$$('.el-form-item');
    if (formItems.length > 0) {
      console.log(`         发现 ${formItems.length} 个表单项`);
    }

    const inputs = await dialog.$$('input:not([type="hidden"]):not([type="file"])');
    const selects = await dialog.$$('.el-select');
    const textareas = await dialog.$$('textarea');
    
    console.log(`         输入框: ${inputs.length} 个`);
    console.log(`         下拉选择: ${selects.length} 个`);
    console.log(`         文本域: ${textareas.length} 个`);

    const dialogButtons = await dialog.$$('button');
    console.log(`         按钮: ${dialogButtons.length} 个`);

    for (const btn of dialogButtons) {
      try {
        const text = await btn.textContent();
        const isEnabled = await btn.isEnabled();
        if (text && text.trim()) {
          console.log(`            - "${text.trim()}" ${isEnabled ? '可点击' : '禁用'}`);
          this.results.buttonTests.push({ 
            page: pageName, 
            button: `弹窗按钮: ${text.trim()}`, 
            status: isEnabled ? 'PASS' : 'DISABLED' 
          });
        }
      } catch (e) {}
    }
  }

  async testFilterAndSearch(pageName) {
    console.log(`\n   📌 测试筛选和搜索功能`);

    const searchInput = await this.page.$('input[placeholder*="搜索"], input[placeholder*="查询"], input.search');
    if (searchInput) {
      const isVisible = await searchInput.isVisible();
      if (isVisible) {
        console.log('      ✅ 搜索框存在');
        
        await searchInput.fill('测试搜索关键词');
        await this.page.waitForTimeout(500);
        
        const value = await searchInput.inputValue();
        if (value === '测试搜索关键词') {
          console.log('      ✅ 搜索框输入正常');
          this.results.formTests.push({ page: pageName, field: '搜索框', status: 'PASS' });
        }
        
        await searchInput.fill('');
      }
    }

    const selects = await this.page.$$('.filter-card .el-select, .search-card .el-select');
    for (let i = 0; i < selects.length; i++) {
      try {
        const select = selects[i];
        await select.click();
        await this.page.waitForTimeout(500);

        const options = await this.page.$$('.el-select-dropdown__item');
        if (options.length > 0) {
          console.log(`      ✅ 筛选下拉框 ${i + 1} 有 ${options.length} 个选项`);
          this.results.formTests.push({ page: pageName, field: `筛选下拉框${i + 1}`, status: 'PASS', options: options.length });
        }

        await this.page.keyboard.press('Escape');
        await this.page.waitForTimeout(200);
      } catch (e) {}
    }

    const datePickers = await this.page.$$('.el-date-editor, [class*="date-picker"]');
    if (datePickers.length > 0) {
      console.log(`      ✅ 发现 ${datePickers.length} 个日期选择器`);
    }
  }

  async testDialogsAndForms(pageName) {
    console.log(`\n   📌 测试新建/编辑弹窗`);

    const newButtons = [
      'button:has-text("新建")',
      'button:has-text("新增")',
      'button:has-text("添加")',
      'button:has-text("创建")',
    ];

    for (const selector of newButtons) {
      try {
        const btn = await this.page.$(selector);
        if (btn) {
          const isVisible = await btn.isVisible();
          const isEnabled = await btn.isEnabled();
          
          if (isVisible && isEnabled) {
            console.log(`      📝 点击新建按钮打开表单`);
            await btn.click();
            await this.page.waitForTimeout(1500);

            const dialog = await this.page.$('.el-dialog, [role="dialog"]');
            if (dialog) {
              const isDialogVisible = await dialog.isVisible();
              if (isDialogVisible) {
                console.log('      ✅ 新建弹窗已打开');
                
                const dialogTitle = await dialog.$('.el-dialog__title');
                if (dialogTitle) {
                  const title = await dialogTitle.textContent();
                  console.log(`         弹窗标题: ${title}`);
                }

                await this.testFormFields(dialog, pageName);

                await this.testFormValidation(dialog, pageName);

                const cancelBtn = await dialog.$('button:has-text("取消"), button:has-text("关闭"), button:has-text("取 消")');
                if (cancelBtn) {
                  try {
                    await cancelBtn.click({ timeout: 3000 });
                    await this.page.waitForTimeout(500);
                    console.log('      ✅ 关闭弹窗');
                  } catch (e) {
                    await this.page.keyboard.press('Escape');
                    await this.page.waitForTimeout(500);
                    console.log('      ✅ 通过ESC关闭弹窗');
                  }
                } else {
                  await this.page.keyboard.press('Escape');
                  await this.page.waitForTimeout(500);
                }
              }
            }
            break;
          }
        }
      } catch (e) {
        console.log(`      ⚠️  弹窗测试异常: ${e.message}`);
        try {
          await this.page.keyboard.press('Escape');
          await this.page.waitForTimeout(500);
        } catch (err) {}
      }
    }
  }

  async testFormFields(dialog, pageName) {
    console.log(`      📌 测试表单字段`);

    const textInputs = await dialog.$$('input[type="text"], input:not([type])');
    for (let i = 0; i < textInputs.length; i++) {
      try {
        const input = textInputs[i];
        const placeholder = await input.getAttribute('placeholder');
        const isVisible = await input.isVisible();
        
        if (isVisible && placeholder) {
          console.log(`         输入框: ${placeholder}`);
          
          await input.fill('测试输入内容');
          await this.page.waitForTimeout(200);
          
          const value = await input.inputValue();
          if (value === '测试输入内容') {
            this.results.formTests.push({ page: pageName, field: placeholder, status: 'PASS' });
          }
        }
      } catch (e) {}
    }

    const selects = await dialog.$$('.el-select');
    for (let i = 0; i < selects.length; i++) {
      try {
        const select = selects[i];
        await select.click();
        await this.page.waitForTimeout(500);

        const options = await this.page.$$('.el-select-dropdown__item');
        if (options.length > 0) {
          console.log(`         下拉选择框: ${options.length} 个选项`);
          this.results.formTests.push({ page: pageName, field: `下拉框${i + 1}`, status: 'PASS', options: options.length });
        }

        await this.page.keyboard.press('Escape');
        await this.page.waitForTimeout(200);
      } catch (e) {}
    }

    const textareas = await dialog.$$('textarea');
    for (let i = 0; i < textareas.length; i++) {
      try {
        const textarea = textareas[i];
        const placeholder = await textarea.getAttribute('placeholder');
        const isVisible = await textarea.isVisible();
        
        if (isVisible && placeholder) {
          console.log(`         文本域: ${placeholder}`);
          await textarea.fill('测试文本内容');
          this.results.formTests.push({ page: pageName, field: placeholder, status: 'PASS' });
        }
      } catch (e) {}
    }

    const checkboxes = await dialog.$$('.el-checkbox');
    if (checkboxes.length > 0) {
      console.log(`         复选框: ${checkboxes.length} 个`);
    }

    const radioGroups = await dialog.$$('.el-radio-group');
    if (radioGroups.length > 0) {
      console.log(`         单选组: ${radioGroups.length} 个`);
    }

    const datePickers = await dialog.$$('.el-date-editor');
    if (datePickers.length > 0) {
      console.log(`         日期选择器: ${datePickers.length} 个`);
    }

    const uploadAreas = await dialog.$$('.el-upload, [class*="upload"]');
    if (uploadAreas.length > 0) {
      console.log(`         上传区域: ${uploadAreas.length} 个`);
    }
  }

  async testFormValidation(dialog, pageName) {
    console.log(`      📌 测试表单验证`);

    const submitBtn = await dialog.$('button:has-text("确定"), button:has-text("保存"), button:has-text("提交"), button[type="submit"]');
    if (submitBtn) {
      const text = await submitBtn.textContent();
      console.log(`         提交按钮: "${text.trim()}"`);
      
      await submitBtn.click();
      await this.page.waitForTimeout(1000);

      const errorMessages = await dialog.$$('.el-form-item__error, .el-message--error');
      if (errorMessages.length > 0) {
        console.log(`         ✅ 表单验证生效，显示 ${errorMessages.length} 个错误提示`);
        this.results.formTests.push({ page: pageName, field: '表单验证', status: 'PASS' });
        
        for (const error of errorMessages) {
          const text = await error.textContent();
          if (text) {
            console.log(`            - ${text.trim()}`);
          }
        }
      } else {
        console.log(`         ⚠️  未检测到表单验证错误提示`);
      }
    }
  }

  async testDropdownMenus(pageName) {
    console.log(`\n   📌 测试下拉菜单`);

    const dropdownButtons = await this.page.$$('.el-dropdown button, .el-dropdown-link');
    
    for (let i = 0; i < dropdownButtons.length; i++) {
      try {
        const btn = dropdownButtons[i];
        await btn.click();
        await this.page.waitForTimeout(500);

        const dropdownItems = await this.page.$$('.el-dropdown-menu__item');
        if (dropdownItems.length > 0) {
          console.log(`      ✅ 下拉菜单 ${i + 1} 有 ${dropdownItems.length} 个选项`);
          
          for (const item of dropdownItems) {
            const text = await item.textContent();
            if (text) {
              console.log(`         - ${text.trim()}`);
              this.results.buttonTests.push({ page: pageName, button: `下拉选项: ${text.trim()}`, status: 'PASS' });
            }
          }
        }

        await this.page.keyboard.press('Escape');
        await this.page.waitForTimeout(200);
      } catch (e) {}
    }
  }

  async testPagination(pageName) {
    console.log(`\n   📌 测试分页功能`);

    const pagination = await this.page.$('.el-pagination');
    if (pagination) {
      console.log('      ✅ 分页组件存在');

      const total = await this.page.$('.el-pagination__total');
      if (total) {
        const text = await total.textContent();
        console.log(`         ${text}`);
      }

      const nextBtn = await this.page.$('.el-pagination .btn-next');
      if (nextBtn) {
        const isEnabled = await nextBtn.isEnabled();
        if (isEnabled) {
          console.log('         下一页按钮可用');
        }
      }

      const prevBtn = await this.page.$('.el-pagination .btn-prev');
      if (prevBtn) {
        const isEnabled = await prevBtn.isEnabled();
        console.log(`         上一页按钮 ${isEnabled ? '可用' : '禁用'}`);
      }

      const sizeSelect = await this.page.$('.el-pagination .el-select');
      if (sizeSelect) {
        console.log('         每页条数选择器存在');
      }
    }
  }

  async testTabs(pageName) {
    console.log(`\n   📌 测试标签页`);

    const tabs = await this.page.$$('.el-tabs__item');
    if (tabs.length > 0) {
      console.log(`      ✅ 发现 ${tabs.length} 个标签页`);

      for (let i = 0; i < tabs.length; i++) {
        const tab = tabs[i];
        const text = await tab.textContent();
        const isActive = await tab.evaluate(el => el.classList.contains('is-active'));
        
        console.log(`         ${i + 1}. ${text?.trim()} ${isActive ? '(当前)' : ''}`);
        
        if (!isActive) {
          await tab.click();
          await this.page.waitForTimeout(500);
          console.log(`            ✅ 切换成功`);
        }
      }
    }
  }

  async testKanbanView(pageName) {
    console.log(`\n   📌 测试看板视图`);

    const columns = await this.page.$$('.kanban-column');
    if (columns.length > 0) {
      console.log(`      ✅ 看板有 ${columns.length} 列`);

      for (let i = 0; i < columns.length; i++) {
        const column = columns[i];
        const header = await column.$('.column-header, .kanban-column-header');
        if (header) {
          const text = await header.textContent();
          console.log(`         列 ${i + 1}: ${text?.trim()}`);
        }

        const cards = await column.$$('.task-card, .kanban-card');
        console.log(`            ${cards.length} 个卡片`);
      }

      const cards = await this.page.$$('.task-card, .kanban-card');
      if (cards.length > 0) {
        console.log('      📝 测试卡片点击');
        await cards[0].click();
        await this.page.waitForTimeout(1000);

        const dialog = await this.page.$('.el-dialog, [role="dialog"]');
        if (dialog) {
          console.log('         ✅ 点击卡片打开详情弹窗');
          
          const closeBtn = await this.page.$('.el-dialog__close, button:has-text("取消")');
          if (closeBtn) await closeBtn.click();
          await this.page.waitForTimeout(500);
        }
      }
    }
  }

  generateReport() {
    const duration = ((Date.now() - this.testStartTime) / 1000).toFixed(2);

    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('📊 深度测试结果汇总');
    console.log('='.repeat(70));

    console.log(`\n⏱️  测试耗时: ${duration} 秒`);
    console.log(`📸 截图数量: ${this.results.screenshots.length}`);
    console.log(`✅ 通过测试: ${this.results.passed.length}`);
    console.log(`❌ 失败测试: ${this.results.failed.length}`);
    console.log(`⚠️  警告数量: ${this.results.warnings.length}`);
    console.log(`🔴 Console错误: ${this.results.consoleErrors.length}`);
    console.log(`🌐 API错误: ${this.results.apiErrors.length}`);

    console.log(`\n🔘 按钮测试: ${this.results.buttonTests.length} 个`);
    const passedButtons = this.results.buttonTests.filter(b => b.status === 'PASS').length;
    console.log(`   ✅ 可用: ${passedButtons}`);
    const disabledButtons = this.results.buttonTests.filter(b => b.status === 'DISABLED').length;
    console.log(`   ⚠️  禁用: ${disabledButtons}`);

    console.log(`\n📝 表单测试: ${this.results.formTests.length} 个`);
    const passedForms = this.results.formTests.filter(f => f.status === 'PASS').length;
    console.log(`   ✅ 通过: ${passedForms}`);

    console.log(`\n💬 弹窗测试: ${this.results.dialogTests.length} 个`);

    const report = {
      timestamp: new Date().toISOString(),
      duration: `${duration}s`,
      summary: {
        passed: this.results.passed.length,
        failed: this.results.failed.length,
        warnings: this.results.warnings.length,
        consoleErrors: this.results.consoleErrors.length,
        apiErrors: this.results.apiErrors.length,
        buttonTests: this.results.buttonTests.length,
        formTests: this.results.formTests.length,
        dialogTests: this.results.dialogTests.length
      },
      details: {
        passed: this.results.passed,
        failed: this.results.failed,
        warnings: this.results.warnings,
        buttonTests: this.results.buttonTests,
        formTests: this.results.formTests,
        dialogTests: this.results.dialogTests,
        consoleErrors: this.results.consoleErrors.slice(0, 20),
        apiErrors: this.results.apiErrors.slice(0, 20)
      }
    };

    const reportPath = path.join(OUTPUT_DIR, 'deep-e2e-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');

    const mdReportPath = path.join(OUTPUT_DIR, 'deep-e2e-report.md');
    fs.writeFileSync(mdReportPath, this.generateMarkdownReport(report), 'utf-8');

    console.log(`\n📄 JSON报告: ${reportPath}`);
    console.log(`📄 Markdown报告: ${mdReportPath}`);

    return report;
  }

  generateMarkdownReport(report) {
    return `# EventPilot 深度用户视角端到端测试报告

**测试时间**: ${report.timestamp}
**测试耗时**: ${report.duration}

## 测试概要

| 指标 | 数量 |
|------|------|
| ✅ 通过测试 | ${report.summary.passed} |
| ❌ 失败测试 | ${report.summary.failed} |
| ⚠️ 警告 | ${report.summary.warnings} |
| 🔘 按钮测试 | ${report.summary.buttonTests} |
| 📝 表单测试 | ${report.summary.formTests} |
| 💬 弹窗测试 | ${report.summary.dialogTests} |
| 🔴 Console错误 | ${report.summary.consoleErrors} |
| 🌐 API错误 | ${report.summary.apiErrors} |

## 按钮测试详情

| 页面 | 按钮 | 状态 |
|------|------|------|
${report.details.buttonTests.map(b => `| ${b.page} | ${b.button} | ${b.status === 'PASS' ? '✅ 可用' : '⚠️ 禁用'} |`).join('\n')}

## 表单测试详情

| 页面 | 字段 | 状态 |
|------|------|------|
${report.details.formTests.map(f => `| ${f.page} | ${f.field} | ${f.status === 'PASS' ? '✅ 通过' : '❌ 失败'} |`).join('\n')}

## 弹窗测试详情

| 页面 | 弹窗 | 状态 |
|------|------|------|
${report.details.dialogTests.map(d => `| ${d.page} | ${d.dialog} | ${d.status} |`).join('\n')}

## 通过的测试

${report.details.passed.map(item => `- ✅ ${item.test}: ${item.message}`).join('\n') || '无'}

## 失败的测试

${report.details.failed.map(item => `- ❌ ${item.test}: ${item.error}`).join('\n') || '无'}

---
*报告由 EventPilot 深度E2E测试框架自动生成*
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
  const tester = new DeepE2ETester();

  try {
    await tester.init();

    const loginSuccess = await tester.login();
    if (!loginSuccess) {
      console.log('\n❌ 登录失败，无法继续测试');
      tester.generateReport();
      await tester.cleanup();
      process.exit(1);
    }

    await tester.testAllButtonsOnPage('活动管理', '/events');
    await tester.testAllButtonsOnPage('任务管理', '/tasks');
    await tester.testAllButtonsOnPage('用户管理', '/users');
    await tester.testAllButtonsOnPage('清单管理', '/checklists');
    await tester.testAllButtonsOnPage('文件管理', '/files');
    await tester.testAllButtonsOnPage('关联方档案', '/profiles');
    await tester.testAllButtonsOnPage('知识库', '/knowledge');
    await tester.testAllButtonsOnPage('活动复盘', '/reviews');
    await tester.testAllButtonsOnPage('数据分析', '/analytics');
    await tester.testAllButtonsOnPage('预算管理', '/budget');

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
