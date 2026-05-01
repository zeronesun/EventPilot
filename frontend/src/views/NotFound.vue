<template>
  <div class="not-found-page">
    <div class="content">
      <h1>404</h1>
      <p>页面未找到</p>
      <router-link
        to="/"
        class="back-link"
      >
        返回首页
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
// 404页面组件
</script>

<style scoped>
.not-found-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.content {
  text-align: center;
  color: white;
}

.content h1 {
  font-size: 6rem;
  margin: 0;
  font-weight: bold;
}

.content p {
  font-size: 1.5rem;
  margin: 1rem 0 2rem;
}

.back-link {
  color: white;
  text-decoration: underline;
  cursor: pointer;
  padding: 10px 20px;
  border: 1px solid white;
  border-radius: 4px;
}
</style>