<template>
  <div class="tasks-container">
    <div class="page-header">
      <h1>任务管理</h1>
      <div class="header-actions">
        <el-button
          :type="showKanbanView ? 'default' : 'primary'"
          @click="showKanbanView = false"
        >
          列表视图
        </el-button>
        <el-button
          :type="showKanbanView ? 'primary' : 'default'"
          @click="showKanbanView = true"
        >
          看板视图
        </el-button>
        <el-button
          type="primary"
          @click="showCreateDialog"
        >
          新建任务
        </el-button>
      </div>
    </div>

    <!-- 看板视图 -->
    <div
      v-if="showKanbanView"
      v-loading="tasksStore.isLoading"
      class="kanban-view"
    >
      <el-row :gutter="20">
        <el-col
          v-for="status in kanbanStatuses"
          :key="status.value"
          :span="6"
        >
          <el-card class="kanban-column-card">
            <template #header>
              <div class="kanban-column-header">
                <span class="status-name">{{ status.name }}</span>
                <el-badge
                  :value="getTasksByStatus(status.value).length"
                  class="status-badge"
                />
              </div>
            </template>

            <KanbanColumn
              :tasks="getTasksByStatus(status.value)"
              :status="status.value"
              :disabled="tasksStore.isDragging"
              @drag-end="handleDragEnd"
              @card-click="handleEdit"
            >
              <template #card="{ task, click }">
                <div @click="click(task)">
                  <div class="task-title">
                    {{ task.title }}
                  </div>
                  <div class="task-meta">
                    <el-tag
                      size="small"
                      :type="getPriorityType(task.priority)"
                    >
                      {{ getPriorityText(task.priority) }}
                    </el-tag>
                    <span class="task-assignee">
                      {{ task.assignee_name || task.assignee?.username || '未分配' }}
                    </span>
                  </div>
                </div>
              </template>
            </KanbanColumn>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 列表视图 -->
    <el-card
      v-else
      class="table-card"
    >
      <template #header>
        <div class="table-header">
          <div class="filter-section">
            <el-input
              v-model="searchQuery"
              placeholder="搜索任务..."
              clearable
              style="width: 300px"
              @input="handleSearch"
            />
            <el-select
              v-model="filterStatus"
              placeholder="状态筛选"
              clearable
              style="width: 150px"
              @change="handleSearch"
            >
              <el-option
                label="全部状态"
                value=""
              />
              <el-option
                label="待处理"
                value="pending"
              />
              <el-option
                label="进行中"
                value="in_progress"
              />
              <el-option
                label="已完成"
                value="completed"
              />
              <el-option
                label="已取消"
                value="cancelled"
              />
            </el-select>
          </div>
        </div>
      </template>

      <el-table
        v-loading="tasksStore.isLoading"
        :data="filteredTasks"
        stripe
        border
      >
        <el-table-column
          prop="title"
          label="任务标题"
          min-width="200"
        />
        <el-table-column
          prop="type"
          label="类型"
          width="120"
        >
          <template #default="{ row }">
            <el-tag size="small">
              {{ getTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="priority"
          label="优先级"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              :type="getPriorityType(row.priority)"
              size="small"
            >
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="progress"
          label="进度"
          width="100"
        >
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column
          prop="assignee"
          label="负责人"
          width="120"
        >
          <template #default="{ row }">
            {{ row.assignee?.username || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="due_date"
          label="截止日期"
          width="140"
        >
          <template #default="{ row }">
            {{ formatDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status !== 'completed'"
              link
              type="success"
              size="small"
              @click="handleComplete(row)"
            >
              完成
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 任务表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑任务' : '新建任务'"
      width="700px"
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskRules"
        label-width="100px"
      >
        <el-form-item
          label="任务标题"
          prop="title"
        >
          <el-input
            v-model="taskForm.title"
            placeholder="请输入任务标题"
          />
        </el-form-item>
        <el-form-item
          label="任务类型"
          prop="type"
        >
          <el-select
            v-model="taskForm.type"
            placeholder="请选择任务类型"
          >
            <el-option
              label="类型选择"
              value=""
            />
            <el-option
              label="活动策划"
              value="activity_planning"
            />
            <el-option
              label="场地布置"
              value="venue_setup"
            />
            <el-option
              label="设备调试"
              value="equipment_testing"
            />
            <el-option
              label="人员协调"
              value="personnel_coordination"
            />
            <el-option
              label="物资准备"
              value="material_preparation"
            />
            <el-option
              label="沟通对接"
              value="communication"
            />
            <el-option
              label="执行监控"
              value="execution_monitoring"
            />
            <el-option
              label="会后收尾"
              value="post_event_cleanup"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="状态"
          prop="status"
        >
          <el-select
            v-model="taskForm.status"
            placeholder="请选择状态"
          >
            <el-option
              label="待处理"
              value="pending"
            />
            <el-option
              label="进行中"
              value="in_progress"
            />
            <el-option
              label="已完成"
              value="completed"
            />
            <el-option
              label="已取消"
              value="cancelled"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="优先级"
          prop="priority"
        >
          <el-select
            v-model="taskForm.priority"
            placeholder="请选择优先级"
          >
            <el-option
              label="低"
              value="low"
            />
            <el-option
              label="中"
              value="medium"
            />
            <el-option
              label="高"
              value="high"
            />
            <el-option
              label="紧急"
              value="urgent"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="进度"
          prop="progress"
        >
          <el-slider
            v-model="taskForm.progress"
            :max="100"
          />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="taskForm.due_date"
            type="date"
            placeholder="选择截止日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useTasksStore } from '../store'
import { useWebSocketStore } from '../stores/websocket'
import { useAuthStore } from '../store'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tasksApi } from '../api/client'
import notification from '../services/notification'
import KanbanColumn from '../components/KanbanColumn.vue'

const tasksStore = useTasksStore()
const wsStore = useWebSocketStore()
const authStore = useAuthStore()

const showKanbanView = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const taskFormRef = ref()

const searchQuery = ref('')
const filterStatus = ref('')

const kanbanStatuses = [
  { name: '待处理', value: 'pending' },
  { name: '进行中', value: 'in_progress' },
  { name: '已完成', value: 'completed' },
  { name: '已取消', value: 'cancelled' }
]

const taskForm = reactive({
  title: '',
  type: '',
  status: 'pending',
  priority: 'medium',
  progress: 0,
  due_date: '',
  description: ''
})

const taskRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ]
}

const filteredTasks = computed(() => {
  return tasksStore.tasks.filter(task => {
    const matchSearch = !searchQuery.value ||
      task.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = !filterStatus.value ||
      task.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

function getTasksByStatus(status) {
  return tasksStore.tasks.filter(task => task.status === status)
}

function getStatusType(status) {
  const types = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
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

function getTypeText(type) {
  const texts = {
    activity_planning: '活动策划',
    venue_setup: '场地布置',
    equipment_testing: '设备调试',
    personnel_coordination: '人员协调',
    material_preparation: '物资准备',
    communication: '沟通对接',
    execution_monitoring: '执行监控',
    post_event_cleanup: '会后收尾'
  }
  return texts[type] || type
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function handleSearch() {
  // 搜索逻辑由computed filteredTasks处理
}

// 拖拽结束处理
async function handleDragEnd(event) {
  const { item, to, from, added, removed } = event;

  // 只处理跨栏拖拽
  if (!added && !removed) {
    return;
  }

  const task = item.__draggable_context?.element;
  if (!task) {
    notification.notify({
      type: 'error',
      message: '拖拽数据错误，请重试',
    });
    return;
  }

  const originalStatus = from?.dataset?.status || task.status;
  const newStatus = to?.dataset?.status;

  if (originalStatus === newStatus) {
    return;
  }

  tasksStore.isDragging = true;

  try {
    try {
      // 1. 乐观更新：本地先更新 UI
      tasksStore.optimisticUpdateTaskStatus(task.id, newStatus);

      // 2. 设置超时（10 秒）
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      // 3. 调用 API

      await tasksApi.update(task.id, { status: newStatus });

      clearTimeout(timeoutId);

      // 4. 成功通知
      notification.toast({
        type: 'success',
        message: '状态已更新',
      });

      // 5. WebSocket 广播
      if (wsStore.connected) {
        wsStore.send({
          type: 'task_status_changed',
          data: {
            task_id: task.id,
            status: newStatus,
            user: authStore.username,
            timestamp: new Date().toISOString(),
          },
        });
      }

    } catch (error) {
      // 6. 错误处理：UI 回滚
      tasksStore.optimisticUpdateTaskStatus(task.id, originalStatus);

      const errorMsg = error.message || '网络错误';
      notification.notify({
        type: 'error',
        message: `更新失败：${errorMsg}，已自动回滚`,
        duration: 5000,
      });

      console.error('Drag update failed:', error);

    } finally {
      tasksStore.isDragging = false;
    }
  } catch (err) {
    console.error('Drag error:', err);
    tasksStore.isDragging = false;
  }
}

async function handleComplete(task) {
  try {
    await tasksStore.completeTask(task.id)
    ElMessage.success('任务完成')
  } catch (error) {
    console.error('Complete task failed:', error)
    ElMessage.error('任务完成失败')
  }
}

function handleEdit(task) {
  isEdit.value = true
  dialogVisible.value = true
  Object.assign(taskForm, {
    ...task,
    progress: task.progress || 0
  })
}

async function handleDelete(task) {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${task.title}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await tasksStore.deleteTask(task.id)
    ElMessage.success('任务删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

function showCreateDialog() {
  isEdit.value = false
  dialogVisible.value = true
  Object.assign(taskForm, {
    title: '',
    type: '',
    status: 'pending',
    priority: 'medium',
    progress: 0,
    due_date: '',
    description: ''
  })
}

async function handleSubmit() {
  if (!taskFormRef.value) return

  try {
    await taskFormRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await tasksStore.updateTask(taskForm.id, taskForm)
      ElMessage.success('更新成功')
    } else {
      await tasksStore.createTask(taskForm)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    showCreateDialog() // 重置表单
  } catch (error) {
    if (error !== false) {
      console.error('Form validation failed:', error)
    }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    await tasksStore.fetchTasks()
  } catch (error) {
    console.error('Failed to load tasks:', error)
    ElMessage.error('加载任务失败')
  }
})
</script>

<style scoped>
.tasks-container {
  padding: 20px;
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
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.kanban-view {
  min-height: 400px;
}

.kanban-column-card {
  min-height: 120px;
}

.kanban-column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-name {
  font-weight: 500;
  font-size: 14px;
}

.status-badge {
  min-width: 20px;
}

.task-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: #333;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.task-assignee {
  color: #409eff;
}

.table-card {
  min-height: 400px;
}

.filter-section {
  display: flex;
}
</style>
