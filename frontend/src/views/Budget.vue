<template>
  <div class="budget-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="budget-overview">
          <template #header>
            <div class="card-header">
              <h3>预算概览</h3>
              <el-select v-model="selectedEventId" placeholder="选择活动" style="width: 300px" @change="loadBudgetData">
                <el-option v-for="event in events" :key="event.id" :label="event.name" :value="event.id" />
              </el-select>
            </div>
          </template>

          <el-row :gutter="20" v-if="currentEvent">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">预估预算</div>
                <div class="stat-value">{{ formatCurrency(currentEvent.estimated_budget) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">实际支出</div>
                <div class="stat-value">{{ formatCurrency(currentEvent.actual_budget) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">预算偏差</div>
                <div class="stat-value" :class="budgetVarianceClass">
                  {{ formatCurrency(currentEvent.budget_variance) }}
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">预算使用率</div>
                <div class="stat-value">{{ budgetUsageRate }}%</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>预算明细</h3>
              <el-button type="primary" @click="showCreateDialog" :disabled="!selectedEventId">添加预算项</el-button>
            </div>
          </template>

          <el-table v-loading="loading" :data="budgetItems" stripe style="width: 100%">
            <el-table-column prop="category_name" label="预算科目" width="150" />
            <el-table-column prop="name" label="预算项名称" width="200" />
            <el-table-column prop="estimated_amount" label="预估金额" width="120">
              <template #default="{ row }">
                {{ formatCurrency(row.estimated_amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="actual_amount" label="实际金额" width="120">
              <template #default="{ row }">
                {{ formatCurrency(row.actual_amount) }}
              </template>
            </el-table-column>
            <el-table-column prop="variance" label="偏差" width="120">
              <template #default="{ row }">
                <span :class="getVarianceClass(row.variance)">{{ formatCurrency(row.variance) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="responsible_name" label="负责人" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="预算科目" prop="category_name">
          <el-input v-model="form.category_name" placeholder="如：场地费、餐饮费" />
        </el-form-item>
        <el-form-item label="预算项名称" prop="name">
          <el-input v-model="form.name" placeholder="如：会场租赁费" />
        </el-form-item>
        <el-form-item label="预估金额" prop="estimated_amount">
          <el-input-number v-model="form.estimated_amount" :min="0" :precision="2" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="实际金额" prop="actual_amount">
          <el-input-number v-model="form.actual_amount" :min="0" :precision="2" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="负责人" prop="responsible">
          <el-input v-model="form.responsible" placeholder="用户ID" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" placeholder="选择状态">
            <el-option label="待定" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useEventsStore } from '../store'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createBudgetItem, updateBudgetItem, deleteBudgetItem } from '../api/budget'

const eventsStore = useEventsStore()
const loading = ref(false)
const events = ref([])
const selectedEventId = ref(null)
const currentEvent = ref(null)
const budgetItems = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加预算项')
const formRef = ref(null)
const isEditing = ref(false)
const editingId = ref(null)

const form = ref({
  category_name: '',
  name: '',
  estimated_amount: 0,
  actual_amount: 0,
  responsible: '',
  status: 'pending'
})

const rules = {
  category_name: [
    { required: true, message: '请输入预算科目', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入预算项名称', trigger: 'blur' }
  ],
  estimated_amount: [
    { required: true, message: '请输入预估金额', trigger: 'blur' }
  ]
}

const budgetVarianceClass = computed(() => {
  if (!currentEvent.value) return ''
  const variance = currentEvent.value.budget_variance
  return variance > 0 ? 'variance-positive' : variance < 0 ? 'variance-negative' : ''
})

const budgetUsageRate = computed(() => {
  if (!currentEvent.value || !currentEvent.value.estimated_budget) return 0
  return ((currentEvent.value.actual_budget / currentEvent.value.estimated_budget) * 100).toFixed(2)
})

onMounted(async () => {
  await loadEvents()
})

async function loadEvents() {
  try {
    await eventsStore.fetchEvents()
    events.value = eventsStore.events
    if (events.value.length > 0) {
      selectedEventId.value = events.value[0].id
      await loadBudgetData()
    }
  } catch (error) {
    ElMessage.error('加载活动失败')
    console.error('Load events error:', error)
  }
}

async function loadBudgetData() {
  if (!selectedEventId.value) return

  loading.value = true
  try {
    // 获取活动详情和预算明细
    const event = events.value.find(e => e.id === selectedEventId.value)
    currentEvent.value = event

    // 加载预算明细 - 这里需要调用 API
    if (event && event.budget_items) {
      budgetItems.value = event.budget_items
    } else {
      budgetItems.value = []
    }
  } catch (error) {
    ElMessage.error('加载预算数据失败')
    console.error('Load budget error:', error)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  dialogTitle.value = '添加预算项'
  isEditing.value = false
  editingId.value = null
  form.value = {
    category_name: '',
    name: '',
    estimated_amount: 0,
    actual_amount: 0,
    responsible: '',
    status: 'pending'
  }
  dialogVisible.value = true
}

function handleEdit(row) {
  dialogTitle.value = '编辑预算项'
  isEditing.value = true
  editingId.value = row.id
  form.value = {
    category_name: row.category_name,
    name: row.name,
    estimated_amount: row.estimated_amount,
    actual_amount: row.actual_amount,
    responsible: row.responsible,
    status: row.status
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    const eventData = {
      ...form.value,
      event: selectedEventId.value
    }

    if (isEditing.value) {
      await updateBudgetItem(editingId.value, eventData)
      ElMessage.success('预算项更新成功')
    } else {
      await createBudgetItem(eventData)
      ElMessage.success('预算项创建成功')
    }

    dialogVisible.value = false
    await loadBudgetData()
  } catch (error) {
    if (error !== false) { // 表单验证失败返回 false
      ElMessage.error(isEditing.value ? '更新失败' : '创建失败')
      console.error('Submit error:', error)
    }
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除预算项 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })

    await deleteBudgetItem(row.id)
    ElMessage.success('删除成功')
    await loadBudgetData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete error:', error)
    }
  }
}

function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(value || 0)
}

function getVarianceClass(variance) {
  if (variance > 0) return 'text-success'
  if (variance < 0) return 'text-danger'
  return ''
}

function getStatusType(status) {
  const types = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    pending: '待定',
    in_progress: '进行中',
    completed: '已完成'
  }
  return texts[status] || status
}
</script>

<style scoped>
.budget-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.stat-card {
  padding: 15px;
  border-radius: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.variance-positive {
  color: #67c23a;
}

.variance-negative {
  color: #f56c6c;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.budget-overview {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}
</style>
