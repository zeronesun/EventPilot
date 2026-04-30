import { createRouter, createWebHistory } from 'vue-router'

// 使用懒加载优化性能
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/test',
    name: 'test',
    component: () => import('../views/TestPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/events',
    name: 'events',
    component: () => import('../views/Events.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('../views/Tasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/Users.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/checklists',
    name: 'checklists',
    component: () => import('../views/Checklists.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'files',
    component: () => import('../views/Files.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles',
    name: 'profiles',
    component: () => import('../views/Profiles.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/budget',
    name: 'budget',
    component: () => import('../views/Budget.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: () => import('../views/Knowledge.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reviews',
    name: 'reviews',
    component: () => import('../views/Reviews.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('../views/Analytics.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('../views/NotFound.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导出路由实例，在App.vue中进行认证检查
export default router

// 延迟导入认证store以避免循环依赖
let authStore = null
const getAuthStore = () => {
  if (!authStore) {
    // 动态导入store
    const { useAuthStore } = require('../store/index')
    authStore = useAuthStore()
  }
  return authStore
}

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  // 延迟检查，避免初始化时的导入问题
  try {
    const store = getAuthStore()
    
    if (to.meta.requiresAuth && !store.isAuthenticated) {
      next('/login')
    } else if (to.name === 'login' && store?.isAuthenticated) {
      next('/')
    } else {
      next()
    }
  } catch (error) {
    console.error('Router guard error:', error)
    next() // 出错时继续，避免阻塞
  }
})