<template>
  <div class="tasks-container">
    <div class="page-header">
      <h1>任务管理</h1>
      <div class="header-actions">
        <el-button @click="openCreateDialog" type="primary">
          <el-icon><Plus /></el-icon>
          新建任务
        </el-button>
      </div>
    </div>

    <!-- 看板视图 -->
    <el-row :gutter="20" class="kanban-container">
      <el-col :span="8" v-for="status in taskStatuses" :key="status.key">
        <div class="kanban-column">
          <div class="column-header">
            <div class="column-title">
              <el-tag :type="status.type" size="small">{{ status.label }}</el-tag>
              <span class="task-count">{{ getTasksByStatus(status.key).length }}</span>
            </div>
          </div>

          <div class="column-content">
            <div
              v-for="task in getTasksByStatus(status.key)"
              :key="task.id"
              class="task-card"
              @click="viewTask(task)"
            >
              <div class="task-card-header">
                <h4>{{ task.title }}</h4>
                <el-tag :type="getPriorityType(task.priority)" size="small">
                  {{ getPriorityText(task.priority) }}
                </el-tag>
              </div>

              <div class="task-card-body">
                <p v-if="task.description">{{ task.description.substring(0, 100) }}...</p>
                <div class="task-meta">
                  <span v-if="task.due_date">
                    <el-icon><Calendar /></el-icon>
                    {{ formatDate(task.due_date) }}
                  </span>
                  <span v-if="task.assigned_to_name">
                    <el-icon><User /></el-icon>
                    {{ task.assigned_to_name }}
                  </span>
                </div>
              </div>

              <div class="task-card-footer">
                <el-progress
                  :percentage="task.progress || 0"
                  :stroke-width="6"
                />
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 统一的任务表单对话框（详情/新建/编辑） -->
    <TaskFormDialog
      v-model="showFormDialog"
      :mode="formDialogMode"
      :task-data="selectedTaskData"
      :events-list="eventsStore.events"
      @success="handleFormSuccess"
      @delete="handleDeleteTask"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useTasksStore, useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { Plus, Calendar, User } from '@element-plus/icons-vue'
import TaskFormDialog from '@/components/TaskFormDialog.vue'

const tasksStore = useTasksStore()
const eventsStore = useEventsStore()

// 统一的对话框状态
const showFormDialog = ref(false)
const formDialogMode = ref<'view' | 'create' | 'edit'>('create')
const selectedTaskData = ref(null)

const taskStatuses = [
  { key: 'pending', label: '待处理', type: 'info' },
  { key: 'in_progress', label: '进行中', type: 'warning' },
  { key: 'completed', label: '已完成', type: 'success' }
]

onMounted(async () => {
  try {
    await Promise.all([
      tasksStore.fetchTasks(),
      eventsStore.fetchEvents()
    ])
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
})

onActivated(async () => {
  // 每次页面激活时刷新数据
  try {
    await tasksStore.fetchTasks()
  } catch (error) {
    console.error('Failed to refresh tasks:', error)
  }
})

function getTasksByStatus(status) {
  return (tasksStore.tasks || []).filter(task => task.status === status)
}

function getPriorityType(priority) {
  const types = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return types[priority] || 'info'
}

function getPriorityText(priority) {
  const texts = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return texts[priority] || priority
}

function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

function viewTask(task) {
  selectedTaskData.value = task
  formDialogMode.value = 'view'
  showFormDialog.value = true
}

function openCreateDialog() {
  selectedTaskData.value = null
  formDialogMode.value = 'create'
  showFormDialog.value = true
}

function handleFormSuccess(data) {
  // 刷新任务列表
  tasksStore.fetchTasks()

  // 如果是从查看模式切换到编辑模式
  if (data?.action === 'edit') {
    selectedTaskData.value = data.data
    formDialogMode.value = 'edit'
    showFormDialog.value = true
  } else {
    ElMessage.success(formDialogMode.value === 'create' ? '任务创建成功' : '任务更新成功')
  }
}

async function handleDeleteTask(task) {
  try {
    if (task?.id) {
      await tasksStore.deleteTask(task.id)
      ElMessage.success('任务删除成功')
      // 刷新列表
      tasksStore.fetchTasks()
    }
  } catch (error) {
    console.error('Delete task failed:', error)
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.tasks-container {
  padding: 20px;
  height: 100%;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.kanban-container {
  height: calc(100% - 80px);
}

.kanban-column {
  height: 100%;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.column-header {
  padding: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.task-count {
  margin-left: auto;
  font-size: 14px;
  color: #909399;
}

.column-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.task-card {
  background: white;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.task-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.task-card-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.task-card-body {
  margin-bottom: 12px;
}

.task-card-body p {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.task-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.task-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-card-footer {
  margin-top: 10px;
}
</style>
