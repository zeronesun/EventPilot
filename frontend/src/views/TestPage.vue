<template>
  <div class="test-container">
    <h1>布局测试页面</h1>
    <p>如果你能看到这个页面，说明路由工作正常</p>
    <p>当前路由：{{ $route.path }}</p>
    <p>登录状态：{{ authStore.isAuthenticated ? '已登录' : '未登录' }}</p>
  </div>
</template>

<script setup>
import { useAuthStore } from '../store'
const authStore = useAuthStore()
</script>

<style scoped>
.test-container {
  padding: 20px;
  background: #f0f0f0;
  border: 2px solid red;
}
</style>
