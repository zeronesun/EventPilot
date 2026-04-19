<template>
  <div class="events-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>活动管理</h3>
              <el-button type="primary" @click="showCreateDialog">新建活动</el-button>
            </div>
          </template>
          
          <el-table
            :data="eventsStore.events"
            v-loading="eventsStore.isLoading"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="name" label="活动名称" width="200" />
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="start_date" label="开始时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.start_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <el-alert
      v-if="eventsStore.error"
      :title="eventsStore.error"
      type="error"
      :closable="false"
      show-icon
      style="margin-top: 20px"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEventsStore } from '../store'
import { ElMessage, ElMessageBox } from 'element-plus'

const eventsStore = useEventsStore()

onMounted(async () => {
  try {
    await eventsStore.fetchEvents()
  } catch (error) {
    console.error('Failed to load events:', error)
  }
})

function getStatusType(status) {
  const types = {
    planning: 'info',
    executing: 'warning',
    completed: 'success',
    reviewed: 'info',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    planning: '策划中',
    executing: '执行中',
    completed: '已完成',
    reviewed: '已复盘',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-CN')
}

function showCreateDialog() {
  ElMessage.info('创建活动功能即将开放')
}

function handleEdit(event) {
  ElMessage.info(`编辑活动: ${event.name}`)
}

async function handleDelete(event) {
  try {
    await ElMessageBox.confirm(`确定要删除活动 "${event.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    await eventsStore.deleteEvent(event.id)
    ElMessage.success('活动删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.events-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>