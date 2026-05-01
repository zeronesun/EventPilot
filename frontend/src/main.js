console.log('🚀 App initializing...');

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { ToastPlugin } from './plugins/toast'

console.log('📦 Modules loaded: Vue, Pinia, ElementPlus, Router, Toast');

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(ToastPlugin)

console.log('🔌 Plugins installed');

console.log('🏗️ Mounting app to #app');
app.mount('#app')

console.log('✅ App mounted successfully!');

// 隐藏加载屏幕
const loadingScreen = document.getElementById('loading-screen');
if (loadingScreen) {
  loadingScreen.style.display = 'none';
}

// 错误监听
window.addEventListener('error', (event) => {
  console.error('❌ Global error:', event)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ Unhandled promise rejection:', event)
})