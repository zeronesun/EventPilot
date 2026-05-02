const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  console.log('💡 Debugging: 列出实际加载的router文件');

  const browser = await chromium.launch({
    headless: false
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('router')) {
      console.log('\n📄 Loading:', url);
      const content = await response.text();
      if (content.includes('require')) {
        console.log('❌ Found require() in loaded code!');
        // 找到require在文件中的位置
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('require')) {
            console.log(`    Line ${i}: ${lines[i].trim()}`);
          }
        }
      }
    }
  });

  await page.goto('http://172.28.166.164:5173/login');

  await page.waitForTimeout(3000);

  await browser.close();
  console.log('\n✅ Done');
})();
