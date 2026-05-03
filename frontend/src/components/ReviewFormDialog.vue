<template>
  <el-dialog
    v-model="isOpen"
    :title="dialogTitle"
    width="92%"
    top="3vh"
    :close-on-click-modal="false"
    @close="handleClose"
    class="review-form-dialog"
  >
    <el-skeleton v-if="loading" :rows="12" animated />

    <div v-else class="dialog-container">
      <!-- 左侧：表单/详情区域 -->
      <div class="main-section">
        <!-- 查看模式 -->
        <div v-if="isViewMode" class="view-mode">
          <div class="review-header">
            <h2>{{ formData.title || '未命名复盘' }}</h2>
            <div class="header-tags">
              <el-tag :type="getStatusType(formData.status)" size="large" effect="dark">
                {{ getStatusText(formData.status) }}
              </el-tag>
              <el-tag type="info" size="small" v-if="formData.event_name">
                {{ formData.event_name }}
              </el-tag>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="复盘状态">
              <el-tag :type="getStatusType(formData.status)">
                {{ getStatusText(formData.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="关联活动">
              {{ formData.event_name || '未关联' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatFullDate(formData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间">
              {{ formatFullDate(formData.completed_at) || '未完成' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 复盘维度 -->
          <div class="dimensions-section">
            <h3><el-icon><DataAnalysis /></el-icon> 复盘维度</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="目标达成">
                <div class="dimension-content">{{ formData.goal_achievement || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="流程执行">
                <div class="dimension-content">{{ formData.process_execution || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="成本控制">
                <div class="dimension-content">{{ formData.cost_control || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="客户反馈">
                <div class="dimension-content">{{ formData.customer_feedback || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="团队协作">
                <div class="dimension-content">{{ formData.team_collaboration || '未填写' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 总结与改进 -->
          <div class="summary-section">
            <h3><el-icon><Document /></el-icon> 总结与改进</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="成功经验">
                <div class="summary-content success">{{ formData.successes || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="待改进项">
                <div class="summary-content warning">{{ formData.improvements || '未填写' }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="行动项">
                <div class="summary-content info">{{ formData.action_items || '未填写' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 完成度统计 -->
          <div v-if="mode === 'view'" class="completion-stats">
            <h3>填写完成度</h3>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="复盘维度" :precision="0">
                  <template #formatter>
                    <span :class="getCompletionClass(getDimensionsCompletion())">
                      {{ getDimensionsCompletion() }}%
                    </span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="总结改进" :precision="0">
                  <template #formatter>
                    <span :class="getCompletionClass(getSummaryCompletion())">
                      {{ getSummaryCompletion() }}%
                    </span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="总体完成度" :precision="0">
                  <template #formatter>
                    <span :class="getCompletionClass(getTotalCompletion())">
                      {{ getTotalCompletion() }}%
                    </span>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            <el-progress
              :percentage="getTotalCompletion()"
              :color="getProgressColor(getTotalCompletion())"
              :stroke-width="12"
              class="total-progress"
            />
          </div>
        </div>

        <!-- 编辑/新建模式：表单 -->
        <div v-else class="edit-mode">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="120px"
            class="review-form"
          >
            <!-- 基本信息 -->
            <div class="section-title">
              <el-icon><InfoFilled /></el-icon>
              <span>基本信息</span>
            </div>

            <el-form-item label="复盘标题" prop="title">
              <el-input
                v-model="formData.title"
                placeholder="请输入复盘标题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="关联活动" prop="event">
              <el-select
                v-model="formData.event"
                placeholder="请选择关联活动（可选）"
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

            <!-- 复盘维度 -->
            <div class="section-title">
              <el-icon><DataAnalysis /></el-icon>
              <span>复盘维度</span>
            </div>

            <el-form-item label="目标达成">
              <el-input
                v-model="formData.goal_achievement"
                type="textarea"
                placeholder="请描述目标达成情况，包括是否达成、达成程度等"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="流程执行">
              <el-input
                v-model="formData.process_execution"
                type="textarea"
                placeholder="请描述流程执行情况，包括流程顺畅度、问题点等"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="成本控制">
              <el-input
                v-model="formData.cost_control"
                type="textarea"
                placeholder="请描述成本控制情况，包括预算使用、超支原因等"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="客户反馈">
              <el-input
                v-model="formData.customer_feedback"
                type="textarea"
                placeholder="请描述客户反馈，包括满意度、建议等"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="团队协作">
              <el-input
                v-model="formData.team_collaboration"
                type="textarea"
                placeholder="请描述团队协作情况，包括沟通效率、配合度等"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <!-- 总结与改进 -->
            <div class="section-title">
              <el-icon><Document /></el-icon>
              <span>总结与改进</span>
            </div>

            <el-form-item label="成功经验">
              <el-input
                v-model="formData.successes"
                type="textarea"
                placeholder="请总结本次活动的成功经验，便于后续复用"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="待改进项">
              <el-input
                v-model="formData.improvements"
                type="textarea"
                placeholder="请列出需要改进的地方，避免再次发生"
                :rows="3"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="行动项">
              <el-input
                v-model="formData.action_items"
                type="textarea"
                placeholder="请列出后续的行动项和责任人"
                :rows="3"
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

          <div class="review-preview">
            <h3>{{ formData.title || '未命名复盘' }}</h3>

            <div class="meta-info">
              <el-tag :type="getStatusType(formData.status)" size="small">
                {{ getStatusText(formData.status) }}
              </el-tag>
            </div>

            <div class="info-list">
              <div class="info-item">
                <label>关联活动</label>
                <value>{{ getEventName() }}</value>
              </div>
              <div class="info-item">
                <label>状态</label>
                <value>{{ getStatusText(formData.status) }}</value>
              </div>
              <div class="info-item">
                <label>维度完成度</label>
                <value>{{ getDimensionsCompletion() }}%</value>
              </div>
              <div class="info-item">
                <label>总完成度</label>
                <value>{{ getTotalCompletion() }}%</value>
              </div>
            </div>

            <el-progress
              :percentage="getTotalCompletion()"
              :color="getProgressColor(getTotalCompletion())"
              :stroke-width="8"
              class="preview-progress"
            />
          </div>
        </div>

        <!-- 填写指南 -->
        <div class="guide-card">
          <div class="card-header">
            <el-icon><Reading /></el-icon>
            <span>填写指南</span>
          </div>
          <ul class="guide-list">
            <li><strong>目标达成：</strong>对比预期目标和实际结果</li>
            <li><strong>流程执行：</strong>评估流程的效率和问题</li>
            <li><strong>成本控制：</strong>分析预算使用情况</li>
            <li><strong>客户反馈：</strong>收集整理客户意见</li>
            <li><strong>团队协作：</strong>评价团队配合效果</li>
          </ul>
        </div>

        <!-- 操作提示 -->
        <div class="tips-card">
          <div class="card-header">
            <el-icon><Warning /></el-icon>
            <span>操作提示</span>
          </div>
          <ul class="tips-list">
            <li>复盘标题为必填项</li>
            <li>尽可能详细地填写各维度内容</li>
            <li>成功经验要具体可复制</li>
            <li>改进项要有可执行的方案</li>
            <li>行动项要明确责任人和时间</li>
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
              编辑复盘
            </el-button>
            <el-button
              v-if="formData.status !== 'completed'"
              type="success"
              @click="handleComplete"
            >
              <el-icon><CircleCheck /></el-icon>
              标记完成
            </el-button>
            <el-button type="danger" plain @click="handleDelete">
              <el-icon><Delete /></el-icon>
              删除复盘
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
            {{ mode === 'create' ? '创建复盘' : '保存更改' }}
          </el-button>
        </template>

        <template v-else>
          <el-button type="primary" @click="switchToEdit">编辑复盘</el-button>
          <el-button type="danger" plain @click="handleDelete">删除复盘</el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '@/api/client'
import {
  InfoFilled,
  DataAnalysis,
  Document,
  View,
  Warning,
  Operation,
  Edit,
  Delete,
  Reading,
  CircleCheck
} from '@element-plus/icons-vue'

interface ReviewData {
  id?: string | number
  title: string
  event: string | number
  event_name?: string
  goal_achievement: string
  process_execution: string
  cost_control: string
  customer_feedback: string
  team_collaboration: string
  successes: string
  improvements: string
  action_items: string
  status: string
  created_at?: string
  completed_at?: string
}

interface Props {
  modelValue: boolean
  mode?: 'view' | 'create' | 'edit'
  reviewData?: any
  eventsList?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  reviewData: () => null,
  eventsList: () => []
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', data?: any): void
  (e: 'delete', data?: any): void
}>()

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
    view: '复盘详情',
    create: '新建复盘',
    edit: '编辑复盘'
  }
  return titles[props.mode] || '复盘'
})

const formData = ref<ReviewData>({
  title: '',
  event: '',
  goal_achievement: '',
  process_execution: '',
  cost_control: '',
  customer_feedback: '',
  team_collaboration: '',
  successes: '',
  improvements: '',
  action_items: '',
  status: 'draft'
})

const formRules = {
  title: [
    { required: true, message: '请输入复盘标题', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ]
}

// 监听复盘数据变化，填充表单
watch(() => [props.reviewData, props.mode], ([newData, mode]) => {
  if ((mode === 'view' || mode === 'edit') && newData && Object.keys(newData).length > 0) {
    loading.value = true

    setTimeout(() => {
      formData.value = {
        id: newData.id,
        title: newData.title || '',
        event: newData.event || '',
        event_name: newData.event_name || '',
        goal_achievement: newData.goal_achievement || '',
        process_execution: newData.process_execution || '',
        cost_control: newData.cost_control || '',
        customer_feedback: newData.customer_feedback || '',
        team_collaboration: newData.team_collaboration || '',
        successes: newData.successes || '',
        improvements: newData.improvements || '',
        action_items: newData.action_items || '',
        status: newData.status || 'draft',
        created_at: newData.created_at || '',
        completed_at: newData.completed_at || ''
      }
      loading.value = false
    }, 300)
  } else if (mode === 'create') {
    resetForm()
  }
}, { immediate: true, deep: true })

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    draft: 'info',
    in_progress: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    draft: '草稿',
    in_progress: '进行中',
    completed: '已完成'
  }
  return texts[status] || status
}

function formatDate(date?: string): string {
  if (!date) return ''
  try {
    return new Date(date).toLocaleDateString('zh-CN')
  } catch {
    return date
  }
}

function formatFullDate(date?: string): string {
  if (!date) return ''
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

function getEventName(): string {
  if (!formData.value.event) return '未关联'

  const event = props.eventsList.find(e => e.id === formData.value.event)
  if (event) return event.name

  if (formData.value.event_name) return formData.value.event_name

  return '已关联'
}

// 计算各部分完成度
function getDimensionsCompletion(): number {
  const fields = [
    formData.value.goal_achievement,
    formData.value.process_execution,
    formData.value.cost_control,
    formData.value.customer_feedback,
    formData.value.team_collaboration
  ]

  const filledCount = fields.filter(field => field && field.trim().length > 0).length
  return Math.round((filledCount / fields.length) * 100)
}

function getSummaryCompletion(): number {
  const fields = [
    formData.value.successes,
    formData.value.improvements,
    formData.value.action_items
  ]

  const filledCount = fields.filter(field => field && field.trim().length > 0).length
  return Math.round((filledCount / fields.length) * 100)
}

function getTotalCompletion(): number {
  const dimensionsWeight = 5 / 8 // 维度占 62.5%
  const summaryWeight = 3 / 8 // 总结占 37.5%

  const total = (getDimensionsCompletion() * dimensionsWeight) + (getSummaryCompletion() * summaryWeight)
  return Math.round(total)
}

function getCompletionClass(percentage: number): string {
  if (percentage >= 80) return 'completion-high'
  if (percentage >= 50) return 'completion-medium'
  return 'completion-low'
}

function getProgressColor(percentage: number): string {
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 50) return '#e6a23c'
  return '#f56c6c'
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (!formData.value.title) {
      ElMessage.error('请输入复盘标题')
      return
    }

    submitLoading.value = true

    const submitData = {
      title: formData.value.title,
      event: formData.value.event,
      goal_achievement: formData.value.goal_achievement,
      process_execution: formData.value.process_execution,
      cost_control: formData.value.cost_control,
      customer_feedback: formData.value.customer_feedback,
      team_collaboration: formData.value.team_collaboration,
      successes: formData.value.successes,
      improvements: formData.value.improvements,
      action_items: formData.value.action_items
    }

    if (props.mode === 'edit' && formData.value.id) {
      await apiClient.put(`/reviews/${formData.value.id}/`, submitData)
      ElMessage.success('更新成功')
      emit('success', formData.value)
      handleClose()
    } else {
      await apiClient.post('/reviews/', { ...submitData, status: 'draft' })
      ElMessage.success('创建成功')
      emit('success', formData.value)
      handleClose()
    }
  } catch (error: any) {
    console.error('Submit error:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    submitLoading.value = false
  }
}

function switchToEdit() {
  emit('update:modelValue', false)
  setTimeout(() => {
    emit('success', { action: 'edit', data: props.reviewData })
  }, 100)
}

function handleDelete() {
  ElMessageBox.confirm(
    `确定要删除复盘"${formData.value.title}"吗？删除后无法恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('delete', props.reviewData)
    handleClose()
  }).catch(() => {})
}

function handleComplete() {
  ElMessageBox.confirm(
    '确定要将该复盘标记为已完成吗？完成后将无法再编辑。',
    '确认完成',
    {
      confirmButtonText: '确定完成',
      cancelButtonText: '取消',
      type: 'success'
    }
  ).then(async () => {
    try {
      if (formData.value.id) {
        await apiClient.post(`/reviews/${formData.value.id}/complete/`)
        formData.value.status = 'completed'
        ElMessage.success('复盘已完成')
        emit('success', formData.value)
      }
    } catch (error) {
      console.error('Complete failed:', error)
      ElMessage.error('完成失败')
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
    event: '',
    goal_achievement: '',
    process_execution: '',
    cost_control: '',
    customer_feedback: '',
    team_collaboration: '',
    successes: '',
    improvements: '',
    action_items: '',
    status: 'draft'
  }
}
</script>

<style scoped>
.review-form-dialog .dialog-container {
  display: flex;
  gap: 24px;
  max-height: calc(90vh - 120px);
  overflow-y: auto;
}

.review-form-dialog .main-section {
  flex: 1;
  min-width: 500px;
}

.review-form-dialog .main-section .view-mode .review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #409eff;
}

.review-form-dialog .main-section .view-mode .review-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.review-form-dialog .main-section .view-mode .review-header .header-tags {
  display: flex;
  gap: 8px;
}

.review-form-dialog .main-section .view-mode .detail-descriptions {
  margin-bottom: 24px;
}

.review-form-dialog .main-section .view-mode .dimensions-section,
.review-form-dialog .main-section .view-mode .summary-section,
.review-form-dialog .main-section .view-mode .completion-stats {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.review-form-dialog .main-section .view-mode .dimensions-section h3,
.review-form-dialog .main-section .view-mode .summary-section h3,
.review-form-dialog .main-section .view-mode .completion-stats h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.review-form-dialog .main-section .view-mode .dimensions-section h3 .el-icon,
.review-form-dialog .main-section .view-mode .summary-section h3 .el-icon,
.review-form-dialog .main-section .view-mode .completion-stats h3 .el-icon {
  color: #409eff;
}

.review-form-dialog .main-section .view-mode .dimension-content,
.review-form-dialog .main-section .view-mode .summary-content {
  white-space: pre-wrap;
  line-height: 1.8;
  word-break: break-word;
}

.review-form-dialog .main-section .view-mode .dimension-content.success,
.review-form-dialog .main-section .view-mode .summary-content.success {
  color: #67c23a;
}

.review-form-dialog .main-section .view-mode .dimension-content.warning,
.review-form-dialog .main-section .view-mode .summary-content.warning {
  color: #e6a23c;
}

.review-form-dialog .main-section .view-mode .dimension-content.info,
.review-form-dialog .main-section .view-mode .summary-content.info {
  color: #409eff;
}

.review-form-dialog .main-section .view-mode .completion-high {
  color: #67c23a;
  font-weight: 600;
  font-size: 18px;
}

.review-form-dialog .main-section .view-mode .completion-medium {
  color: #e6a23c;
  font-weight: 600;
  font-size: 18px;
}

.review-form-dialog .main-section .view-mode .completion-low {
  color: #f56c6c;
  font-weight: 600;
  font-size: 18px;
}

.review-form-dialog .main-section .view-mode .total-progress {
  margin-top: 20px;
}

.review-form-dialog .main-section .edit-mode .review-form .section-title {
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

.review-form-dialog .main-section .edit-mode .review-form .section-title:first-child {
  margin-top: 0;
}

.review-form-dialog .main-section .edit-mode .review-form .section-title .el-icon {
  color: #409eff;
}

.review-form-dialog .sidebar-section {
  width: 320px;
  flex-shrink: 0;
}

.review-form-dialog .sidebar-section .preview-card,
.review-form-dialog .sidebar-section .guide-card,
.review-form-dialog .sidebar-section .tips-card,
.review-form-dialog .sidebar-section .actions-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.review-form-dialog .sidebar-section .card-header {
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

.review-form-dialog .sidebar-section .card-header .el-icon {
  color: #409eff;
}

.review-form-dialog .sidebar-section .review-preview h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.review-form-dialog .sidebar-section .review-preview .meta-info {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.review-form-dialog .sidebar-section .review-preview .info-list .info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.review-form-dialog .sidebar-section .review-preview .info-list .info-item:last-child {
  border-bottom: none;
}

.review-form-dialog .sidebar-section .review-preview .info-list .info-item label {
  color: #606266;
  font-size: 13px;
}

.review-form-dialog .sidebar-section .review-preview .info-list .info-item value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.review-form-dialog .sidebar-section .review-preview .preview-progress {
  margin-top: 16px;
}

.review-form-dialog .sidebar-section .guide-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.review-form-dialog .sidebar-section .guide-list li {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.review-form-dialog .sidebar-section .guide-list li:last-child {
  border-bottom: none;
}

.review-form-dialog .sidebar-section .guide-list li strong {
  color: #303133;
  font-weight: 600;
}

.review-form-dialog .sidebar-section .tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.review-form-dialog .sidebar-section .tips-list li {
  padding: 6px 0;
  padding-left: 16px;
  position: relative;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.review-form-dialog .sidebar-section .tips-list li:before {
  content: "•";
  position: absolute;
  left: 0;
  color: #e6a23c;
  font-weight: bold;
}

.review-form-dialog .sidebar-section .quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.review-form-dialog .sidebar-section .quick-actions .el-button {
  justify-content: flex-start;
}

.review-form-dialog .footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.review-form-dialog :deep(.el-dialog__body) {
  padding: 20px;
}
</style>
