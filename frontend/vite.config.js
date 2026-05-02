import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
      interval: 100,
    },
    // 跨域和API代理配置（解决CORS问题）
    proxy: {
      '/api': {
        target: 'http://172.28.166.164:8000',
        changeOrigin: true,
        secure: false,
        // 不重写路径，直接转发 /api/* 到后端
      },
    },
  },
  optimizeDeps: {
    force: true,
    include: ['vue', 'vue-router', 'pinia', 'element-plus'],
  },
  cacheDir: undefined,
})
