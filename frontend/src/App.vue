<template>
  <div id="app">
    <!-- 全局布局 -->
    <el-container v-if="layout === 'app'" class="app-layout">
      <el-aside width="250px" class="sidebar">
        <div class="logo-section">
          <h2>EventPilot</h2>
          <p>活动领航系统</p>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="/events">
            <el-icon><HomeFilled /></el-icon>
            <span>活动管理</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/checklists">
            <el-icon><DocumentChecked /></el-icon>
            <span>清单管理</span>
          </el-menu-item>
          <el-menu-item index="/files">
            <el-icon><Folder /></el-icon>
            <span>文件管理</span>
          </el-menu-item>
          
          <div class="menu-divider"></div>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="main-header">
          <div class="header-left">
            <el-breadcrumb>
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentPage !== '首页'">
                {{ currentPage }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-badge :value="unreadCount" class="notification-badge">
              <el-button circle @click="showNotifications">
                <el-icon><Bell /></el-icon>
              </el-button>
            </el-badge>
            <el-dropdown @command="handleUserMenu">
              <div class="user-avatar">
                <el-avatar :size="32">{{ userInitial }}</el-avatar>
              </div>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item disabled>
                  <span>{{ authStore.username }}</span>
                </el-dropdown-item>
                <el-dropdown-item divided>
                  <el-icon></el-icon>
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item>
                  <el-icon></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item @command="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
        </el-header>

        <el-main>
          <router-view v-slot="{ Component, route }">
            <transition name="fade-transform" mode="out-in">
              <component :is="Component" :key="route.path" />
            </transition>
          </router-view>
        </el-main>

        <el-footer height="40px" class="main-footer">
          <div class="footer-content">
            <span>© 2026 EventPilot - 活动领航系统 v1.2 Phase 2</span>
            <a href="https://github.com/eventpilot" target="_blank">
              <el-icon><Link /></el-icon>
              GitHub
            </a>
          </div>
        </el-footer>
      </el-container>
    </el-container>

    <!-- 登录页面布局 -->
    <div v-else class="login-layout">
      <router-view />
    </div>

    <!-- 全局通知和加载状态 -->
    <el-backtop :right="40" :bottom="40" />
    
    <!-- WebSocket连接状态指示器 -->
    <div v-if="websocketStore.isConnected" class="websocket-status">
      <el-tag type="success" effect="dark" size="small">
        <el-icon><Connection /></el-icon>
        实时连接
      </el-tag>
    </div>
    <div v-else class="websocket-status disconnected">
      <el-tag type="danger" effect="dark" size="small">
        <el-icon><Connection /></el-icon>
        连接断开
      </el-tag>
    </div>

    <el-backtop />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store'
import { useWebSocketStore } from '../stores/websocket'
import {
  HomeFilled,
  List,
  User,
  DocumentChecked,
  Folder,
  Setting,
  Bell,
  SwitchButton,
  Link,
  Connection
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const webSocketStore = useWebSocketStore()

const layout = ref('app')
const activeMenu = ref('/')
const currentPage = ref('首页')
const unreadCount = ref(0)
const userInitial = computed(() => 
  authStore.currentUser?.username?.charAt(0)?.toUpperCase() || 'U'
)

// 监听路由变化
watch(() => route.path, (newPath) => {
  if (newPath === '/login') {
    layout.value = 'login'
  } else {
    layout.value = 'app'
    activeMenu.value = newPath
    currentPage.value = getPageTitle(newPath)
  }
}, { immediate: true })

function getPageTitle(path) {
  const titles = {
    '/': '工作台',
    '/events': '活动管理',
    '/tasks': '任务管理',
    '/users': '用户管理',
    '/checklists': '清单管理',
    '/files': '文件管理',
    '/settings': '系统设置'
  }
  return titles[path] || 'EventPilot'
}

function showNotifications() {
  const count = webSocketStore.notifications.filter(n => !n.read).length
  if (count === 0) {
    ElMessage.info('暂未读通知')
  } else {
    ElMessage.success(`有 ${count} 条未读通知`)
  }
}

function handleUserMenu(command) {
  console.log('User menu command:', command)
}

async function handleLogout() {
  try {
    await authStore.logout()
    webSocketStore.disconnect()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    console.error('Logout error:', error)
    ElMessage.error('退出登录失败')
  }
}

onMounted(async () => {
  authStore.initialize()
  // 根据初始路由设置布局
  layout.value = route.path === '/login' ? 'login' : 'app'
  
  try {
    await webSocketStore.connect()
  } catch (error) {
    console.error('WebSocket connection failed:', error)
  }
})

onUnmounted(() => {
  webSocketStore.disconnect()
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.logo-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  text-align: center;
}

.logo-section h2 {
  margin: 0;
  color: white;
  font-size: 20px;
}

.logo-section p {
  margin: 5px 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  height: 100vh;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-menu-item {
  margin: 5px 10px;
  border-radius: 4px;
}

.sidebar-menu .el-menu-item.is-active {
  background: #ecf5ff;
  color: #409eff;
}

.sidebar-menu .el-menu-item:hover:not(.is-active) {
  background: #f5f7fa;
}

.menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 20px 0;
}

.main-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 15px;
  align-items: center;
}

.user-avatar {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.notification-badge {
  --el-badge-bg-color: #f56c6c;
}

.notification-badge :deep(.el-badge__content) {
  top: -2px;
  right: -2px;
}

.el-main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.main-footer {
  background: #fff;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #999;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-content a {
  color: #409eff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 5px;
}

.footer-content a:hover {
  color: #66b1ff;
}

.login-layout {
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from,
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.websocket-status {
  position: fixed;
  bottom: 80px;
  right: 40px;
  z-index: 1000;
}

.websocket-status.disconnected {
  bottom: 80px;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
</style>