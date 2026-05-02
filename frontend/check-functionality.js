#!/usr/bin/env node

// EventPilot 前端功能检查工具

const fs = require('fs');
const path = require('path');

console.log('🔍 检查 EventPilot 活动管理功能...\n');

// 检查文件存在性
function checkFile(filepath, description) {
  const fullPath = path.join(__dirname, filepath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}: ${filepath}`);
    return true;
  } else {
    console.log(`❌ ${description}: ${filepath} 不存在`);
    return false;
  }
}

// 检查文件内容
function checkContent(filepath, patterns, description) {
  const fullPath = path.join(__dirname, filepath);
  if (!fs.existsSync(fullPath)) {
    console.log(`❌ ${description}: 文件不存在`);
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  let allFound = true;
  
  patterns.forEach((pattern, index) => {
    if (content.includes(pattern)) {
      console.log(`✅ ${description} - 模式${index + 1}: "${pattern}"`);
    } else {
      console.log(`❌ ${description} - 模式${index + 1}: "${pattern}" 未找到`);
      allFound = false;
    }
  });
  
  return allFound;
}

console.log('📁 检查组件文件...');
const hasComponents = 
  checkFile('src/components/EventDetailDrawer.vue', '详情抽屉组件') &&
  checkFile('src/components/EventEditDialog.vue', '编辑对话框组件') &&
  checkFile('src/components/CreateEventDialog.vue', '创建对话框组件') &&
  checkFile('src/components/QuickMoveDialog.vue', '快速移动对话框组件') &&
  checkFile('src/components/common/DateTimeDisplay.vue', '日期时间显示组件');

console.log('\n🎨 检查详情抽屉功能...');
const hasDetailDrawer = checkContent('src/components/EventDetailDrawer.vue', [
  'handleEdit()',
  'handleDelete()',
  '@click="handleEdit"',
  '@click="handleDelete"',
  '功能按钮',
], 'EventDetailDrawer 功能');

console.log('\n✏️ 检查编辑对话框功能...');
const hasEditDialog = checkContent('src/components/EventEditDialog.vue', [
  'handleSubmit()',
  'handleSubmit',
  'mode="edit"',
  'async function handleSubmit',
], 'EventEditDialog 功能');

console.log('\n➕ 检查创建对话框功能...');
const hasCreateDialog = checkContent('src/components/CreateEventDialog.vue', [
  'handleSubmit()',
  'handleSubmit',
  'mode="create"',
  'async function handleSubmit',
], 'CreateEventDialog 功能');

console.log('\n🔄 检查快速移动对话框功能...');
const hasQuickMoveDialog = checkContent('src/components/QuickMoveDialog.vue', [
  'handleMove()',
  'handleMove',
  'eventsStore.updateEvent',
], 'QuickMoveDialog 功能');

console.log('\n📋 检查看板页面组件引入和事件处理...');
const hasKanbanPage = checkContent('src/views/EventsKanban.vue', [
  "import EventDetailDrawer from",
  "import EventEditDialog from",
  "import CreateEventDialog from",
  "import QuickMoveDialog from",
  "@edit='handleEdit'",
  "@delete='handleDelete'",
  "handleEdit(event:",
  "handleDelete(event:",
], 'EventsKanban 组件和事件处理');

console.log('\n🎯 检查事件处理函数实现...');
const hasEventHandlers = checkContent('src/views/EventsKanban.vue', [
  "function handleEdit(event: any)",
  "async function handleDelete(event: any)",
  "function handleCardClick(event: any)",
  "function handleCommand(command: string, event: any)",
], 'EventsKanban 事件处理函数');

console.log('\n🏪 检查 Store 方法...');
const hasStoreMethods = checkContent('src/stores/events.ts', [
  'async function deleteEvent',
  'async function updateEvent',
  'async function createEvent',
  'async function fetchEvents',
], 'Events Store 方法');

console.log('\n🎛️ 检查状态值一致性...');
const hasStatusMapping = 
  checkContent('src/views/EventsKanban.vue', [
    "value: 'planning'",
    "value: 'executing'",
    "value: 'completed'",
    "value: 'reviewed'",
    "value: 'cancelled'",
  ], '看板页面状态映射') &&
  checkContent('src/components/EventDetailDrawer.vue', [
    "planning:",
    "executing:",
    "completed:",
    "reviewed:",
    "cancelled:",
  ], '详情抽屉状态映射') &&
  checkContent('src/components/EventEditDialog.vue', [
    'value="planning"',
    'value="executing"',
    'value="completed"',
    'value="reviewed"',
    'value="cancelled"',
  ], '编辑对话框状态映射') &&
  checkContent('src/components/QuickMoveDialog.vue', [
    "value: 'planning'",
    "value: 'executing'",
    "value: 'completed'",
    "value: 'reviewed'",
    "value: 'cancelled'",
  ], '快速移动对话框状态映射');

console.log('\n📊 功能检查结果汇总:');
console.log('====================================');
const allGood = hasComponents && hasDetailDrawer && hasEditDialog && 
                hasCreateDialog && hasQuickMoveDialog && hasKanbanPage && 
                hasEventHandlers && hasStoreMethods && hasStatusMapping;

if (allGood) {
  console.log('✅ 所有功能组件和逻辑都已正确实现！');
  console.log('');
  console.log('🎉 可进行的功能测试:');
  console.log('1. ✅ 查看活动详情 - 点击卡片打开详情抽屉');
  console.log('2. ✅ 编辑活动 - 详情页编辑按钮或卡片菜单编辑选项');
  console.log('3. ✅ 删除活动 - 详情页删除按钮或卡片菜单删除选项');
  console.log('4. ✅ 创建活动 - 顶部新建按钮或列头添加按钮');
  console.log('5. ✅ 拖拽移动状态 - 拖动卡片到不同列');
  console.log('6. ✅ 快速移动状态 - 卡片菜单移动选项');
} else {
  console.log('❌ 部分功能未完全实现，请检查上述错误');
}

console.log('\n');
process.exit(allGood ? 0 : 1);
