<template>
  <div class="analytics-container">
    <div class="page-header">
      <h2>数据分析</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
        />
        <el-button type="primary" @click="loadAnalytics" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="error" class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="loadAnalytics">重试</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="analytics-content">
      <!-- 概览卡片 -->
      <el-row :gutter="20" class="overview-section">
        <el-col :span="6">
          <el-card class="stat-card total-events">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ analytics.overview?.total_events || 0 }}</div>
                <div class="stat-label">总活动数</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="stat-card total-tasks">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><List /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ analytics.overview?.total_tasks || 0 }}</div>
                <div class="stat-label">总任务数</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="stat-card completion-rate">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ analytics.overview?.task_completion_rate || 0 }}%</div>
                <div class="stat-label">任务完成率</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="stat-card budget-variance">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Money /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value" :class="{ 'negative': (analytics.overview?.budget_variance || 0) < 0 }">
                  {{ formatCurrency(analytics.overview?.budget_variance || 0) }}
                </div>
                <div class="stat-label">预算差异</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="charts-section">
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <h3>活动状态分布</h3>
              </div>
            </template>
            <div class="chart-container">
              <div v-if="Object.keys(analytics.status_distribution || {}).length > 0" class="status-charts">
                <div
                  v-for="(data, status) in analytics.status_distribution"
                  :key="status"
                  class="status-item"
                >
                  <div class="status-bar-wrapper">
                    <div
                      class="status-bar"
                      :class="`status-${status}`"
                      :style="{ width: data.percentage + '%' }"
                    ></div>
                  </div>
                  <div class="status-info">
                    <span class="status-name">{{ getStatusName(status) }}</span>
                    <span class="status-count">{{ data.count }} ({{ data.percentage }}%)</span>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <h3>活动类型分布</h3>
              </div>
            </template>
            <div class="chart-container">
              <div v-if="Object.keys(analytics.type_distribution || {}).length > 0" class="type-charts">
                <div
                  v-for="(data, type) in analytics.type_distribution"
                  :key="type"
                  class="type-item"
                >
                  <div class="type-bar-wrapper">
                    <div
                      class="type-bar"
                      :style="{ width: data.percentage + '%' }"
                    ></div>
                  </div>
                  <div class="type-info">
                    <span class="type-name">{{ data.name }}</span>
                    <span class="type-count">{{ data.count }} ({{ data.percentage }}%)</span>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 月度趋势 -->
      <el-row :gutter="20" class="trend-section">
        <el-col :span="24">
          <el-card class="trend-card">
            <template #header>
              <div class="card-header">
                <h3>月度趋势</h3>
              </div>
            </template>
            <div class="trend-container">
              <div v-if="analytics.monthly_trend && analytics.monthly_trend.length > 0" class="monthly-trend">
                <div
                  v-for="item in analytics.monthly_trend"
                  :key="item.month"
                  class="trend-item"
                >
                  <div class="trend-month">{{ item.month }}</div>
                  <div class="trend-bars">
                    <div class="trend-bar-wrapper">
                      <div
                        class="trend-bar count-bar"
                        :style="{ height: getTrendHeight(item.count, 'count') + '%' }"
                        :title="`活动数: ${item.count}`"
                      ></div>
                    </div>
                    <div class="trend-bar-wrapper">
                      <div
                        class="trend-bar budget-bar"
                        :style="{ height: getTrendHeight(item.total_budget, 'budget') + '%' }"
                        :title="`预算: ${formatCurrency(item.total_budget)}`"
                      ></div>
                    </div>
                  </div>
                  <div class="trend-values">
                    <span class="count-value">{{ item.count }}</span>
                    <span class="budget-value">{{ formatCurrency(item.total_budget) }}</span>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无趋势数据" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 预警信息 -->
      <el-row :gutter="20" class="alerts-section">
        <el-col :span="12">
          <el-card class="alert-card risk-alerts">
            <template #header>
              <div class="card-header">
                <h3>高风险活动</h3>
                <el-tag type="danger" size="small">
                  {{ analytics.high_risk_events?.length || 0 }} 个
                </el-tag>
              </div>
            </template>
            <div class="alert-list">
              <div
                v-for="event in analytics.high_risk_events"
                :key="event.id"
                class="alert-item risk"
              >
                <el-icon class="alert-icon"><Warning /></el-icon>
                <div class="alert-content">
                  <div class="alert-title">{{ event.name }}</div>
                  <div class="alert-desc">
                    风险因素: {{ event.factors_count }} 个
                  </div>
                </div>
                <el-tag type="danger" size="small">高风险</el-tag>
              </div>
              <el-empty v-if="!analytics.high_risk_events || analytics.high_risk_events.length === 0" description="暂无高风险活动" :image-size="60" />
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="alert-card deadline-alerts">
            <template #header>
              <div class="card-header">
                <h3>即将到期活动</h3>
                <el-tag type="warning" size="small">
                  {{ analytics.upcoming_deadlines?.length || 0 }} 个
                </el-tag>
              </div>
            </template>
            <div class="alert-list">
              <div
                v-for="event in analytics.upcoming_deadlines"
                :key="event.id"
                class="alert-item deadline"
              >
                <el-icon class="alert-icon"><Clock /></el-icon>
                <div class="alert-content">
                  <div class="alert-title">{{ event.name }}</div>
                  <div class="alert-desc">
                    剩余 {{ event.days_remaining }} 天
                  </div>
                </div>
                <el-tag
                  :type="event.days_remaining <= 3 ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ event.days_remaining }}天
                </el-tag>
              </div>
              <el-empty v-if="!analytics.upcoming_deadlines || analytics.upcoming_deadlines.length === 0" description="暂无即将到期活动" :image-size="60" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- TOP负责人和任务类型 -->
      <el-row :gutter="20" class="details-section">
        <el-col :span="12">
          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <h3>TOP活跃负责人</h3>
              </div>
            </template>
            <div class="owners-list">
              <div
                v-for="(owner, index) in analytics.top_owners"
                :key="owner.username"
                class="owner-item"
              >
                <div class="owner-rank" :class="{ 'top-three': index < 3 }">
                  {{ index + 1 }}
                </div>
                <div class="owner-info">
                  <div class="owner-name">{{ owner.username }}</div>
                  <div class="owner-stats">
                    <span>{{ owner.event_count }} 个活动</span>
                    <span>{{ formatCurrency(owner.total_budget) }} 预算</span>
                  </div>
                </div>
              </div>
              <el-empty v-if="!analytics.top_owners || analytics.top_owners.length === 0" description="暂无数据" :image-size="60" />
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <h3>任务类型分布</h3>
              </div>
            </template>
            <div class="task-types-list">
              <div
                v-for="(data, taskType) in analytics.task_type_distribution"
                :key="taskType"
                class="task-type-item"
              >
                <div class="task-type-name">{{ getTaskTypeName(taskType) }}</div>
                <div class="task-type-bar-wrapper">
                  <div
                    class="task-type-bar"
                    :style="{ width: data.percentage + '%' }"
                  ></div>
                </div>
                <div class="task-type-count">
                  {{ data.count }} ({{ data.percentage }}%)
                </div>
              </div>
              <el-empty v-if="!analytics.task_type_distribution || Object.keys(analytics.task_type_distribution).length === 0" description="暂无数据" :image-size="60" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Refresh,
  Calendar,
  List,
  CircleCheck,
  Money,
  Warning,
  Clock,
} from '@element-plus/icons-vue';
import { apiClient } from '@/api/client';

