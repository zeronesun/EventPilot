<template>
  <div class="event-edit-page">
    <!-- 加载状态 -->
    <el-skeleton v-if="isLoading" :loading="true" animated :count="3">
      <template #template>
        <el-card>
          <el-skeleton-item variant="h3" style="width: 50%" />
          <el-divider />
          <el-row :gutter="20">
            <el-col :span="16">
              <el-skeleton-item variant="p" style="width: 100%" />
            </el-col>
            <el-col :span="8">
              <el-skeleton-item variant="p" style="width: 100%" />
            </el-col>
          </el-row>
        </el-card>
      </template>
    </el-skeleton>

    <!-- 编辑表单 -->
    <div v-else-if="!isLoading">
      <!-- 面包屑和操作栏 -->
      <div class="page-header">
        <el-breadcrumb>
          <el-breadcrumb-item :to="{ path: '/events' }">
            活动管理
          </el-breadcrumb-item>
          <el-breadcrumb-item :to="`/events/${route.params.id}`">
            活动详情
          </el-breadcrumb-item>
          <el-breadcrumb-item>编辑活动</el-breadcrumb-item>
        </el-breadcrumb>
        
        <div class="header-actions">
          <el-button @click="$router.back()" :disabled="isSubmitting">
            <el-icon><ArrowLeft /></el-icon>
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="isSubmitting"
            @click="handleSubmit"
          >
            <el-icon><Check /></el-icon>
            {{ submitButtonText }}
          </el-button>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 左侧表单区 -->
        <el-col :span="16">
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="120px"
            @submit.prevent="handleSubmit"
          >
            <el-card shadow="hover" class="form-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Edit /></el-icon>
                  <h3>基本信息</h3>
                </div>
              </template>

              <el-form-item label="活动名称" prop="name">
                <el-input
                  v-model="form.name"
                  placeholder="请输入活动名称"
                  clearable
                  maxlength="100"
                  show-word-limit
                  @input="handleNameInput"
                >
                  <template #prefix>
                    <el-icon><Memo /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="活动类型" prop="type">
                    <el-select
                      v-model="form.type"
                      placeholder="请选择活动类型"
                      style="width: 100%"
                      filterable
                    >
                      <el-option
                        v-for="option in typeOptions"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="活动状态" prop="status">
                    <el-select
                      v-model="form.status"
                      placeholder="请选择活动状态"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="option in statusOptions"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="负责人">
                <el-input
                  v-model="form.owner_name"
                  placeholder="请输入负责人"
                  clearable
                >
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-card>

            <el-card shadow="hover" class="form-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Clock /></el-icon>
                  <h3>时间规划</h3>
                </div>
              </template>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="开始时间" prop="start_date">
                    <el-date-picker
                      v-model="form.start_date"
                      type="datetime"
                      placeholder="请选择开始时间"
                      format="YYYY-MM-DD HH:mm"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      style="width: 100%"
                      :disabled-date="disabledStartDate"
                    />
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="结束时间">
                    <el-date-picker
                      v-model="form.end_date"
                      type="datetime"
                      placeholder="请选择结束时间"
                      format="YYYY-MM-DD HH:mm"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      style="width: 100%"
                      :disabled-date="disabledEndDate"
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="客户名称">
                <el-input
                  v-model="form.client"
                  placeholder="请输入客户名称"
                  clearable
                />
              </el-form-item>

              <el-form-item label="客户联系人">
                <el-input
                  v-model="form.client_contact"
                  placeholder="请输入客户联系人"
                  clearable
                />
              </el-form-item>
            </el-card>

            <el-card shadow="hover" class="form-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Coin /></el-icon>
                  <h3>预算信息</h3>
                </div>
              </template>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="预算金额">
                    <el-input-number
                      v-model="form.estimated_budget"
                      :min="0"
                      :precision="2"
                      :step="1000"
                      :max="10000000"
                      style="width: 100%"
                      placeholder="请输入预算金额"
                    />
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="实际支出">
                    <el-input-number
                      v-model="form.actual_budget"
                      :min="0"
                      :precision="2"
                      :step="1000"
                      :max="10000000"
                      style="width: 100%"
                      placeholder="请输入实际支出"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>

            <el-card shadow="hover" class="form-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Document /></el-icon>
                  <h3>详细说明</h3>
                </div>
              </template>

              <el-form-item label="活动说明">
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="6"
                  placeholder="请输入活动说明"
                  clearable
                  maxlength="1000"
                  show-word-limit
                />
              </el-form-item>
            </el-card>
          </el-form>
        </el-col>

        <!-- 右侧预览区 -->
        <el-col :span="8">
          <el-card shadow="hover" class="preview-card">
            <template #header>
              <div class="card-header">
                <el-icon><View /></el-icon>
                <h3>实时预览</h3>
              </div>
            </template>
            
            <el-alert
              title="活动预览"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                <div class="preview-content">
                  <div class="preview-title">
                    {{ form.name || '未命名活动' }}
                  </div>
                  
                  <div class="preview-meta">
                    <el-tag :type="getStatusType(form.status)">
                      {{ getStatusText(form.status) }}
                    </el-tag>
                    <span class="preview-type">{{ formatEventType(form.type) }}</span>
                  </div>
                  
                  <div class="preview-description" v-if="form.description">
                    {{ form.description.substring(0, 150) }}{{ form.description.length > 150 ? '...' : '' }}
                  </div>

                  <div class="preview-stats">
                    <div class="preview-stat">
                      <span class="stat-label">预算</span>
                      <span class="stat-value">￥{{ (form.estimated_budget || 0).toLocaleString() }}</span>
                    </div>
                    <div class="preview-stat">
                      <span class="stat-label">开始时间</span>
                      <span class="stat-value">{{ formatDate(form.start_date) }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </el-alert>

            <el-divider />

            <el-alert
              title="编辑提示"
              type="warning"
              :closable="false"
            >
              <ul class="edit-tips">
                <li v-for="tip in editTips" :key="tip">{{ tip }}</li>
              </ul>
            </el-alert>

            <el-divider />

            <div class="quick-stats">
              <el-statistic title="字段完成度">
                <template #formatter>
                  <el-progress
                    :percentage="fieldCompletion"
                    :color="getCompletionColor(fieldCompletion)"
                    :stroke-width="8"
                  />
                </template>
              </el-statistic>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 错误状态 -->
    <el-result
      v-else
      icon="error"
      title="加载失败"
      sub-title="请重试或联系管理员"
    >
      <template #extra>
        <el-button type="primary" @click="loadData">重新加载</el-button>
        <el-button @click="$router.back()">返回</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  ArrowLeft, Check, Edit, Clock, Coin, Document, View,
  Memo, User, Location
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const eventsStore = useEventsStore()

const formRef = ref<FormInstance>()
const isLoading = ref(false)
const isSubmitting = ref(false)

const submitButtonText = computed(() => {
  return isSubmitting.value ? '保存中...' : '保存'
})

const fieldCompletion = computed(() => {
  const required = [
    form.value.name,
    form.value.type,
    form.value.status,
    form.value.start_date
  ].filter(Boolean).length
  
  return Math.round((required / 4) * 100)
})

const editTips = [
  '所有带 * 的字段为必填项',
  '保存后会返回活动详情页',
  '取消操作将不会保存修改',
  '可实时查看预览效果'
]

const form = ref({
  name: '',
  type: 'conference',
  status: 'planning',
  start_date: '',
  end_date: '',
  estimated_budget: 0,
  actual_budget: null as number | null,
  description: '',
  client: '',
  client_contact: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' },
    { min: 2, max: 100, message: '活动名称长度为 2-100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择活动状态', trigger: 'change' }
  ],
  start_date: [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ]
}

// 下拉选项
const typeOptions = [
  { label: '会议', value: 'conference' },
  { label: '展会', value: 'exhibition' },
  { label: '演出', value: 'performance' },
  { label: '派对', value: 'party' },
  { label: '培训', value: 'training' },
  { label: '其他', value: 'other' }
]

const statusOptions = [
  { label: '策划中', value: 'planning' },
  { label: '执行中', value: 'executing' },
  { label: '已完成', value: 'completed' },
  { label: '已复盘', value: 'reviewed' },
  { label: '已取消', value: 'cancelled' }
]

onMounted(async () => {
  const eventId = route.params.id as string
  if (eventId) {
    await loadData()
  }
})

async function loadData() {
  const eventId = route.params.id as string
  if (!eventId) {
    ElMessage.error('活动ID不存在')
    router.push('/events')
    return
  }

  isLoading.value = true
  try {
    await eventsStore.fetchEvent(eventId)
    const event = eventsStore.currentEvent
    if (event) {
      fillForm(event)
    }
  } catch (error) {
    console.error('Failed to load event:', error)
    ElMessage.error('加载活动数据失败')
  } finally {
    isLoading.value = false
  }
}

function fillForm(event: any) {
  form.value = {
    name: event.name || '',
    type: event.type || 'conference',
    status: event.status || 'planning',
    start_date: event.start_date || '',
    end_date: event.end_date || '',
    estimated_budget: event.estimated_budget || 0,
    actual_budget: event.actual_budget ?? null,
    description: event.description || '',
    client: event.client || '',
    client_contact: event.client_contact || ''
  }
}

function handleNameInput() {
  // 可以添加实时验证或其他逻辑
}

function disabledStartDate(time: Date) {
  return time.getTime() < Date.now() - 8.64e7
}

function disabledEndDate(time: Date) {
  if (!form.value.start_date) return false
  return time.getTime() < new Date(form.value.start_date).getTime()
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请检查表单填写')
    return
  }

  const eventId = route.params.id as string
  if (!eventId) {
    ElMessage.error('活动ID不存在')
    return
  }

  isSubmitting.value = true
  try {
    await eventsStore.updateEvent(eventId, form.value)
    ElMessage.success('活动更新成功')
    router.push(`/events/${eventId}`)
  } catch (error) {
    console.error('Update failed:', error)
    ElMessage.error('活动更新失败')
  } finally {
    isSubmitting.value = false
  }
}

