<template>
  <div class="user-display">
    <el-tooltip
      v-if="!name"
      :content="emptyTooltip"
      placement="top"
    >
      <span class="user-empty">
        {{ emptyText }}
      </span>
    </el-tooltip>
    
    <div v-else class="user-content">
      <el-avatar v-if="showAvatar" :size="avatarSize" class="user-avatar">
        {{ userInitial }}
      </el-avatar>
      <span class="user-name">{{ name }}</span>
      <el-tag v-if="role" size="small" class="user-role">{{ role }}</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  name?: string | null
  showAvatar?: boolean
  avatarSize?: number | 'small' | 'default' | 'large'
  role?: string
  emptyText?: string
  emptyTooltip?: string
}>(), {
  showAvatar: true,
  avatarSize: 'default',
  emptyText: '未设置',
  emptyTooltip: '用户未设置'
})

const userInitial = computed(() => {
  if (!props.name) return '?'
  return props.name.charAt(0).toUpperCase()
})
</script>

<style scoped>
.user-display {
  display: inline-flex;
  align-items: center;
}

.user-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.user-name {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.user-role {
  font-size: 11px;
  padding: 2px 6px;
}

.user-empty {
  color: #c0c4cc;
  font-size: 14px;
  font-style: italic;
}
</style>
