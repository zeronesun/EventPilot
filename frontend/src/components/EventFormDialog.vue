<template>
  <el-dialog
    v-model="isOpen"
    :title="dialogTitle"
    width="92%"
    top="3vh"
    :close-on-click-modal="false"
    @close="handleClose"
    class="event-form-dialog"
  >
    <!-- 加载状态 -->
    <el-skeleton v-if="loading" :rows="12" animated />

    <div v-else class="dialog-container">
      <!-- 左侧：表单/详情区域 -->
      <div class="main-section">
        <!-- 查看模式：详细描述展示 -->
        <div v-if="isViewMode" class="view-mode">
          <div class="event-header">
            <h2>{{ formData.name || '未命名活动' }}</h2>
            <div class="header-tags">
              <el-tag :type="getStatusType(formData.status)" size="large" effect="dark">
                {{ getStatusText(formData.status) }}
              </el-tag>
              <el-tag type="info" size="small">
                {{ formatEventType(formData.type) }}
              </el-tag>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="活动类型">
              {{ formatEventType(formData.type) }}
            </el-descriptions-item>
            <el-descriptions-item label="负责人">
              {{ formData.owner_name || '未指定' }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatDate(formData.start_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="结束时间">
              {{ formatDate(formData.end_date) || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="活动地点" :span="2">
              {{ formData.location || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatFullDate(formData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatFullDate(formData.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="formData.description" class="description-section">
            <h3>活动说明</h3>
            <p>{{ formData.description }}</p>
          </div>

          <!-- 预算信息卡片 -->
          <div v-if="hasBudgetInfo" class="budget-section">
            <h3><el-icon><Coin /></el-icon>预算信息</h3>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="预算金额" :precision="2">
                  <template #formatter>
                    <span class="budget-amount">{{ formatCurrency(formData.estimated_budget) }}</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="实际支出" :precision="2">
                  <template #formatter>
                    {{ formData.actual_budget ? formatCurrency(formData.actual_budget) : '未结算' }}
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="预算偏差" :precision="2">
                  <template #formatter>
                    <el-tag
                      :type="getBudgetDeviationType()"
                      effect="dark"
                    >
                      {{ getBudgetDeviationText() }}
                    </el-tag>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>

            <el-progress
              v-if="formData.actual_budget && formData.estimated_budget"
              :percentage="getBudgetUsage()"
              :color="getProgressColor()"
              :stroke-width="10"
              class="budget-progress"
            >
              <template #default="{ percentage }">
                <span>已使用 {{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </div>

        <!-- 编辑/新建模式：表单 -->
        <div v-else class="edit-mode">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
            class="event-form"
          >
            <!-- 基本信息 -->
            <div class="section-title">
              <el-icon><InfoFilled /></el-icon>
              <span>基本信息</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="活动名称" prop="name">
                  <el-input v-model="formData.name" placeholder="请输入活动名称" maxlength="100" show-word-limit />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="活动类型" prop="type">
                  <el-select v-model="formData.type" placeholder="请选择活动类型" style="width: 100%">
                    <el-option label="会议" value="conference" />
                    <el-option label="培训" value="training" />
                    <el-option label="活动" value="event" />
                    <el-option label="团建" value="team_building" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="活动状态" prop="status">
                  <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
                    <el-option label="策划中" value="planning" />
                    <el-option label="执行中" value="executing" />
                    <el-option label="已完成" value="completed" />
                    <el-option label="已复盘" value="reviewed" />
                    <el-option label="已取消" value="cancelled" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="负责人" prop="owner_name">
                  <el-input v-model="formData.owner_name" placeholder="请输入负责人" :disabled="true" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 时间规划 -->
            <div class="section-title">
              <el-icon><Timer /></el-icon>
              <span>时间规划</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开始时间" prop="start_date">
                  <el-date-picker
                    v-model="formData.start_date"
                    type="datetime"
                    placeholder="选择开始时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    style="width: 100%"
                    :clearable="true"
                    :disabled-date="disabledStartDate"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="结束时间" prop="end_date">
                  <el-date-picker
                    v-model="formData.end_date"
                    type="datetime"
                    placeholder="选择结束时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DD HH:mm:ss"
                    style="width: 100%"
                    :clearable="true"
                    :disabled-date="disabledEndDate"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="活动地点" prop="location">
              <el-input v-model="formData.location" placeholder="请输入活动地点" />
            </el-form-item>

            <!-- 预算信息 -->
            <div class="section-title">
              <el-icon><Money /></el-icon>
              <span>预算信息</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="预算金额" prop="estimated_budget">
                  <el-input-number
                    v-model="formData.estimated_budget"
                    :min="0"
                    :max="9999999"
                    :step="100"
                    placeholder="请输入预算金额"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="实际支出" prop="actual_budget">
                  <el-input-number
                    v-model="formData.actual_budget"
                    :min="0"
                    :disabled="true"
                    placeholder="自动计算"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 详细说明 -->
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>详细说明</span>
            </div>

            <el-form-item label="活动描述" prop="description">
              <el-input
                v-model="formData.description"
                type="textarea"
                placeholder="请输入活动描述"
                :rows="4"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 右侧：预览和操作区域 -->
      <div class="sidebar-section">
        <!-- 实时预览卡片 -->
        <div class="preview-card">
          <div class="card-header">
            <el-icon><View /></el-icon>
            <span>实时预览</span>
          </div>

          <div class="activity-preview">
            <h3>{{ formData.name || '未命名活动' }}</h3>

            <div class="meta-info">
              <el-tag :type="getStatusType(formData.status)" size="small">
                {{ getStatusText(formData.status) }}
              </el-tag>
              <el-tag type="info" size="small">
                {{ formatEventType(formData.type) }}
              </el-tag>
            </div>

            <div class="info-list">
              <div class="info-item">
                <label>负责人</label>
                <span>{{ formData.owner_name || '未指定' }}</span>
              </div>
              <div class="info-item">
                <label>预算</label>
                <span>￥{{ (formData.estimated_budget || 0).toLocaleString() }}</span>
              </div>
              <div class="info-item">
                <label>开始时间</label>
                <span>{{ formatDate(formData.start_date) }}</span>
              </div>
              <div class="info-item">
                <label>结束时间</label>
                <span>{{ formatDate(formData.end_date) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 统计数据 -->
        <div v-if="mode !== 'create'" class="stats-card">
          <div class="card-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计数据</span>
          </div>

          <div class="stat-items">
            <div class="stat-item">
              <el-icon><List /></el-icon>
              <span>任务统计</span>
              <strong>{{ stats.taskCount || 0 }}个关联任务</strong>
            </div>
            <div class="stat-item">
              <el-icon><Money /></el-icon>
              <span>预算使用</span>
              <strong>{{ stats.budgetUsage || '未计算' }}</strong>
            </div>
          </div>
        </div>

        <!-- 操作提示 -->
        <div class="tips-card">
          <div class="card-header">
            <el-icon><Warning /></el-icon>
            <span>操作提示</span>
          </div>
          <ul class="tips-list">
            <li>所有带 * 号的字段为必填项</li>
            <li>保存后会自动记录操作日志</li>
            <li>取消编辑不会保存修改内容</li>
            <li>删除操作不可恢复，请谨慎操作</li>
          </ul>
        </div>

        <!-- 快捷操作 -->
        <div v-if="mode === 'view'" class="actions-card">
          <div class="card-header">
            <el-icon><Operation /></el-icon>
            <span>快捷操作</span>
          </div>

          <div class="quick-actions">
            <el-button type="primary" @click="switchToEdit">
              <el-icon><Edit /></el-icon>
              编辑活动
            </el-button>
            <el-button @click="handleCreateTask">
              <el-icon><Plus /></el-icon>
              创建任务
            </el-button>
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            <el-button @click="handleShare">
              <el-icon><Share /></el-icon>
              分享活动
            </el-button>
            <el-button type="danger" plain @click="handleDelete">
              <el-icon><Delete /></el-icon>
              删除活动
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <template #footer>
      <div class="footer-actions">
        <el-button @click="handleClose">
          {{ isViewMode ? '返回列表' : '取消' }}
        </el-button>

        <template v-if="!isViewMode">
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ mode === 'create' ? '创建活动' : '保存更改' }}
          </el-button>
        </template>

        <template v-else>
          <el-button type="primary" @click="switchToEdit">编辑活动</el-button>
          <el-button type="danger" plain @click="handleDelete">删除活动</el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventsStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  InfoFilled,
  Timer,
  Money,
  Document,
  View,
  DataAnalysis,
  Warning,
  Operation,
  Edit,
  Download,
  Delete,
  List,
  Coin,
  Plus,
  Share
} from '@element-plus/icons-vue'

interface EventData {
  id?: string | number
  name: string
  type: string
  status: string
  start_date: string
  end_date: string
  location: string
  estimated_budget: number
  actual_budget: number
  description: string
  owner_name: string
  created_at?: string
  updated_at?: string
}

interface Props {
  modelValue: boolean
  mode?: 'view' | 'create' | 'edit'
  eventData?: any
  stats?: {
    taskCount?: number
    budgetUsage?: string
  }
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  eventData: () => null,
  stats: () => ({})
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', data?: any): void
  (e: 'delete', data?: any): void
  (e: 'export'): void
  (e: 'createTask'): void
}>()

const eventsStore = useEventsStore()
const formRef = ref()
const loading = ref(false)
const submitLoading = ref(false)

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isViewMode = computed(() => props.mode === 'view')

const dialogTitle = computed(() => {
  const titles = {
    view: '活动详情',
    create: '新建活动',
    edit: '编辑活动'
  }
  return titles[props.mode] || '活动'
})

const hasBudgetInfo = computed(() => {
  return formData.value.estimated_budget > 0 || formData.value.actual_budget > 0
})

const formData = ref<EventData>({
  name: '',
  type: '',
  status: '',
  start_date: '',
  end_date: '',
  location: '',
  estimated_budget: 0,
  actual_budget: 0,
  description: '',
  owner_name: ''
})

const formRules = {
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' },
    { min: 3, max: 100, message: '长度在 3 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择活动状态', trigger: 'change' }
  ],
  start_date: [
    { required: true, message: '请选择开始时间', trigger: 'change' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (!value) {
          callback(new Error('请选择开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  end_date: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (!value) {
          callback(new Error('请选择结束时间'))
        } else if (formData.value.start_date && new Date(value) < new Date(formData.value.start_date)) {
          callback(new Error('结束时间不能早于开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 监听事件数据变化，填充表单
watch(() => [props.eventData, props.mode], ([newData, mode]) => {
  if ((mode === 'view' || mode === 'edit') && newData && Object.keys(newData).length > 0) {
    loading.value = true

    // 模拟加载延迟
    setTimeout(() => {
      formData.value = {
        id: newData.id,
        name: newData.name || '',
        type: newData.type || 'conference',
        status: newData.status || 'planning',
        start_date: newData.start_date || '',
        end_date: newData.end_date || '',
        location: newData.location || '',
        estimated_budget: parseFloat(newData.estimated_budget) || parseFloat(newData.budget) || 0,
        actual_budget: parseFloat(newData.actual_budget) || parseFloat(newData.actual_cost) || 0,
        description: newData.description || '',
        owner_name: newData.owner_name || '',
        created_at: newData.created_at || '',
        updated_at: newData.updated_at || ''
      }
      loading.value = false
    }, 300)
  } else if (mode === 'create') {
    resetForm()
  }
}, { immediate: true, deep: true })

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    planning: 'warning',
    executing: 'primary',
    completed: 'success',
    reviewed: 'info',
    cancelled: 'info',
    pending: 'info',
    in_progress: 'warning'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    planning: '策划中',
    executing: '执行中',
    completed: '已完成',
    reviewed: '已复盘',
    cancelled: '已取消',
    pending: '策划中',
    in_progress: '进行中'
  }
  return texts[status] || status
}

function formatEventType(type: string): string {
  const types: Record<string, string> = {
    conference: '会议',
    training: '培训',
    event: '活动',
    team_building: '团建',
    other: '其他'
  }
  return types[type] || type
}

function formatDate(date?: string): string {
  if (!date) return '未设置'
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

function formatFullDate(date?: string): string {
  if (!date) return '未设置'
  try {
    return new Date(date).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return date
  }
}

function formatCurrency(amount: number | undefined): string {
  if (!amount) return '￥0.00'
  return `￥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function getBudgetDeviationType(): string {
  const budget = formData.value.estimated_budget
  const actual = formData.value.actual_budget

  if (!budget || !actual) return 'info'

  const deviation = ((actual - budget) / budget) * 100

  if (deviation > 10) return 'danger'
  if (deviation > 5) return 'warning'
  if (deviation < -10) return 'success'
  return 'info'
}

function getBudgetDeviationText(): string {
  const budget = formData.value.estimated_budget
  const actual = formData.value.actual_budget

  if (!budget || !actual) return '未结算'

  const deviation = ((actual - budget) / budget) * 100

  if (deviation === 0) return '预算准确'
  if (deviation > 0) return `超支 ${Math.abs(deviation).toFixed(1)}%`
  return `节约 ${Math.abs(deviation).toFixed(1)}%`
}

function getBudgetUsage(): number {
  const budget = formData.value.estimated_budget
  const actual = formData.value.actual_budget

  if (!budget || !actual) return 0
  return Math.min(100, Math.max(0, (actual / budget) * 100))
}

function getProgressColor(): string {
  const usage = getBudgetUsage()

  if (usage > 90) return '#f56c6c'
  if (usage > 70) return '#e6a23c'
  return '#67c23a'
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    // 验证所有字段
    await formRef.value.validate()

    // 数据完整性检查
    if (!formData.value.name) {
      ElMessage.error('请填写活动名称')
      return
    }
    if (!formData.value.type) {
      ElMessage.error('请选择活动类型')
      return
    }
    if (!formData.value.status) {
      ElMessage.error('请选择活动状态')
      return
    }

    // 时间验证
    if (!formData.value.start_date) {
      ElMessage.error('请选择开始时间')
      return
    }
    if (!formData.value.end_date) {
      ElMessage.error('请选择结束时间')
      return
    }

    // 检查时间逻辑
    if (new Date(formData.value.end_date) < new Date(formData.value.start_date)) {
      ElMessage.error('结束时间不能早于开始时间')
      return
    }

    submitLoading.value = true

    // 转换字段名以匹配后端 API
    const submitData = {
      name: formData.value.name,
      type: formData.value.type,
      status: formData.value.status,
      start_date: formData.value.start_date,
      end_date: formData.value.end_date,
      location: formData.value.location,
      budget: formData.value.estimated_budget,
      actual_cost: formData.value.actual_budget,
      description: formData.value.description,
      owner_name: formData.value.owner_name
    }

    if (props.mode === 'edit' && formData.value.id) {
      const success = await eventsStore.updateEvent(formData.value.id, submitData)
      if (success) {
        ElMessage.success('更新成功')
        emit('success', formData.value)
        handleClose()
      } else {
        ElMessage.error(eventsStore.error || '更新失败')
      }
    } else {
      await eventsStore.createEvent(submitData)
      ElMessage.success('创建成功')
      emit('success', formData.value)
      handleClose()
    }
  } catch (error: any) {
    console.error('Submit error:', error)
    // 显示具体验证错误
    if (error && Array.isArray(error)) {
      const firstError = error[0]
      if (firstError && firstError.message) {
        ElMessage.error(firstError.message)
      }
    } else if (error && error.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('请检查表单填写是否完整')
    }
  } finally {
    submitLoading.value = false
  }
}

function switchToEdit() {
  emit('update:modelValue', false)
  setTimeout(() => {
    emit('success', { action: 'edit', data: props.eventData })
  }, 100)
}

function handleDelete() {
  ElMessageBox.confirm(
    `确定要删除活动"${formData.value.name}"吗？删除后无法恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('delete', props.eventData)
    handleClose()
  }).catch(() => {})
}

function handleExport() {
  emit('export')
}

function handleCreateTask() {
  emit('createTask')
}

function handleShare() {
  const url = window.location.href
  navigator.clipboard?.writeText(url).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

function handleClose() {
  isOpen.value = false
  if (props.mode === 'create') {
    resetForm()
  }
}

function resetForm() {
  formData.value = {
    name: '',
    type: '',
    status: '',
    start_date: '',
    end_date: '',
    location: '',
    estimated_budget: 0,
    actual_budget: 0,
    description: '',
    owner_name: ''
  }
}

// 禁用开始时间：不能早于当前时间
function disabledStartDate(time: Date): boolean {
  return time.getTime() < Date.now() - 8.64e7
}

// 禁用结束时间：不能早于开始时间
function disabledEndDate(time: Date): boolean {
  if (!formData.value.start_date) return false
  return time.getTime() < new Date(formData.value.start_date).getTime()
}
</script>

<style scoped>
.event-form-dialog .dialog-container {
  display: flex;
  gap: 24px;
  max-height: calc(90vh - 120px);
  overflow-y: auto;
}

.event-form-dialog .main-section {
  flex: 1;
  min-width: 500px;
}

.event-form-dialog .main-section .view-mode .event-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #409eff;
}

.event-form-dialog .main-section .view-mode .event-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.event-form-dialog .main-section .view-mode .event-header .header-tags {
  display: flex;
  gap: 8px;
}

.event-form-dialog .main-section .view-mode .detail-descriptions {
  margin-bottom: 24px;
}

.event-form-dialog .main-section .view-mode .description-section {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.event-form-dialog .main-section .view-mode .description-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.event-form-dialog .main-section .view-mode .description-section p {
  color: #606266;
  line-height: 1.8;
  word-break: break-word;
  white-space: pre-wrap;
  margin: 0;
}

.event-form-dialog .main-section .view-mode .budget-section {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.event-form-dialog .main-section .view-mode .budget-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.event-form-dialog .main-section .view-mode .budget-section h3 .el-icon {
  color: #409eff;
}

.event-form-dialog .main-section .view-mode .budget-section .budget-amount {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.event-form-dialog .main-section .view-mode .budget-section .budget-progress {
  margin-top: 20px;
}

.event-form-dialog .main-section .edit-mode .event-form .section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.event-form-dialog .main-section .edit-mode .event-form .section-title:first-child {
  margin-top: 0;
}

.event-form-dialog .main-section .edit-mode .event-form .section-title .el-icon {
  color: #409eff;
}

.event-form-dialog .sidebar-section {
  width: 320px;
  flex-shrink: 0;
}

.event-form-dialog .sidebar-section .preview-card,
.event-form-dialog .sidebar-section .stats-card,
.event-form-dialog .sidebar-section .tips-card,
.event-form-dialog .sidebar-section .actions-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.event-form-dialog .sidebar-section .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #dcdfe6;
}

.event-form-dialog .sidebar-section .card-header .el-icon {
  color: #409eff;
}

.event-form-dialog .sidebar-section .activity-preview h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.event-form-dialog .sidebar-section .activity-preview .meta-info {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.event-form-dialog .sidebar-section .activity-preview .info-list .info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.event-form-dialog .sidebar-section .activity-preview .info-list .info-item:last-child {
  border-bottom: none;
}

.event-form-dialog .sidebar-section .activity-preview .info-list .info-item label {
  color: #606266;
  font-size: 13px;
}

.event-form-dialog .sidebar-section .activity-preview .info-list .info-item value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.event-form-dialog .sidebar-section .stat-items .stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.event-form-dialog .sidebar-section .stat-items .stat-item:last-child {
  border-bottom: none;
}

.event-form-dialog .sidebar-section .stat-items .stat-item .el-icon {
  color: #409eff;
  font-size: 16px;
}

.event-form-dialog .sidebar-section .stat-items .stat-item span {
  flex: 1;
  color: #606266;
  font-size: 13px;
}

.event-form-dialog .sidebar-section .stat-items .stat-item strong {
  color: #303133;
  font-size: 13px;
}

.event-form-dialog .sidebar-section .tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.event-form-dialog .sidebar-section .tips-list li {
  padding: 6px 0;
  padding-left: 16px;
  position: relative;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.event-form-dialog .sidebar-section .tips-list li:before {
  content: "•";
  position: absolute;
  left: 0;
  color: #e6a23c;
  font-weight: bold;
}

.event-form-dialog .sidebar-section .quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-form-dialog .sidebar-section .quick-actions .el-button {
  justify-content: flex-start;
}

.event-form-dialog .footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.event-form-dialog :deep(.el-dialog__body) {
  padding: 20px;
}
</style>
