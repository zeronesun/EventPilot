const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function systematicUserTest() {
  console.log('\n');
  console.log('========================================');
  console.log('🐕 系统性用户视角功能测试');
  console.log('========================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const results = [];
  const issues = [];
  const consoleErrors = [];

  // 监控console
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      consoleErrors.push(text);
      console.log('🔴 [Console]', text.substring(0, 100));
    }
  });

  // 监控API请求
  const apiRequests = {};
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/')) {
      const status = response.status();
      const shortUrl = url.split('?')[0];
      if (!apiRequests[shortUrl]) {
        apiRequests[shortUrl] = { count: 0, success: 0, fail: 0 };
      }
      apiRequests[shortUrl].count++;
      if (status >= 200 && status < 300) {
        apiRequests[shortUrl].success++;
      } else {
        apiRequests[shortUrl].fail++;
        console.log(`🌐 [API ${status}]`, shortUrl.substring(0, 60));
      }
    }
  });

  // ========== 定义测试矩阵 ==========
  const testMatrix = [
    {
      pageName: '登录',
      path: '/login',
      actions: [
        { type: 'navigate', desc: '打开登录页' },
        { type: 'fill', selector: 'input[placeholder="用户名"]', value: 'admin', desc: '填写用户名' },
        { type: 'fill', selector: 'input[type="password"]', value: 'admin123', desc: '填写密码' },
        { type: 'click', selector: 'button[type="button"]', desc: '点击登录' },
        { type: 'wait', timeout: 3000, desc: '等待登录完成' }
      ]
    },
    {
      pageName: '工作台',
      path: '/',
      actions: [
        { type: 'navigate', desc: '打开工作台' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'workbench', desc: '截图' }
      ]
    },
    {
      pageName: '活动管理',
      path: '/events',
      actions: [
        { type: 'navigate', desc: '打开活动管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'events', desc: '截图' },
        { type:'test-button', text: '新建活动', desc: '测试新建活动按钮' }
      ]
    },
    {
      pageName: '任务管理',
      path: '/tasks',
      actions: [
        { type: 'navigate', desc: '打开任务管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'tasks', desc: '截图' }
      ]
    },
    {
      pageName: '用户管理',
      path: '/users',
      actions: [
        { type: 'navigate', desc: '打开用户管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'users', desc: '截图' }
      ]
    },
    {
      pageName: '清单管理',
      path: '/checklists',
      actions: [
        { type: 'navigate', desc: '打开清单管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'checklists', desc: '截图' },
        { type: 'test-button', text: '新建清单实例', desc: '测试新建清单实例' }
      ]
    },
    {
      pageName: '文件管理',
      path: '/files',
      actions: [
        { type: 'navigate', desc: '打开文件管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'files', desc: '截图' },
        { type: 'test-upload', desc: '测试文件上传按钮' }
      ]
    },
    {
      pageName: '个人档案',
      path: '/profiles',
      actions: [
        { type: 'navigate', desc: '打开个人档案' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'profiles', desc: '截图' }
      ]
    },
    {
      pageName: '预算管理',
      path: '/budget',
      actions: [
        { type: 'navigate', desc: '打开预算管理' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'budget', desc: '截图' }
      ]
    },
    {
      pageName: '知识库',
      path: '/knowledge',
      actions: [
        { type: 'navigate', desc: '打开知识库' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'knowledge', desc: '截图' }
      ]
    },
    {
      pageName: '活动复盘',
      path: '/reviews',
      actions: [
        { type: 'navigate', desc: '打开活动复盘' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'reviews', desc: '截图' }
      ]
    },
    {
      pageName: '数据分析',
      path: '/analytics',
      actions: [
        { type: 'navigate', desc: '打开数据分析' },
        { type: 'check-errors', desc: '检查错误提示' },
        { type: 'screenshot', name: 'analytics', desc: '截图' }
      ]
    }
  ];

  // ========== 执行测试 ==========
  const outputDir = '/mnt/d/projects/sourcecode/EventPilot/dogfood-output';
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  for (const test of testMatrix) {
    console.log(`\n📍 测试: ${test.pageName}`);
    console.log('  路径:', test.path);

    const pageResult = {
      page: test.pageName,
      path: test.path,
      status: 'PASS',
      issues: [],
      notes: []
    };

    try {
      for (const action of test.actions) {
        const actionText = `    - ${action.desc}`;

        try {
          switch (action.type) {
            case 'navigate':
              await page.goto(`http://172.28.166.164:5173${test.path}`, {
                waitUntil: 'networkidle',
                timeout: 10000
              });
              await page.waitForTimeout(2000);
              console.log(actionText, '✅');
              break;

            case 'fill':
              await page.waitForSelector(action.selector, { timeout: 5000 });
              await page.fill(action.selector, action.value);
              await page.waitForTimeout(500);
              console.log(actionText, '✅');
              break;

            case 'click':
              await page.click(action.selector);
              await page.waitForTimeout(1000);
              console.log(actionText, '✅');
              break;

            case 'wait':
              await page.waitForTimeout(action.timeout);
              break;

            case 'check-errors':
              const errorTexts = await page.evaluate(() => {
                const texts = [];
                document.querySelectorAll('.el-message--error, .el-message.error, [role="alert"]').forEach(el => {
                  const text = el.textContent?.trim();
                  if (text && text.length > 0 && text.length < 200) {
                    texts.push(text);
                  }
                });
                // 查找包含特定关键词的文本
                const allText = document.body.innerText;
                const keywords = ['加载数据失败', '即将开放', '待完成', '功能',
                                 '上传', '失败', '初始化', 'error', 'Error', '404'];
                keywords.forEach(keyword => {
                  const matches = allText.match(new RegExp(`.{0,100}${keyword}.{0,100}`, 'g'));
                  if (matches) {
                    matches.forEach(m => {
                      if (!texts.includes(m)) texts.push(m);
                    });
                  }
                });
                return [...new Set(texts)];
              });

              if (errorTexts.length > 0) {
                pageResult.status = 'FAIL';
                errorTexts.forEach(text => {
                  pageResult.issues.push(text);
                  console.log(`${actionText} ❌`, `"${text.substring(0, 80)}"`);
                });
              } else {
                console.log(actionText, '✅ (无错误)');
              }
              break;

            case 'screenshot':
              const screenshotPath = path.join(outputDir, `${action.name}.png`);
              await page.screenshot({ path: screenshotPath, fullPage: true });
              pageResult.notes.push(`截图: ${action.name}.png`);
              console.log(actionText, '✅');
              break;

            case 'test-button':
              try {
                await page.waitForSelector(`text=${action.text}`, { timeout: 3000 });
                await page.click(`text=${action.text}`);
                await page.waitForTimeout(2000);

                const dialogText = await page.evaluate(() => {
                  const el = document.querySelector('.el-message--error, .el-message');
                  return el?.textContent?.trim();
                });

                if (dialogText) {
                  pageResult.status = 'FAIL';
                  pageResult.issues.push(dialogText);
                  console.log(`${actionText} ❌`, `"${dialogText.substring(0, 80)}"`);
                } else {
                  pageResult.notes.push('点击按钮无反应或成功');
                  console.log(`${actionText} ✅`);
                }
              } catch (e) {
                pageResult.issues.push('按钮未找到或不可点击');
                console.log(`${actionText} ❌`, '按钮未找到');
              }
              break;

            case 'test-upload':
              try {
                const uploadBtn = await page.$('[class*="upload"] button, [class*="upload"]');
                if (uploadBtn) {
                  await uploadBtn.click();
                  await page.waitForTimeout(2000);

                  const uploadError = await page.evaluate(() => {
                    const el = document.querySelector('.el-message--error, .el-message');
                    return el?.textContent?.trim();
                  });

                  if (uploadError?.includes('初始化')) {
                    pageResult.status = 'FAIL';
                    pageResult.issues.push(uploadError);
                    console.log(`${actionText} ❌`, `"${uploadError.substring(0, 80)}"`);
                  } else {
                    console.log(`${actionText} ✅`);
                  }
                } else {
                  pageResult.issues.push('上传按钮未找到');
                  console.log(`${actionText} ❌`, '按钮未找到');
                }
              } catch (e) {
                pageResult.issues.push('上传测试失败');
                console.log(`${actionText} ❌`, e.message);
              }
              break;
          }
        } catch (error) {
          pageResult.status = 'ERROR';
          pageResult.issues.push(`执行失败: ${error.message}`);
          console.log(`${actionText} ❌`, error.message);
        }
      }
    } catch (error) {
      pageResult.status = 'ERROR';
      pageResult.issues.push(`页面加载失败: ${error.message}`);
      console.log(`  ❌ 页面加载失败:`, error.message);
    }

    results.push(pageResult);
  }

  // ========== 生成报告 ==========
  console.log('\n\n');
  console.log('========================================');
  console.log('📊 测试结果汇总');
  console.log('========================================\n');

  const passCount = results.filter(r => r.status === 'PASS').length;
  const failCount = results.filter(r => r.status === 'FAIL' || r.status === 'ERROR').length;

  console.log(`✅ PASS: ${passCount}/${results.length}`);
  console.log(`❌ FAIL: ${failCount}/${results.length}`);

  console.log(`\n📋 详细结果`);
  console.log('---');
  for (const result of results) {
    const status = result.status === 'PASS' ? '✅' : '❌';
    console.log(`${status} ${result.pageName.padEnd(15)} ${result.status}`);
    for (const issue of result.issues) {
      console.log(`   - ${issue.substring(0, 100)}`);
    }
  }

  console.log(`\n📊 统计`);
  console.log('---');
  console.log(`  Console错误: ${consoleErrors.length}`);
  console.log(`  API 请求:`);
  for (const [url, stats] of Object.entries(apiRequests)) {
    if (stats.fail > 0) {
      console.log(`    ${url.substring(0, 50)}: FAIL ${stats.fail}/${stats.count}`);
    }
  }

  // 保存报告
  const reportPath = path.join(outputDir, 'full-system-report.md');
  const report = `# EventPilot 系统性用户测试报告

生成时间: ${new Date().toLocaleString('zh-CN')}

## 测试统计

- **总测试数**: ${results.length}
- **通过**: ${passCount}
- **失败**: ${failCount}
- **Console错误**: ${consoleErrors.length}

## 按页面详细结果

| 页面 | 状态 | 问题 |
|------|------|------|
${results.map(r => `| ${r.page} | ${r.status} | ${r.issues.length > 0 ? r.issues[0].substring(0, 50) : '-' } |`).join('\n')}

## 发现的问题

${results.filter(r => r.issues.length > 0).map(r => `
### ${r.page}

${r.issues.map((issue, i) => `${i+1}. ${issue}`).join('\n')}
`).join('\n')}

## Console错误

${consoleErrors.map(e => `- ${e}`).join('\n')}
`;

  fs.writeFileSync(reportPath, report, 'utf-8');
  console.log(`\n📄 完整报告已保存: ${reportPath}`);

  await browser.waitForTimeout(3000);
  await browser.close();

  console.log('\n========================================');
  console.log('✅ 测试完成');
  console.log('========================================');
}

systematicUserTest().catch(error => {
  console.error('\n❌ 测试异常:', error);
  process.exit(1);
});
