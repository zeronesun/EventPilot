/**
 * 加密和安全工具函数
 *
 * 安全说明：
 * 当前使用 crypto-js 进行HMAC-SHA256签名，这是前端常用的加密库。
 * 生产环境建议：
 * 1. 将签名验证移至后端，使用更强的密钥管理（如 vault）
 * 2. 前端仅做基础的消息完整性检查
 * 3. 考虑使用 WebCrypto API 替代 crypto-js (现代浏览器原生支持)
 */

import CryptoJS from 'crypto-js'

/**
 * 简单的HMAC-SHA256签名
 * 注意：这是一个用于演示的基础实现，生产环境应由后端验证
 */
export function signMessage(message: any, secret: string): string {
  const messageString = JSON.stringify(message)
  return CryptoJS.HmacSHA256(messageString, secret).toString(CryptoJS.enc.Hex)
}

/**
 * 验证消息签名
 */
export function verifyMessageSignature(message: any, signature: string, secret: string): boolean {
  const expected = signMessage(message, secret)
  // 使用固定时间比较防止时序攻击
  const a = expected
  const b = signature
  if (a.length !== b.length) {
    return false
  }
  
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  
  return result === 0
}

/**
 * 生成随机nonce
 *
 * 安全说明：
 * 使用 Web Crypto API 的 getRandomValues()，这是浏览器中原生的加密安全的随机数生成器。
 * 如果环境不支持 crypto.getRandomValues()（如某些旧浏览器或 SSR 环境），会回退到 Math.random()。
 * 生产环境建议确保支持 Web Crypto API。
 */
export function generateNonce(): string {
  try {
    const array = new Uint8Array(16)

    // 检查是否支持 crypto.getRandomValues()
    if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
      crypto.getRandomValues(array)
    } else {
      // 回退方案：使用 Math.random()（非加密安全，但至少不会崩溃）
      console.warn('[Crypto] crypto.getRandomValues() not available, falling back to Math.random()')
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256)
      }
    }

    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  } catch (error) {
    console.error('[Crypto] Failed to generate nonce:', error)
    // 最终回退
    const fallbackBytes = new Array(16).fill(0).map(() =>
      Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
    )
    return fallbackBytes.join('')
  }
}

/**
 * 验证时间戳是否在有效范围内
 */
export function verifyTimestamp(timestamp?: number, maxAge: number = 60): boolean {
  if (!timestamp) {
    return false
  }
  
  const now = Date.now() / 1000
  const diff = now - timestamp
  
  return diff >= 0 && diff <= maxAge
}

/**
 * 验证消息基本结构
 */
export function validateMessage(message: any): boolean {
  if (!message || typeof message !== 'object') {
    return false
  }
  
  if (!message.type || typeof message.type !== 'string') {
    return false
  }
  
  if (!verifyTimestamp(message.timestamp)) {
    return false
  }
  
  return true
}

/**
 * 检查消息来源是否授权
 */
export function isAuthorizedSource(message: any, allowedSources: Set<number>): boolean {
  // 如果没有限制来源，则允许所有消息
  if (allowedSources.size === 0) {
    return true
  }
  
  if (!message.user_id) {
    return false
  }
  
  return allowedSources.has(message.user_id)
}
