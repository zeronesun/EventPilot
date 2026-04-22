<!-- 智能推荐组件 -->
<template>
  <div class="recommendations-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>智能推荐引擎</h3>
          <el-button type="primary" @click="resetRecommendations">
            <el-icon><Refresh /></el-icon>
            重新推荐
          </el-button>
        </div>
      </template>

      <!-- 推荐配置 -->
      <div class="recommendation-config">
        <el-form :model="config" label-width="120px" inline>
          <el-form-item label="活动类型">
            <el-input 
              v-model="config.event_type" 
              placeholder="例如：大型商务会议"
              clearable
            />
          </el-form-item>

          <el-form-item label="最低信用分">
            <el-slider 
              v-model="config.min_credit_score" 
              :max="100"
              :marks="{ 0: '0', 50: '50', 100: '100' }"
            />
          </el-form-item>

          <el-form-item label="风险等级">
            <el-select v-model="config.max_risk_level" placeholder="选择最大风险等级">
              <el-option label="低风险" value="low" />
              <el-option label="中风险" value="medium" />
              <el-option label="高风险" value="high" />
            </el-select>
          </el-form-item>

          <el-form-item label="推荐数量">
            <el-input-number 
              v-model="config.limit" 
              :min="5" 
              :max="20" 
              :step="5"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="getRecommendations">
              <el-icon><Search /></el-icon>
              获取推荐
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 推荐结果 -->
      <div v-loading="loading" class="recommendations-results">
        <el-empty v-if="!loading && recommendations.length === 0" description="暂无推荐结果">
          <el-button type="primary" @click="getRecommendations">
            开始推荐
          </el-button>
        </el-empty>

        <div v-else class="recommendations-list">
          <div 
            v-for="(recommendation, index) in recommendations" 
            :key="recommendation.profile_id"
            class="recommendation-card"
            :class="{ 'top-recommendation': index === 0 }"
          >
            <!-- 推荐排名 -->
            <div class="recommendation-rank">
              <div v-if="index === 0" class="rank-first">
                <el-icon><Trophy /></el-icon>
                No.1
              </div>
              <div v-else class="rank-normal">
                No.{{ index + 1 }}
              </div>
            </div>

            <!-- 推荐分数 -->
            <div class="recommendation-score">
              <div class="score-value">
                {{ recommendation.recommendation_score }}
              </div>
              <div class="score-label">推荐分数</div>
              <div class="score-bar">
                <el-progress 
                  :percentage="Math.min(recommendation.recommendation_score, 100)"
                  :color="getScoreColor(recommendation.recommendation_score)"
                  :show-text="false"
                />
              </div>
            </div>

            <!-- 档案信息 -->
            <div class="recommendation-profile">
              <div class="profile-header">
                <h4>{{ recommendation.name }}</h4>
                <el-tag 
                  :type="getTypeColor(recommendation.profile_type)" 
                  size="small"
                >
                  {{ getTypeLabel(recommendation.profile_type) }}
                </el-tag>
              </div>
              
              <div v-if="recommendation.company_name" class="profile-company">
                {{ recommendation.company_name }}
              </div>

              <div class="profile-details">
                <div class="detail-item">
                  <span class="detail-label">信用评分:</span>
                  <el-progress 
                    :percentage="recommendation.credit_score" 
                    :color="getScoreColor(recommendation.credit_score)"
                    :stroke-width="6"
                    :show-text="false"
                  />
                  <span class="detail-value">{{ recommendation.credit_score }}</span>
                </div>
                
                <div class="detail-item">
                  <span class="detail-label">质量评分:</span>
                  <el-progress 
                    :percentage="recommendation.quality_score" 
                    :color="getScoreColor(recommendation.quality_score)"
                    :stroke-width="6"
                    :show-text="false"
                  />
                  <span class="detail-value">{{ recommendation.quality_score }}</span>
                </div>

                <div class="detail-item">
                  <span class="detail-label">风险等级:</span>
                  <el-tag :type="getRiskType(recommendation.risk_level)" size="small">
                    {{ getRiskLabel(recommendation.risk_level) }}
                  </el-tag>
                </div>

                <div v-if="recommendation.primary_contact" class="detail-item">
                  <span class="detail-label">主要联系人:</span>
                  <span class="detail-value">{{ recommendation.primary_contact }}</span>
                </div>
              </div>

              <!-- 推荐原因 -->
              <div class="recommendation-reasons">
                <div class="reasons-label">
                  <el-icon><Document /></el-icon>
                  推荐原因
                </div>
                <div class="reasons-list">
                  <el-tag
                    v-for="reason in recommendation.reasons"
                    :key="reason"
                    size="small"
                    type="info"
                    class="reason-tag"
                  >
                    {{ reason }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="recommendation-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="viewProfile(recommendation)"
              >
                查看详情
              </el-button>
              <el-button 
                size="small" 
                @click="viewContacts(recommendation)"
              >
                联系方式
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click="selectSupplier(recommendation)"
              >
                合作
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 推荐条件预设 -->
    <el-card class="presets-card">
      <template #header>
        <div class="card-header">
          <h3>快速预设</h3>
        </div>
      </template>

      <div class="presets-grid">
        <div 
          v-for="preset in presets" 
          :key="preset.name"
          class="preset-item"
          @click="applyPreset(preset)"
        >
          <div class="preset-icon">
            <el-icon :size="24"><component :is="preset.icon" /></el-icon>
          </div>
          <div class="preset-info">
            <h4>{{ preset.name }}</h4>
            <p>{{ preset.description }}</p>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Refresh, Search, Trophy,
  FolderOpened, DocumentChecked,
  Briefcase, Star, Monitor
} from '@element-plus/icons-vue';
import { profilesApi, type RecommendationResult, type RecommendationRequest } from '@/lib/profiles-client';

