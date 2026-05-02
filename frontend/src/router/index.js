import { createRouter, createWebHistory } from 'vue-router'

// 使用懒加载优化性能
const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
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
    path: '/events-kanban',
    name: 'events-kanban',
    component: () => import('../views/EventsKanban.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/events/:id',
    name: 'event-detail',
    component: () => import('../views/EventDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/events/:id/edit',
    name: 'event-edit',
    component: () => import('../views/EventEdit.vue'),
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
    path: '/notifications',
    name: 'notifications',
    component: () => import('../views/Notifications.vue'),
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
  {    path: '/analytics',    name: 'analytics',    component: () => import('../views/Analytics.vue'),
    meta: { requiresAuth: true }  },  {    path: '/settings',    name: 'settings',    component: () => import('../views/Settings.vue'),
    meta: { requiresAuth: true }  },
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

// 导出路由实例
export default router

// 简化的路由守卫 - 延迟到App.vue中的组件中检查认证状态
// 这样可以避免循环依赖和require的问题
router.beforeEach((to, from, next) => {
  // 只处理需要认证但已到登录页面的情况
  if (to.path === '/login' || !to.meta.requiresAuth) {
    next()
    return
  }
  
  // 其他需要认证的页面延迟在组件内检查
  // 组件可以通过检查localStorage中的token来判断
  next()
})
