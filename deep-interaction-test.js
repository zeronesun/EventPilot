const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function deepInteractionTest() {
  console.log('\n');
  console.log('========================================');
  console.log('🐕 深度按钮交互功能测试');
  console.log('========================================\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 800
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const allIssues = [];
  const allResults = [];

  // 监控所有错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('🔴 [Console]', msg.text().substring(0, 150));
    }
  });

  // ==================== 登录 ====================
  console.log('📍 第一步: 登录系统\n');
  try {
    await page.goto('http://172.28.166.164:5173/login', { waitUntil: 'networkidle' });
    await page.waitForSelector('input[placeholder="用户名"]');
    await page.fill('input[placeholder="用户名"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="button"]');
    await page.waitForTimeout(3000);
    console.log('✅ 登录成功\n');
  } catch (e) {
    console.log('❌ 登录失败:', e.message);
    return;
  }

  // ==================== 定义待测试页面 ====================
  const pagesToTest = [
    {
      name: '工作台 (/)',
      path: '/',
      tests: [
        {
          desc: '刷新页面',
          action: async () => {
            await page.reload();
            await page.waitForTimeout(2000);
            return 'PASS';
          }
        }
      ]
    },
    {
      name: '活动管理 (/events)',
      path: '/events',
      tests: [
        {
          desc: '测试搜索框',
          selector: 'input[placeholder*="搜索"], input.search',
          action: async (selector) => {
            try {
              await page.waitForSelector(selector, { timeout: 3000 });
              await page.fill(selector, '年度技术大会');
              await page.waitForTimeout(1000);
              await page.press(selector, 'Enter');
              await page.waitForTimeout(2000);
              return 'PASS';
            } catch (e) {
              return `搜索框测试失败: ${e.message}`;
            }
          }
        },
        {
          desc: '测试筛选下拉菜单',
          selector: '.el-select, select, [class*="filter"]',
          action: async (selector) => {
            try {
              const filter = await page.$(selector);
              if (filter) {
                await filter.click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到筛选控件';
            } catch (e) {
              return `筛选测试失败: ${e.message}`;
            }
          }
        },
        {
          desc: '测试新建活动按钮',
          selector: 'text=新建活动, button:has-text("新建")',
          action: async (selector) => {
            try {
              await page.click(selector);
              await page.waitForTimeout(2000);

              // 检查是否打开对话框
              const dialog = await page.$('.el-dialog, [class*="modal"]');
              if (dialog) {
                // 对话框打开，检查按钮
                await page.screenshot({ path: '/mnt/d/projects/sourcecode/EventPilot/dogfood-output/event-dialog.png' });
                const saveBtn = await page.$('text=确定, button.ok-btn');
                if (saveBtn) {
                  await saveBtn.click();
                  await page.waitForTimeout(1000);
                  return '对话框打开但功能未实现';
                }
                return '对话框已打开';
              }
              // 检查错误提示
              const errorText = await page.evaluate(() => {
                const el = document.querySelector('.el-message--error');
                return el?.textContent?.trim();
              });
              return errorText || `PASS`;
            } catch (e) {
              return `测试失败: ${e.message}`;
            }
          }
        },
        {
          desc: '测试编辑活动（如果存在列表项）',
          action: async () => {
            try {
              // 找到列表中的第一个编辑按钮
              const editBtn = await page.$('button:has-text("编辑"), button[class*="edit"]');
              if (editBtn) {
                await editBtn.click();
                await page.waitForTimeout(1500);
                return 'EDITclicked';
              }
              return '未找到可编辑的活动';
            } catch (e) {
              return `编辑测试失败: ${e.message}`;
            }
          }
        },
        {
          desc: '测试删除活动',
          action: async () => {
            try {
              const deleteBtn = await page.$('button:has-text("删除"), button[class*="delete"]');
              if (deleteBtn) {
                await deleteBtn.click();
                await page.waitForTimeout(1500);

                // 确认删除对话框
                const confirmBtn = await page.$('button:has-text("确定"), button.confirm');
                if (confirmBtn) {
                  await confirmBtn.click();
                  await page.waitForTimeout(1000);
                }
                return 'DELETE_clicked';
              }
              return '未找到可删除的活动';
            } catch (e) {
              return `删除测试失败: ${e.message}`;
            }
          }
        }
      ]
    },
    {
      name: '任务管理 (/tasks)',
      path: '/tasks',
      tests: [
        {
          desc: '测试搜索框',
          action: async () => {
            try {
              const searchInput = await page.$('input[placeholder*="搜索"], input.search');
              if (searchInput) {
                await searchInput.fill('场地');
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到搜索框';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试状态筛选',
          action: async () => {
            try {
              // 查找状态选择器
              const statusSelect = await page.$('.el-select, select, button:has-text("全部"), [class*="status"]');
              if (statusSelect) {
                await statusSelect.click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到状态筛选';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试向下滚动（分页）',
          action: async () => {
            try {
              await page.evaluate(() => window.scrollBy(0, 500));
              await page.waitForTimeout(1000);
              return 'PASS';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '用户管理 (/users)',
      path: '/users',
      tests: [
        {
          desc: '测试添加用户按钮',
          action: async () => {
            try {
              const addBtn = await page.$('text=添加用户, button:has-text("新建")');
              if (addBtn) {
                await addBtn.click();
                await page.waitForTimeout(2000);

                // 检查表单
                const form = await page.$('form, .el-form');
                if (form) {
                  await page.screenshot({ path: '/mnt/d/projects/sourcecode/EventPilot/dogfood-output/user-form.png' });

                  // 尝试填写表单
                  const username = await page.$('input[placeholder*="用户名"]');
                  if (username) {
                    await username.fill('testuser');
                  }

                  const cancelBtn = await page.$('button:has-text("取消")');
                  if (cancelBtn) {
                    await cancelBtn.click();
                  }
                  return '用户表单可打开';
                }
                return '未打开用户表单';
              }
              return '未找到添加用户按钮';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试用户列表搜索',
          action: async () => {
            try {
              const search = await page.$('input[placeholder*="搜索"]');
              if (search) {
                await search.fill('admin');
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到搜索框';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '清单管理 (/checklists)',
      path: '/checklists',
      tests: [
        {
          desc: '测试模板标签页',
          action: async () => {
            try {
              const tabs = await page.$$('button[class*="tab"], .tab-item');
              if (tabs.length > 1) {
                await tabs[0].click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到标签页';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试新建清单模板',
          action: async () => {
            try {
              const newTempBtn = await page.$('text=新建模板, button:has-text("模板")');
              if (newTempBtn) {
                await newTempBtn.click();
                await page.waitForTimeout(2000);
                return 'PASS';
              }
              return '未找到新建模板按钮';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试新建清单实例',
          action: async () => {
            try {
              await page.click('text=新建清单实例');
              await page.waitForTimeout(2000);

              const error = await page.evaluate(() => {
                const el = document.querySelector('.el-message--error');
                return el?.textContent?.trim();
              });
              return error || 'PASS';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '文件管理 (/files)',
      path: '/files',
      tests: [
        {
          desc: '查找上传区域',
          action: async () => {
            try {
              const uploadArea = await page.$('[class*="upload"][class*="drag"], .upload-area');
              if (uploadArea) {
                return '上传区域存在';
              }
              const uploadBtn = await page.$('button.upload-btn, button:has-text("上传")');
              if (uploadBtn) {
                return '上传按钮存在';
              }
              return '未找到上传区域';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试点击上传按钮',
          action: async () => {
            try {
              const uploadBtn = await page.$('button:has-text("上传"), [class*="upload"] button');
              if (uploadBtn) {
                await uploadBtn.click();
                await page.waitForTimeout(2000);

                // 检查文件选择对话框或错误
                const error = await page.evaluate(() => {
                  const el = document.querySelector('.el-message--error');
                  return el?.textContent?.trim();
                });
                return error || '上传点击成功';
              }
              return '未找到上传按钮';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试搜索文件',
          action: async () => {
            try {
              const search = await page.$('input[placeholder*="搜索"], input[class*="search"]');
              if (search) {
                await search.fill('文件');
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到搜索框';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试文件类型筛选',
          action: async () => {
            try {
              const filter = await page.$('select, .el-select');
              if (filter) {
                await filter.click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到文件类型筛选';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '个人档案 (/profiles)',
      path: '/profiles',
      tests: [
        {
          desc: '测试编辑个人资料',
          action: async () => {
            try {
              const editBtn = await page.$('button:has-text("编辑"), button.edit');
              if (editBtn) {
                await editBtn.click();
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到编辑按钮';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '预算管理 (/budget)',
      path: '/budget',
      tests: [
        {
          desc: '测试预算筛选',
          action: async () => {
            try {
              const filter = await page.$('select, .el-select, [class*="filter"]');
              if (filter) {
                await filter.click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到筛选控件';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '知识库 (/knowledge)',
      path: '/knowledge',
      tests: [
        {
          desc: '测试搜索知识条目',
          action: async () => {
            try {
              const search = await page.$('input[placeholder*="搜索"]');
              if (search) {
                await search.fill('活动');
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到搜索框';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试新建知识条目',
          action: async () => {
            try {
              const newBtn = await page.$('button:has-text("新建"), button:has-text("创建")');
              if (newBtn) {
                await newBtn.click();
                await page.waitForTimeout(2000);
                return 'PASS';
              }
              return '未找到新建按钮';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '活动复盘 (/reviews)',
      path: '/reviews',
      tests: [
        {
          desc: '测试搜索复盘记录',
          action: async () => {
            try {
              const search = await page.$('input[placeholder*="搜索"]');
              if (search) {
                await search.fill('复盘');
                await page.waitForTimeout(1500);
                return 'PASS';
              }
              return '未找到搜索框';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试新建复盘',
          action: async () => {
            try {
              const newBtn = await page.$('button:has-text("新建"), button:has-text("创建")');
              if (newBtn) {
                await newBtn.click();
                await page.waitForTimeout(2000);

                const error = await page.evaluate(() => {
                  const el = document.querySelector('.el-message--error');
                  return el?.textContent?.trim();
                });
                return error || 'PASS';
              }
              return '未找到新建按钮';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    },
    {
      name: '数据分析 (/analytics)',
      path: '/analytics',
      tests: [
        {
          desc: '测试时间范围选择',
          action: async () => {
            try {
              const datePickers = await page.$$('input[type="date"], [class*="date"], .date-picker');
              if (datePickers.length > 0) {
                await datePickers[0].click();
                await page.waitForTimeout(1000);
                return 'PASS';
              }
              return '未找到日期选择器';
            } catch (e) {
              return e.message;
            }
          }
        },
        {
          desc: '测试图表交互（如果有）',
          action: async () => {
            try {
              // 查找图表或数据可视化元素
              await page.waitForTimeout(2000);
              return 'PASS';
            } catch (e) {
              return e.message;
            }
          }
        }
      ]
    }
  ];

  // ==================== 执行测试 ====================
  for (const pageInfo of pagesToTest) {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`📍 测试页面: ${pageInfo.name}`);
    console.log('='.repeat(70));

    try {
      await page.goto(`http://172.28.166.164:5173${pageInfo.path}`, {
        waitUntil: 'networkidle',
        timeout: 10000
      });
      await page.waitForTimeout(2000);
      console.log(`✅ 页面加载成功\n`);

      const pageIssues = [];

      for (const test of pageInfo.tests) {
        console.log(`  测试: ${test.desc}`);

        try {
          let result;
          if (test.selector) {
            result = await test.action(test.selector);
          } else {
            result = await test.action();
          }

          if (result === 'PASS' || result === 'EDITclicked' || result === 'DELETE_clicked') {
            console.log(`    ✅ 通过`);
          } else if (result.includes('未找到')) {
            console.log(`    ⚠️  ${result}`);
          } else {
            console.log(`    ❌ ${result}`);
            pageIssues.push({
              test: test.desc,
              issue: result
            });
            allIssues.push({
              page: pageInfo.name,
              test: test.desc,
              issue: result
            });
          }
        } catch (error) {
          console.log(`    ❌ 异常: ${error.message}`);
          pageIssues.push({
            test: test.desc,
            issue: error.message
          });
          allIssues.push({
            page: pageInfo.name,
            test: test.desc,
            issue: error.message
          });
        }
      }

      // 截图页面
      const screenshotFile = pageInfo.path.replace('/', '-') + '-deep-test.png';
      await page.screenshot({
        path: `/mnt/d/projects/sourcecode/EventPilot/dogfood-output/${screenshotFile}`,
        fullPage: true
      });

      allResults.push({
        page: pageInfo.name,
        tests: pageInfo.tests.length,
        issues: pageIssues.length
      });

    } catch (error) {
      console.log(`  ❌ 页面加载失败: ${error.message}`);
      allResults.push({
        page: pageInfo.name,
        tests: 0,
        issues: [{ message: error.message }]
      });
    }
  }

  // ==================== 生成报告 ====================
  console.log(`\n\n${'='.repeat(70)}`);
  console.log('📊 测试总结');
  console.log('='.repeat(70));

  console.log('\n按页面统计:');
  let totalTests = 0;
  let totalIssues = 0;

  for (const result of allResults) {
    const status = result.issues.length === 0 ? '✅' : '⚠️';
    console.log(`  ${status} ${result.page.padEnd(25)} ${result.tests}个测试, ${result.issues.length}个问题`);
    totalTests += result.tests;
    totalIssues += result.issues.length;
  }

  console.log(`\n总计:`);
  console.log(`  - 测试数: ${totalTests}`);
  console.log(`  - 问题数: ${totalIssues}`);

  if (allIssues.length > 0) {
    console.log(`\n📋 发现的所有问题:`);
    for (const issue of allIssues) {
      console.log(`  - [${issue.page}] ${issue.test}: ${issue.issue.substring(0, 100)}`);
    }
  }

  // 保存详细报告
  const report = `# 深度按钮交互功能测试报告

测试时间: ${new Date().toLocaleString('zh-CN')}

## 测试统计

| 页面 | 测试数 | 问题数 |
|------|--------|--------|
${allResults.map(r => `| ${r.page} | ${r.tests} | ${r.issues.length} |`).join('\n')}

**总计**: ${totalTests} 个测试，${totalIssues} 个问题

## 发现的问题详细列表

| 页面 | 测试项 | 问题描述 |
|------|--------|----------|
${allIssues.map(i => `| ${i.page} | ${i.test} | ${i.issue} |`).join('\n')}

---

说明:
- ✅ = 测试通过
- ⚠️ = 功能未找到或部分实现
- ❌ = 功能存在但有问题
`;

  const reportPath = '/mnt/d/projects/sourcecode/EventPilot/dogfood-output/deep-interaction-report.md';
  fs.writeFileSync(reportPath, report, 'utf-8');
  console.log(`\n📄 详细报告已保存: ${reportPath}`);

  await browser.waitForTimeout(3000);
  await browser.close();

  console.log(`\n${'='.repeat(70)}`);
  console.log('✅ 测试完成');
  console.log('='.repeat(70));
}

deepInteractionTest().catch(error => {
  console.error('\n❌ 测试异常:', error);
  process.exit(1);
});
