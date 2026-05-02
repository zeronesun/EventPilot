<template>
  <div class="profiles-page">
    <div class="page-header">
      <h1>关联方档案管理</h1>
      <div class="header-actions">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建档案
        </el-button>
      </div>
    </div>

    <!-- 仪表盘统计 -->
    <div class="dashboard-stats" v-if="dashboardStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-number">{{ dashboardStats.total_profiles || 0 }}</div>
              <div class="stat-label">总档案数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-number">{{ dashboardStats.high_score_count || 0 }}</div>
              <div class="stat-label">高评分档案</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card stat-warning">
              <div class="stat-number">{{ dashboardStats.high_risk_count || 0 }}</div>
              <div class="stat-label">高风险档案</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-number">{{ dashboardStats.recent_interactions || 0 }}</div>
              <div class="stat-label">近期交互</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-form :inline="true" :model="searchForm">
        <el-form-item>
          <el-input
            v-model="searchForm.search"
            placeholder="搜索档案名称、公司、行业..."
            clearable
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-select v-model="searchForm.profile_type" placeholder="档案类型" clearable>
            <el-option label="客户" value="client" />
            <el-option label="供应商" value="supplier" />
            <el-option label="合作伙伴" value="partner" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="searchForm.status" placeholder="状态" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="潜在" value="prospective" />
            <el-option label="非活跃" value="inactive" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 档案列表 -->
    <div class="profiles-list">
      <el-table
        :data="profiles"
        v-loading="loading"
        @row-click="handleRowClick"
        style="cursor: pointer"
      >
        <el-table-column prop="profile_type_display" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getProfileTypeColor(row.profile_type)">
              {{ row.profile_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="company_name" label="公司名称" min-width="180" />
        <el-table-column label="综合评分" width="100" align="center">
          <template #default="{ row }">
            <div :class="getScoreClass(row.aggregate_score)">
              {{ row.aggregate_score || 0 }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level_display" label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getRiskTypeColor(row.risk_level)" size="small">
              {{ row.risk_level_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTypeColor(row.status)" size="small">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="viewProfile(row.id)">
              查看详情
            </el-button>
            <el-button link type="primary" @click.stop="editProfile(row.id)">
              编辑
            </el-button>
            <el-button 
              link 
              type="danger" 
              @click.stop="deleteProfile(row.id)"
              v-if="!row.is_deleted"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEditing ? '编辑档案' : '新建档案'"
      width="600px"
    >
      <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="120px">
        <el-form-item label="档案类型" prop="profile_type">
          <el-select v-model="profileForm.profile_type" placeholder="请选择档案类型">
            <el-option label="客户" value="client" />
            <el-option label="供应商" value="supplier" />
            <el-option label="合作伙伴" value="partner" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="profileForm.name" placeholder="请输入档案名称" />
        </el-form-item>
        <el-form-item label="公司名称">
          <el-input v-model="profileForm.company_name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="行业">
          <el-input v-model="profileForm.industry" placeholder="请输入行业" />
        </el-form-item>
        <el-form-item label="信用评分">
          <el-input-number v-model="profileForm.credit_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="质量评分">
          <el-input-number v-model="profileForm.quality_score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="profileForm.risk_level" placeholder="请选择风险等级">
            <el-option label="低风险" value="low" />
            <el-option label="中风险" value="medium" />
            <el-option label="高风险" value="high" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="profileForm.status" placeholder="请选择状态">
            <el-option label="潜在" value="prospective" />
            <el-option label="活跃" value="active" />
            <el-option label="非活跃" value="inactive" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitProfile" :loading="submitLoading">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onActivated } from 'vue';
import { Plus, Refresh, Search } from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { ContactProfile, ProfileType } from '@/lib/profiles-client';

const profilesStore = useProfilesStore();

const loading = computed(() => profilesStore.loading);
const profiles = computed(() => profilesStore.profiles || []);
const dashboardStats = computed(() => profilesStore.dashboardStats);

const showCreateDialog = ref(false);
const isEditing = ref(false);
const submitLoading = ref(false);
const profileFormRef = ref();

const searchForm = reactive({
  search: '',
  profile_type: undefined as ProfileType | undefined,
  status: undefined as string | undefined
});

const profileForm = reactive({
  id: '',
  profile_type: 'client' as ProfileType,
  name: '',
  company_name: '',
  industry: '',
  credit_score: 0,
  quality_score: 0,
  risk_level: 'medium',
  status: 'prospective'
});

const profileRules = {
  profile_type: [{ required: true, message: '请选择档案类型', trigger: 'change' }],
  name: [{ required: true, message: '请输入档案名称', trigger: 'blur' }]
};

async function refreshData() {
  await profilesStore.fetchProfiles();
  await profilesStore.getDashboardStats();
  ElMessage.success('数据已刷新');
}

onMounted(async () => {
  await refreshData();
});

onActivated(async () => {
  await refreshData();
});

async function handleSearch() {
  await profilesStore.fetchProfiles({
    search: searchForm.search,
    profile_type: searchForm.profile_type,
    status: searchForm.status
  });
}

function handleCreate() {
  resetForm();
  showCreateDialog.value = true;
}

function handleRowClick(row: ContactProfile) {
  viewProfile(row.id);
}

async function viewProfile(id: string) {
  await profilesStore.selectProfile(id);
  ElMessage.success('查看档案详情');
}

async function editProfile(id: string) {
  const profile = profiles.value.find(p => p.id === id);
  if (profile) {
    Object.assign(profileForm, {
      id: profile.id,
      profile_type: profile.profile_type,
      name: profile.name,
      company_name: profile.company_name || '',
      industry: profile.industry || '',
      credit_score: profile.credit_score,
      quality_score: profile.quality_score,
      risk_level: profile.risk_level,
      status: profile.status
    });
    isEditing.value = true;
    showCreateDialog.value = true;
  }
}

async function deleteProfile(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这个档案吗？', '删除确认', {
      type: 'warning'
    });
    
    const success = await profilesStore.deleteProfile(id);
    if (success) {
      ElMessage.success('删除成功');
    }
  } catch (err: any) {
    console.error('Delete error:', err);
  }
}

async function submitProfile() {
  const form = profileFormRef.value;
  if (!form) return;
  
  await form.validate();
  
  submitLoading.value = true;
  try {
    if (isEditing.value) {
      await profilesStore.updateProfile(profileForm.id, profileForm);
      ElMessage.success('更新成功');
    } else {
      await profilesStore.createProfile(profileForm);
      ElMessage.success('创建成功');
    }
    showCreateDialog.value = false;
    resetForm();
  } catch (err: any) {
    console.error('Submit error:', err);
  } finally {
    submitLoading.value = false;
  }
}

function resetForm() {
  Object.assign(profileForm, {
    id: '',
    profile_type: 'client',
    name: '',
    company_name: '',
    industry: '',
    credit_score: 0,
    quality_score: 0,
    risk_level: 'medium',
    status: 'prospective'
  });
  isEditing.value = false;
}

function formatDate(dateString: string | undefined) {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function getProfileTypeColor(type: string) {
  const colors: Record<string, any> = {
    client: 'primary',
    supplier: 'success',
    partner: 'warning'
  };
  return colors[type] || '';
}

function getRiskTypeColor(risk: string) {
  const colors: Record<string, any> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  };
  return colors[risk] || 'info';
}

function getStatusTypeColor(status: string) {
  const colors: Record<string, any> = {
    active: 'success',
    prospective: 'info',
    inactive: 'warning',
    blacklisted: 'danger'
  };
  return colors[status] || '';
}

function getScoreClass(score: number) {
  if (score >= 80) return 'stat-excellent';
  if (score >= 60) return 'stat-good';
  if (score >= 40) return 'stat-average';
  return 'stat-poor';
}
</script>

<style scoped>
.profiles-page {
  padding: 20px;
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

.header-actions {
  display: flex;
  gap: 10px;
}

.dashboard-stats {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-warning {
  color: #f56c6c;
}

.stat-excellent {
  color: #67c23a;
}

.stat-good {
  color: #409eff;
}

.stat-average {
  color: #e6a23c;
}

.stat-poor {
  color: #f56c6c;
}

.toolbar {
  margin-bottom: 20px;
}

.profiles-list {
  background: #fff;
  border-radius: 4px;
}
</style>
