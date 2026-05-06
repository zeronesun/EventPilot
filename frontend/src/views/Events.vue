<template>
  <div class="events-container">
    <!-- 快捷键提示 -->
    <el-alert
      v-if="showShortcutTip"
      title="快捷键提示"
      type="info"
      :closable="true"
      @close="showShortcutTip = false"
      style="margin-bottom: 16px"
    >
      <template #default>
        <div class="shortcuts-grid">
          <div><kbd>N</kbd> 新建活动</div>
          <div><kbd>R</kbd> 刷新</div>
          <div><kbd>F</kbd> 聚焦搜索</div>
          <div><kbd>Ctrl+A</kbd> 全选</div>
          <div><kbd>Esc</kbd> 取消选择</div>
          <div><kbd>?</kbd> 显示帮助</div>
        </div>
      </template>
    </el-alert>

    <!-- 顶部工具栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">活动管理</h2>
        <p class="page-subtitle">管理所有活动信息，支持快速查看和编辑</p>
      </div>
      <div class="header-actions">
        <el-button
          @click="switchToKanbanView"
        >
          <el-icon><Menu /></el-icon>
          看板视图
        </el-button>
        <el-button
          @click="exportData"
          :disabled="selectedEvents.length === 0"
          :title="selectedEvents.length > 0 ? '导出选中的活动' : '请先选择活动'"
        >
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button
          @click="batchEdit"
          :disabled="selectedEvents.length === 0"
          :title="selectedEvents.length > 0 ? '批量编辑选中的活动' : '请先选择活动'"
        >
          <el-icon><Edit /></el-icon>
          批量编辑
        </el-button>
        <el-button
          type="danger"
          @click="batchDelete"
          :disabled="selectedEvents.length === 0"
          :title="selectedEvents.length > 0 ? '删除选中的活动' : '请先选择活动'"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button type="primary" @click="formDialogMode = 'create'; showFormDialog = true" :shortcut="'N'">
          <el-icon><Plus /></el-icon>
          新建活动
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card" shadow="never">
      <el-row :gutter="12" align="middle">
        <el-col :span="10">
          <el-input
            ref="searchInput"
            v-model="searchQuery"
            placeholder="搜索活动名称、类型...（按 F 聚焦）"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
            @keyup.f="searchInput?.focus?.()"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterStatus"
            placeholder="活动状态"
            clearable
            @change="handleFilter"
            style="width: 100%"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterType"
            placeholder="活动类型"
            clearable
            @change="handleFilter"
            style="width: 100%"
          >
            <el-option
              v-for="option in typeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <div class="filter-actions">
            <el-button circle size="default" @click="refreshData" :loading="eventsStore.isLoading">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button circle size="default" @click="toggleView">
              <el-icon><Grid /></el-icon>
            </el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 活动列表 -->
    <el-card class="events-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="card-title">活动列表</span>
            <el-tag type="info" size="small" class="ml-2">
              共 {{ totalEvents }} 个活动
            </el-tag>
          </div>
          <div class="header-right">
            <!-- 选中状态显示 -->
            <div v-if="selectedEvents.length > 0" class="selection-info">
              <span class="text">已选择 {{ selectedEvents.length }} 个活动</span>
              <el-button text type="primary" @click="clearSelection" size="small">
                取消选择
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <div v-loading="eventsStore.isLoading" :min="100">
        <el-table
          ref="tableRef"
          :data="filteredEvents"
          stripe
          style="width: 100%"
          @sort-change="handleSort"
          @row-click="handleRowClick"
          @selection-change="handleSelectionChange"
          class="clickable-rows"
        >
          <el-table-column
            type="selection"
            width="55"
            :selectable="(row, index) => true"
          />
          
          <el-table-column type="index" label="#" width="60" align="center" />
          
          <el-table-column
            prop="name"
            label="活动名称"
            min-width="200"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="event-name-cell">
                <div class="event-name">{{ row.name }}</div>
                <div class="event-meta">
                  <el-tag size="small" :type="getStatusType(row.status)">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                  <span class="event-type">{{ formatEventType(row.type) }}</span>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column
            prop="type"
            label="类型"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <el-tag size="small">{{ formatEventType(row.type) }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="start_date"
            label="开始时间"
            width="180"
            sortable="custom"
          >
            <template #default="{ row }">
              <DateTimeDisplay :datetime="row.start_date" :show-icon="false" />
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-tooltip content="查看详情" placement="top">
                  <el-button
                    type="primary"
                    size="small"
                    circle
                    @click.stop="handleViewDetails(row)"
                  >
                    <el-icon><View /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="编辑" placement="top">
                  <el-button
                    size="small"
                    circle
                    @click.stop="handleEdit(row)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-dropdown @command="(cmd) => handleMoreAction(cmd, row)" trigger="click">
                  <el-button size="small" circle @click.stop>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="duplicate">
                        <el-icon><CopyDocument /></el-icon>
                        复制
                      </el-dropdown-item>
                      <el-dropdown-item command="export">
                        <el-icon><Download /></el-icon>
                        导出
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" divided>
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalEvents"
            layout="total, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="!eventsStore.isLoading && filteredEvents.length === 0"
          description="暂无活动数据"
          :image-size="120"
        >
          <el-button type="primary" @click="formDialogMode = 'create'; showFormDialog = true">
            创建第一个活动
          </el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 统一的活动表单对话框（详情/新建/编辑） -->
    <EventFormDialog
      v-model="showFormDialog"
      :mode="formDialogMode"
      :event-data="selectedEventData"
      @success="handleFormSuccess"
      @delete="handleDeleteFromForm"
    />

    <!-- 批量编辑对话框 -->
    <BatchEditEventsDialog
      v-model="showBatchEditDialog"
      :events="selectedEvents"
      @success="handleBatchUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTable } from 'element-plus'
import {
  Plus, Search, Refresh, View, Edit, MoreFilled,
  CopyDocument, Download, Delete, Grid, Menu
} from '@element-plus/icons-vue'
import EventFormDialog from '../components/EventFormDialog.vue'
import BatchEditEventsDialog from '../components/BatchEditEventsDialog.vue'
import DateTimeDisplay from '../components/common/DateTimeDisplay.vue'
import type { Event } from '@/stores'

const router = useRouter()
const eventsStore = useEventsStore()

// 搜索和筛选
const searchQuery = ref('')
const filterStatus = ref('')
const filterType = ref('')
const sortField = ref('')
const sortOrder = ref<'ascending' | 'descending'>('ascending')

// 表格相关
const tableRef = ref<InstanceType<typeof ElTable>>()
const searchInput = ref()

// 选择相关
const selectedEvents = ref<[]>([])
const selectAll = ref(false)

// 对话框状态
const showFormDialog = ref(false)
const formDialogMode = ref<'view' | 'create' | 'edit'>('create')
const selectedEventId = ref<string | null>(null)
const selectedEventData = ref<Event | null>(null)
const showBatchEditDialog = ref(false)

// 视图状态
const currentView = ref('list') // 'list' or 'kanban'

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)

