<template>
  <div class="tasks-container">
    <div class="page-header">
      <h1>任务管理</h1>
      <div class="header-actions">
        <el-button @click="showKanbanView = false" :type="showKanbanView ? 'default' : 'primary'">
          列表视图
        </el-button>
        <el-button @click="showKanbanView = true" :type="showKanbanView ? 'primary' : 'default'">
          看板视图
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          新建任务
        </el-button>
      </div>
    </div>

    <!-- 看板视图 -->
    <div v-if="showKanbanView" class="kanban-view" v-loading="tasksStore.isLoading">
      <el-row :gutter="20">
        <el-col :span="6" v-for="status in kanbanStatuses" :key="status.value">
          <el-card class="kanban-column-card">
            <template #header>
              <div class="kanban-column-header">
                <span class="status-name">{{ status.name }}</span>
                <el-badge :value="getTasksByStatus(status.value).length" class="status-badge" />
              </div>
            </template>

            <KanbanColumn
              :tasks="getTasksByStatus(status.value)"
              :status="status.value"
              :disabled="handleTaskDrag.isDragging"
              @dragEnd="onDragEnd"
              @cardClick="handleEdit"
            >
              <template #card="{ task, click }">
                <div @click="click(task)">
                  <div class="task-title">{{ task.title }}</div>
                  <div class="task-meta">
                    <el-tag size="small" :type="getPriorityType(task.priority)">
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
    <el-card v-else class="table-card">
      <template #header>
        <div class="table-header">
          <div class="filter-section">
            <el-input
              v-model="taskFilters.searchQuery"
              placeholder="搜索任务..."
              clearable
              style="width: 300px"
              @input="taskFilters.handleSearch"
            />
            <el-select
              v-model="taskFilters.filterStatus"
              placeholder="状态筛选"
              clearable
              style="width: 150px"
              @change="taskFilters.handleSearch"
            >
              <el-option label="全部状态" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredTasks"
        v-loading="tasksStore.isLoading"
        stripe
        border
      >
        <el-table-column prop="title" label="任务标题" min-width="200" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getTypeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="负责人" width="120">
          <template #default="{ row }">
            {{ row.assignee?.username || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止日期" width="140">
          <template #default="{ row }">
            {{ formatDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              link
              type="success"
              size="small"
              v-if="row.status !== 'completed'"
              @click="handleComplete(row)"
            >
              完成
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
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
      <el-form :model="taskForm" :rules="taskRules" ref="taskFormRef" label-width="100px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务类型" prop="type">
          <el-select v-model="taskForm.type" placeholder="请选择任务类型">
            <el-option label="类型选择" value="" />
            <el-option label="活动策划" value="activity_planning" />
            <el-option label="场地布置" value="venue_setup" />
            <el-option label="设备调试" value="equipment_testing" />
            <el-option label="人员协调" value="personnel_coordination" />
            <el-option label="物资准备" value="material_preparation" />
            <el-option label="沟通对接" value="communication" />
            <el-option label="执行监控" value="execution_monitoring" />
            <el-option label="会后收尾" value="post_event_cleanup" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="taskForm.status" placeholder="请选择状态">
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="taskForm.priority" placeholder="请选择优先级">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="进度" prop="progress">
          <el-slider v-model="taskForm.progress" :max="100" />
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
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
// 引入 Composables
import { useTaskFilters } from '../composables/useTaskFilters'
import { useTaskDrag } from '../composables/useTaskDrag'
import { useErrorHandler } from '../composables/useErrorHandler'

const tasksStore = useTasksStore()
const wsStore = useWebSocketStore()
const authStore = useAuthStore()

// 使用 Composables
const taskFilters = useTaskFilters(tasksStore.tasks)
const handleTaskDrag = useTaskDrag()
const errorHandler = useErrorHandler({
  enableNotification: true,
  enableLogging: true,
})

const showKanbanView = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const taskFormRef = ref()

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

// 使用 taskFilters.computed 对应的 filteredTasks
const filteredTasks = computed(() => taskFilters.filteredTasks)

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

// 使用新 Composable 的拖拽处理（保留原有提取逻辑，使用新错误处理）
async function onDragEnd(event) {
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
      // 6. 错误处理：UI 回滚（区别：使用新错误处理器）
      tasksStore.optimisticUpdateTaskStatus(task.id, originalStatus);
      await errorHandler.handleError(error, {
        component: 'Tasks',
        action: 'drag_end',
        data: { taskId: task.id, originalStatus, newStatus }
      });
    } finally {
      tasksStore.isDragging = false;
    }
  } catch (err) {
    console.error('Drag error:', err);
    tasksStore.isDragging = false;
    await errorHandler.handleError(err, {
      component: 'Tasks',
      action: 'drag_end',
      data: { internal: true }
    });
  }
}

async function handleComplete(task) {
  try {
    await tasksStore.completeTask(task.id)
    ElMessage.success('任务完成')
  } catch (error) {
    await errorHandler.handleError(error, { component: 'Tasks', action: 'complete_task' })
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
      await errorHandler.handleError(error, { component: 'Tasks', action: 'delete_task' })
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
      await errorHandler.handleError(error, { component: 'Tasks', action: 'submit_form' })
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  tasksStore.fetchTasks()
})
</script>
