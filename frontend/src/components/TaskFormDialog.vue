<template>
  <el-dialog
    v-model="isOpen"
    :title="dialogTitle"
    width="90%"
    top="5vh"
    :close-on-click-modal="false"
    @close="handleClose"
    class="task-form-dialog"
  >
    <el-skeleton v-if="loading" :rows="10" animated />

    <div v-else class="dialog-container">
      <!-- 左侧：表单/详情区域 -->
      <div class="main-section">
        <!-- 查看模式 -->
        <div v-if="isViewMode" class="view-mode">
          <div class="task-header">
            <h2>{{ formData.title || '未命名任务' }}</h2>
            <div class="header-tags">
              <el-tag :type="getStatusType(formData.status)" size="large" effect="dark">
                {{ getStatusText(formData.status) }}
              </el-tag>
              <el-tag :type="getPriorityType(formData.priority)" size="small">
                {{ getPriorityText(formData.priority) }}
              </el-tag>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="优先级">
              <el-tag :type="getPriorityType(formData.priority)" size="small">
                {{ getPriorityText(formData.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="负责人">
              {{ formData.assigned_to_name || '未指定' }}
            </el-descriptions-item>
            <el-descriptions-item label="截止日期">
              {{ formatDate(formData.due_date) || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="关联活动">
              {{ formData.event_name || '未关联' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatFullDate(formData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatFullDate(formData.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 进度展示 -->
          <div class="progress-section" v-if="formData.progress !== undefined">
            <h3>任务进度</h3>
            <el-progress
              :percentage="formData.progress || 0"
              :color="getProgressColor(formData.progress)"
              :stroke-width="12"
            >
              <template #default="{ percentage }">
                <span class="progress-text">完成 {{ percentage }}%</span>
              </template>
            </el-progress>
          </div>

          <!-- 任务描述 -->
          <div v-if="formData.description" class="description-section">
            <h3>任务描述</h3>
            <p>{{ formData.description }}</p>
          </div>
        </div>

        <!-- 编辑/新建模式：表单 -->
        <div v-else class="edit-mode">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
            class="task-form"
          >
            <!-- 基本信息 -->
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>基本信息</span>
            </div>

            <el-form-item label="任务标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入任务标题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="任务描述">
              <el-input
                v-model="formData.description"
                type="textarea"
                placeholder="请输入任务描述"
                :rows="4"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="优先级" prop="priority">
                  <el-select v-model="formData.priority" placeholder="选择优先级" style="width: 100%">
                    <el-option label="低" value="low" />
                    <el-option label="中" value="medium" />
                    <el-option label="高" value="high" />
                    <el-option label="紧急" value="urgent" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态" prop="status">
                  <el-select v-model="formData.status" placeholder="选择状态" style="width: 100%">
                    <el-option label="待处理" value="pending" />
                    <el-option label="进行中" value="in_progress" />
                    <el-option label="已完成" value="completed" />
                    <el-option label="已取消" value="cancelled" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 时间安排 -->
            <div class="section-title">
              <el-icon><Timer /></el-icon>
              <span>时间安排</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="截止日期">
                  <el-date-picker
                    v-model="formData.due_date"
                    type="datetime"
                    placeholder="选择截止日期"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="任务进度">
                  <el-slider
                    v-model="formData.progress"
                    :marks="{ 0: '0%', 50: '50%', 100: '100%' }"
                    :show-input="true"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 关联信息 -->
            <div class="section-title">
              <el-icon><Link /></el-icon>
              <span>关联信息</span>
            </div>

            <el-form-item label="关联活动">
              <el-select
                v-model="formData.event"
                placeholder="选择关联活动（可选）"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="event in eventsList"
                  :key="event.id"
                  :label="event.name"
                  :value="event.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="负责人">
              <el-input
                v-model="formData.assigned_to_name"
                placeholder="负责人（自动分配或手动填写）"
                :disabled="true"
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

          <div class="task-preview">
            <h3>{{ formData.title || '未命名任务' }}</h3>

            <div class="meta-info">
              <el-tag :type="getStatusType(formData.status)" size="small">
                {{ getStatusText(formData.status) }}
              </el-tag>
              <el-tag :type="getPriorityType(formData.priority)" size="small">
                {{ getPriorityText(formData.priority) }}
              </el-tag>
            </div>

            <div class="info-list">
              <div class="info-item">
                <label>截止日期</label>
                <value>{{ formatDate(formData.due_date) }}</value>
              </div>
              <div class="info-item">
                <label>进度</label>
                <value>{{ formData.progress || 0 }}%</value>
              </div>
              <div class="info-item">
                <label>负责人</label>
                <value>{{ formData.assigned_to_name || '未指定' }}</value>
              </div>
              <div class="info-item">
                <label>关联活动</label>
                <value>{{ getEventName() }}</value>
              </div>
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
            <li>任务标题为必填项</li>
            <li>优先级决定任务处理顺序</li>
            <li>设置截止日期便于跟踪进度</li>
            <li>可关联到具体活动便于管理</li>
          </ul>
        </div>

        <!-- 快捷操作（仅查看模式） -->
        <div v-if="mode === 'view'" class="actions-card">
          <div class="card-header">
            <el-icon><Operation /></el-icon>
            <span>快捷操作</span>
          </div>

          <div class="quick-actions">
            <el-button type="primary" @click="switchToEdit">
              <el-icon><Edit /></el-icon>
              编辑任务
            </el-button>
            <el-button @click="handleChangeStatus">
              <el-icon><RefreshRight /></el-icon>
              更改状态
            </el-button>
            <el-button type="danger" plain @click="handleDelete">
              <el-icon><Delete /></el-icon>
              删除任务
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
            {{ mode === 'create' ? '创建任务' : '保存更改' }}
          </el-button>
        </template>

        <template v-else>
          <el-button type="primary" @click="switchToEdit">编辑任务</el-button>
          <el-button type="danger" plain @click="handleDelete">删除任务</el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTasksStore, useEventsStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Timer,
  Link,
  View,
  Warning,
  Operation,
  Edit,
  Delete,
  RefreshRight
} from '@element-plus/icons-vue'

interface TaskData {
  id?: string | number
  title: string
  description: string
  priority: string
  status: string
  due_date: string
  progress: number
  event: string | number
  event_name?: string
  assigned_to_name: string
  created_at?: string
  updated_at?: string
}

interface Props {
  modelValue: boolean
  mode?: 'view' | 'create' | 'edit'
  taskData?: any
  eventsList?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  taskData: () => null,
  eventsList: () => []
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', data?: any): void
  (e: 'delete', data?: any): void
}>()

const tasksStore = useTasksStore()
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
    view: '任务详情',
    create: '新建任务',
    edit: '编辑任务'
  }
  return titles[props.mode] || '任务'
})

const formData = ref<TaskData>({
  title: '',
  description: '',
  priority: 'medium',
  status: 'pending',
  due_date: '',
  progress: 0,
  event: '',
  assigned_to_name: ''
})

const formRules = {
  title: [
    { required: true, message: '请输入任务标题', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 监听任务数据变化，填充表单
watch(() => [props.taskData, props.mode], ([newData, mode]) => {
  if ((mode === 'view' || mode === 'edit') && newData && Object.keys(newData).length > 0) {
    loading.value = true

    setTimeout(() => {
      formData.value = {
        id: newData.id,
        title: newData.title || '',
        description: newData.description || '',
        priority: newData.priority || 'medium',
        status: newData.status || 'pending',
        due_date: newData.due_date || '',
        progress: newData.progress || 0,
        event: newData.event || '',
        event_name: newData.event_name || '',
        assigned_to_name: newData.assigned_to_name || '',
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
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function getPriorityType(priority: string): string {
  const types: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return types[priority] || 'info'
}

function getPriorityText(priority: string): string {
  const texts: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return texts[priority] || priority
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

function getProgressColor(percentage: number): string {
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 50) return '#e6a23c'
  if (percentage >= 25) return '#409eff'
  return '#909399'
}

function getEventName(): string {
  if (!formData.value.event) return '未关联'

  // 先检查本地数据
  const event = props.eventsList.find(e => e.id === formData.value.event)
  if (event) return event.name

  // 再检查表单数据中的 event_name
  if (formData.value.event_name) return formData.value.event_name

  return '已关联'
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (!formData.value.title) {
      ElMessage.error('请输入任务标题')
      return
    }

    submitLoading.value = true

    if (props.mode === 'edit' && formData.value.id) {
      await tasksStore.updateTask(formData.value.id, formData.value)
      ElMessage.success('更新成功')
      emit('success', formData.value)
      handleClose()
    } else {
      await tasksStore.createTask(formData.value)
      ElMessage.success('创建成功')
      emit('success', formData.value)
      handleClose()
    }
  } catch (error: any) {
    console.error('Submit error:', error)
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

function switchToEdit() {
  emit('update:modelValue', false)
  setTimeout(() => {
    emit('success', { action: 'edit', data: props.taskData })
  }, 100)
}

function handleDelete() {
  ElMessageBox.confirm(
    `确定要删除任务"${formData.value.title}"吗？删除后无法恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('delete', props.taskData)
    handleClose()
  }).catch(() => {})
}

function handleChangeStatus() {
  const nextStatus = {
    pending: 'in_progress',
    in_progress: 'completed',
    completed: 'pending',
    cancelled: 'pending'
  }

  const currentStatus = formData.value.status
  const newStatus = nextStatus[currentStatus] || 'pending'

  ElMessageBox.confirm(
    `确定要将任务状态更改为"${getStatusText(newStatus)}"吗？`,
    '确认更改',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      if (formData.value.id) {
        await tasksStore.updateTask(formData.value.id, { ...formData.value, status: newStatus })
        formData.value.status = newStatus
        ElMessage.success('状态更新成功')
      }
    } catch (error) {
      console.error('Update status failed:', error)
      ElMessage.error('状态更新失败')
    }
  }).catch(() => {})
}

function handleClose() {
  isOpen.value = false
  if (props.mode === 'create') {
    resetForm()
  }
}

function resetForm() {
  formData.value = {
    title: '',
    description: '',
    priority: 'medium',
    status: 'pending',
    due_date: '',
    progress: 0,
    event: '',
    assigned_to_name: ''
  }
}
</script>

<style scoped>
.task-form-dialog .dialog-container {
  display: flex;
  gap: 24px;
  max-height: calc(90vh - 120px);
  overflow-y: auto;
}

.task-form-dialog .main-section {
  flex: 1;
  min-width: 500px;
}

.task-form-dialog .main-section .view-mode .task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #409eff;
}

.task-form-dialog .main-section .view-mode .task-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.task-form-dialog .main-section .view-mode .task-header .header-tags {
  display: flex;
  gap: 8px;
}

.task-form-dialog .main-section .view-mode .detail-descriptions {
  margin-bottom: 24px;
}

.task-form-dialog .main-section .view-mode .progress-section {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.task-form-dialog .main-section .view-mode .progress-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.task-form-dialog .main-section .view-mode .progress-section .progress-text {
  font-size: 14px;
  font-weight: 500;
}

.task-form-dialog .main-section .view-mode .description-section {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.task-form-dialog .main-section .view-mode .description-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.task-form-dialog .main-section .view-mode .description-section p {
  color: #606266;
  line-height: 1.8;
  word-break: break-word;
  white-space: pre-wrap;
  margin: 0;
}

.task-form-dialog .main-section .edit-mode .task-form .section-title {
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

.task-form-dialog .main-section .edit-mode .task-form .section-title:first-child {
  margin-top: 0;
}

.task-form-dialog .main-section .edit-mode .task-form .section-title .el-icon {
  color: #409eff;
}

.task-form-dialog .sidebar-section {
  width: 320px;
  flex-shrink: 0;
}

.task-form-dialog .sidebar-section .preview-card,
.task-form-dialog .sidebar-section .tips-card,
.task-form-dialog .sidebar-section .actions-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.task-form-dialog .sidebar-section .card-header {
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

.task-form-dialog .sidebar-section .card-header .el-icon {
  color: #409eff;
}

.task-form-dialog .sidebar-section .task-preview h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.task-form-dialog .sidebar-section .task-preview .meta-info {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.task-form-dialog .sidebar-section .task-preview .info-list .info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.task-form-dialog .sidebar-section .task-preview .info-list .info-item:last-child {
  border-bottom: none;
}

.task-form-dialog .sidebar-section .task-preview .info-list .info-item label {
  color: #606266;
  font-size: 13px;
}

.task-form-dialog .sidebar-section .task-preview .info-list .info-item value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.task-form-dialog .sidebar-section .tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.task-form-dialog .sidebar-section .tips-list li {
  padding: 6px 0;
  padding-left: 16px;
  position: relative;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.task-form-dialog .sidebar-section .tips-list li:before {
  content: "•";
  position: absolute;
  left: 0;
  color: #e6a23c;
  font-weight: bold;
}

.task-form-dialog .sidebar-section .quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-form-dialog .sidebar-section .quick-actions .el-button {
  justify-content: flex-start;
}

.task-form-dialog .footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.task-form-dialog :deep(.el-dialog__body) {
  padding: 20px;
}
</style>
