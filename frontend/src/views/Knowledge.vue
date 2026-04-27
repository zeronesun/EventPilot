<template>
  <div class="knowledge-container">
    <div class="page-header">
      <h1>知识库管理</h1>
      <div class="header-actions">
        <el-button @click="showSearch = true">
          <el-icon><Search /></el-icon>
          高级搜索
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建知识条目
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.total }}</div>
          <div class="stat-label">总条目数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.issues }}</div>
          <div class="stat-label">问题</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.experiences }}</div>
          <div class="stat-label">经验</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-number">{{ statistics.bestPractices }}</div>
          <div class="stat-label">最佳实践</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="filter-card" style="margin-top: 20px">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input v-model="searchQuery" placeholder="搜索知识条目..." clearable @input="handleSearch">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="条目类型" clearable @change="handleSearch">
            <el-option label="全部类型" value="" />
            <el-option label="问题" value="issue" />
            <el-option label="经验" value="experience" />
            <el-option label="最佳实践" value="best_practice" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterCategory" placeholder="分类" clearable @change="handleSearch">
            <el-option label="全部分类" value="" />
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-checkbox v-model="showPublicOnly">仅公开</el-checkbox>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="table-card" style="margin-top: 20px">
      <el-table :data="entries" v-loading="loading" stripe border>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <div class="entry-title" @click="viewEntry(row)">
              {{ row.title }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="entry_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEntryTypeTag(row.entry_type)" size="small">
              {{ getEntryTypeText(row.entry_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.category || '未分类' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || []).slice(0, 3)" :key="tag" size="small" style="margin-right: 5px">
              {{ tag }}
            </el-tag>
            <span v-if="(row.tags || []).length > 3">+{{ row.tags.length - 3 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_public" label="公开" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_verified" label="验证" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_verified ? 'success' : 'warning'" size="small">
              {{ row.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="popularity" label="热度" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editEntry(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteEntry(row)">删除</el-button>
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
        @size-change="loadEntries"
        @current-change="loadEntries"
      />
    </el-card>

    <el-dialog v-model="showCreateDialog" :title="editingEntry ? '编辑知识条目' : '新建知识条目'" width="600px">
      <el-form :model="entryForm" :rules="entryRules" ref="entryFormRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="entryForm.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="类型" prop="entry_type">
          <el-select v-model="entryForm.entry_type" placeholder="请选择类型">
            <el-option label="问题" value="issue" />
            <el-option label="经验" value="experience" />
            <el-option label="最佳实践" value="best_practice" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="entryForm.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="entryForm.content" type="textarea" :rows="6" placeholder="请输入内容" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="entryForm.tags" multiple filterable allow-create placeholder="请选择或输入标签">
            <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联活动">
          <el-input v-model="entryForm.related_events" placeholder="活动ID，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="关联任务">
          <el-input v-model="entryForm.related_tasks" placeholder="任务ID，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="公开">
          <el-switch v-model="entryForm.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEntry">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="知识条目详情" width="700px">
      <template v-if="currentEntry">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ currentEntry.title }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getEntryTypeTag(currentEntry.entry_type)">{{ getEntryTypeText(currentEntry.entry_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentEntry.category || '未分类' }}</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag v-for="tag in currentEntry.tags" :key="tag" size="small" style="margin-right: 5px">{{ tag }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="内容" :span="2">
            <div style="white-space: pre-wrap">{{ currentEntry.content }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="公开">{{ currentEntry.is_public ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="验证">{{ currentEntry.is_verified ? '已验证' : '待验证' }}</el-descriptions-item>
          <el-descriptions-item label="热度">{{ currentEntry.popularity }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentEntry.created_at) }}</el-descriptions-item>
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
const entries = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const filterType = ref('')
const filterCategory = ref('')
const showPublicOnly = ref(false)
const categories = ref([])
const commonTags = ref(['活动策划', '现场执行', '客户沟通', '预算管理', '团队协作', '风险管理'])

const statistics = computed(() => {
  const stats = { total: total.value, issues: 0, experiences: 0, bestPractices: 0 }
  entries.value.forEach(e => {
    if (e.entry_type === 'issue') stats.issues++
    else if (e.entry_type === 'experience') stats.experiences++
    else if (e.entry_type === 'best_practice') stats.bestPractices++
  })
  return stats
})

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showSearch = ref(false)
const editingEntry = ref(null)
const currentEntry = ref(null)
const entryFormRef = ref()

const entryForm = reactive({
  title: '',
  entry_type: 'experience',
  category: '',
  content: '',
  tags: [],
  related_events: '',
  related_tasks: '',
  is_public: false
})

const entryRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  entry_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const getEntryTypeTag = (type) => {
  const map = { issue: 'danger', experience: 'success', best_practice: 'primary' }
  return map[type] || 'info'
}

const getEntryTypeText = (type) => {
  const map = { issue: '问题', experience: '经验', best_practice: '最佳实践' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadEntries = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', currentPage.value)
    params.append('page_size', pageSize.value)
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (filterType.value) params.append('entry_type', filterType.value)
    if (filterCategory.value) params.append('category', filterCategory.value)
    if (showPublicOnly.value) params.append('is_public', 'true')

    const response = await apiClient.get(`/knowledge/?${params.toString()}`)
    entries.value = response.data || response.results || []
    total.value = response.total || response.count || entries.value.length
  } catch (error) {
    console.error('加载知识条目失败:', error)
    ElMessage.error('加载知识条目失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadEntries()
}

const viewEntry = (entry) => {
  currentEntry.value = entry
  showDetailDialog.value = true
}

const editEntry = (entry) => {
  editingEntry.value = entry
  Object.assign(entryForm, {
    title: entry.title,
    entry_type: entry.entry_type,
    category: entry.category || '',
    content: entry.content,
    tags: entry.tags || [],
    related_events: (entry.related_events || []).join(', '),
    related_tasks: (entry.related_tasks || []).join(', '),
    is_public: entry.is_public
  })
  showCreateDialog.value = true
}

const saveEntry = async () => {
  try {
    await entryFormRef.value.validate()
    const data = {
      ...entryForm,
      related_events: entryForm.related_events ? entryForm.related_events.split(',').map(s => s.trim()) : [],
      related_tasks: entryForm.related_tasks ? entryForm.related_tasks.split(',').map(s => s.trim()) : []
    }

    if (editingEntry.value) {
      await apiClient.put(`/knowledge/${editingEntry.value.id}/`, data)
      ElMessage.success('更新成功')
    } else {
      await apiClient.post('/knowledge/', data)
      ElMessage.success('创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    loadEntries()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

const deleteEntry = async (entry) => {
  try {
    await ElMessageBox.confirm('确定要删除该知识条目吗？', '确认删除', { type: 'warning' })
    await apiClient.delete(`/knowledge/${entry.id}/`)
    ElMessage.success('删除成功')
    loadEntries()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  editingEntry.value = null
  Object.assign(entryForm, {
    title: '',
    entry_type: 'experience',
    category: '',
    content: '',
    tags: [],
    related_events: '',
    related_tasks: '',
    is_public: false
  })
}

onMounted(() => {
  loadEntries()
})
</script>

<style scoped>
.knowledge-container {
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

.entry-title {
  color: #409eff;
  cursor: pointer;
}

.entry-title:hover {
  text-decoration: underline;
}
</style>
