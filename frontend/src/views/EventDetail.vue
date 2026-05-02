<template>
  <div class="event-detail-page">
    <!-- 加载状态 -->
    <el-skeleton v-if="isLoading" :loading="true" animated :count="3">
      <template #template>
        <el-card>
          <el-skeleton-item variant="h3" style="width: 50%" />
          <el-divider />
          <el-row :gutter="20">
            <el-col :span="16">
              <el-skeleton-item variant="p" style="width: 100%" />
              <el-skeleton-item variant="p" style="width: 80%" />
              <el-skeleton-item variant="p" style="width: 60%" />
            </el-col>
            <el-col :span="8">
              <el-skeleton-item variant="p" style="width: 100%" />
              <el-skeleton-item variant="p" style="width: 70%" />
            </el-col>
          </el-row>
        </el-card>
      </template>
    </el-skeleton>

    <div v-else-if="event">
      <!-- 面包屑和操作栏 -->
      <div class="page-header">
        <el-breadcrumb>
          <el-breadcrumb-item :to="{ path: '/events' }">
            活动管理
          </el-breadcrumb-item>
          <el-breadcrumb-item>{{ event.name }}</el-breadcrumb-item>
        </el-breadcrumb>
        
        <div class="header-actions">
          <el-button @click="$router.back()">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <el-button type="primary" @click="handleEdit">
            <el-icon><Edit /></el-icon>
            编辑活动
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 左侧主要信息 -->
        <el-col :span="16">
          <el-card shadow="hover" class="info-card">
            <template #header>
              <div class="card-header">
                <div class="event-title">
                  <h2>{{ event.name }}</h2>
                  <el-tag :type="getStatusType(event.status)" size="large" effect="dark">
                    {{ getStatusText(event.status) }}
                  </el-tag>
                </div>
              </div>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="活动类型">
                <el-tag size="small">{{ formatEventType(event.type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                <UserDisplay :name="event.owner_name" :show-avatar="true" />
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">
                <DateTimeDisplay :datetime="event.start_date" />
              </el-descriptions-item>
              <el-descriptions-item label="结束时间">
                <DateTimeDisplay :datetime="event.end_date" empty-text="未设置" />
              </el-descriptions-item>
              <el-descriptions-item label="活动地点" :span="2">
                <LocationDisplay :location="event.location" />
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatFullDate(event.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatFullDate(event.updated_at) }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="description-section" v-if="event.description">
              <h3 class="section-title">活动说明</h3>
              <p class="description-text">{{ event.description }}</p>
            </div>
          </el-card>

          <!-- 预算信息 -->
          <el-card shadow="hover" class="info-card" v-if="hasBudgetInfo">
            <template #header>
              <div class="card-header">
                <el-icon><Coin /></el-icon>
                <h3>预算信息</h3>
              </div>
            </template>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="预算金额" :precision="2">
                  <template #formatter>
                    <span class="budget-amount">{{ formatCurrency(event.budget) }}</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="实际支出" :precision="2">
                  <template #formatter>
                    {{ event.actual_cost != null ? formatCurrency(event.actual_cost) : '未结算' }}
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="预算偏差" :precision="2">
                  <template #formatter>
                    <el-tag
                      :type="getBudgetDeviationType(event.budget, event.actual_cost)"
                      effect="dark"
                    >
                      {{ getBudgetDeviationText(event.budget, event.actual_cost) }}
                    </el-tag>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>

            <el-progress
              v-if="event.actual_cost != null && event.budget"
              :percentage="getBudgetUsage(event.budget, event.actual_cost)"
              :color="getProgressColor(event.budget, event.actual_cost)"
              :stroke-width="10"
              class="budget-progress"
            >
              <template #default="{ percentage }">
                <span class="progress-text">已使用 {{ percentage }}%</span>
              </template>
            </el-progress>
          </el-card>
        </el-col>

        <!-- 右侧统计和操作 -->
        <el-col :span="8">
          <el-card shadow="hover" class="stats-card">
            <template #header>
              <div class="card-header">
                <el-icon><TrendCharts /></el-icon>
                <h3>统计数据</h3>
              </div>
            </template>

            <el-alert
              title="任务统计"
              :description="`${totalTasks} 个关联任务`"
              type="info"
              :closable="false"
              show-icon
              class="stat-item"
            />
            <el-alert
              title="预算使用"
              :description="getBudgetUsageText(event.budget, event.actual_cost)"
              :type="getBudgetUsageType(event.budget, event.actual_cost)"
              :closable="false"
              show-icon
              class="stat-item"
            />
          </el-card>

          <el-card shadow="hover" class="actions-card">
            <template #header>
              <div class="card-header">
                <el-icon><Operation /></el-icon>
                <h3>快捷操作</h3>
              </div>
            </template>

            <el-button type="primary" block @click="handleCreateTask" class="action-btn">
              <el-icon><Plus /></el-icon>
              创建任务
            </el-button>
            <el-button block @click="handleEdit" class="action-btn">
              <el-icon><Edit /></el-icon>
              编辑活动
            </el-button>
            <el-button block @click="handleExport" class="action-btn">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            <el-button block @click="handleShare" class="action-btn">
              <el-icon><Share /></el-icon>
              分享活动
            </el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 错误状态 -->
    <el-result
      v-else
      icon="error"
      title="加载失败"
      sub-title="请重试或联系管理员"
    >
      <template #extra>
        <el-button type="primary" @click="loadData">重新加载</el-button>
        <el-button @click="$router.back()">返回</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventsStore, useTasksStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Edit, Delete, Coin, TrendCharts, Operation,
  Plus, Download, Share
} from '@element-plus/icons-vue'
import DateTimeDisplay from '../components/common/DateTimeDisplay.vue'
import LocationDisplay from '../components/common/LocationDisplay.vue'
import UserDisplay from '../components/common/UserDisplay.vue'

const route = useRoute()
const router = useRouter()
const eventsStore = useEventsStore()
const tasksStore = useTasksStore()

const isLoading = ref(false)
const totalTasks = ref(0)

const event = computed(() => eventsStore.currentEvent)

const hasBudgetInfo = computed(() => {
  return event.value?.budget || event.value?.actual_cost != null
})

onMounted(async () => {
  const eventId = route.params.id as string
  if (eventId) {
    await loadData()
  }
})

async function loadData() {
  const eventId = route.params.id as string
  if (!eventId) {
    ElMessage.error('活动ID不存在')
    router.push('/events')
    return
  }

  isLoading.value = true
  try {
    await Promise.all([
      eventsStore.fetchEvent(eventId),
      loadTasksStatistics(eventId)
    ])
  } catch (error) {
    console.error('Failed to load event:', error)
    ElMessage.error('加载活动详情失败')
  } finally {
    isLoading.value = false
  }
}

async function loadTasksStatistics(eventId: string) {
  try {
    const response = await eventsStore.fetchEventStatistics(eventId)
    if (response.task_count !== undefined) {
      totalTasks.value = response.task_count
    }
  } catch (error) {
    console.error('Failed to load task statistics:', error)
    totalTasks.value = 0
  }
}

function handleEdit() {
  if (event.value?.id) {
    router.push(`/events/${event.value.id}/edit`)
  }
}

async function handleDelete() {
  if (!event.value?.id) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除活动"${event.value.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await eventsStore.deleteEvent(String(event.value.id))
    ElMessage.success('活动删除成功')
    router.push('/events')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
  }
}

function handleCreateTask() {
  if (event.value?.id) {
    router.push({
      path: '/tasks',
      query: { event: event.value.id }
    })
  }
}

function handleExport() {
  ElMessage.info('导出功能即将开放')
}

function handleShare() {
  const url = window.location.href
  navigator.clipboard?.writeText(url).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

// 工具函数
function formatFullDate(date: string): string {
  if (!date) return '未设置'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatCurrency(amount: number | undefined): string {
  if (!amount) return '￥0.00'
  return `￥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
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

function getBudgetDeviationType(budget: number | undefined, actual: number | null): string {
  if (!budget || actual == null) return 'info'
  
  const deviation = ((actual - budget) / budget) * 100
  
  if (deviation > 10) return 'danger'
  if (deviation > 5) return 'warning'
  if (deviation < -10) return 'success'
  return 'info'
}

function getBudgetDeviationText(budget: number | undefined, actual: number | null): string {
  if (!budget || actual == null) return '未结算'
  
  const deviation = ((actual - budget) / budget) * 100
  
  if (deviation === 0) return '预算准确'
  if (deviation > 0) return `超支 ${Math.abs(deviation).toFixed(1)}%`
  return `节约 ${Math.abs(deviation).toFixed(1)}%`
}

function getBudgetUsage(budget: number, actual: number): number {
  if (!budget || actual == null) return 0
  return Math.min(100, Math.max(0, (actual / budget) * 100))
}

function getBudgetUsageText(budget: number | undefined, actual: number | null): string {
  if (!budget || actual == null) return '未结算'
  const usage = getBudgetUsage(budget, actual)
  return `已使用 ${usage.toFixed(1)}%`
}

function getBudgetUsageType(budget: number | undefined, actual: number | null): string {
  if (!budget || actual == null) return 'info'
  const usage = getBudgetUsage(budget, actual)
  
  if (usage > 90) return 'danger'
  if (usage > 70) return 'warning'
  return 'success'
}

function getProgressColor(budget: number, actual: number): string {
  const usage = getBudgetUsage(budget, actual)
  
  if (usage > 90) return '#f56c6c'
  if (usage > 70) return '#e6a23c'
  return '#67c23a'
}
</script>

<style scoped>
.event-detail-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h2,
.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.event-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.info-card,
.stats-card,
.actions-card {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  transition: box-shadow 0.3s;
}

.info-card:hover,
.stats-card:hover,
.actions-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.description-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.description-text {
  color: #606266;
  line-height: 1.8;
  word-break: break-word;
  white-space: pre-wrap;
}

.budget-amount {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.budget-progress {
  margin-top: 20px;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.stat-item {
  margin-bottom: 16px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.action-btn {
  margin-bottom: 12px;
}

.action-btn:last-child {
  margin-bottom: 0;
}
</style>
