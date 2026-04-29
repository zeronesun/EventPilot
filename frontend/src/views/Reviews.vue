<template>
  <div class="reviews-container">
    <div class="page-header">
      <h1>复盘管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建复盘
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.total }}</div>
          <div class="stat-label">总复盘数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.drafts }}</div>
          <div class="stat-label">草稿</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.inProgress }}</div>
          <div class="stat-label">进行中</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.completed }}</div>
          <div class="stat-label">已完成</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card" style="margin-top: 20px">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input v-model="searchQuery" placeholder="搜索复盘..." clearable @input="handleSearch">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterStatus" placeholder="状态" clearable @change="handleSearch">
            <el-option label="全部状态" value="" />
            <el-option label="草稿" value="draft" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card" style="margin-top: 20px">
      <el-table :data="reviews" v-loading="loading" stripe border>
        <el-table-column prop="title" label="复盘标题" min-width="200">
          <template #default="{ row }">
            <div class="review-title" @click="viewReview(row)">
              {{ row.title }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="event_name" label="关联活动" width="150">
          <template #default="{ row }">
            {{ row.event_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="160">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editReview(row)">编辑</el-button>
            <el-button type="success" size="small" @click="completeReview(row)" v-if="row.status !== 'completed'">
              完成
            </el-button>
            <el-button type="danger" size="small" @click="deleteReview(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="loadReviews"
        @current-change="loadReviews"
      />
    </el-card>

    <el-dialog v-model="showCreateDialog" :title="editingReview ? '编辑复盘' : '新建复盘'" width="800px">
      <el-form :model="reviewForm" :rules="reviewRules" ref="reviewFormRef" label-width="120px">
        <el-form-item label="复盘标题" prop="title">
          <el-input v-model="reviewForm.title" placeholder="请输入复盘标题" />
        </el-form-item>
        <el-form-item label="关联活动" prop="event">
          <el-select v-model="reviewForm.event" placeholder="请选择关联活动" filterable>
            <el-option v-for="event in events" :key="event.id" :label="event.name" :value="event.id" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">复盘维度</el-divider>
        <el-form-item label="目标达成">
          <el-input v-model="reviewForm.goal_achievement" type="textarea" :rows="3" placeholder="请描述目标达成情况" />
        </el-form-item>
        <el-form-item label="流程执行">
          <el-input v-model="reviewForm.process_execution" type="textarea" :rows="3" placeholder="请描述流程执行情况" />
        </el-form-item>
        <el-form-item label="成本控制">
          <el-input v-model="reviewForm.cost_control" type="textarea" :rows="3" placeholder="请描述成本控制情况" />
        </el-form-item>
        <el-form-item label="客户反馈">
          <el-input v-model="reviewForm.customer_feedback" type="textarea" :rows="3" placeholder="请描述客户反馈" />
        </el-form-item>
        <el-form-item label="团队协作">
          <el-input v-model="reviewForm.team_collaboration" type="textarea" :rows="3" placeholder="请描述团队协作情况" />
        </el-form-item>
        <el-divider content-position="left">总结与改进</el-divider>
        <el-form-item label="成功经验">
          <el-input v-model="reviewForm.successes" type="textarea" :rows="3" placeholder="请总结成功经验" />
        </el-form-item>
        <el-form-item label="待改进项">
          <el-input v-model="reviewForm.improvements" type="textarea" :rows="3" placeholder="请列出待改进项" />
        </el-form-item>
        <el-form-item label="行动项">
          <el-input v-model="reviewForm.action_items" type="textarea" :rows="3" placeholder="请列出后续行动项" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveReview">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="复盘详情" width="800px">
      <template v-if="currentReview">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="复盘标题" :span="2">{{ currentReview.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTag(currentReview.status)">{{ getStatusText(currentReview.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentReview.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">复盘维度</el-divider>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="目标达成">
            <div style="white-space: pre-wrap">{{ currentReview.goal_achievement || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="流程执行">
            <div style="white-space: pre-wrap">{{ currentReview.process_execution || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="成本控制">
            <div style="white-space: pre-wrap">{{ currentReview.cost_control || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="客户反馈">
            <div style="white-space: pre-wrap">{{ currentReview.customer_feedback || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="团队协作">
            <div style="white-space: pre-wrap">{{ currentReview.team_collaboration || '未填写' }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">总结与改进</el-divider>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="成功经验">
            <div style="white-space: pre-wrap">{{ currentReview.successes || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="待改进项">
            <div style="white-space: pre-wrap">{{ currentReview.improvements || '未填写' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="行动项">
            <div style="white-space: pre-wrap">{{ currentReview.action_items || '未填写' }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { apiClient } from '../api/client'

const loading = ref(false)
const reviews = ref([])
const events = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterStatus = ref('')

const statistics = computed(() => {
  const stats = { total: total.value, drafts: 0, inProgress: 0, completed: 0 }
  reviews.value.forEach(r => {
    if (r.status === 'draft') stats.drafts++
    else if (r.status === 'in_progress') stats.inProgress++
    else if (r.status === 'completed') stats.completed++
  })
  return stats
})

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const editingReview = ref(null)
const currentReview = ref(null)
const reviewFormRef = ref()

const reviewForm = reactive({
  title: '',
  event: '',
  goal_achievement: '',
  process_execution: '',
  cost_control: '',
  customer_feedback: '',
  team_collaboration: '',
  successes: '',
  improvements: '',
  action_items: ''
})

const reviewRules = {
  title: [{ required: true, message: '请输入复盘标题', trigger: 'blur' }]
}

const getStatusTag = (status) => {
  const map = { draft: 'info', in_progress: 'warning', completed: 'success' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { draft: '草稿', in_progress: '进行中', completed: '已完成' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadReviews = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', currentPage.value)
    params.append('page_size', pageSize.value)
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (filterStatus.value) params.append('status', filterStatus.value)

    const response = await apiClient.get(`/reviews/?${params.toString()}`)
    reviews.value = response.data || response.results || []
    total.value = response.total || response.count || reviews.value.length
  } catch (error) {
    console.error('加载复盘失败:', error)
    ElMessage.error('加载复盘失败')
  } finally {
    loading.value = false
  }
}

const loadEvents = async () => {
  try {
    const response = await apiClient.get('/events/?page_size=100')
    events.value = response.data || response.results || []
  } catch (error) {
    console.error('加载活动失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadReviews()
}

const viewReview = (review) => {
  currentReview.value = review
  showDetailDialog.value = true
}

const editReview = (review) => {
  editingReview.value = review
  Object.assign(reviewForm, {
    title: review.title,
    event: review.event,
    goal_achievement: review.goal_achievement || '',
    process_execution: review.process_execution || '',
    cost_control: review.cost_control || '',
    customer_feedback: review.customer_feedback || '',
    team_collaboration: review.team_collaboration || '',
    successes: review.successes || '',
    improvements: review.improvements || '',
    action_items: review.action_items || ''
  })
  showCreateDialog.value = true
}

const saveReview = async () => {
  try {
    await reviewFormRef.value.validate()

    if (editingReview.value) {
      await apiClient.put(`/reviews/${editingReview.value.id}/`, reviewForm)
      ElMessage.success('更新成功')
    } else {
      await apiClient.post('/reviews/', reviewForm)
      ElMessage.success('创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    loadReviews()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

const completeReview = async (review) => {
  try {
    await ElMessageBox.confirm('确定要完成该复盘吗？', '确认完成', { type: 'success' })
    await apiClient.post(`/reviews/${review.id}/complete/`)
    ElMessage.success('复盘已完成')
    loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('完成失败:', error)
      ElMessage.error('完成失败')
    }
  }
}

const deleteReview = async (review) => {
  try {
    await ElMessageBox.confirm('确定要删除该复盘吗？', '确认删除', { type: 'warning' })
    await apiClient.delete(`/reviews/${review.id}/`)
    ElMessage.success('删除成功')
    loadReviews()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  editingReview.value = null
  Object.assign(reviewForm, {
    title: '',
    event: '',
    goal_achievement: '',
    process_execution: '',
    cost_control: '',
    customer_feedback: '',
    team_collaboration: '',
    successes: '',
    improvements: '',
    action_items: ''
  })
}

onMounted(() => {
  loadReviews()
  loadEvents()
})
</script>

<style scoped>
.reviews-container {
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

.filter-card {
  padding: 15px;
}

.review-title {
  color: #409eff;
  cursor: pointer;
}

.review-title:hover {
  text-decoration: underline;
}
</style>
