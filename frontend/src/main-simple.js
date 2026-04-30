// 简化版main.js - 用于排查问题
console.log('🚀 App initializing...');

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

console.log('📦 Modules loaded: Vue, Pinia, ElementPlus, Router');

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

console.log('🔌 Plugins installed');

console.log('🏗️ Mounting app to #app');
app.mount('#app')

console.log('✅ App mounted successfully!');

// 错误监听
window.addEventListener('error', (event) => {
  console.error('❌ Global error:', event)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ Unhandled promise rejection:', event)
})