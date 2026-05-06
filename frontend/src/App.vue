<template>
  <div id="app">
    <!-- 全局布局 -->
    <div
      v-if="isAuthenticated"
      class="app-layout"
    >
      <!-- 侧边栏 -->
      <div class="sidebar">
        <div class="logo-section">
          <h2>EventPilot</h2>
          <p>活动领航系统</p>
        </div>

        <div class="sidebar-menu">
          <div
            class="menu-item"
            :class="{ active: $route.path === '/dashboard' }"
            @click="$router.push('/dashboard')"
          >
            <el-icon><HomeFilled /></el-icon>
            <span>工作台</span>
          </div>
          <el-dropdown @command="handleEventsMenuCommand" trigger="click">
            <div
              class="menu-item"
              :class="{ active: $route.path.startsWith('/events') && !$route.path.includes('/events/') }"
            >
              <el-icon><HomeFilled /></el-icon>
              <span>活动管理</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="list">
                  <el-icon><List /></el-icon>
                  列表视图
                </el-dropdown-item>
                <el-dropdown-item command="kanban">
                  <el-icon><Menu /></el-icon>
                  看板视图
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/tasks' }"
            @click="$router.push('/tasks')"
          >
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/users' }"
            @click="$router.push('/users')"
          >
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/checklists' }"
            @click="$router.push('/checklists')"
          >
            <el-icon><DocumentChecked /></el-icon>
            <span>清单管理</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/files' }"
            @click="$router.push('/files')"
          >
            <el-icon><Folder /></el-icon>
            <span>文件管理</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/budget' }"
            @click="$router.push('/budget')"
          >
            <el-icon><Coin /></el-icon>
            <span>预算管理</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/profiles' }"
            @click="$router.push('/profiles')"
          >
            <el-icon><User /></el-icon>
            <span>关联方档案</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/knowledge' }"
            @click="$router.push('/knowledge')"
          >
            <el-icon><Document /></el-icon>
            <span>知识库</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/reviews' }"
            @click="$router.push('/reviews')"
          >
            <el-icon><Memo /></el-icon>
            <span>活动复盘</span>
          </div>
          <div
            class="menu-item"
            :class="{ active: $route.path === '/analytics' }"
            @click="$router.push('/analytics')"
          >
            <el-icon><DataLine /></el-icon>
            <span>数据分析</span>
          </div>

          <div class="menu-divider" />

          <div
            class="menu-item"
            @click="$router.push('/settings')"
          >
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </div>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 顶部导航 -->
        <div class="main-header">
          <div class="header-left">
            <el-breadcrumb>
              <el-breadcrumb-item :to="{ path: '/dashboard' }">
                首页
              </el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentPage !== '首页'">
                {{ currentPage }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <NotificationCenter />
            <el-dropdown @command="handleUserMenu">
              <div class="user-avatar">
                <el-avatar :size="32">
                  {{ userInitial }}
                </el-avatar>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>
                    {{ authStore.username }}
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="router.push('/settings')">
                    <el-icon><Setting /></el-icon>
                    个人资料
                  </el-dropdown-item>
                  <el-dropdown-item @click="router.push('/settings')">
                    <el-icon><Setting /></el-icon>
                    系统设置
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 页面内容 -->
        <div class="page-content">
          <router-view v-slot="{ Component, route }">
            <transition
              name="fade-transform"
              mode="out-in"
            >
              <component
                :is="Component"
                :key="route.path"
              />
            </transition>
          </router-view>
        </div>

        <!-- 底部 -->
        <div class="main-footer">
          <div class="footer-content">
            <span>© 2026 EventPilot - 活动领航系统 v1.2 Phase 2</span>
            <a
              href="https://github.com/eventpilot"
              target="_blank"
            >
              <el-icon><Link /></el-icon>
              GitHub
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- 登录页面布局 -->
    <div
      v-else
      class="login-layout"
    >
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores';
import { ElMessage } from 'element-plus';
import {
  HomeFilled,
  List,
  User,
  DocumentChecked,
  Document,
  Folder,
  Coin,
  Setting,
  SwitchButton,
  Link,
  Memo,
  DataLine,
  ArrowDown,
  Menu,
} from '@element-plus/icons-vue'

import NotificationCenter from './components/NotificationCenter.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const activeMenu = ref('/');
const currentPage = ref('首页');

const userInitial = computed(
  () => authStore.currentUser?.username?.charAt(0)?.toUpperCase() || 'U'
);
const isAuthenticated = computed(() => authStore.isAuthenticated);

// 监听路由变化
watch(
  () => route.path,
  (newPath) => {
    activeMenu.value = newPath;
    currentPage.value = getPageTitle(newPath);
  },
  { immediate: true }
);

function getPageTitle(path) {
  const titles = {
    '/dashboard': '工作台',
    '/': '工作台',
    '/events': '活动管理（列表视图）',
    '/events-kanban': '活动管理（看板视图）',
    '/tasks': '任务管理',
    '/users': '用户管理',
    '/checklists': '清单管理',
    '/files': '文件管理',
    '/budget': '预算管理',
    '/profiles': '关联方档案',
    '/knowledge': '知识库',
    '/reviews': '活动复盘',
    '/analytics': '数据分析',
    '/notifications': '通知中心',
    '/settings': '系统设置',
  };
  return titles[path] || path.slice(1).charAt(0).toUpperCase() + path.slice(2) || '首页';
}

function getUserInitial() {
  return authStore.currentUser?.username?.charAt(0).toUpperCase() || 'U';
}

function handleUserMenu(command) {
  switch (command) {
    case 'profile':
      router.push('/profiles');
      break;
    case 'settings':
      ElMessage.info('系统设置即将开放');
      break;
    case 'logout':
      handleLogout();
      break;
  }
}

function handleEventsMenuCommand(command) {
  switch (command) {
    case 'list':
      router.push('/events');
      break;
    case 'kanban':
      router.push('/events-kanban');
      break;
  }
}

function handleLogout() {
  try {
    authStore.logout();
    ElMessage.success('已退出登录');
    router.push('/login');
  } catch (error) {
    console.error('Logout error:', error);
    ElMessage.error('退出登录失败');
  }
}

onMounted(async () => {
  authStore.initialize();

  // 检查认证状态并重定向
  if (!isAuthenticated.value && route.path !== '/login') {
    router.push('/login');
  }
});

onUnmounted(() => {
  // Clean up if needed
});
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  width: 100%;
}

.sidebar {
  width: 250px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  overflow-y: auto;
}

.logo-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  text-align: center;
  flex-shrink: 0;
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

.sidebar-menu {
  padding: 10px 0;
}

.menu-item {
  padding: 12px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #606266;
  transition: all 0.3s;
  border-radius: 6px;
  margin: 4px 10px;
}

.menu-item:hover {
  background: #f5f7fa;
  color: #409eff;
}

.menu-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}

.menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 15px 10px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.main-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  flex-shrink: 0;
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

.page-content {
  flex: 1;
  background: #f5f7fa;
  padding: 20px;
}

.main-footer {
  background: #fff;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #999;
  height: 40px;
  flex-shrink: 0;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 40px;
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

#app {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  width: 100%;
}
</style>