// 快捷键提示
const showShortcutTip = ref(false)

const hasActiveFilters = computed(() => {
  return searchQuery.value || filterStatus.value || filterType.value
})

const totalEvents = computed(() => {
  return eventsStore.events?.length || 0
})

// 选项数据
const statusOptions = [
  { label: '策划中', value: 'planning' },
  { label: '执行中', value: 'executing' },
  { label: '已完成', value: 'completed' },
  { label: '已复盘', value: 'reviewed' },
  { label: '已取消', value: 'cancelled' }
]

const typeOptions = [
  { label: '会议', value: 'conference' },
  { label: '培训', value: 'training' },
  { label: '活动', value: 'event' },
  { label: '团建', value: 'team_building' },
  { label: '其他', value: 'other' }
]

// 计算属性：过滤和排序
const filteredEvents = computed(() => {
  let result = eventsStore.events || []

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(event =>
      event.name?.toLowerCase().includes(query) ||
      event.type?.toLowerCase().includes(query) ||
      event.status?.toLowerCase().includes(query)
    )
  }

  // 状态过滤
  if (filterStatus.value) {
    result = result.filter(event => event.status === filterStatus.value)
  }

  // 类型过滤
  if (filterType.value) {
    result = result.filter(event => event.type === filterType.value)
  }

  // 排序
  if (sortField.value) {
    result = [...result].sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]

      if (aVal === bVal) return 0

      if (sortOrder.value === 'ascending') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

// 生命周期
onMounted(async () => {
  await refreshData()
  setupKeyboardShortcuts()
})

onUnmounted(() => {
  cleanupKeyboardShortcuts()
})

onActivated(async () => {
  await refreshData()
})

// 键盘快捷键
const keydownHandler = (e: KeyboardEvent) => {
  // 忽略在输入框中的按键
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
    if (e.key === 'f' || e.key === 'F') {
      handleFocusSearch()
    }
    return
  }

  switch (e.key.toLowerCase()) {
    case 'n':
      formDialogMode.value = 'create'
      showFormDialog.value = true
      break
    case 'r':
      refreshData()
      break
    case 'f':
      handleFocusSearch()
      break
    case '?':
      showShortcutTip.value = !showShortcutTip.value
      break
    case 'escape':
      clearSelection()
      break
  }

  // Ctrl+A 全选
  if (e.ctrlKey && (e.key === 'a' || e.key === 'A')) {
    e.preventDefault()
    if (selectedEvents.value.length > 0) {
      // 如果已经有选中的，则取消选择
      clearSelection()
    } else {
      // 否则全选当前页面
      const table = tableRef.value
      if (table) {
        // 获取当前页面的所有行
        const rows = table.getSelectionRows()
        if (rows.length === 0) {
          // 如果没有选中的，则全选
          table.toggleAllSelection()
        }
      }
    }
  }
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', keydownHandler)
}

function cleanupKeyboardShortcuts() {
  window.removeEventListener('keydown', keydownHandler)
}

// 事件处理
async function refreshData() {
  await eventsStore.fetchEvents()
}

function handleSearch() {
  // 筛选逻辑已通过computed filteredEvents自动处理
}

