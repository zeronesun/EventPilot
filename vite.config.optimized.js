import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@api': resolve(__dirname, 'src/api'),
      '@store': resolve(__dirname, 'src/store'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
    },
  },

  // 构建优化
  build: {
    // 代码分割策略
    rollupOptions: {
      output: {
        // 手动分包
        manualChunks: {
          // Vue 核心库
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // Element Plus 组件库
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          // 工具库
          'utils': ['@vueuse/core', 'axios'],
        },
        // 为代码块生成 chunk
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    // 压缩选项
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 生产环境移除 console
        drop_debugger: true,
      },
    },
    // 源码映射
    sourcemap: false,
    // 块大小警告阈值 (kb)
    chunkSizeWarningLimit: 1000,
  },

  // 开发服务器配置
  server: {
    port: 3000,
    host: '0.0.0.0',
    open: false,
    cors: true,
    // 代理后端 API
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // 预览服务器配置
  preview: {
    port: 3000,
    host: '0.0.0.0',
    cors: true,
  },

  // 依赖预构建优化
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus',
      '@element-plus/icons-vue',
      '@vueuse/core',
      'axios',
      'vuedraggable',
    ],
  },

  // CSS 配置
  css: {
    devSourcemap: false,
    preprocessorOptions: {
      // 如果使用 scss
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`,
      },
    },
  },
})
