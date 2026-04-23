/**
 * 加密和安全工具函数
 */

import CryptoJS from 'crypto-js'

/**
 * 简单的HMAC-SHA256签名
 * 注意：这是一个临时实现，生产环境应该使用更安全的方案
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
 */
export function generateNonce(): string {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
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