function handleFilter() {
  // 筛选逻辑已通过computed filteredEvents自动处理
}

function resetFilters() {
  searchQuery.value = ''
  filterStatus.value = ''
  filterType.value = ''
  sortField.value = ''
  sortOrder.value = 'ascending'
}

function handleSort({ prop, order }: { prop: string; order: string }) {
  sortField.value = prop
  sortOrder.value = order === 'ascending' ? 'ascending' : 'descending'
}

function handleFocusSearch() {
  searchInput.value?.focus()
}

function toggleView() {
  if (currentView.value === 'list') {
    router.replace('/events-kanban')
  } else {
    router.replace('/events')
  }
}

function switchToKanbanView() {
  router.push('/events-kanban')
}

// 选择相关
function handleSelectionChange(selection: any[]) {
  selectedEvents.value = selection
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  // 改变每页大小时重置到第一页
  currentPage.value = 1
}

function handlePageChange(page: number) {
  currentPage.value = page
}

function clearSelection() {
  tableRef.value?.clearSelection()
  selectedEvents.value = []
}

// 批量操作
function batchEdit() {
  if (selectedEvents.value.length === 0) {
    ElMessage.warning('请先选择要编辑的活动')
    return
  }
  showBatchEditDialog.value = true
}

async function batchDelete() {
  if (selectedEvents.value.length === 0) {
    ElMessage.warning('请先选择要删除的活动')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除已选中的 ${selectedEvents.value.length} 个活动吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    for (const event of selectedEvents.value) {
      await eventsStore.deleteEvent(String(event.id))
    }

    ElMessage.success(`成功删除 ${selectedEvents.value.length} 个活动`)
    clearSelection()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Batch delete failed:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 导出功能
async function exportData() {
  try {
    const dataToExport = selectedEvents.value.length > 0 
      ? selectedEvents.value 
      : filteredEvents.value
    
    if (dataToExport.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }

    // 转换为CSV
    const headers = ['ID', '名称', '类型', '状态', '开始时间', '结束时间', '预算', '负责人']
    const rows = dataToExport.map(e => [
      e.id,
      e.name,
      formatEventType(e.type),
      getStatusText(e.status),
      e.start_date,
      e.end_date,
      e.budget,
      e.owner_name
    ])

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell || ''}"`).join(','))
    ].join('\n')

    // 下载
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `events_export_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('导出失败')
  }
}

function handleRowClick(row: Event) {
  handleViewDetails(row)
}

function handleViewDetails(event: Event) {
  selectedEventId.value = String(event.id)
  selectedEventData.value = event
  formDialogMode.value = 'view'
  showFormDialog.value = true
}

function handleEdit(event: Event) {
  selectedEventData.value = event
  formDialogMode.value = 'edit'
  showFormDialog.value = true
}

function handleEditFromDrawer(eventId: string) {
  const event = eventsStore.events.find(e => String(e.id) === eventId)
  if (event) {
    handleEdit(event)
  }
}

function handleFormSuccess(data?: any) {
  refreshData()
  
  // 如果是从查看模式切换到编辑模式
  if (data?.action === 'edit') {
    selectedEventData.value = data.data
    formDialogMode.value = 'edit'
    showFormDialog.value = true
  } else {
    ElMessage.success(formDialogMode.value === 'create' ? '活动创建成功' : '活动更新成功')
  }
}

function handleDeleteFromForm(data?: any) {
  if (data) {
    handleDelete(data)
  }
}

function handleMoreAction(command: string, event: Event) {
  switch (command) {
    case 'duplicate':
      handleDuplicate(event)
      break
    case 'export':
      exportSingleEvent(event)
      break
    case 'delete':
      handleDelete(event)
      break
  }
}

async function handleDelete(event: Event) {
  try {
    await ElMessageBox.confirm(
      `确定要删除活动"${event.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await eventsStore.deleteEvent(String(event.id))
    ElMessage.success('活动删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

function handleDuplicate(event: Event) {
  ElMessage.info('复制功能即将开放')
}

async function exportSingleEvent(event: Event) {
  selectedEvents.value = [event]
  exportData()
}

// 批量更新
async function handleBatchUpdate(updateData: any) {
  const { ids, data } = updateData

  try {
    for (const id of ids) {
      await eventsStore.updateEvent(String(id), data)
    }
    ElMessage.success(`成功更新 ${ids.length} 个活动`)
    clearSelection()
  } catch (error) {
    console.error('Batch update failed:', error)
    ElMessage.error('批量更新失败')
  }
}

// 工具函数
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

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    pending: '策划中',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}
</script>

<style scoped>
.events-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.ml-2 {
  margin-left: 8px;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-info .text {
  font-weight: 500;
  color: #409eff;
}

.batch-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-info .text {
  font-weight: 500;
}

.header-right {
  display: flex;
  gap: 8px;
}

/* 分页容器 */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
  margin-top: 8px;
}

.clickable-rows :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-rows :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.event-name-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-type {
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.events-card {
  border: 1px solid #ebeef5;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.shortcuts-grid div {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

kbd {
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  font-family: monospace;
  font-weight: 500;
}
</style>
