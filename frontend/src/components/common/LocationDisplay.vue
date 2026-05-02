<template>
  <div class="location-display">
    <el-icon v-if="showIcon && location" class="location-icon"><Location /></el-icon>
    <span v-if="location" class="location-value">{{ location }}</span>
    <span v-else class="location-empty">{{ emptyText }}</span>
  </div>
</template>

<script setup lang="ts">
import { Location } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  location?: string | null
  showIcon?: boolean
  emptyText?: string
}>(), {
  showIcon: true,
  emptyText: '未设置'
})
</script>

<style scoped>
.location-display {
  display: flex;
  align-items: center;
  gap: 6px;
}

.location-icon {
  color: #909399;
  font-size: 14px;
}

.location-value {
  color: #303133;
  font-size: 14px;
}

.location-empty {
  color: #c0c4cc;
  font-size: 14px;
  font-style: italic;
}
</style>
