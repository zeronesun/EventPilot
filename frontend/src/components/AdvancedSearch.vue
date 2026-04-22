<!-- 高级搜索组件 -->
<template>
  <div class="advanced-search">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>高级搜索</h3>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form 
        ref="formRef" 
        :model="searchForm" 
        label-width="120px"
        @submit.prevent="performSearch"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="关键词">
              <el-input
                v-model="searchForm.query"
                placeholder="搜索档案名称、公司、行业等..."
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="档案类型">
              <el-select 
                v-model="searchForm.profile_type" 
                placeholder="选择档案类型" 
                clearable
                style="width: 100%"
              >
                <el-option label="客户" value="client" />
                <el-option label="供应商" value="supplier" />
                <el-option label="合作伙伴" value="partner" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="状态">
              <el-select 
                v-model="searchForm.status" 
                placeholder="选择状态" 
                clearable
                style="width: 100%"
              >
                <el-option label="活跃" value="active" />
                <el-option label="潜在" value="potential" />
                <el-option label="非活跃" value="inactive" />
                <el-option label="黑名单" value="blacklist" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="风险等级">
              <el-select 
                v-model="searchForm.risk_level" 
                placeholder="选择风险等级" 
                clearable
                style="width: 100%"
              >
                <el-option label="低风险" value="low" />
                <el-option label="中风险" value="medium" />
                <el-option label="高风险" value="high" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">评分筛选</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="信用评分范围">
              <div class="score-range">
                <el-slider
                  v-model="searchForm.credit_range"
                  range
                  :max="100"
                  :marks="{ 0: '0', 50: '50', 100: '100' }"
                />
                <span class="range-value">
                  {{ searchForm.credit_range[0] }} - {{ searchForm.credit_range[1] }}
                </span>
              </div>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="质量评分范围">
              <div class="score-range">
                <el-slider
                  v-model="searchForm.quality_range"
                  range
                  :max="100"
                  :marks="{ 0: '0', 50: '50', 100: '100' }"
                />
                <span class="range-value">
                  {{ searchForm.quality_range[0] }} - {{ searchForm.quality_range[1] }}
                </span>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">时间筛选</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="创建时间">
              <el-date-picker
                v-model="searchForm.created_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="最后联系时间">
              <el-date-picker
                v-model="searchForm.contact_range"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">其他筛选</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="行业">
              <el-input
                v-model="searchForm.industry"
                placeholder="搜索行业..."
                clearable
              >
                <template #prefix>
                  <el-icon><OfficeBuilding /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="标签">
              <el-input
                v-model="searchForm.tags"
                placeholder="搜索标签..."
                clearable
              >
                <template #prefix>
                  <el-icon><PriceTag /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item>
              <div class="search-actions">
                <el-button type="primary" @click="performSearch">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
                <el-button @click="resetSearch">
                  <el-icon><Refresh /></el-icon>
                  重置
                </el-button>
                <el-button @click="saveSearch">
                  <el-icon><Star /></el-icon>
                  保存搜索
                </el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 搜索结果 -->
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <div class="header-info">
            <h3>搜索结果</h3>
            <span v-if="!loading" class="results-count">
              找到 {{ results.length }} 个结果
            </span>
          </div>
          <div class="header-actions">
            <el-dropdown @command="handleSort">
              <el-button>
                排序方式
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="relevance">相关性</el-dropdown-item>
                  <el-dropdown-item command="credit">信用评分</el-dropdown-item>
                  <el-dropdown-item command="quality">质量评分</el-dropdown-item>
                  <el-dropdown-item command="date">创建时间</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="results-container">
        <el-empty v-if="!loading && results.length === 0" description="未找到匹配的档案">
          <el-button type="primary" @click="resetSearch">
            清除筛选条件
          </el-button>
        </el-empty>

        <div v-else class="results-grid">
          <div 
            v-for="result in results" 
            :key="result.profile_id"
            class="result-card"
            @click="viewResult(result)"
          >
            <div class="result-header">
              <h4>{{ result.name }}</h4>
              <el-tag 
                :type="getTypeColor(result.profile_type)" 
                size="small"
              >
                {{ getTypeLabel(result.profile_type) }}
              </el-tag>
            </div>

            <div v-if="result.company_name" class="result-company">
              {{ result.company_name }}
            </div>

            <div class="result-scores">
              <div class="score-item">
                <span class="score-label">信用:</span>
                <el-progress 
                  :percentage="result.credit_score" 
                  :color="getScoreColor(result.credit_score)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="score-value">{{ result.credit_score }}</span>
              </div>
              <div class="score-item">
                <span class="score-label">质量:</span>
                <el-progress 
                  :percentage="result.quality_score" 
                  :color="getScoreColor(result.quality_score)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="score-value">{{ result.quality_score }}</span>
              </div>
            </div>

            <div class="result-meta">
              <el-tag 
                :type="getStatusColor(result.status)" 
                size="small"
              >
                {{ getStatusLabel(result.status) }}
              </el-tag>
              <el-tag 
                :type="getRiskType(result.risk_level)" 
                size="small"
              >
                {{ getRiskLabel(result.risk_level) }}
              </el-tag>
            </div>

            <div class="result-relevance" v-if="result.relevance_score">
              <div class="relevance-label">相关度</div>
              <el-progress 
                :percentage="Math.round(result.relevance_score * 100)" 
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 保存搜索对话框 -->
    <el-dialog v-model="showSaveDialog" title="保存搜索条件" width="500px">
      <el-form ref="saveFormRef" :model="saveForm" label-width="100px">
        <el-form-item label="搜索名称" prop="name">
          <el-input 
            v-model="saveForm.name" 
            placeholder="为这个搜索条件命名"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            placeholder="添加备注说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import {
  Search, Refresh, Star, ArrowDown,
  OfficeBuilding, PriceTag
} from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores/profiles';
import type { SearchResult } from '@/lib/profiles-client';

