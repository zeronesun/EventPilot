<template>
  <div class="home">
    <h1>欢迎来到 EventPilot</h1>
    <p>活动领航系统 MVP版本</p>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
                <span>活动管理</span>
              </div>
          </template>
          <p>创建和管理活动项目</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>任务管理</span>
            </div>
          </template>
          <p>跟踪和管理任务进度</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>核验清单</span>
            </div>
          </template>
          <p>现场核验和检查记录</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
// Home.vue 首页组件
</script>

<style scoped>
.home {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>