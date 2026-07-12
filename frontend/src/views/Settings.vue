<template>
  <div class="settings-container">
    <el-page-header @back="goBack" content="系统设置" />
    
    <el-card style="margin-top: 20px">
      <template #header>
        <h3>个人设置</h3>
      </template>
      
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card style="margin-top: 20px">
      <template #header>
        <h3>系统偏好</h3>
      </template>
      
      <el-form label-width="100px">
        <el-form-item label="主题">
          <el-select v-model="theme" placeholder="选择主题">
            <el-option label="浅色" value="light" />
            <el-option label="深色" value="dark" />
          </el-select>
        </el-form-item>
        <el-form-item label="语言">
          <el-select v-model="language" placeholder="选择语言">
            <el-option label="中文" value="zh-CN" />
            <el-option label="English" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { apiClient, usersApi } from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()

const theme = ref('light')
const language = ref('zh-CN')
const form = ref({
  username: '',
  email: '',
  display_name: ''
})

onMounted(() => {
  loadUserInfo()
})

onActivated(() => {
  loadUserInfo()
})

function loadUserInfo() {
  if (authStore.user) {
    form.value = {
      username: authStore.user.username || '',
      email: authStore.user.email || '',
      display_name: authStore.user.first_name + ' ' + authStore.user.last_name || ''
    }
  }
}

function goBack() {
  router.back()
}

async function saveSettings() {
  try {
    const [firstName, ...lastNameParts] = form.value.display_name.split(' ')
    const updateData = {
      email: form.value.email,
      first_name: firstName,
      last_name: lastNameParts.join(' ')
    }
    
    await apiClient.patch(`/users/${authStore.user?.id || ''}/`, updateData)
    
    if (authStore.user) {
      authStore.user.email = form.value.email
      authStore.user.first_name = firstName
      authStore.user.last_name = lastNameParts.join(' ')
    }
    
    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('Save settings failed:', error)
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}
</style>
