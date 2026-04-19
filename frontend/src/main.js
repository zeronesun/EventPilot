import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './store'
import { apiClient } from './api/client'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// Initialize authentication state
const authStore = useAuthStore()
authStore.initialize()

// Set API client token if available
if (authStore.token) {
  apiClient.setAuthToken(authStore.token)
}

// Mount app
app.mount('#app')