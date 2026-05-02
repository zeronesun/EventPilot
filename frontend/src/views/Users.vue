<template>
  <div class="users-container">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button
        type="primary"
        @click="dialogVisible = true"
      >
        新增用户
      </el-button>
    </div>

    <el-card class="search-card">
      <el-form
        :inline="true"
        :model="searchForm"
      >
        <el-form-item label="用户名">
          <el-input
            v-model="searchForm.username"
            placeholder="搜索用户名"
            clearable
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="searchForm.role"
            placeholder="选择角色"
            clearable
          >
            <el-option
              label="全部"
              value=""
            />
            <el-option
              label="管理员"
              value="admin"
            />
            <el-option
              label="项目负责人"
              value="project_owner"
            />
            <el-option
              label="执行者"
              value="executor"
            />
            <el-option
              label="观察者"
              value="observer"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleSearch"
          >
            搜索
          </el-button>
          <el-button @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table 
        v-loading="usersStore.isLoading" 
        :data="users"
        stripe
        border
      >
        <el-table-column
          prop="username"
          label="用户名"
          width="150"
        />
        <el-table-column
          prop="email"
          label="邮箱"
          width="200"
        />
        <el-table-column
          prop="first_name"
          label="姓名"
          width="120"
        />
        <el-table-column
          prop="department"
          label="部门"
          width="120"
        />
        <el-table-column
          prop="position"
          label="职位"
          width="120"
        />
        <el-table-column
          prop="is_active"
          label="状态"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="row.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="180"
        >
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="pagination.total > 0"
        v-model:current-page="pagination.current"
        :page-size="20"
        :total="pagination.total"
        layout="total, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="600px"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item
          label="用户名"
          prop="username"
        >
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
          />
        </el-form-item>
        <el-form-item
          label="邮箱"
          prop="email"
        >
          <el-input
            v-model="userForm.email"
            type="email"
            placeholder="请输入邮箱"
          />
        </el-form-item>
        <el-form-item
          label="密码"
          prop="password"
        >
          <el-input 
            v-model="userForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item
          label="姓名"
          prop="first_name"
        >
          <el-input
            v-model="userForm.first_name"
            placeholder="请输入姓名"
          />
        </el-form-item>
        <el-form-item label="部门">
          <el-input
            v-model="userForm.department"
            placeholder="请输入部门"
          />
        </el-form-item>
        <el-form-item label="职位">
          <el-input
            v-model="userForm.position"
            placeholder="请输入职位"
          />
        </el-form-item>
        <el-form-item
          label="角色"
          prop="role"
        >
          <el-select
            v-model="userForm.role"
            placeholder="请选择角色"
          >
            <el-option
              label="执行者"
              value="executor"
            />
            <el-option
              label="项目负责人"
              value="project_owner"
            />
            <el-option
              label="管理员"
              value="admin"
            />
            <el-option
              label="观察者"
              value="observer"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="userForm.is_active" 
            :active-text="userForm.is_active ? '启用' : '禁用'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onActivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 临时状态管理（实际应该连接到后端API）
const users = ref([
  {
    id: '1',
    username: 'admin',
    email: 'admin@example.com',
    first_name: '管理员',
    department: '技术部',
    position: '系统管理员',
    role: 'admin',
    is_active: true,
    created_at: '2026-04-19T10:00:00Z'
  }
])

const usersStore = reactive({
  isLoading: false
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const userFormRef = ref()

const searchForm = reactive({
  username: '',
  role: ''
})

const pagination = reactive({
  current: 1,
  total: 1
})

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  first_name: '',
  department: '',
  position: '',
  role: 'executor',
  is_active: true
})

const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

onMounted(() => {
  // 数据已硬编码，无需加载
  console.log('Users page mounted')
})

onActivated(() => {
  // 页面激活时确保数据可见
  console.log('Users page activated')
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleSearch() {
  // TODO: 实现搜索逻辑
  ElMessage.info('搜索功能待实现')
}

function handleReset() {
  searchForm.username = ''
  searchForm.role = ''
}

function handleEdit(row) {
  isEdit.value = true
  dialogVisible.value = true
  Object.assign(userForm, {
    ...row,
    password: '' // 编辑时密码不回显
  })
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // TODO: 实现删除逻辑
    ElMessage.success('删除成功')
  }).catch(() => {})
}

async function handleSubmit() {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    // TODO: 实现表单提交逻辑
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    
    // 重置表单
    Object.assign(userForm, {
      username: '',
      email: '',
      password: '',
      first_name: '',
      department: '',
      position: '',
      role: 'executor',
      is_active: true
    })
  } catch (error) {
    console.error('Validation failed:', error)
  } finally {
    submitting.value = false
  }
}

function handlePageChange(page) {
  pagination.current = page
  // TODO: 实现分页逻辑
}
</script>

<style scoped>
.users-container {
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

.search-card {
  margin-bottom: 20px;
}

.table-card {
  min-height: 400px;
}
</style>