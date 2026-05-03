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
    // HMR (Hot Module Replacement) 配置 - 修复 WebSocket 连接问题
    hmr: {
      // 当通过代理或非 localhost 访问时，使用客户端端口
      clientPort: 5173,
      // 或者使用 ws 协议（如果上述不行，可以尝试这个）
      // protocol: 'ws',
      // host: 'localhost',
    },
    // 允许跨源请求（CORS）
    cors: true,
    proxy: {
      '/api': {
        target: 'http://172.28.166.164:8000',
        changeOrigin: true,
        // 添加超时和错误处理
        timeout: 30000,
        proxyTimeout: 30000,
        onError(err, req, res) {
          console.error('Proxy error:', err.message);
          if (!res.headersSent) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
          }
          res.end(JSON.stringify({ error: 'Proxy error', message: err.message }));
        },
      },
      '/ws': {
        target: 'ws://172.28.166.164:8000',
        ws: true,
        changeOrigin: true,
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
    // 生产环境移除console.log和debugger
    esbuild: {
      drop: ['console', 'debugger'],
    },
  },
})
