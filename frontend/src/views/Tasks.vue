<template>
  <div class="tasks-container">
    <div class="page-header">
      <h1>任务管理</h1>
      <div class="header-actions">
        <el-button @click="showCreateDialog = true" type="primary">
          <el-icon><Plus /></el-icon>
          新建任务
        </el-button>
      </div>
    </div>

    <!-- 看板视图 -->
    <el-row :gutter="20" class="kanban-container">
      <el-col :span="6" v-for="status in taskStatuses" :key="status.key">
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

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建任务" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" placeholder="选择优先级">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="form.due_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="选择状态">
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联活动">
          <el-select v-model="form.event" placeholder="选择活动" clearable>
            <el-option
              v-for="event in eventsStore.events"
              :key="event.id"
              :label="event.name"
              :value="event.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="tasksStore.isLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from 'vue'
import { useTasksStore, useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { Plus, Calendar, User } from '@element-plus/icons-vue'

const tasksStore = useTasksStore()
const eventsStore = useEventsStore()

const showCreateDialog = ref(false)
const formRef = ref()

const form = ref({
  title: '',
  description: '',
  priority: 'medium',
  due_date: '',
  status: 'pending',
  event: ''
})

const rules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

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
  ElMessage.info(`查看任务: ${task.title}`)
}

async function handleCreate() {
  const valid = await formRef.value?.validate(validate => !validate)
  if (!valid) {
    ElMessage.error('请填写必要信息')
    return
  }

  try {
    await tasksStore.createTask(form.value)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    resetForm()
  } catch (error) {
    console.error('Create task failed:', error)
    ElMessage.error('创建任务失败')
  }
}

function resetForm() {
  formRef.value?.resetFields()
  form.value = {
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    status: 'pending',
    event: ''
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
