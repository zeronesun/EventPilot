<template>
  <div class="tasks-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>任务管理</h3>
              <el-button type="primary" @click="showCreateDialog">新建任务</el-button>
            </div>
          </template>
          
          <el-table
            :data="tasksStore.tasks"
            v-loading="tasksStore.isLoading"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="title" label="任务标题" width="250" />
            <el-table-column prop="task_type" label="类型" width="120">
              <template #default="{ row }">
                {{ getTaskTypeText(row.task_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="100">
              <template #default="{ row }">
                {{ row.progress }}%
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止时间" width="180">
              <template #default="{ row }">
                {{ row.due_date ? formatDate(row.due_date) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="primary" @click="handleComplete(row)">完成</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-alert
      v-if="tasksStore.error"
      :title="tasksStore.error"
      type="error"
      :closable="false"
      show-icon
      style="margin-top: 20px"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTasksStore } from '../store'
import { ElMessage, ElMessageBox } from 'element-plus'

const tasksStore = useTasksStore()

onMounted(async () => {
  try {
    await tasksStore.fetchTasks()
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
})

function getTaskTypeText(type) {
  const types = {
    planning: '策划',
    guest: '嘉宾',
    material: '物料',
    venue: '场地',
    promotion: '宣传',
    onsite: '现场',
    review: '复盘'
  }
  return types[type] || type
}

function getStatusType(status) {
  const types = {
    pending: 'info',
    ready: 'success',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger',
    blocked: 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    pending: '待办',
    ready: '就绪',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消',
    blocked: '阻塞'
  }
  return texts[status] || status
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-CN')
}

function showCreateDialog() {
  ElMessage.info('创建任务功能即将开放')
}

function handleEdit(task) {
  ElMessage.info(`编辑任务: ${task.title}`)
}

async function handleComplete(task) {
  try {
    await ElMessageBox.confirm(`确定要将任务 "${task.title}" 标记为完成吗？`, '确认完成', {
      type: 'success'
    })
    
    await tasksStore.completeTask(task.id)
    ElMessage.success('任务已标记为完成')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Complete failed:', error)
      ElMessage.error('操作失败')
    }
  }
}
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>