const loading = ref(false);
const error = ref<string | null>(null);
const dateRange = ref<[string, string] | null>(null);
const analytics = ref<any>({});

const loadAnalytics = async () => {
  loading.value = true;
  error.value = null;

  try {
    const params = new URLSearchParams();
    if (dateRange.value && dateRange.value.length === 2) {
      params.append('start_date_from', dateRange.value[0]);
      params.append('start_date_to', dateRange.value[1]);
    }

    const response = await apiClient.get(`/events/dashboard_analytics/?${params.toString()}`);
    
    if (response.data && typeof response.data === 'object') {
      analytics.value = response.data;
    } else {
      analytics.value = response;
    }

    ElMessage.success('数据加载成功');
  } catch (err: any) {
    console.error('加载分析数据失败:', err);
    error.value = err.message || '加载分析数据失败，请稍后重试';
    ElMessage.error(error.value);
  } finally {
    loading.value = false;
  }
};

const handleDateChange = () => {
  loadAnalytics();
};

const formatCurrency = (value: number): string => {
  if (!value && value !== 0) return '¥0.00';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const getStatusName = (status: string): string => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    planning: '计划中',
    executing: '执行中',
    completed: '已完成',
    cancelled: '已取消',
    paused: '已暂停',
  };
  return statusMap[status] || status;
};

