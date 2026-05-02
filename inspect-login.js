const { chromium } = require('playwright');

async function inspectLoginPage() {
  console.log('🔍 检查登录页面实际DOM结构');

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('http://172.28.166.164:5173/login');
  await page.waitForTimeout(3000);

  console.log('\n=== 找到的所有按钮 ===');
  const buttons = await page.$$('button');
  console.log(`共找到 ${buttons.length} 个按钮`);

  for (let btn of buttons) {
    try {
      const text = await btn.textContent();
      const type = await btn.getAttribute('type');
      const disabled = await btn.getAttribute('disabled');
      console.log(`  - 按钮: "${text.trim()}"`);
      console.log(`    type="${type || '无'}" disabled="${disabled || 'false'}"`);
    } catch(e) {
      console.log('  - 按钮（无法读取属性）');
    }
  }

  console.log('\n=== 找到的所有form ===');
  const forms = await page.$$('form');
  console.log(`共找到 ${forms.length} 个form`);

  for (let form of forms) {
    try {
      const inputs = await form.$$('input');
      console.log(`  - Form 包含 ${inputs.length} 个输入框`);
    } catch(e) {}
  }

  console.log('\n=== 页面标题 ===');
  const title = await page.title();
  console.log(title);

  await browser.close();
  console.log('\n✅ 检查完成');
}

inspectLoginPage().catch(console.error);
