<!-- 数据仪表盘组件 -->
<template>
  <div class="analytics-dashboard">
    <!-- 概览卡片 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="stat-card total-profiles">
          <div class="card-content">
            <div class="card-icon">
              <el-icon><User /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ dashboard.total_profiles }}</div>
              <div class="card-label">总档案数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card active-profiles">
          <div class="card-content">
            <div class="card-icon">
              <el-icon><Star /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ activeCount }}</div>
              <div class="card-label">活跃档案</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card high-score">
          <div class="card-content">
            <div class="card-icon">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ dashboard.high_score_count }}</div>
              <div class="card-label">高分档案</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card risk-alert">
          <div class="card-content">
            <div class="card-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-value">{{ dashboard.high_risk_count }}</div>
              <div class="card-label">高风险档案</div>
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
              <h3>档案分布</h3>
            </div>
          </template>
          <div class="chart-container">
            <div class="pie-chart">
              <el-pie-chart :data="pieData" style="height: 400px" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>评分统计</h3>
            </div>
          </template>
          <div class="chart-container">
            <div class="bar-chart">
              <el-bar-chart :data="barData" style="height: 400px" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-section">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>风险等级分布</h3>
            </div>
          </template>
          <div class="chart-container">
            <div class="donut-chart">
              <el-pie-chart :data="riskData" style="height: 400px" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>活动分析</h3>
            </div>
          </template>
          <div class="chart-container">
            <div class="line-chart">
              <el-line-chart :data="lineData" style="height: 400px" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细统计表格 -->
    <el-row :gutter="20" class="details-section">
      <el-col :span="24">
        <el-card class="details-card">
          <template #header>
            <div class="card-header">
              <h3>详细统计</h3>
              <el-button @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <el-table :data="detailStats" stripe>
            <el-table-column prop="category" label="类别" width="120" />
            <el-table-column prop="client" label="客户" width="100" />
            <el-table-column prop="supplier" label="供应商" width="100" />
            <el-table-column prop="partner" label="合作伙伴" width="100" />
            <el-table-column prop="total" label="总计" width="100" />
            <el-table-column prop="percentage" label="占比" width="100">
              <template #default="{ row }">
                {{ row.percentage }}%
              </template>
            </el-table-column>
            <el-table-column prop="trend" label="趋势" width="80">
              <template #default="{ row }">
                <el-icon v-if="row.trend === 'up'" color="#67C23A">
                  <Trend-up />
                </el-icon>
                <el-icon v-else-if="row.trend === 'down'" color="#F56C6C">
                  <Trend-down />
                </el-icon>
                <el-icon v-else color="#909399">
                  <Trend-up />
                </el-icon>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动和预警 -->
    <el-row :gutter="20" class="activity-section">
      <el-col :span="12">
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <h3>最近交互</h3>
              <el-tag type="info">{{ dashboard.recent_interactions }} 次</el-tag>
            </div>
          </template>
          <div class="activity-list">
            <div v-for="i in 5" :key="i" class="activity-item">
              <div class="activity-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="activity-details">
                <div class="activity-title">合同签署 - 测试公司 {{ i }}</div>
                <div class="activity-time">{{ i }} 小时前</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <h3>风险预警</h3>
              <el-tag type="warning">{{ dashboard.high_risk_count }} 个</el-tag>
            </div>
          </template>
          <div class="alerts-list">
            <div v-for="i in 3" :key="i" class="alert-item warning">
              <el-icon><Warning-filled /></el-icon>
              <div class="alert-details">
                <div class="alert-title">风险档案 - 测试公司 {{ i }}</div>
                <div class="alert-desc">信用评分下降至 55，建议跟进</div>
              </div>
              <el-button size="small" type="text">处理</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  User, Star, Trophy, Warning, Refresh, Document,
  Trend-up, Trend-down, Warning-filled
} from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores/profiles';
import type { AnalyticsDashboard } from '@/lib/profiles-client';

const profilesStore = useProfilesStore();

// 响应式数据
const dashboard = ref<AnalyticsDashboard>({
  total_profiles: 0,
  by_type: {},
  by_status: {},
  average_scores: {
    credit: 0,
    quality: 0
  },
  risk_distribution: {},
  recent_interactions: 0,
  high_risk_count: 0,
  high_score_count: 0
});

