<template>
  <div class="reviews-container">
    <div class="page-header">
      <h1>复盘管理</h1>
      <div class="header-actions">
        <el-button
          type="primary"
          @click="openCreateDialog"
        >
          <el-icon><Plus /></el-icon>
          新建复盘
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
            {{ statistics.total }}
          </div>
          <div class="stat-label">
            总复盘数
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ statistics.drafts }}
          </div>
          <div class="stat-label">
            草稿
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ statistics.inProgress }}
          </div>
          <div class="stat-label">
            进行中
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-number">
            {{ statistics.completed }}
          </div>
          <div class="stat-label">
            已完成
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card
      class="filter-card"
      style="margin-top: 20px"
    >
      <el-row
        :gutter="20"
        align="middle"
      >
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索复盘..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            clearable
            @change="handleSearch"
          >
            <el-option
              label="全部状态"
              value=""
            />
            <el-option
              label="草稿"
              value="draft"
            />
            <el-option
              label="进行中"
              value="in_progress"
            />
            <el-option
              label="已完成"
              value="completed"
            />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-card
      class="table-card"
      style="margin-top: 20px"
    >
      <el-table
        v-loading="loading"
        :data="reviews"
        stripe
        border
      >
        <el-table-column
          prop="title"
          label="复盘标题"
          min-width="200"
        >
          <template #default="{ row }">
            <div
              class="review-title"
              @click="viewReview(row)"
            >
              {{ row.title }}
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="event_name"
          label="关联活动"
          width="150"
        >
          <template #default="{ row }">
            {{ row.event_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              :type="getStatusTag(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="160"
        >
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="completed_at"
          label="完成时间"
          width="160"
        >
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="editReview(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status !== 'completed'"
              type="success"
              size="small"
              @click="completeReview(row)"
            >
              完成
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteReview(row)"
            >
              删除
            </el-button>
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

    <!-- 统一的复盘表单对话框（详情/新建/编辑） -->
    <ReviewFormDialog
      v-model="showFormDialog"
      :mode="formMode"
      :review-data="selectedReviewData"
      :events-list="events"
      @success="handleFormSuccess"
      @delete="handleDeleteFromForm"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { apiClient } from '../api/client'
import ReviewFormDialog from '@/components/ReviewFormDialog.vue'

const loading = ref(false)
const reviews = ref([])
const events = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterStatus = ref('')

// 统一的对话框状态
const showFormDialog = ref(false)
const formMode = ref<'view' | 'create' | 'edit'>('create')
const selectedReviewData = ref(null)

// 统计数据
const statistics = computed(() => {
  const stats = { total: total.value, drafts: 0, inProgress: 0, completed: 0 }
  reviews.value.forEach(r => {
    if (r.status === 'draft') stats.drafts++
    else if (r.status === 'in_progress') stats.inProgress++
    else if (r.status === 'completed') stats.completed++
  })
  return stats
})

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
  selectedReviewData.value = review
  formMode.value = 'view'
  showFormDialog.value = true
}

function openCreateDialog() {
  selectedReviewData.value = null
  formMode.value = 'create'
  showFormDialog.value = true
}

const editReview = (review) => {
  selectedReviewData.value = review
  formMode.value = 'edit'
  showFormDialog.value = true
}

function handleFormSuccess(data) {
  // 刷新复盘列表
  loadReviews()

  // 如果是从查看模式切换到编辑模式
  if (data?.action === 'edit') {
    selectedReviewData.value = data.data
    formMode.value = 'edit'
    showFormDialog.value = true
  } else {
    ElMessage.success(formMode.value === 'create' ? '复盘创建成功' : '复盘更新成功')
  }
}

function handleDeleteFromForm(review) {
  if (review?.id) {
    loadReviews()
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
