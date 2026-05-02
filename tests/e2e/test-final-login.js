const { chromium } = require('playwright');

async function testLogin() {
  console.log('========================================');
  console.log('🐕 真实用户登录测试（包含所有修复）');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });

  const context = await browser.newContext();
  const page = await context.newPage();

  let loginRequestSuccess = false;
  let loginRequestStatus = null;
  let loginResponseText = '';

  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'error') {
      console.log('🔴 [Console Error]', text);
    }
  });

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/users/auth/login')) {
      console.log('\n🌐 登录API请求:', url);
      loginRequestStatus = response.status();
      console.log('   状态:', loginRequestStatus);
      try {
        const text = await response.text();
        loginResponseText = text;
        console.log('   响应:', text.substring(0, 300));
        if (response.status() === 200 && text.includes('token')) {
          loginRequestSuccess = true;
        }
      } catch(e) {
        console.log('   响应：无法读取');
      }
    }
  });

  console.log('📍 Step 1: 访问登录页面');
  try {
    await page.goto('http://172.28.166.164:5173/login', { waitUntil: 'networkidle' });
    console.log('✅ 页面加载成功');
  } catch(e) {
    console.log('❌ 页面加载失败:', e.message);
    await browser.close();
    return;
  }

  console.log('\n📍 Step 2: 填写登录信息');
  try {
    await page.waitForSelector('input[placeholder="用户名"]', { timeout: 5000 });
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    console.log('✅ 表单填写完成');
  } catch(e) {
    console.log('❌ 表单填写失败:', e.message);
    await browser.close();
    return;
  }

  console.log('\n📍 Step 3: 点击登录按钮');
  // 使用正确的选择器：type="button" 且文本为"登录"
  const loginBtn = await page.$('button[type="button"]');
  if (loginBtn) {
    const btnText = await loginBtn.textContent();
    console.log(`找到按钮: "${btnText.trim()}"`);
    await loginBtn.click();
    console.log('✅ 已点击登录按钮');
  } else {
    console.log('❌ 未找到登录按钮');
  }

  console.log('\n📍 Step 4: 等待结果（8秒）...');
  await page.waitForTimeout(8000);

  const currentUrl = page.url();
  console.log('当前URL:', currentUrl);

  let success = false;
  if (loginRequestSuccess) {
    console.log('\n🎉✅✅ 登录API请求成功！');
    success = true;
  } else if (!currentUrl.endsWith('/login')) {
    console.log('\n🎉✅✅ 登录成功！已跳转！');
    success = true;
  } else {
    console.log('\n❌ 登录失败');
    console.log('   API状态:', loginRequestStatus);
  }

  await page.screenshot({ path: '/mnt/d/projects/sourcecode/EventPilot/dogfood-output/test-result-final.png', fullPage: true });
  console.log('📸 截图已保存');

  await browser.close();
  console.log('\n========================================');
  if (success) {
    console.log('🎉🎉🎉 测试通过 - 登录成功！');
  } else {
    console.log('❌ 测试失败 - 登录不成功');
  }
  console.log('========================================');
}

testLogin().catch(error => {
  console.error('测试出错:', error);
  process.exit(1);
});