// 工具函数
function formatDate(date: string): string {
  if (!date) return '未设置'
  return new Date(date).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatEventType(type: string): string {
  const types: Record<string, string> = {
    conference: '会议',
    exhibition: '展会',
    performance: '演出',
    party: '派对',
    training: '培训',
    other: '其他'
  }
  return types[type] || type
}

function getStatusType(status: string): string {
  const types: Record<string, string> = {
    planning: 'info',
    executing: 'warning',
    completed: 'success',
    reviewed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    planning: '策划中',
    executing: '执行中',
    completed: '已完成',
    reviewed: '已复盘',
    cancelled: '已取消'
  }
  return texts[status] || status
}

function getCompletionColor(percentage: number): string {
  if (percentage >= 80) return '#67c23a'
  if (percentage >= 50) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.event-edit-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.form-card,
.preview-card {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  transition: box-shadow 0.3s;
}

.form-card:hover,
.preview-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-word;
}

.preview-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.preview-type {
  font-size: 14px;
  color: #606266;
}

.preview-description {
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
  word-break: break-word;
}

.preview-stats {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.preview-stat {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.preview-stat:last-child {
  margin-bottom: 0;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.edit-tips {
  margin: 0;
  padding-left: 20px;
}

.edit-tips li {
  margin: 6px 0;
  font-size: 13px;
  color: #606266;
}

.quick-stats {
  margin-top: 20px;
}
</style>
