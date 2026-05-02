import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
      lines: 60,
      functions: 60,
      branches: 60,
      statements: 60,
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://172.28.166.164:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://172.28.166.164:8000',
        ws: true,
      },
    },
  },
  build: {
    // 提高chunk大小警告阈值
    chunkSizeWarningLimit: 800,
    // 代码分割优化
    rollupOptions: {
      output: {
        manualChunks: {
          // 将第三方库单独打包
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          'vue-core': ['vue', 'vue-router', 'pinia'],
          'axios': ['axios'],
          'crypto': ['crypto-js'],
        },
      },
    },
    // 压缩配置
    minify: 'esbuild',
    cssCodeSplit: true,
  },
})
