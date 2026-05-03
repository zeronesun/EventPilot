<template>
  <el-dialog
    v-model="isOpen"
    :title="dialogTitle"
    width="90%"
    top="5vh"
    :close-on-click-modal="false"
    @close="handleClose"
    class="user-form-dialog"
  >
    <el-skeleton v-if="loading" :rows="10" animated />

    <div v-else class="dialog-container">
      <!-- 左侧：表单/详情区域 -->
      <div class="main-section">
        <!-- 查看模式 -->
        <div v-if="isViewMode" class="view-mode">
          <div class="user-header">
            <div class="user-avatar">
              <el-avatar :size="80" :icon="UserFilled" />
            </div>
            <div class="user-info">
              <h2>{{ formData.first_name || formData.username || '未命名用户' }}</h2>
              <div class="header-tags">
                <el-tag :type="getRoleType(formData.role)" size="small">
                  {{ getRoleText(formData.role) }}
                </el-tag>
                <el-tag :type="formData.is_active ? 'success' : 'danger'" size="small">
                  {{ formData.is_active ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </div>
          </div>

          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="用户名">
              {{ formData.username }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ formData.email || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="部门">
              {{ formData.department || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="职位">
              {{ formData.position || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">
              {{ formatFullDate(formData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="最后登录" :span="2">
              {{ formatFullDate(formData.last_login) || '从未登录' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 权限说明 -->
          <div class="permissions-section">
            <h3>角色权限说明</h3>
            <el-alert
              :title="getRoleDescription(formData.role)"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
        </div>

        <!-- 编辑/新建模式：表单 -->
        <div v-else class="edit-mode">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
            class="user-form"
          >
            <!-- 基本信息 -->
            <div class="section-title">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名" prop="username">
                  <el-input
                    v-model="formData.username"
                    placeholder="请输入用户名"
                    :disabled="mode === 'edit'"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="邮箱" prop="email">
                  <el-input
                    v-model="formData.email"
                    type="email"
                    placeholder="请输入邮箱"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="姓名" prop="first_name">
                  <el-input
                    v-model="formData.first_name"
                    placeholder="请输入姓名"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="密码" prop="password">
                  <el-input
                    v-model="formData.password"
                    type="password"
                    :placeholder="mode === 'edit' ? '留空则不修改密码' : '请输入密码'"
                    show-password
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 工作信息 -->
            <div class="section-title">
              <el-icon><OfficeBuilding /></el-icon>
              <span>工作信息</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="部门">
                  <el-input
                    v-model="formData.department"
                    placeholder="请输入部门"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="职位">
                  <el-input
                    v-model="formData.position"
                    placeholder="请输入职位"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 权限设置 -->
            <div class="section-title">
              <el-icon><Lock /></el-icon>
              <span>权限设置</span>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="角色" prop="role">
                  <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
                    <el-option label="管理员" value="admin">
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>管理员</span>
                        <el-tag size="small" type="danger">最高权限</el-tag>
                      </div>
                    </el-option>
                    <el-option label="项目负责人" value="project_owner">
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>项目负责人</span>
                        <el-tag size="small" type="warning">管理权限</el-tag>
                      </div>
                    </el-option>
                    <el-option label="执行者" value="executor">
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>执行者</span>
                        <el-tag size="small" type="primary">普通权限</el-tag>
                      </div>
                    </el-option>
                    <el-option label="观察者" value="observer">
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>观察者</span>
                        <el-tag size="small" type="info">只读权限</el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态">
                  <el-switch
                    v-model="formData.is_active"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
              </el-col>
            </el-row>
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

          <div class="user-preview">
            <div class="preview-avatar">
              <el-avatar :size="60" :icon="UserFilled" />
            </div>
            <h3>{{ formData.first_name || formData.username || '新用户' }}</h3>

            <div class="meta-info">
              <el-tag :type="getRoleType(formData.role)" size="small">
                {{ getRoleText(formData.role) }}
              </el-tag>
              <el-tag :type="formData.is_active ? 'success' : 'danger'" size="small">
                {{ formData.is_active ? '启用' : '禁用' }}
              </el-tag>
            </div>

            <div class="info-list">
              <div class="info-item">
                <label>用户名</label>
                <value>{{ formData.username || '未填写' }}</value>
              </div>
              <div class="info-item">
                <label>邮箱</label>
                <value>{{ formData.email || '未填写' }}</value>
              </div>
              <div class="info-item">
                <label>部门</label>
                <value>{{ formData.department || '未填写' }}</value>
              </div>
              <div class="info-item">
                <label>职位</label>
                <value>{{ formData.position || '未填写' }}</value>
              </div>
            </div>
          </div>
        </div>

        <!-- 权限说明卡片 -->
        <div class="permissions-card">
          <div class="card-header">
            <el-icon><InfoFilled /></el-icon>
            <span>权限说明</span>
          </div>
          <ul class="permissions-list">
            <li>
              <strong>管理员：</strong>
              系统全部权限，包括用户管理、系统配置等
            </li>
            <li>
              <strong>项目负责人：</strong>
              项目管理、任务分配、数据查看等
            </li>
            <li>
              <strong>执行者：</strong>
              任务执行、进度更新、基础操作
            </li>
            <li>
              <strong>观察者：</strong>
              只读访问，可查看但不能修改数据
            </li>
          </ul>
        </div>

        <!-- 操作提示 -->
        <div class="tips-card">
          <div class="card-header">
            <el-icon><Warning /></el-icon>
            <span>操作提示</span>
          </div>
          <ul class="tips-list">
            <li>用户名和邮箱为必填项</li>
            <li>密码长度至少8位，包含字母和数字</li>
            <li>编辑时留空密码表示不修改</li>
            <li>禁用用户后将无法登录系统</li>
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
              编辑用户
            </el-button>
            <el-button
              :type="formData.is_active ? 'warning' : 'success'"
              @click="handleToggleStatus"
            >
              <el-icon><SwitchButton /></el-icon>
              {{ formData.is_active ? '禁用账户' : '启用账户' }}
            </el-button>
            <el-button type="danger" plain @click="handleDelete">
              <el-icon><Delete /></el-icon>
              删除用户
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
            {{ mode === 'create' ? '创建用户' : '保存更改' }}
          </el-button>
        </template>

        <template v-else>
          <el-button type="primary" @click="switchToEdit">编辑用户</el-button>
          <el-button type="danger" plain @click="handleDelete">删除用户</el-button>
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
  User,
  UserFilled,
  OfficeBuilding,
  Lock,
  View,
  InfoFilled,
  Warning,
  Operation,
  Edit,
  Delete,
  SwitchButton
} from '@element-plus/icons-vue'

interface UserData {
  id?: string | number
  username: string
  email: string
  password: string
  first_name: string
  department: string
  position: string
  role: string
  is_active: boolean
  created_at?: string
  last_login?: string
}

interface Props {
  modelValue: boolean
  mode?: 'view' | 'create' | 'edit'
  userData?: any
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  userData: () => null
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
    view: '用户详情',
    create: '新增用户',
    edit: '编辑用户'
  }
  return titles[props.mode] || '用户'
})

const formData = ref<UserData>({
  username: '',
  email: '',
  password: '',
  first_name: '',
  department: '',
  position: '',
  role: 'executor',
  is_active: true
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    {
      required: true,
      validator: (rule: any, value: string, callback: Function) => {
        if (props.mode === 'edit' && !value) {
          callback()
        } else if (!value || value.length === 0) {
          callback(new Error('请输入密码'))
        } else if (value.length < 8) {
          callback(new Error('密码长度至少 8 位'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 监听用户数据变化，填充表单
watch(() => [props.userData, props.mode], ([newData, mode]) => {
  if ((mode === 'view' || mode === 'edit') && newData && Object.keys(newData).length > 0) {
    loading.value = true

    setTimeout(() => {
      formData.value = {
        id: newData.id,
        username: newData.username || '',
        email: newData.email || '',
        password: '', // 编辑时不回显密码
        first_name: newData.first_name || '',
        department: newData.department || '',
        position: newData.position || '',
        role: newData.role || 'executor',
        is_active: newData.is_active !== undefined ? newData.is_active : true,
        created_at: newData.created_at || '',
        last_login: newData.last_login || ''
      }
      loading.value = false
    }, 300)
  } else if (mode === 'create') {
    resetForm()
  }
}, { immediate: true, deep: true })

function getRoleType(role: string): string {
  const types: Record<string, string> = {
    admin: 'danger',
    project_owner: 'warning',
    executor: 'primary',
    observer: 'info'
  }
  return types[role] || 'info'
}

function getRoleText(role: string): string {
  const texts: Record<string, string> = {
    admin: '管理员',
    project_owner: '项目负责人',
    executor: '执行者',
    observer: '观察者'
  }
  return texts[role] || role
}

function getRoleDescription(role: string): string {
  const descriptions: Record<string, string> = {
    admin: '拥有系统的全部管理权限，可以管理用户、配置系统、查看所有数据',
    project_owner: '可以管理项目、分配任务、查看项目相关的所有数据和报表',
    executor: '可以执行被分配的任务、更新任务进度、参与协作',
    observer: '只能查看数据，无法进行任何修改操作'
  }
  return descriptions[role] || '普通用户'
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

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    submitLoading.value = true

    const submitData: any = {
      username: formData.value.username,
      email: formData.value.email,
      first_name: formData.value.first_name,
      department: formData.value.department,
      position: formData.value.position,
      role: formData.value.role,
      is_active: formData.value.is_active
    }

    // 仅在新建或编辑时有密码时才提交
    if (formData.value.password) {
      submitData.password = formData.value.password
    }

    if (props.mode === 'edit' && formData.value.id) {
      await apiClient.put(`/users/${formData.value.id}/`, submitData)
      ElMessage.success('更新成功')
      emit('success', formData.value)
      handleClose()
    } else {
      if (!formData.value.password) {
        ElMessage.error('请输入密码')
        submitLoading.value = false
        return
      }

      await apiClient.post('/users/', {
        ...submitData,
        password: formData.value.password
      })
      ElMessage.success('创建成功')
      emit('success', formData.value)
      handleClose()
    }
  } catch (error) {
    console.error('Submit error:', error)
    if (error?.response?.data) {
      const errorMsg = Object.values(error.response.data).flat().join('; ')
      ElMessage.error(errorMsg)
    } else {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitLoading.value = false
  }
}

function switchToEdit() {
  emit('update:modelValue', false)
  setTimeout(() => {
    emit('success', { action: 'edit', data: props.userData })
  }, 100)
}

function handleDelete() {
  ElMessageBox.confirm(
    `确定要删除用户"${formData.value.username}"吗？删除后无法恢复。`,
    '确认删除',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    emit('delete', props.userData)
    handleClose()
  }).catch(() => {})
}

function handleToggleStatus() {
  const newStatus = !formData.value.is_active
  const action = newStatus ? '启用' : '禁用'

  ElMessageBox.confirm(
    `确定要${action}用户"${formData.value.username}"吗？`,
    `确认${action}`,
    {
      confirmButtonText: `确定${action}`,
      cancelButtonText: '取消',
      type: newStatus ? 'success' : 'warning'
    }
  ).then(async () => {
    try {
      if (formData.value.id) {
        await apiClient.patch(`/users/${formData.value.id}/`, { is_active: newStatus })
        formData.value.is_active = newStatus
        ElMessage.success(`用户已${action}`)
      }
    } catch (error) {
      console.error('Toggle status failed:', error)
      ElMessage.error(`${action}失败`)
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
    username: '',
    email: '',
    password: '',
    first_name: '',
    department: '',
    position: '',
    role: 'executor',
    is_active: true
  }
}
</script>

<style scoped>
.user-form-dialog .dialog-container {
  display: flex;
  gap: 24px;
  max-height: calc(90vh - 120px);
  overflow-y: auto;
}

.user-form-dialog .main-section {
  flex: 1;
  min-width: 500px;
}

.user-form-dialog .main-section .view-mode .user-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 2px solid #409eff;
}

.user-form-dialog .main-section .view-mode .user-header .user-avatar {
  flex-shrink: 0;
}

.user-form-dialog .main-section .view-mode .user-header .user-info {
  flex: 1;
}

.user-form-dialog .main-section .view-mode .user-header .user-info h2 {
  margin: 0 0 8px 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.user-form-dialog .main-section .view-mode .user-header .user-info .header-tags {
  display: flex;
  gap: 8px;
}

.user-form-dialog .main-section .view-mode .detail-descriptions {
  margin-bottom: 24px;
}

.user-form-dialog .main-section .view-mode .permissions-section {
  margin-top: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.user-form-dialog .main-section .view-mode .permissions-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.user-form-dialog .main-section .edit-mode .user-form .section-title {
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

.user-form-dialog .main-section .edit-mode .user-form .section-title:first-child {
  margin-top: 0;
}

.user-form-dialog .main-section .edit-mode .user-form .section-title .el-icon {
  color: #409eff;
}

.user-form-dialog .sidebar-section {
  width: 320px;
  flex-shrink: 0;
}

.user-form-dialog .sidebar-section .preview-card,
.user-form-dialog .sidebar-section .permissions-card,
.user-form-dialog .sidebar-section .tips-card,
.user-form-dialog .sidebar-section .actions-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.user-form-dialog .sidebar-section .card-header {
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

.user-form-dialog .sidebar-section .card-header .el-icon {
  color: #409eff;
}

.user-form-dialog .sidebar-section .user-preview {
  text-align: center;
}

.user-form-dialog .sidebar-section .user-preview .preview-avatar {
  margin-bottom: 12px;
}

.user-form-dialog .sidebar-section .user-preview h3 {
  font-size: 18px;
  margin: 0 0 12px 0;
  color: #303133;
}

.user-form-dialog .sidebar-section .user-preview .meta-info {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.user-form-dialog .sidebar-section .user-preview .info-list {
  text-align: left;
}

.user-form-dialog .sidebar-section .user-preview .info-list .info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.user-form-dialog .sidebar-section .user-preview .info-list .info-item:last-child {
  border-bottom: none;
}

.user-form-dialog .sidebar-section .user-preview .info-list .info-item label {
  color: #606266;
  font-size: 13px;
}

.user-form-dialog .sidebar-section .user-preview .info-list .info-item value {
  color: #303133;
  font-weight: 500;
  font-size: 13px;
}

.user-form-dialog .sidebar-section .permissions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-form-dialog .sidebar-section .permissions-list li {
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.user-form-dialog .sidebar-section .permissions-list li:last-child {
  border-bottom: none;
}

.user-form-dialog .sidebar-section .permissions-list li strong {
  color: #303133;
  font-weight: 600;
}

.user-form-dialog .sidebar-section .tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-form-dialog .sidebar-section .tips-list li {
  padding: 6px 0;
  padding-left: 16px;
  position: relative;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.user-form-dialog .sidebar-section .tips-list li:before {
  content: "•";
  position: absolute;
  left: 0;
  color: #e6a23c;
  font-weight: bold;
}

.user-form-dialog .sidebar-section .quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-form-dialog .sidebar-section .quick-actions .el-button {
  justify-content: flex-start;
}

.user-form-dialog .footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.user-form-dialog :deep(.el-dialog__body) {
  padding: 20px;
}
</style>
