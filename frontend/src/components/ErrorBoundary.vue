<template>
  <slot v-if="!hasError"></slot>

  <div v-else class="error-boundary">
    <el-card class="error-card">
      <template #header>
        <div class="error-header">
          <el-icon :size="32" color="var(--el-color-danger)">
            <Warning />
          </el-icon>
          <span>应用出现错误</span>
        </div>
      </template>

      <div class="error-content">
        <p class="error-message">
          {{ errorMessage }}
        </p>

        <el-collapse v-if="showDetails && errorDetails" class="error-details">
          <el-collapse-item title="错误详情" name="details">
            <pre class="error-stack">{{ errorDetails }}</pre>
          </el-collapse-item>
        </el-collapse>

        <div class="error-actions">
          <el-button type="primary" @click="handleReload">
            <el-icon><RefreshRight /></el-icon>
            重新加载
          </el-button>

          <el-button @click="handleReport">
            <el-icon><message /></el-icon>
            上报错误
          </el-button>

          <el-button @click="toggleDetails">
            <el-icon><View /></el-icon>
            {{ showDetails ? '隐藏详情' : '显示详情' }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Warning, RefreshRight, Message, View, Message as ElMessage } from 'element-plus';

// Props
interface Props {
  // 自定义错误处理函数
  onError?: (error: Error, errorInfo: any) => void;
  // 是否显示返回首页按钮
  showHome?: boolean;
  // 自定义错误消息
  fallbackMessage?: string;
}

const props = withDefaults(defineProps<Props>(), {
  onError: undefined,
  showHome: true,
  fallbackMessage: undefined,
});

// 事件
const emit = defineEmits<{
  error: [error: Error, errorInfo: any];
}>();

// State
const hasError = ref(false);
const errorMessage = ref('');
const errorDetails = ref('');
const errorInstance = ref<Error | null>(null);
const showDetails = ref(false);

// 配置对象（用于 ErrorBoundary 注册）
const boundaryConfig = {
  onError: (error: Error, errorInfo: any) => {
    hasError.value = true;
    errorMessage.value = props.fallbackMessage || error.message || '未知错误';
    errorDetails.value = error.stack || '';
    errorInstance.value = error;

    // 调用外部错误处理
    if (props.onError) {
      props.onError(error, errorInfo);
    }

    // 触发事件
    emit('error', error, errorInfo);

    // 记录错误
    console.error('[ErrorBoundary]', error, errorInfo);
  },
};

// 暴露配置对象，供外部注册使用
defineExpose({ boundaryConfig });

// 方法
function handleReload() {
  // 重新加载页面
  window.location.reload();
}

function toggleDetails() {
  showDetails.value = !showDetails.value;
}

async function handleReport() {
  // 上报错误到服务器
  try {
    const errorData = {
      message: errorMessage.value,
      stack: errorDetails.value,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    };

    // 这里应该调用API上报错误
    // await api.reportError(errorData)

    ElMessage.success('错误已上报，感谢您的反馈');
  } catch (err) {
    ElMessage.error('错误上报失败');
  }
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 20px;
}

.error-card {
  max-width: 800px;
  width: 100%;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 500;
}

.error-content {
  padding: 20px 0;
}

.error-message {
  margin: 0 0 20px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.error-details {
  margin: 20px 0;
}

.error-stack {
  margin: 0;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  color: var(--el-text-color-regular);
}

.error-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
