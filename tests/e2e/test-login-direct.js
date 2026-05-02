// 直接测试login功能，不依赖router
import { chromium } from require('playwright');

async function testLoginDirect() {
  console.log('直接测试login功能');
  
  const browser = await chromium.launch({headless: false});
  const page = await browser.newPage();
  
  // 1. 打开登录页面
  await page.goto('http://172.28.166.164:5173/login');
  
  // 2. 等待输入框
  await page.waitForSelector('input[placeholder="用户名"]');
  
  // 3. 手动触发login（绕过router guard的错误）
  const username = 'admin';
  const password = 'admin123';
  
  console.log('填写登录信息...');
  await page.fill('input[placeholder="用户名"]', username);
  await page.fill('input[type="password"]', password);
  
  // 4. 点击登录按钮
  console.log('点击登录...');
  await page.click('button[type="submit"]:not([disabled])');
  
  // 5. 等待结果
  await page.waitForTimeout(5000);
  
  // 6. 检查console错误
  const errors = await page.evaluate(() => {
    return window.__ERRORS__ || [];
  });
  
  console.log('Console errors:', errors);
  
  // 7. 截图
  await page.screenshot({path: '/tmp/direct-login-test.png'});
  
  await browser.close();
  console.log('完成');
}

testLoginDirect().catch(console.error);
