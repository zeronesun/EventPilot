<template>
  <div class="analytics-container">
    <div class="page-header">
      <h1>活动数据分析</h1>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="margin-right: 10px"
          @change="handleDateChange"
        />
        <el-button @click="loadAnalytics">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ analytics.overview?.total_events || 0 }}
          </div>
          <div class="stat-label">
            活动总数
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ analytics.overview?.total_tasks || 0 }}
          </div>
          <div class="stat-label">
            任务总数
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ analytics.overview?.task_completion_rate || 0 }}%
          </div>
          <div class="stat-label">
            任务完成率
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ analytics.overview?.budget_variance_rate || 0 }}%
          </div>
          <div class="stat-label">
            预算偏差率
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>活动状态分布</h3>
            </div>
          </template>
          <div class="chart-container">
            <el-table
              :data="statusTableData"
              stripe
              border
            >
              <el-table-column
                prop="status"
                label="状态"
                width="120"
              >
                <template #default="{ row }">
                  <el-tag :type="row.type">
                    {{ row.label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="count"
                label="数量"
              />
              <el-table-column
                prop="percentage"
                label="占比"
              >
                <template #default="{ row }">
                  {{ row.percentage }}%
                </template>
              </el-table-column>
              <el-table-column label="分布">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.percentage"
                    :stroke-width="10"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>活动类型分布</h3>
            </div>
          </template>
          <div class="chart-container">
            <el-table
              :data="typeTableData"
              stripe
              border
            >
              <el-table-column
                prop="name"
                label="类型"
              />
              <el-table-column
                prop="count"
                label="数量"
              />
              <el-table-column
                prop="percentage"
                label="占比"
              >
                <template #default="{ row }">
                  {{ row.percentage }}%
                </template>
              </el-table-column>
              <el-table-column label="分布">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.percentage"
                    :stroke-width="10"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>任务类型分布</h3>
            </div>
          </template>
          <div class="chart-container">
            <el-table
              :data="taskTypeTableData"
              stripe
              border
            >
              <el-table-column
                prop="type"
                label="任务类型"
                width="120"
              >
                <template #default="{ row }">
                  <el-tag size="small">
                    {{ row.label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                prop="count"
                label="数量"
              />
              <el-table-column
                prop="percentage"
                label="占比"
              >
                <template #default="{ row }">
                  {{ row.percentage }}%
                </template>
              </el-table-column>
              <el-table-column label="分布">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.percentage"
                    :stroke-width="10"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>预算概览</h3>
            </div>
          </template>
          <div class="budget-overview">
            <el-descriptions
              :column="1"
              border
            >
              <el-descriptions-item label="总预算">
                ¥{{ formatNumber(analytics.overview?.total_estimated_budget || 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="实际支出">
                ¥{{ formatNumber(analytics.overview?.total_actual_budget || 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="预算偏差">
                <span :class="budgetVarianceClass">
                  ¥{{ formatNumber(analytics.overview?.budget_variance || 0) }}
                </span>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>高风险活动</h3>
              <el-tag
                type="danger"
                size="small"
              >
                需要关注
              </el-tag>
            </div>
          </template>
          <div class="event-list">
            <el-empty
              v-if="!analytics.high_risk_events?.length"
              description="暂无高风险活动"
            />
            <div v-else>
              <div
                v-for="event in analytics.high_risk_events"
                :key="event.id"
                class="event-item"
              >
                <div class="event-info">
                  <span class="event-name">{{ event.name }}</span>
                  <el-tag
                    type="danger"
                    size="small"
                  >
                    {{ event.risk_level }}
                  </el-tag>
                </div>
                <div class="event-meta">
                  风险因素: {{ event.factors_count }}个
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>即将到期</h3>
              <el-tag
                type="warning"
                size="small"
              >
                7天内
              </el-tag>
            </div>
          </template>
          <div class="event-list">
            <el-empty
              v-if="!analytics.upcoming_deadlines?.length"
              description="暂无即将到期的活动"
            />
            <div v-else>
              <div
                v-for="event in analytics.upcoming_deadlines"
                :key="event.id"
                class="event-item"
              >
                <div class="event-info">
                  <span class="event-name">{{ event.name }}</span>
                  <el-tag
                    type="warning"
                    size="small"
                  >
                    {{ event.days_remaining }}天后
                  </el-tag>
                </div>
                <div class="event-meta">
                  截止: {{ formatDate(event.end_date) }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>TOP活跃负责人</h3>
            </div>
          </template>
          <div class="owner-list">
            <el-table
              :data="analytics.top_owners"
              stripe
              border
            >
              <el-table-column
                prop="username"
                label="负责人"
              />
              <el-table-column
                prop="event_count"
                label="活动数"
              />
              <el-table-column label="总预算">
                <template #default="{ row }">
                  ¥{{ formatNumber(row.total_budget) }}
                </template>
              </el-table-column>
              <el-table-column label="操作">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    link
                  >
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      style="margin-top: 20px"
    >
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>月度活动趋势</h3>
            </div>
          </template>
          <div class="trend-chart">
            <el-table
              :data="analytics.monthly_trend"
              stripe
              border
            >
              <el-table-column
                prop="month"
                label="月份"
              />
              <el-table-column
                prop="count"
                label="活动数"
              />
              <el-table-column label="预算">
                <template #default="{ row }">
                  ¥{{ formatNumber(row.total_budget) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div
      v-if="analytics.generated_at"
      class="update-time"
    >
      数据更新时间: {{ formatDateTime(analytics.generated_at) }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { apiClient } from '../api/client'

const loading = ref(false)
const dateRange = ref([])
const analytics = ref({
  overview: {},
  status_distribution: {},
  type_distribution: {},
  task_type_distribution: {},
  monthly_trend: [],
  high_risk_events: [],
  upcoming_deadlines: [],
  top_owners: [],
  generated_at: null
})

const statusMap = {
  planning: { label: '策划中', type: 'info' },
  executing: { label: '执行中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  reviewed: { label: '已复盘', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' }
}

const taskTypeMap = {
  planning: '策划',
  guest: '嘉宾',
  material: '物料',
  venue: '场地',
  promotion: '宣传',
  onsite: '现场',
  review: '复盘'
}

const statusTableData = computed(() => {
  return Object.entries(analytics.value.status_distribution || {}).map(([key, value]) => ({
    status: key,
    ...statusMap[key],
    ...value
  }))
})

const typeTableData = computed(() => {
  return Object.entries(analytics.value.type_distribution || {}).map(([key, value]) => ({
    type: key,
    ...value
  }))
})

const taskTypeTableData = computed(() => {
  return Object.entries(analytics.value.task_type_distribution || {}).map(([key, value]) => ({
    type: key,
    label: taskTypeMap[key] || key,
    ...value
  }))
})

const budgetVarianceClass = computed(() => {
  const variance = analytics.value.overview?.budget_variance || 0
  if (variance > 0) return 'text-success'
  if (variance < 0) return 'text-danger'
  return ''
})

const loadAnalytics = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (dateRange.value && dateRange.value.length === 2) {
      params.append('start_date_from', dateRange.value[0].toISOString().split('T')[0])
      params.append('start_date_to', dateRange.value[1].toISOString().split('T')[0])
    }

    const response = await apiClient.get(`/events/events/dashboard_analytics/?${params.toString()}`)
    if (response.data && typeof response.data === 'object') {
      analytics.value = response.data
    } else {
      analytics.value = response
    }
  } catch (error) {
    console.error('加载分析数据失败:', error)
    ElMessage.error('加载分析数据失败')
  } finally {
    loading.value = false
  }
}

const handleDateChange = () => {
  loadAnalytics()
}

const formatNumber = (num) => {
  if (!num) return 0
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.analytics-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
}

.chart-container {
  min-height: 200px;
}

.event-list {
  min-height: 150px;
}

.event-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.event-item:last-child {
  border-bottom: none;
}

.event-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.event-name {
  font-weight: 500;
  color: #333;
}

.event-meta {
  font-size: 13px;
  color: #666;
}

.budget-overview {
  padding: 10px 0;
}

.text-success {
  color: #67c23a;
  font-weight: bold;
}

.text-danger {
  color: #f56c6c;
  font-weight: bold;
}

.update-time {
  text-align: right;
  color: #999;
  font-size: 12px;
  margin-top: 20px;
  padding: 10px 0;
}
</style>
