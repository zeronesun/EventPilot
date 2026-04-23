import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import crypto from 'node:crypto'

// Mock Element Plus
vi.mock('element-plus', ({
  ElNotification: vi.fn(),
  ElMessage: vi.fn(),
  ElMessageBox: vi.fn(),
}))

config.global.mocks = {
  $t: (key: string) => key,
  $notify: vi.fn(),
  $message: vi.fn(),
  $confirm: vi.fn(() => Promise.resolve()),
}

// Mock window.crypto for crypto-js - 使用真实 Node.js crypto
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: vi.fn((arr: Uint8Array) => {
      const buf = crypto.randomBytes(arr.length)
      for (let i = 0; i < arr.length; i++) {
        arr[i] = buf[i]
      }
      return arr
    }),
  },
})