// 默认配置
const defaultConfig: RecommendationRequest = {
  event_type: '',
  min_credit_score: 60,
  max_risk_level: 'medium',
  limit: 10
};

// 响应式数据
const loading = ref(true);
const config = ref<RecommendationRequest>({ ...defaultConfig });
const recommendations = ref<RecommendationResult[]>([]);

// 预设配置
const presets = [
  {
    name: '高标准供应商',
    description: '信用80+，低风险，优质服务',
    config: {
      event_type: '重大项目合作',
      min_credit_score: 80,
      max_risk_level: 'low' as const,
      limit: 5
    },
    icon: Star
  },
  {
    name: '风险可控型',
    description: '信用60+，中等风险为主',
    config: {
      event_type: '常规项目合作',
      min_credit_score: 60,
      max_risk_level: 'medium' as const,
      limit: 10
    },
    icon: DocumentChecked
  },
  {
    name: '成本优先型',
    description: '信用40+，可接受高风险',
    config: {
      event_type: '成本敏感项目',
      min_credit_score: 40,
      max_risk_level: 'high' as const,
      limit: 15
    },
    icon: Briefcase
  },
  {
    name: '紧急响应型',
    description: '信用70+，响应速度优先',
    config: {
      event_type: '紧急项目',
      min_credit_score: 70,
      max_risk_level: 'low' as const,
      limit: 8
    },
    icon: Monitor
  }
];

// 获取推荐结果
const getRecommendations = async () => {
  loading.value = true;
  try {
    const response = await profilesApi.recommendSuppliers(config.value);
    recommendations.value = (response as any).recommendations || [];
    
    if (recommendations.value.length === 0) {
      ElMessage.warning('未找到符合条件的推荐');
    } else {
      ElMessage.success(`找到 ${recommendations.value.length} 个推荐`);
    }
  } catch (error) {
    console.error('获取推荐失败:', error);
    ElMessage.error('获取推荐失败');
  } finally {
    loading.value = false;
  }
};

// 重置推荐
const resetRecommendations = () => {
  config.value = { ...defaultConfig };
  recommendations.value = [];
  getRecommendations();
};

// 应用预设
const applyPreset = (preset: typeof presets[0]) => {
  config.value = { ...preset.config };
  getRecommendations();
};

// 获取分数颜色
const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A';
  if (score >= 60) return '#409EFF';
  if (score >= 40) return '#E6A23C';
  return '#F56C6C';
};

// 获取类型颜色
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'client': 'success',
    'supplier': 'warning',
    'partner': 'primary'
  };
  return colorMap[type] || 'info';
};

// 获取类型标签
const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'client': '客户',
    'supplier': '供应商',
    'partner': '合作伙伴'
  };
  return labelMap[type] || type;
};

// 获取风险类型
const getRiskType = (level: string) => {
  const typeMap: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger'
  };
  return typeMap[level] || 'info';
};

// 获取风险标签
const getRiskLabel = (level: string) => {
  const labelMap: Record<string, string> = {
    'low': '低风险',
    'medium': '中风险',
    'high': '高风险'
  };
  return labelMap[level] || level;
};

// 查看档案详情
const viewProfile = (recommendation: RecommendationResult) => {
  // 这里应该跳转到档案详情页面
  ElMessage.info(`查看档案: ${recommendation.name}`);
};

// 查看联系方式
const viewContacts = (recommendation: RecommendationResult) => {
  ElMessage.info(`查看联系方式: ${recommendation.name}`);
};

// 选择供应商
const selectSupplier = (recommendation: RecommendationResult) => {
  ElMessage.success(`已选择供应商: ${recommendation.name}`);
};

// 组件挂载时获取推荐
onMounted(() => {
  getRecommendations();
});
</script>

<style scoped>
.recommendations-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendation-config {
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.recommendations-results {
  min-height: 400px;
}

.recommendations-list {
  display: grid;
  gap: 20px;
}

.recommendation-card {
  display: grid;
  grid-template-columns: 80px 150px 1fr auto;
  gap: 20px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s;
}

.recommendation-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.recommendation-card.top-recommendation {
  border-color: #409EFF;
  background: linear-gradient(135deg, #f5f7ff 0%, #ffffff 100%);
}

.recommendation-rank {
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank-first {
  width: 60px;
  height: 60px;
  background: #f0f9ff;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #409EFF;
  font-size: 14px;
}

.rank-first .el-icon {
  font-size: 20px;
  margin-bottom: 4px;
  color: #FFD700;
}

.rank-normal {
  width: 60px;
  height: 60px;
  background: #f5f7fa;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #606266;
  font-size: 14px;
}

.recommendation-score {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-bar {
  width: 100%;
}

.recommendation-profile {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-header h4 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.profile-company {
  font-size: 14px;
  color: #606266;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.detail-label {
  width: 80px;
  color: #909399;
}

.detail-value {
  font-weight: 500;
  color: #303133;
}

.recommendation-reasons {
  margin-top: 8px;
}

.reasons-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.reasons-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reason-tag {
  font-size: 12px;
}

.recommendation-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.presets-card {
  margin-top: 20px;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.preset-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.preset-item:hover {
  border-color: #409EFF;
  background: #f5f7ff;
}

.preset-icon {
  width: 48px;
  height: 48px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409EFF;
}

.preset-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
}

.preset-info p {
  margin: 0;
  font-size: 12px;
  color: #909399;
}
</style>