const getTaskTypeName = (taskType: string): string => {
  const taskTypeMap: Record<string, string> = {
    preparation: '准备工作',
    execution: '执行工作',
    review: '审查工作',
    follow_up: '后续工作',
    other: '其他',
  };
  return taskTypeMap[taskType] || taskType;
};

const getTrendHeight = (value: number | undefined, type: 'count' | 'budget'): number => {
  if (!value) return 0;

  if (type === 'count') {
    const counts = analytics.value.monthly_trend?.map((item: any) => item.count) || [];
    const maxCount = Math.max(...counts, 1);
    return (value / maxCount) * 100;
  } else {
    const budgets = analytics.value.monthly_trend?.map((item: any) => item.total_budget) || [];
    const maxBudget = Math.max(...budgets, 1);
    return (value / maxBudget) * 100;
  }
};

onMounted(() => {
  loadAnalytics();
});
</script>

<style scoped>
.analytics-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.loading-container,
.error-container {
  padding: 40px;
}

.overview-section {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 16px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.total-events .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.total-tasks .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.completion-rate .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.budget-variance .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-value.negative {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.charts-section,
.trend-section,
.alerts-section,
.details-section {
  margin-bottom: 20px;
}

.chart-card,
.trend-card,
.alert-card,
.detail-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.chart-container {
  padding: 20px;
  min-height: 300px;
}

.status-charts,
.type-charts {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item,
.type-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-bar-wrapper,
.type-bar-wrapper {
  height: 24px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.status-bar,
.type-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.status-draft { background: #909399; }
.status-planning { background: #409eff; }
.status-executing { background: #67c23a; }
.status-completed { background: #e6a23c; }
.status-cancelled { background: #f56c6c; }
.status-paused { background: #909399; }

.type-bar {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
}

.status-info,
.type-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.status-name,
.type-name {
  color: #303133;
  font-weight: 500;
}

.status-count,
.type-count {
  color: #909399;
}

.trend-container {
  padding: 20px;
}

.monthly-trend {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 16px;
}

.trend-item {
  flex: 0 0 auto;
  width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.trend-month {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.trend-bars {
  display: flex;
  gap: 4px;
  align-items: flex-end;
  height: 150px;
}

.trend-bar-wrapper {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.trend-bar {
  width: 100%;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
  min-height: 4px;
}

.count-bar {
  background: #409eff;
}

.budget-bar {
  background: #67c23a;
}

.trend-values {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  text-align: center;
}

.count-value {
  color: #409eff;
  font-weight: 500;
}

.budget-value {
  color: #67c23a;
  font-size: 10px;
}

.alert-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #fafafa;
}

.alert-item.risk {
  background: #fef0f0;
  border-left: 4px solid #f56c6c;
}

.alert-item.deadline {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
}

.alert-icon {
  font-size: 20px;
  color: #f56c6c;
}

.alert-item.deadline .alert-icon {
  color: #e6a23c;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 12px;
  color: #909399;
}

.owners-list,
.task-types-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

.owner-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.owner-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #909399;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.owner-rank.top-three {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #303133;
}

.owner-info {
  flex: 1;
}

.owner-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.owner-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.task-type-item {
  display: grid;
  grid-template-columns: 100px 1fr 120px;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.task-type-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.task-type-bar-wrapper {
  height: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.task-type-bar {
  height: 100%;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.task-type-count {
  font-size: 13px;
  color: #909399;
  text-align: right;
}
</style>
