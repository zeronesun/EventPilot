import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Mock Element Plus
vi.mock('element-plus', () => ({
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

// Mock window.crypto for crypto-js
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: vi.fn(() => new Uint32Array(1)),
  },
})
