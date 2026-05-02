<template>
  <el-dialog
    v-model="isOpen"
    title="快速移动状态"
    width="400px"
    @close="handleClose"
  >
    <el-form label-width="80px">
      <el-form-item label="当前状态">
        <el-tag :type="getCurrentStatusType()">
          {{ getCurrentStatusText() }}
        </el-tag>
      </el-form-item>

      <el-form-item label="移动到">
        <el-select v-model="targetStatus" placeholder="选择目标状态" style="width: 100%">
          <el-option
            v-for="status in availableStatuses"
            :key="status.value"
            :label="status.label"
            :value="status.value"
            :disabled="status.value === currentStatus"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleMove" :loading="loading">
          移动
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  eventData: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const targetStatus = ref('')
const currentStatus = ref('')

const availableStatuses = [
  { label: '策划中', value: 'planning' },
  { label: '执行中', value: 'executing' },
  { label: '已完成', value: 'completed' },
  { label: '已复盘', value: 'reviewed' },
  { label: '已取消', value: 'cancelled' }
]

const statusTypes: Record<string, string> = {
  planning: 'warning',
  executing: 'primary',
  completed: 'success',
  reviewed: 'info',
  cancelled: 'info'
}

watch(() => props.eventData, (newData) => {
  if (newData) {
    currentStatus.value = newData.status || 'planning'
    targetStatus.value = ''
  }
}, { immediate: true })

const eventsStore = useEventsStore()

function getCurrentStatusType(): string {
  return statusTypes[currentStatus.value] || 'info'
}

function getCurrentStatusText(): string {
  const status = availableStatuses.find(s => s.value === currentStatus.value)
  return status?.label || currentStatus.value
}

async function handleMove() {
  if (!targetStatus.value) {
    ElMessage.warning('请选择目标状态')
    return
  }

  if (targetStatus.value === currentStatus.value) {
    ElMessage.warning('目标状态与当前状态相同')
    return
  }

  loading.value = true
  try {
    await eventsStore.updateEvent(String(props.eventData.id), {
      ...props.eventData,
      status: targetStatus.value
    })
    ElMessage.success('状态更新成功')
    emit('success')
    handleClose()
  } catch (error: any) {
    console.error('Move failed:', error)
    ElMessage.error(error.message || '移动失败')
  } finally {
    loading.value = false
  }
}

function handleClose() {
  targetStatus.value = ''
  isOpen.value = false
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
