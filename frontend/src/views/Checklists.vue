<template>
  <div class="checklists-container">
    <div class="page-header">
      <h1>清单管理</h1>
      <div class="header-actions">
        <el-button @click="showTemplates = false" :type="!showTemplates ? 'primary' : 'default'">
          清单实例
        </el-button>
        <el-button @click="showTemplates = true" :type="showTemplates ? 'primary' : 'default'">
          模板管理
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          新建{{ showTemplates ? '模板' : '清单实例' }}
        </el-button>
      </div>
    </div>

    <!-- 清单模板管理 -->
    <div v-if="showTemplates">
      <el-card class="table-card">
        <template #header>
          <div class="table-header">
            <h3>清单模板</h3>
            <el-input
              v-model="searchQuery"
              placeholder="搜索模板..."
              clearable
              style="width: 300px"
            />
          </div>
        </template>

        <el-table
          :data="filteredTemplates"
          v-loading="loading"
          stripe
          border
        >
          <el-table-column prop="name" label="模板名称" min-width="180" />
          <el-table-column prop="description" label="描述" min-width="200" />
          <el-table-column prop="category" label="分类" width="120">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.category || '默认' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getTemplateStatusType(row.status)" size="small">
                {{ getTemplateStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleInstantiate(row)">
                实例化
              </el-button>
              <el-button link type="success" size="small" @click="handleEditTemplate(row)">
                编辑
              </el-button>
              <el-button link type="danger" size="small" @click="handleDeleteTemplate(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 清单实例管理 -->
    <el-card v-else class="table-card">
      <template #header>
        <div class="table-header">
          <h3>清单实例</h3>
          <div class="filter-section">
            <el-select
              v-model="filterStatus"
              placeholder="状态筛选"
              clearable
              style="width: 120px"
            >
              <el-option label="全部状态" value="" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="已暂停" value="paused" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredInstances"
        v-loading="loading"
        stripe
        border
      >
        <el-table-column prop="name" label="清单名称" min-width="180" />
        <el-table-column prop="template_name" label="来源模板" width="150" />
        <el-table-column prop="progress" label="完成度" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getInstanceStatusType(row.status)" size="small">
              {{ getInstanceStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleVerify(row)">
              核验
            </el-button>
            <el-button link type="success" size="small" @click="handleViewDetails(row)">
              详情
            </el-button>
            <el-button link type="danger" size="small" @click="handleDeleteInstance(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 清单模板表单对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      :title="isEditTemplate ? '编辑清单模板' : '新建清单模板'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="templateForm" :rules="templateRules" ref="templateFormRef" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="templateForm.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="清单项">
          <div class="checklist-items">
            <div
              v-for="(item, index) in templateForm.items"
              :key="index"
              class="checklist-item-row"
            >
              <el-input
                v-model="item.title"
                placeholder="清单项名称"
                style="flex: 1"
              />
              <el-input-number
                v-model="item.weight"
                :min="1"
                :max="10"
                placeholder="权重"
                style="width: 120px"
              />
              <el-button type="danger" circle @click="removeTemplateItem(index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button type="primary" link @click="addTemplateItem">
              + 添加清单项
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="templateForm.status" placeholder="请选择状态">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTemplate" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 清单核验对话框 -->
    <el-dialog
      v-model="verificationDialogVisible"
      title="清单核验"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="verification-header">
        <h3>{{ currentInstance?.name }}</h3>
        <div class="verification-progress">
          <span>完成度：</span>
          <el-progress :percentage="currentInstance?.progress || 0" :stroke-width="8" />
        </div>
      </div>
      
      <div class="verification-items">
        <div
          v-for="item in verificationItems"
          :key="item.id"
          class="verification-item"
          :class="{ checked: item.checked }"
        >
          <div class="item-left">
            <el-checkbox
              v-model="item.checked"
              @change="handleItemCheck(item)"
            >
              <span class="item-title">{{ item.title }}</span>
            </el-checkbox>
            <div class="item-meta">
              <span class="item-weight">权重: {{ item.weight }}</span>
              <el-tag :type="item.checked ? 'success' : 'info'" size="small">
                {{ item.checked ? '已核验' : '未核验' }}
              </el-tag>
            </div>
          </div>
          <div class="item-attachment" v-if="item.attachment_url">
            <el-button link type="primary" size="small" @click="viewAttachment(item.attachment_url)">
              查看附件
            </el-button>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="verificationDialogVisible = false">
          关闭
        </el-button>
        <el-button type="primary" @click="submitVerification" :loading="submitting">
          提交核验结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const loading = ref(false)
const showTemplates = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const templateDialogVisible = ref(false)
const verificationDialogVisible = ref(false)
const isEditTemplate = ref(false)
const submitting = ref(false)
const templateFormRef = ref()

// 模拟数据 - 实际应该从API获取
const templates = ref([
  {
    id: '1',
    name: '活动布置检查清单',
    description: '活动现场布置前的完整检查清单',
    category: '活动现场',
    status: 'published',
    items: [],
    created_at: '2026-04-19T10:00:00Z'
  },
  {
    id: '2',
    name: '设备调试清单',
    description: '活动设备调试和测试清单',
    category: '设备管理',
    status: 'published',
    items: [],
    created_at: '2026-04-19T11:00:00Z'
  }
])

const instances = ref([
  {
    id: '1',
    name: '周年庆布置检查',
    template_id: '1',
    template_name: '活动布置检查清单',
    progress: 75,
    status: 'in_progress',
    created_at: '2026-04-20T10:00:00Z'
  },
  {
    id: '2',
    name: '设备调试实例',
    template_id: '2',
    template_name: '设备调试清单', 
    progress: 100,
    status: 'completed',
    created_at: '2026-04-20T11:00:00Z'
  }
])

const currentInstance = ref(null)
const verificationItems = ref([])

const templateForm = reactive({
  name: '',
  category: '',
  description: '',
  items: [],
  status: 'draft'
})

const templateRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ]
}

const filteredTemplates = computed(() => {
  return templates.value.filter(tmpl => 
    !searchQuery.value || 
    tmpl.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const filteredInstances = computed(() => {
  return instances.value.filter(inst => 
    (!filterStatus.value || inst.status === filterStatus.value)
  )
})

function getTemplateStatusType(status) {
  const types = {
    draft: 'info',
    published: 'success',
    archived: 'warning'
  }
  return types[status] || 'info'
}

function getTemplateStatusText(status) {
  const texts = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return texts[status] || status
}

function getInstanceStatusType(status) {
  const types = {
    draft: 'info',
    in_progress: 'warning',
    completed: 'success',
    paused: 'info',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getInstanceStatusText(status) {
  const texts = {
    draft: '草稿',
    in_progress: '进行中',
    completed: '已完成',
    paused: '已暂停',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function showCreateDialog() {
  if (showTemplates.value) {
    templateDialogVisible.value = true
    isEditTemplate.value = false
    Object.assign(templateForm, {
      name: '',
      category: '',
      description: '',
      items: [],
      status: 'draft'
    })
  } else {
    ElMessage.info('清单实例创建功能待完成')
  }
}

function addTemplateItem() {
  templateForm.items.push({
    title: '',
    weight: 1
  })
}

function removeTemplateItem(index) {
  templateForm.items.splice(index, 1)
}

function handleInstantiate(template) {
  ElMessage.success(`将以模板 "${template.name}" 创建清单实例`)
}

function handleEditTemplate(template) {
  isEditTemplate.value = true
  templateDialogVisible.value = true
  Object.assign(templateForm, template)
}

async function handleDeleteTemplate(template) {
  try {
    await ElMessageBox.confirm(`确定要删除模板 "${template.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    ElMessage.success('模板删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
    }
  }
}

function handleVerify(instance) {
  currentInstance.value = instance
  verificationItems.value = [
    {
      id: '1',
      title: '场地布置完成检查',
      weight: 5,
      checked: false,
      checked_at: null,
      attachment_url: ''
    },
    {
      id: '2',
      title: '设备连接检查',
      weight: 3,
      checked: false,
      checked_at: null,
      attachment_url: ''
    },
    {
      id: '3',
      title: '安全措施检查',
      weight: 4,
      checked: false,
      checked_at: null,
      attachment_url: ''
    }
  ]
  verificationDialogVisible.value = true
}

function handleItemCheck(item) {
  console.log('Item check status changed:', item)
}

function viewAttachment(url) {
  ElMessage.info('查看附件功能待实现')
}

async function handleViewDetails(instance) {
  ElMessage.info(`查看详情: ${instance.name}`)
}

async function handleDeleteInstance(instance) {
  try {
    await ElMessageBox.confirm(`确定要删除清单实例 "${instance.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    ElMessage.success('清单实例删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
    }
  }
}

async function submitTemplate() {
  if (!templateFormRef.value) return
  
  try {
    await templateFormRef.value.validate()
    submitting.value = true
    
    // TODO: 实现模板提交逻辑
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success(isEditTemplate.value ? '更新成功' : '创建成功')
    templateDialogVisible.value = false
    showCreateDialog() // 重置表单
  } catch (error) {
    if (error !== false) {
      console.error('Form validation failed:', error)
    }
  } finally {
    submitting.value = false
  }
}

async function submitVerification() {
  try {
    submitting.value = true
    
    // TODO: 实现核验结果提交逻辑
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('核验结果提交成功')
    verificationDialogVisible.value = false
  } catch (error) {
    console.error('Verification submit failed:', error)
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  // TODO: 从API加载数据
})
</script>

<style scoped>
.checklists-container {
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
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.table-card {
  min-height: 400px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.filter-section {
  display: flex;
  gap: 10px;
}

.checklist-items {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background: #f5f7fa;
}

.checklist-item-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.verification-header {
  margin-bottom: 20px;
}

.verification-header h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.verification-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #666;
}

.verification-items {
  max-height: 500px;
  overflow-y: auto;
}

.verification-item {
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.verification-item:last-child {
  border-bottom: none;
}

.verification-item.checked {
  background: #f0f9ff;
}

.item-left {
  flex: 1;
}

.el-checkbox .item-title {
  margin-left: 10px;
  font-size: 15px;
  color: #333;
}

.item-meta {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.item-weight {
  color: #409eff;
}

.item-attachment {
  margin-left: 20px;
}
</style>