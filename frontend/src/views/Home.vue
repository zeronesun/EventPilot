<template>
  <div class="home-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>欢迎回来，{{ authStore.username }}！</h2>
              <el-button type="danger" @click="handleLogout" size="small">退出登录</el-button>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="活动总数" :value="eventsStats.total" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="待处理任务" :value="tasksStats.pending" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="进行中活动" :value="eventsStats.active" />
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>最近活动</h3>
          </template>
          
          <el-skeleton :loading="eventsStore.isLoading" :rows="3" animated>
            <el-empty v-if="!eventsStore.isLoading && eventsStore.events.length === 0" />
            <div v-else>
              <div v-for="event in eventsStore.events.slice(0, 5)" :key="event.id" class="event-item">
                <h4>{{ event.name }}</h4>
                <p>{{ event.type }} - {{ event.status }}</p>
              </div>
            </div>
          </el-skeleton>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>最近任务</h3>
          </template>
          
          <el-skeleton :loading="tasksStore.isLoading" :rows="3" animated>
            <el-empty v-if="!tasksStore.isLoading && tasksStore.tasks.length === 0" />
            <div v-else>
              <div v-for="task in tasksStore.tasks.slice(0, 5)" :key="task.id" class="task-item">
                <h4>{{ task.title }}</h4>
                <p>{{ task.task_type }} - {{ task.status }}</p>
              </div>
            </div>
          </el-skeleton>
        </el-card>
      </el-col>
    </el-row>
    
    <el-alert
      v-if="eventsStore.error || tasksStore.error"
      :title="eventsStore.error || tasksStore.error"
      type="error"
      :closable="false"
      show-icon
      style="margin-top: 20px"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useEventsStore, useTasksStore } from '../store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const eventsStore = useEventsStore()
const tasksStore = useTasksStore()

const eventsStats = ref({
  total: 0,
  active: 0
})

const tasksStats = ref({
  pending: 0
})

onMounted(async () => {
  try {
    // Load initial data
    await Promise.all([
      eventsStore.fetchEvents(),
      tasksStore.fetchTasks()
    ])
    
    // Calculate stats
    eventsStats.value.total = eventsStore.events.length
    eventsStats.value.active = eventsStore.events.filter(e => e.status === 'executing').length
    tasksStats.value.pending = tasksStore.tasks.filter(t => t.status === 'pending').length
    
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})

const handleLogout = async () => {
  try {
    await authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    ElMessage.error('退出登录失败')
  }
}
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-item, .task-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.event-item:last-child, .task-item:last-child {
  border-bottom: none;
}

.event-item h4, .task-item h4 {
  margin: 0 0 5px 0;
  font-size: 16px;
}

.event-item p, .task-item p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
</style>