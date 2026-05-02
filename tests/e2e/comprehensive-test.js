const { chromium } = require('playwright');
const fs = require('fs');

async function comprehensiveUserTest() {
  console.log('\n');
  console.log('========================================');
  console.log('🐕 全面用户视角功能测试');
  console.log('========================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 收集所有问题和错误
  const issues = [];
  const consoleErrors = [];
  let api404Count = 0;
  let apiErrorCount = 0;

  // 监控console错误
  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'error') {
      consoleErrors.push(text);
      console.log('🔴 [Console Error]', text.substring(0, 150));
    }
  });

  // 监控网络请求
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/')) {
      const status = response.status();
      if (status === 404) {
        api404Count++;
        console.log(`🌐 [404]`, url.substring(0, 80));
      } else if (status >= 400) {
        apiErrorCount++;
        console.log(`🌐 [${status}]`, url.substring(0, 80));
      }
    }
  });

  // 监控元素上的错误提示
  page.on('load', async () => {
    await page.waitForTimeout(1000);
    const errorElements = await page.$$('.el-message--error');
    for (let el of errorElements) {
      try {
        const text = await el.textContent();
        if (text && text.trim()) {
          issues.push({
            page: page.url(),
            type: '错误提示',
            message: text.trim()
          });
          console.log('❌ [页面错误]', text.trim().substring(0, 100));
        }
      } catch(e) {}
    }
  });

  // ========== 测试：登录 ==========
  console.log('📍 第一步：登录');
  console.log('-'.repeat(50));
  await page.goto('http://172.28.166.164:5173/login');
  await page.waitForSelector('input[placeholder="用户名"]');
  await page.fill('input[placeholder="用户名"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="button"]');
  await page.waitForTimeout(3000);
  console.log('✅ 登录完成\n');

  // 等待页面完全加载
  await page.waitForTimeout(2000);

  // 找到所有菜单项（按功能分类）
  const menuItems = [
    { name: '工作台', path: '/' },
    { name: '活动管理', path: '/events' },
    { name: '任务管理', path: '/tasks' },
    { name: '用户管理', path: '/users' },
    { name: '清单管理', path: '/checklists' },
    { name: '文件管理', path: '/files' },
    { name: '个人档案', path: '/profiles' },
    { name: '预算管理', path: '/budget' },
    { name: '知识库', path: '/knowledge' },
    { name: '活动复盘', path: '/reviews' },
    { name: '数据分析', path: '/analytics' },
  ];

  const testResults = [];

  // ========== 测试每个页面 ==========
  for (const item of menuItems) {
    console.log(`\n📍 测试页面：${item.name}`);
    console.log('  路径:', item.path);

    try {
      await page.goto(`http://172.28.166.164:5173${item.path}`, { waitUntil: 'networkidle', timeout: 10000 });
      await page.waitForTimeout(2000);

      // 截图
      await page.screenshot({ path: `/mnt/d/projects/sourcecode/EventPilot/dogfood-output/${item.name}.png`, fullPage: true });

      // 查找错误提示（加载数据失败等）
      const errorTexts = await page.evaluate(() => {
        const results = [];
        // 查找各种错误提示方式
        document.querySelectorAll('.el-message--error', '.el-message.error', '[role="alert"]', .error, .error-message, .error-info').forEach(el => {
          const text = el.textContent?.trim();
          if (text && !results.includes(text) && text.length < 200) {
            results.push(text);
          }
        });
        // 查找"即将开放"、"待完成"等提示
        document.querySelectorAll('*').forEach(el => {
          if (el.children.length === 0) {
            const text = el.textContent?.trim();
            if (text && (text.includes('即将开放') || text.includes('待完成') || text.includes('失败'))) {
              if (!results.includes(text) && text.length < 200) {
                results.push(text);
              }
            }
          }
        });
        return results;
      });

      if (errorTexts.length > 0) {
        console.log(`  ⚠️  发现 ${errorTexts.length} 个提示:`);
        errorTexts.forEach(text => {
          console.log(`     - "${text.substring(0, 100)}"`);
          issues.push({
            page: item.name,
            path: item.path,
            type: '页面提示',
            message: text
          });
        });
        testResults.push({ page: item.name, status: '有问题', errors: errorTexts });
      } else {
        console.log('  ✅ 加载正常');
        testResults.push({ page: item.name, status: '正常', errors: [] });
      }

    } catch (error) {
      console.log(`  ❌ 加载失败:`, error.message);
      issues.push({
        page: item.name,
        path: item.path,
        type: '页面加载',
        message: error.message
      });
      testResults.push({ page: item.name, status: '加载失败', errors: [error.message] });
    }
  }

  // ========== 测试：文件上传功能 ==========
  console.log(`\n📍 测试文件上传`);
  console.log('-'.repeat(50));
  try {
    await page.goto('http://172.28.166.164:5173/files');
    await page.waitForSelector('[class*="upload"]', { timeout: 5000 });

    // 尝试触发上传
    const uploadBtn = await page.$('[class*="upload"] button, [class*="upload"]');
    if (uploadBtn) {
      await uploadBtn.click();
      await page.waitForTimeout(3000);

      // 检查错误提示
      const errorText = await page.evaluate(() => {
        const el = document.querySelector('.el-message--error, .el-message.error');
        return el?.textContent?.trim();
      });

      if (errorText) {
        console.log('  ⚠️  上传错误:', errorText.substring(0, 100));
        issues.push({ page: '文件上传', type: '上传功能', message: errorText });
      }
    }
  } catch (e) {
    console.log('  ℹ️  未找到上传按钮');
  }

  // ========== 生成测试报告 ==========
  console.log('\n\n');
  console.log('========================================');
  console.log('📊 测试结果汇总');
  console.log('========================================\n');

  console.log(`📄 页面测试`);
  console.log(`---------`);
  let normalCount = 0;
  let issueCount = 0;
  for (const result of testResults) {
    if (result.status === '正常') {
      normalCount++;
      console.log(`  ✅ ${result.page.padEnd(20)} 正常`);
    } else {
      issueCount++;
      console.log(`  ❌ ${result.page.padEnd(20)} ${result.status}`);
      result.errors.forEach(err => console.log(`      - ${err.substring(0, 80)}`));
    }
  }

  console.log(`\n📊 统计`);
  console.log(`---------`);
  console.log(`  正常页面: ${normalCount}/${menuItems.length}`);
  console.log(`  问题页面: ${issueCount}/${menuItems.length}`);
  console.log(`  API 404错误: ${api404Count}`);
  console.log(`  API 错误: ${apiErrorCount}`);
  console.log(`  Console错误: ${consoleErrors.length}`);

  console.log(`\n📋 详细问题`);
  console.log(`---------`);
  if (issues.length > 0) {
    issues.forEach((issue, i) => {
      console.log(`${i + 1}. [${issue.type}] ${issue.page}: ${issue.message.substring(0, 100)}`);
    });
  }

  // 保存报告到文件
  const reportPath = '/mnt/d/projects/sourcecode/EventPilot/dogfood-output/comprehensive-report.md';
  const reportContent = `# EventPilot 全面用户视角测试报告

## 测试时间
${new Date().toLocaleString('zh-CN')}

## 页面加载测试

| 页面 | 状态 | 问题 |
|------|------|------|
${testResults.map(r => `| ${r.page} | ${r.status} | ${r.errors.length > 0 ? r.errors[0].substring(0, 50) : '-' } |`).join('\n')}

## 发现的问题

### Console错误 (${consoleErrors.length})
${consoleErrors.map(e => `- ${e}`).join('\n')}

### 页面功能问题 (${issues.length})
${issues.map((issue, i) => `${i+1}. **[${issue.type}] ${issue.page}**: ${issue.message}`).join('\n')}

### API错误
- 404错误: ${api404Count}
- 其他错误: ${apiErrorCount}
`;

  fs.writeFileSync(reportPath, reportContent, 'utf-8');
  console.log(`\n📄 报告已保存: ${reportPath}`);

  await browser.waitForTimeout(3000);
  await browser.close();

  console.log('\n========================================');
  console.log('✅ 测试完成');
  console.log('========================================');
}

comprehensiveUserTest().catch(error => {
  console.error('\n❌ 测试异常:', error);
  process.exit(1);
});
