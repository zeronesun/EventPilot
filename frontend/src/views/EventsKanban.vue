<template>
  <div class="kanban-container">
    <!-- 筛选和工具栏 -->
    <div class="kanban-toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">
          <el-icon><Menu /></el-icon>
          活动看板
        </h2>
        <p class="page-subtitle">拖拽卡片切换活动状态</p>
      </div>

      <div class="toolbar-center">
        <div class="filter-group">
          <el-input
            v-model="searchQuery"
            placeholder="搜索活动..."
            clearable
            style="width: 200px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select
            v-model="filterType"
            placeholder="活动类型"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="option in typeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>
      </div>

      <div class="toolbar-right">
        <el-button circle @click="refreshData" :loading="isLoading">
          <el-icon><Refresh /></el-icon>
        </el-button>
        <el-button type="primary" @click="handleCreateEvent">
          <el-icon><Plus /></el-icon>
          新建
        </el-button>
        <el-button @click="switchToListView">
          <el-icon><List /></el-icon>
          列表
        </el-button>
      </div>
    </div>

    <!-- 看板区域 -->
    <div class="kanboard-wrapper">
      <div
        v-for="column in columns"
        :key="column.value"
        class="kanban-column"
        :class="`column-${column.value}`"
        @dragover.prevent
        @drop.prevent="handleDrop($event, column.value)"
      >
        <!-- 列头 -->
        <div class="column-header">
          <div class="header-left">
            <div class="column-badge" :style="{ backgroundColor: column.color }">
              {{ getEventCount(column.value) }}
            </div>
            <h3 class="column-title">{{ column.label }}</h3>
          </div>
          <el-button
            circle
            size="small"
            @click="handleCreateEventWithStatus(column.value)"
          >
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>

        <!-- 列内容 -->
        <div class="column-content">
          <div v-if="getFilteredEvents(column.value).length === 0" class="empty-state">
            <el-empty description="暂无活动" :image-size="60" />
          </div>

          <div
            v-for="event in getFilteredEvents(column.value)"
            :key="event.id"
            class="kanban-card"
            draggable="true"
            @dragstart="handleDragStart($event, event)"
            @click="handleCardClick(event)"
          >
            <div class="card-top">
              <div class="card-title">{{ event.name }}</div>
              <el-dropdown @command="(cmd) => handleCommand(cmd, event)" trigger="click">
                <el-button size="small" circle text class="card-menu" @click.stop>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item command="detail">
                      <el-icon><View /></el-icon>
                      详情
                    </el-dropdown-item>
                    <el-dropdown-item command="move" divided>
                      <el-icon><Sort /></el-icon>
                      移动到其他列
                    </el-dropdown-item>
                    <el-dropdown-item command="delete">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="card-body">
              <div class="card-meta">
                <el-tag size="small" :type="getTypeColor(event.type)">
                  {{ formatEventType(event.type) }}
                </el-tag>
              </div>

              <div v-if="event.description" class="card-description">
                {{ truncateText(event.description, 60) }}
              </div>

              <div class="card-info">
                <div class="info-item" v-if="event.start_date">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(event.start_date) }}</span>
                </div>
                <div class="info-item" v-if="event.budget">
                  <el-icon><Coin /></el-icon>
                  <span>￥{{ event.budget.toLocaleString() }}</span>
                </div>
              </div>
            </div>

            <div class="card-footer">
              <div class="card-assignee" v-if="event.owner_name">
                <el-avatar :size="24">
                  {{ event.owner_name.charAt(0) }}
                </el-avatar>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情抽屉 -->
    <EventDetailDrawer
      v-model="showDetailDrawer"
      :event-id="selectedEventId"
      @edit="handleEdit"
      @delete="handleDelete"
      @success="handleActionSuccess"
    />

    <!-- 编辑对话框 -->
    <EventEditDialog
      v-model="showEditDialog"
      :event-data="selectedEventData"
      mode="edit"
      @success="handleActionSuccess"
    />

    <!-- 快速移动对话框 -->
    <QuickMoveDialog
      v-model="showQuickMoveDialog"
      :event="selectedEventData"
      @move="handleQuickMove"
    />

    <!-- 创建活动对话框 -->
    <CreateEventDialog
      v-model="showCreateDialog"
      :default-status="defaultCreateStatus"
      @success="handleCreateSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'
import {
  Menu, Search, Refresh, Plus, List, MoreFilled, Edit,
  View, Delete, Calendar, Coin, Sort
} from '@element-plus/icons-vue'
import EventDetailDrawer from '../components/EventDetailDrawer.vue'
import EventEditDialog from '../components/EventEditDialog.vue'
import CreateEventDialog from '../components/CreateEventDialog.vue'
import QuickMoveDialog from '../components/QuickMoveDialog.vue'

const router = useRouter()
const eventsStore = useEventsStore()

const isLoading = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const defaultCreateStatus = ref('pending')

const showDetailDrawer = ref(false)
const showEditDialog = ref(false)
const showQuickMoveDialog = ref(false)
const showCreateDialog = ref(false)
const selectedEventId = ref<string | null>(null)
const selectedEventData = ref<any>(null)
const draggedEvent = ref<any>(null)