// 计算活跃档案数量
const activeCount = computed(() => {
  return dashboard.value.by_status.active || 0;
});

// 饼图数据
const pieData = computed(() => {
  const data = [];
  const types = ['client', 'supplier', 'partner'];
  const labels = ['客户', '供应商', '合作伙伴'];
  const colors = ['#67C23A', '#409EFF', '#E6A23C'];

  types.forEach((type, index) => {
    const count = dashboard.value.by_type[type] || 0;
    if (count > 0) {
      data.push({
        name: labels[index],
        value: count,
        itemStyle: {
          color: colors[index]
        }
      });
    }
  });

  return data;
});

// 柱状图数据
const barData = computed(() => {
  const data = [
    {
      name: '信用评分',
      value: dashboard.value.average_scores.credit,
      itemStyle: { color: '#409EFF' }
    },
    {
      name: '质量评分', 
      value: dashboard.value.average_scores.quality,
      itemStyle: { color: '#67C23A' }
    }
  ];
  return data;
});

// 风险数据
const riskData = computed(() => {
  const data = [];
  const levels = ['low', 'medium', 'high'];
  const labels = ['低风险', '中风险', '高风险'];
  const colors = ['#67C23A', '#E6A23C', '#F56C6C'];

  levels.forEach((level, index) => {
    const count = dashboard.value.risk_distribution[level] || 0;
    if (count > 0) {
      data.push({
        name: labels[index],
        value: count,
        itemStyle: {
          color: colors[index]
        }
      });
    }
  });

  return data;
});

// 折线图数据（模拟数据）
const lineData = computed(() => {
  return {
    categories: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    series: [
      {
        name: '新增档案',
        data: [12, 19, 3, 5, 2, 3, 8],
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '交互次数',
        data: [45, 32, 67, 23, 89, 56, 78],
        itemStyle: { color: '#67C23A' }
      }
    ]
  };
});

// 详细统计数据
const detailStats = computed(() => {
  const stats = [
    {
      category: '按类型',
      client: dashboard.value.by_type.client || 0,
      supplier: dashboard.value.by_type.supplier || 0,
      partner: dashboard.value.by_type.partner || 0,
      total: dashboard.value.total_profiles,
      percentage: 100,
      trend: 'up'
    },
    {
      category: '按状态',
      client: dashboard.value.by_status.active || 0,
      supplier: dashboard.value.by_status.potential || 0,
      partner: dashboard.value.by_status.inactive || 0,
      total: dashboard.value.total_profiles,
      percentage: 100,
      trend: 'up'
    },
    {
      category: '高分档案',
      client: Math.floor((dashboard.value.by_type.client || 0) * 0.7),
      supplier: Math.floor((dashboard.value.by_type.supplier || 0) * 0.6),
      partner: Math.floor((dashboard.value.by_type.partner || 0) * 0.8),
      total: dashboard.value.high_score_count,
      percentage: Math.round((dashboard.value.high_score_count / dashboard.value.total_profiles) * 100),
      trend: 'up'
    }
  ];

  return stats;
});

// 加载仪表盘数据
const loadDashboardData = async () => {
  try {
    const stats = await profilesStore.getDashboardStats();
    if (stats) {
      dashboard.value = stats;
    }
  } catch (error) {
    console.error('加载仪表盘数据失败:', error);
    ElMessage.error('加载仪表盘数据失败');
  }
};

// 刷新数据
const refreshData = () => {
  loadDashboardData();
  ElMessage.success('数据已刷新');
};

// 组件挂载时加载数据
onMounted(() => {
  loadDashboardData();
});
</script>

<style scoped>
.analytics-dashboard {
  padding: 20px;
}

.overview-cards, .charts-section, .details-section, .activity-section {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-card.total-profiles .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.active-profiles .card-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.high-score .card-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.risk-alert .card-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

.chart-card {
  height: 500px;
}

.chart-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.chart-card .chart-header {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
}

.activity-card, .alerts-card {
  height: 400px;
}

.activity-list, .alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.activity-icon {
  width: 40px;
  height: 40px;
  background: #409EFF;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.activity-details {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fef0f0;
  border-radius: 4px;
  border-left: 4px solid #F56C6C;
}

.alert-item.warning {
  background: #fef9f0;
  border-left-color: #E6A23C;
}

.alert-details {
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
</style>