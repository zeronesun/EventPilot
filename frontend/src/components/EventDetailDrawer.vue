<template>
  <el-drawer v-model="isOpen" :title="`活动详情`" size="50%" @close="handleClose">
    <el-skeleton v-if="loading" :rows="10" animated />

    <div v-else-if="eventData">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="活动名称">
          {{ eventData.name }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(eventData.status)">
            {{ getStatusText(eventData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          {{ formatEventType(eventData.type) }}
        </el-descriptions-item>
        <el-descriptions-item label="预算">
          ￥{{ eventData.budget?.toLocaleString() || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间" :span="2">
          {{ formatDate(eventData.start_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ eventData.description || '无描述' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间" v-if="eventData.end_date">
          {{ formatDate(eventData.end_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="负责人" v-if="eventData.owner_name">
          {{ eventData.owner_name }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDate(eventData.created_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="drawer-actions">
        <el-button @click="handleEdit">编辑</el-button>
        <el-button type="danger" @click="handleDelete">删除</el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventsStore } from '@/stores'
import { ElMessageBox } from 'element-plus'

interface Event {
  id?: string | number
  name: string
  status: string
  type: string
  budget?: number
  start_date?: string
  end_date?: string
  description?: string
  owner_name?: string
  created_at?: string
}

const props = defineProps<{
  modelValue: boolean
  eventId: string | null
}>()

const emit = defineEmits(['update:modelValue', 'edit', 'delete', 'success'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const eventData = ref<Event | null>(null)
const eventsStore = useEventsStore()

watch(() => props.eventId, async (newId) => {
  if (newId && props.modelValue) {
    loading.value = true
    try {
      const event = eventsStore.events?.find(e => String(e.id) === newId)
      eventData.value = event || null
    } catch (error) {
      console.error('Failed to load event details:', error)
    } finally {
      loading.value = false
    }
  }
}, { immediate: true })

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    planning: 'warning',
    executing: 'primary',
    completed: 'success',
    reviewed: 'info',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    planning: '策划中',
    executing: '执行中',
    completed: '已完成',
    reviewed: '已复盘',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function formatEventType(type: string): string {
  const types: Record<string, string> = {
    conference: '会议',
    training: '培训',
    event: '活动',
    team_building: '团建'
  }
  return types[type] || type
}

function formatDate(date?: string): string {
  if (!date) return '未设置'
  return new Date(date).toLocaleString('zh-CN')
}

function handleEdit() {
  if (eventData.value) {
    emit('edit', eventData.value)
  }
}

function handleDelete() {
  if (eventData.value) {
    ElMessageBox.confirm('确定要删除这个活动吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      emit('delete', eventData.value)
    }).catch(() => {})
  }
}

function handleClose() {
  isOpen.value = false
}
</script>

<style scoped>
.drawer-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
</style>
