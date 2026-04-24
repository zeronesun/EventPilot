import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Events from '../views/Events.vue'
import Tasks from '../views/Tasks.vue'
import Users from '../views/Users.vue'
import Checklists from '../views/Checklists.vue'
import Files from '../views/Files.vue'
import Profiles from '../views/Profiles.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
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
    component: Events,
    meta: { requiresAuth: true }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: Tasks,
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'users',
    component: Users,
    meta: { requiresAuth: true }
  },
  {
    path: '/checklists',
    name: 'checklists',
    component: Checklists,
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'files',
    component: Files,
    meta: { requiresAuth: true }
  },
  {
    path: '/profiles',
    name: 'profiles',
    component: Profiles,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router