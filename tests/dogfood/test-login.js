const { chromium } = require('playwright');
const fs = require('fs');

async function runUserTest() {
  console.log('🐕 Starting User Perspective Testing');
  console.log('=====================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log('[Console ' + msg.type() + '] ' + msg.text()));
  page.on('pageerror', error => console.log('[Page Error] ' + error.message));

  try {
    console.log('Phase 1: 打开登录页面');
    console.log('------------------------');
    await page.goto('http://172.28.166.164:5173');
    await page.screenshot({ path: 'dogfood-output/screenshots/01-login-page.png' });
    console.log('i1 page loaded\n');

    await page.waitForTimeout(2000);

    console.log('Phase 2: 检查登录表单');
    console.log('------------------------');

    const usernameSelectors = [
      'input[placeholder="用户名"]',
      'input[placeholder*="user"]',
      '#username',
      '.el-input__inner'
    ];

    let usernameInput = null;
    for (const selector of usernameSelectors) {
      try {
        await page.waitForSelector(selector, { timeout: 2000 });
        usernameInput = selector;
        console.log('i1 username input found: ' + selector);
        break;
      } catch (e) {
      }
    }

    if (!usernameInput) {
      console.log('i1 username input not found!');
      console.log('Page content:');
      console.log(await page.content());
      throw new Error('Login form not found');
    }

    await page.screenshot({ path: 'dogfood-output/screenshots/02-focus-username.png' });
    console.log('');

    console.log('Phase 3: 填写登录信息');
    console.log('-------------------');

    await page.fill(usernameInput, 'admin');
    console.log('i1 entered username: admin');

    await page.press(usernameInput, 'Tab');
    await page.keyboard.type('admin123');
    console.log('i1 entered password: ******');

    await page.screenshot({ path: 'dogfood-output/screenshots/03-form-filled.png' });
    console.log('');

    console.log('Phase 4: 点击登录按钮');
    console.log('-------------------');

    const loginButtonSelectors = [
      'button[type="submit"]',
      'button:has-text("登录")',
      'button:has-text("Login")',
      'button.el-button--primary'
    ];

    let loginButton = null;
    for (const selector of loginButtonSelectors) {
      try {
        await page.click(selector, { timeout: 2000 });
        console.log('i1 clicked login button');
        loginButton = selector;
        break;
      } catch (e) {
      }
    }

    if (!loginButton) {
      console.log('i1 login button not found!');
      throw new Error('Login button not found');
    }

    await page.waitForTimeout(3000);

    await page.screenshot({ path: 'dogfood-output/screenshots/04-after-login.png' });
    console.log('');

    console.log('Phase 5: 验证登录结果');
    console.log('-------------------');

    const currentUrl = page.url();
    console.log('Current URL: ' + currentUrl);

    const successIndicators = [
      'EventPilot',
      'Dashboard',
      '仪表板',
      '任务',
      'Tasks'
    ];

    let loginSuccessful = false;
    for (const text of successIndicators) {
      if (await page.getByText(text).count() > 0) {
        console.log('i1 found success indicator: ' + text);
        loginSuccessful = true;
        break;
      }
    }

    if (!loginSuccessful && currentUrl.includes('login')) {
      console.log('i1 still on login page, login may have failed');
      console.log('Checking for error messages...');

      const errorSelectors = [
        '.el-alert',
        '.error-message',
        '[class*="error"]'
      ];

      for (const selector of errorSelectors) {
        const errorElement = await page.$(selector);
        if (errorElement) {
          const errorText = await errorElement.textContent();
          console.log('i1 error: ' + errorText);
        }
      }
    }

    await page.screenshot({ path: 'dogfood-output/screenshots/05-final-state.png' });

    if (loginSuccessful) {
      console.log('');
      console.log('Phase 6: 测试基本交互');
      console.log('-------------------');

      const actionableElements = await page.$$('a, button, [role="button"]');
      console.log('i1 found ' + actionableElements.length + ' interactive elements');

      try {
        const tasksLink = await page.$('a[href*="tasks"]') || await page.$('text=任务') || await page.$('text=Tasks');
        if (tasksLink) {
          await tasksLink.click();
          await page.waitForTimeout(2000);
          await page.screenshot({ path: 'dogfood-output/screenshots/06-tasks-page.png' });
          console.log('i1 navigated to tasks page');
        }
      } catch (e) {
        console.log('i1 did not navigate to tasks page');
      }
    }

    console.log('');
    console.log('=====================================');
    console.log('测试完成！');
    console.log('=====================================\n');

    console.log('Screenshots saved to: dogfood-output/screenshots/\n');

    const report = `# EventPilot 用户视角测试报告

测试时间: ${new Date().toISOString()}
测试URL: http://172.28.166.164:5173
浏览器: Playwright Chromium

## 测试结果

| 阶段 | 状态 | 详情 |
|------|------|------|
| 打开登录页面 | PASS | 页面成功加载 |
| 找到登录表单 | PASS | 找到用户名输入框 |
| 填写登录信息 | PASS | 输入admin/admin123 |
| 点击登录按钮 | PASS | 成功点击 |
| 验证登录结果 | ${loginSuccessful ? 'PASS' : 'FAIL'} | ${loginSuccessful ? '登录成功' : '登录可能失败'} |

## 截图

- 01-login-page.png - 登录页面
- 02-focus-username.png - 聚焦用户名输入框
- 03-form-filled.png - 表单填写完成
- 04-after-login.png - 点击登录后
- 05-final-state.png - 最终状态
- 06-tasks-page.png - 任务页面（如果登录成功）

## 发现的问题

${!loginSuccessful ? '登录可能失败，仍在登录页面。请检查后端日志和网络连接。' : '无明显问题，登录流程正常。'}`;

    fs.writeFileSync('dogfood-output/report.md', report);
    console.log('i1 report generated: dogfood-output/report.md\n');

  } catch (error) {
    console.error('\ni1 Test error:');
    console.error(error);
    await page.screenshot({ path: 'dogfood-output/screenshots/error.png' });
  } finally {
    await context.close();
    await browser.close();
  }
}

runUserTest().catch(console.error);