const profilesStore = useProfilesStore();

// 响应式数据
const loading = ref(false);
const results = ref<SearchResult[]>([]);
const showSaveDialog = ref(false);

// 搜索表单
const searchForm = reactive({
  query: '',
  profile_type: '' as string,
  status: '' as string,
  risk_level: '' as string,
  credit_range: [0, 100],
  quality_range: [0, 100],
  created_range: [] as Date[],
  contact_range: [] as Date[],
  industry: '',
  tags: ''
});

// 保存表单
const saveForm = reactive({
  name: '',
  description: ''
});

// 排序方式
const sortMethod = ref('relevance');

// 执行搜索
const performSearch = async () => {
  loading.value = true;
  try {
    const searchParams: any = {};
    
    if (searchForm.query) {
      const response = await profilesStore.searchProfiles(
        searchForm.query,
        searchForm.profile_type as any
      );
      results.value = (response as any).results || [];
    } else {
      // 执行普通筛选
      const filters = {
        profile_type: searchForm.profile_type,
        status: searchForm.status,
        min_credit_score: searchForm.credit_range[0],
        max_credit_score: searchForm.credit_range[1],
        industry: searchForm.industry,
        search: searchForm.query
      };
      
      await profilesStore.fetchProfiles(filters);
      // 将profile转换为search result格式
      results.value = (profilesStore.profiles as any).map((profile: any) => ({
        profile_id: profile.id,
        name: profile.name,
        company_name: profile.company_name,
        profile_type: profile.profile_type,
        status: profile.status,
        credit_score: profile.credit_score,
        quality_score: profile.quality_score,
        risk_level: profile.risk_level,
        relevance_score: 0.5 // 默认相关度
      }));
    }
    
    // 应用排序
    applySorting();
    
  } catch (error) {
    console.error('搜索失败:', error);
    ElMessage.error('搜索失败');
  } finally {
    loading.value = false;
  }
};

// 应用排序
const applySorting = () => {
  results.value.sort((a, b) => {
    switch (sortMethod.value) {
      case 'credit':
        return b.credit_score - a.credit_score;
      case 'quality':
        return b.quality_score - a.quality_score;
      case 'date':
        return 0; // 需要返回日期字段才能排序
      case 'relevance':
      default:
        return (b.relevance_score || 0) - (a.relevance_score || 0);
    }
  });
};

// 处理排序
const handleSort = (method: string) => {
  sortMethod.value = method;
  applySorting();
};

// 重置搜索
const resetSearch = () => {
  searchForm.query = '';
  searchForm.profile_type = '';
  searchForm.status = '';
  searchForm.risk_level = '';
  searchForm.credit_range = [0, 100];
  searchForm.quality_range = [0, 100];
  searchForm.created_range = [];
  searchForm.contact_range = [];
  searchForm.industry = '';
  searchForm.tags = '';
  results.value = [];
};

// 保存搜索
const saveSearch = () => {
  showSaveDialog.value = true;
};

// 确认保存
const confirmSave = () => {
  if (!saveForm.name.trim()) {
    ElMessage.warning('请输入搜索名称');
    return;
  }
  
  // 将搜索条件保存到localStorage
  const savedSearches = JSON.parse(localStorage.getItem('savedSearches') || '[]');
  savedSearches.push({
    id: Date.now(),
    name: saveForm.name,
    description: saveForm.description,
    conditions: { ...searchForm },
    created_at: new Date().toISOString()
  });
  
  localStorage.setItem('savedSearches', JSON.stringify(savedSearches));
  
  ElMessage.success('搜索条件已保存');
  showSaveDialog.value = false;
  
  // 重置保存表单
  saveForm.name = '';
  saveForm.description = '';
};

// 查看结果
const viewResult = (result: SearchResult) => {
  // 跳转到档案详情
  ElMessage.info(`查看档案: ${result.name}`);
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

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'active': 'success',
    'potential': 'info',
    'inactive': 'warning',
    'blacklist': 'danger'
  };
  return colorMap[status] || 'info';
};

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'active': '活跃',
    'potential': '潜在',
    'inactive': '非活跃',
    'blacklist': '黑名单'
  };
  return labelMap[status] || status;
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
</script>

<style scoped>
.advanced-search {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-info h3 {
  margin: 0;
}

.results-count {
  font-size: 14px;
  color: #606266;
}

.search-actions {
  display: flex;
  gap: 12px;
}

.score-range {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.range-value {
  font-size: 12px;
  color: #909399;
}

.results-card {
  margin-top: 20px;
}

.results-container {
  min-height: 400px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.result-card {
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.result-company {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.result-scores {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  width: 40px;
  font-size: 12px;
  color: #909399;
}

.score-value {
  font-weight: 500;
  color: #303133;
  min-width: 30px;
}

.result-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.result-relevance {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.relevance-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
</style>
