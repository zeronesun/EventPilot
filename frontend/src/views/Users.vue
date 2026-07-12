<template>
  <div class="users-container">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button
        type="primary"
        @click="openCreateDialog"
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
        v-loading="isLoading" 
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
              @click="handleView(row)"
            >
              详情
            </el-button>
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

    <!-- 用户表单对话框（统一：详情/新建/编辑） -->
    <UserFormDialog
      v-model="dialogVisible"
      :mode="formMode"
      :user-data="selectedUserData"
      @success="handleFormSuccess"
      @delete="handleDeleteFromForm"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onActivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi, apiClient } from '@/api/client'
import UserFormDialog from '@/components/UserFormDialog.vue'

// 用户数据 - 从后端API加载
const users = ref([])
const isLoading = ref(false)

const usersStore = reactive({
  isLoading: false
})

// 统一的对话框状态
const dialogVisible = ref(false)
const formMode = ref<'view' | 'create' | 'edit'>('create')
const selectedUserData = ref(null)

const searchForm = reactive({
  username: '',
  role: ''
})

const pagination = reactive({
  current: 1,
  total: 0,
  pageSize: 20
})

onMounted(() => {
  fetchUsers()
})

onActivated(() => {
  fetchUsers()
})

async function fetchUsers(page = 1) {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('page', page.toString())
    params.set('page_size', pagination.pageSize.toString())
    
    if (searchForm.username) {
      params.set('search', searchForm.username)
    }
    if (searchForm.role) {
      params.set('role', searchForm.role)
    }
    
    const response = await apiClient.get(`/users/?${params.toString()}`)
    users.value = response.results || []
    pagination.total = response.count || 0
    pagination.current = page
  } catch (error) {
    console.error('Failed to fetch users:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    isLoading.value = false
  }
}

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
  pagination.current = 1
  fetchUsers(1)
}

function handleReset() {
  searchForm.username = ''
  searchForm.role = ''
  pagination.current = 1
  fetchUsers(1)
}

function handleView(row) {
  try {
    if (!row || typeof row !== 'object') {
      console.error('handleView: invalid row data', row)
      ElMessage.error('无效的用户数据')
      return
    }

    // 确保 selectedUserData 是 ref 对象
    if (selectedUserData && typeof selectedUserData === 'object' && 'value' in selectedUserData) {
      selectedUserData.value = row
    } else {
      console.error('selectedUserData is not a ref:', selectedUserData)
      return
    }

    // 确保 formMode 是 ref 对象
    if (formMode && typeof formMode === 'object' && 'value' in formMode) {
      formMode.value = 'view'
    } else {
      console.error('formMode is not a ref:', formMode)
      return
    }

    // 确保 dialogVisible 是 ref 对象
    if (dialogVisible && typeof dialogVisible === 'object' && 'value' in dialogVisible) {
      dialogVisible.value = true
    } else {
      console.error('dialogVisible is not a ref:', dialogVisible)
      return
    }
  } catch (error) {
    console.error('handleView error:', error)
    ElMessage.error('操作失败')
  }
}

function openCreateDialog() {
  try {
    if (selectedUserData && typeof selectedUserData === 'object' && 'value' in selectedUserData) {
      selectedUserData.value = null
    }
    if (formMode && typeof formMode === 'object' && 'value' in formMode) {
      formMode.value = 'create'
    }
    if (dialogVisible && typeof dialogVisible === 'object' && 'value' in dialogVisible) {
      dialogVisible.value = true
    }
  } catch (error) {
    console.error('openCreateDialog error:', error)
    ElMessage.error('操作失败')
  }
}

function handleEdit(row) {
  try {
    if (!row || typeof row !== 'object') {
      console.error('handleEdit: invalid row data', row)
      ElMessage.error('无效的用户数据')
      return
    }

    // 确保 selectedUserData 是 ref 对象
    if (selectedUserData && typeof selectedUserData === 'object' && 'value' in selectedUserData) {
      selectedUserData.value = row
    } else {
      console.error('selectedUserData is not a ref:', selectedUserData)
      return
    }

    // 确保 formMode 是 ref 对象
    if (formMode && typeof formMode === 'object' && 'value' in formMode) {
      formMode.value = 'edit'
    } else {
      console.error('formMode is not a ref:', formMode)
      return
    }

    // 确保 dialogVisible 是 ref 对象
    if (dialogVisible && typeof dialogVisible === 'object' && 'value' in dialogVisible) {
      dialogVisible.value = true
    } else {
      console.error('dialogVisible is not a ref:', dialogVisible)
      return
    }
  } catch (error) {
    console.error('handleEdit error:', error)
    ElMessage.error('操作失败')
  }
}

function handleFormSuccess(data) {
  try {
    // 刷新用户列表
    fetchUsers()

    // 如果是从查看模式切换到编辑模式
    if (data?.action === 'edit') {
      if (selectedUserData && typeof selectedUserData === 'object' && 'value' in selectedUserData) {
        selectedUserData.value = data.data
      }
      if (formMode && typeof formMode === 'object' && 'value' in formMode) {
        formMode.value = 'edit'
      }
      if (dialogVisible && typeof dialogVisible === 'object' && 'value' in dialogVisible) {
        dialogVisible.value = true
      }
    } else {
      const currentMode = formMode && typeof formMode === 'object' && 'value' in formMode ? formMode.value : 'create'
      ElMessage.success(currentMode === 'create' ? '用户创建成功' : '用户更新成功')
    }
  } catch (error) {
    console.error('handleFormSuccess error:', error)
  }
}

async function handleDeleteFromForm(user) {
  if (user?.id) {
    try {
      await apiClient.delete(`/users/${user.id}/`)
      ElMessage.success('删除成功')
    } catch (error) {
      console.error('Delete failed:', error)
      ElMessage.error('删除失败')
    }
    fetchUsers()
  }
}

async function handleDelete(row) {
  if (!row || typeof row !== 'object' || !row.id) {
    console.error('handleDelete: invalid row data', row)
    ElMessage.error('无效的用户数据')
    return
  }
  ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await apiClient.delete(`/users/${row.id}/`)
      ElMessage.success('删除成功')
      // 刷新列表
      await fetchUsers()
    } catch (error) {
      console.error('Delete failed:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

function handlePageChange(page) {
  pagination.current = page
  fetchUsers(page)
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