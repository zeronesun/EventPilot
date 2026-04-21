// EventPilot 通知服务
// 统一管理 ElNotification，提供防抖和聚合功能

import { ElNotification } from 'element-plus';

let notificationQueue = [];
let notificationTimer = null;
const AGGREGATE_DELAY = 1000; // 聚合延迟 1 秒

// 显示单个通知
function notify({ type = 'info', title, message, duration = 3000, ...options }) {
  ElNotification({
    type,
    title,
    message,
    duration,
    ...options,
  });
}

// 显示成功提示（toast 风格）
function toast({ type = 'success', message, duration = 2000 }) {
  ElNotification({
    type,
    message,
    duration,
    offset: 80, // 右上角位置
    showClose: false, // 不显示关闭按钮
  });
}

// 防抖通知（防止短时间内多次触发）
function debouncedNotify(config) {
  clearTimeout(notificationTimer);

  notificationTimer = setTimeout(() => {
    notify(config);
  }, 300);
}

// 聚合同类型通知
function aggregateNotify({ type = 'info', messages, ...options }) {
  if (!Array.isArray(messages)) {
    messages = [messages];
  }

  if (messages.length === 1) {
    notify({ type, message: messages[0], ...options });
    return;
  }

  // 多条通知聚合
  notify({
    type,
    title: `${messages.length} 条通知`,
    message: messages.map((msg, index) => `${index + 1}. ${msg}`).join('\n'),
    duration: 5000,
    ...options,
  });
}

// 清除所有通知
function clearAll() {
  ElNotification.closeAll();
  notificationQueue = [];
}

export default {
  notify,
  toast,
  debouncedNotify,
  aggregateNotify,
  clearAll,
};