const columns = [
  { label: '策划中', value: 'planning', color: '#409eff' },
  { label: '执行中', value: 'executing', color: '#e6a23c' },
  { label: '已完成', value: 'completed', color: '#67c23a' },
  { label: '已复盘', value: 'reviewed', color: '#f56c6c' },
  { label: '已取消', value: 'cancelled', color: '#909399' },
]
const typeOptions = [
  { label: '会议', value: 'conference' },
  { label: '培训', value: 'training' },
  { label: '活动', value: 'event' },
  { label: '团建', value: 'team_building' },
  { label: '其他', value: 'other' }
]

onMounted(async () => {
  await refreshData()
})

async function refreshData() {
  isLoading.value = true
  try {
    await eventsStore.fetchEvents()
  } finally {
    isLoading.value = false
  }
}

function getFilteredEvents(status: string) {
  let events = (eventsStore.events || []).filter(e => e.status === status)
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    events = events.filter(e =>
      e.name?.toLowerCase().includes(query) ||
      e.description?.toLowerCase().includes(query)
    )
  }
  
  if (filterType.value) {
    events = events.filter(e => e.type === filterType.value)
  }
  
  return events
}

function getEventCount(status: string) {
  return getFilteredEvents(status).length
}

function handleDragStart(event: DragEvent, eventData: any) {
  draggedEvent.value = eventData
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function handleDrop(event: DragEvent, targetStatus: string) {
  event.preventDefault()
  if (draggedEvent.value && draggedEvent.value.status !== targetStatus) {
    moveEventToStatus(draggedEvent.value, targetStatus)
  }
  draggedEvent.value = null
}

async function moveEventToStatus(eventData: any, newStatus: string) {
  try {
    const updatedEvent = { ...eventData, status: newStatus }
    await eventsStore.updateEvent(String(eventData.id), updatedEvent)
    await refreshData()
    ElMessage.success('状态更新成功')
  } catch (error) {
    console.error('Move failed:', error)
    ElMessage.error('状态更新失败')
  }
}

function handleCardClick(event: any) {
  selectedEventId.value = String(event.id)
  showDetailDrawer.value = true
}

function handleEdit(event: any) {
  selectedEventData.value = event
  showEditDialog.value = true
}

function handleCommand(command: string, event: any) {
  selectedEventData.value = event
  switch (command) {
    case 'edit':
      handleEdit(event)
      break
    case 'detail':
      handleCardClick(event)
      break
    case 'move':
      showQuickMoveDialog.value = true
      break
    case 'delete':
      handleDelete(event)
      break
  }
}

async function handleDelete(event: any) {
  try {
    await eventsStore.deleteEvent(String(event.id))
    await refreshData()
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('Delete failed:', error)
    ElMessage.error('删除失败')
  }
}

function handleActionSuccess() {
  refreshData()
}

function handleCreateEvent() {
  defaultCreateStatus.value = 'planning'
  showCreateDialog.value = true
}

function handleCreateEventWithStatus(status: string) {
  defaultCreateStatus.value = status
  showCreateDialog.value = true
}

function handleCreateSuccess() {
  refreshData()
}

function handleQuickMove(targetStatus: string) {
  if (selectedEventData.value) {
    moveEventToStatus(selectedEventData.value, targetStatus)
    showQuickMoveDialog.value = false
  }
}

function switchToListView() {
  router.push('/events')
}

// 工具函数
function formatDate(date: string): string {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

function formatEventType(type: string): string {
  const types: Record<string, string> = {
    conference: '会议',
    training: '培训',
    event: '活动',
    team_building: '团建',
    other: '其他'
  }
  return types[type] || type
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    conference: '',
    training: 'success',
    event: 'warning',
    team_building: 'info',
    other: 'info'
  }
  return colors[type] || ''
}

function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}
</script>

<style scoped>
.kanban-container {
  padding: 20px;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.kanban-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.toolbar-center {
  flex: 2;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: center;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.kanboard-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  height: calc(100vh - 180px);
  overflow-x: auto;
}

.kanban-column {
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  min-width: 320px;
}

.kanban-column.column-pending {
  background: linear-gradient(135deg, #ecf5ff 0%, #d4e8ff 100%);
}

.kanban-column.column-in_progress {
  background: linear-gradient(135deg, #fdf6ec 0%, #f5e7d0 100%);
}

.kanban-column.column-completed {
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7e6 100%);
}

.kanban-column.column-cancelled {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.column-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 14px;
}

.column-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.column-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.kanban-card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  cursor: grab;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  border: 1px solid #e4e7ed;
}

.kanban-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: #409eff;
}

.kanban-card:active {
  cursor: grabbing;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  gap: 8px;
}

.card-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-menu {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.kanban-card:hover .card-menu {
  opacity: 1;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-meta {
  display: flex;
  gap: 6px;
}

.card-description {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
}

.card-assignee {
  display: flex;
  align-items: center;
}

:deep(.el-dropdown) {
  flex-shrink: 0;
}

:deep(.column-content)::-webkit-scrollbar {
  width: 6px;
}

:deep(.column-content)::-webkit-scrollbar-track {
  background: transparent;
}

:deep(.column-content)::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

:deep(.column-content)::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
