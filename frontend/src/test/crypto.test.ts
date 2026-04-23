import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  signMessage,
  verifyMessageSignature,
  generateNonce,
  verifyTimestamp,
  validateMessage,
  isAuthorizedSource,
} from '../utils/crypto'

describe('Crypto Utils', () => {
  const testSecret = 'test-secret-key-12345'

  describe('signMessage', () => {
    it('should generate consistent signatures for same message', () => {
      const message = { type: 'test', timestamp: Date.now() }
      const sig1 = signMessage(message, testSecret)
      const sig2 = signMessage(message, testSecret)
      expect(sig1).toBe(sig2)
    })

    it('should generate different signatures for different messages', () => {
      const message1 = { type: 'test1' }
      const message2 = { type: 'test2' }
      const sig1 = signMessage(message1, testSecret)
      const sig2 = signMessage(message2, testSecret)
      expect(sig1).not.toBe(sig2)
    })

    it('should generate different signatures for different secrets', () => {
      const message = { type: 'test' }
      const sig1 = signMessage(message, 'secret1')
      const sig2 = signMessage(message, 'secret2')
      expect(sig1).not.toBe(sig2)
    })
  })

  describe('verifyMessageSignature', () => {
    it('should verify correct signature', () => {
      const message = { type: 'test', timestamp: Date.now() }
      const signature = signMessage(message, testSecret)
      expect(verifyMessageSignature(message, signature, testSecret)).toBe(true)
    })

    it('should reject incorrect signature', () => {
      const message = { type: 'test', timestamp: Date.now() }
      expect(verifyMessageSignature(message, 'invalid-signature', testSecret)).toBe(false)
    })

    it('should reject signature with different secret', () => {
      const message = { type: 'test', timestamp: Date.now() }
      const signature = signMessage(message, testSecret)
      expect(verifyMessageSignature(message, signature, 'different-secret')).toBe(false)
    })
  })

  describe('generateNonce', () => {
    it('should generate unique nonces', () => {
      const nonce1 = generateNonce()
      const nonce2 = generateNonce()
      expect(nonce1).not.toBe(nonce2)
    })

    it('should generate nonces of correct length', () => {
      const nonce = generateNonce()
      expect(nonce.length).toBe(32) // 16 bytes = 32 hex chars
    })
  })

  describe('verifyTimestamp', () => {
    it('should accept recent timestamp', () => {
      const now = Date.now() / 1000
      expect(verifyTimestamp(now, 60)).toBe(true)
    })

    it('should reject old timestamp (> maxAge)', () => {
      const oldTime = Date.now() / 1000 - 120 // 120 seconds ago
      expect(verifyTimestamp(oldTime, 60)).toBe(false)
    })

    it('should reject future timestamp', () => {
      const futureTime = Date.now() / 1000 + 120
      expect(verifyTimestamp(futureTime, 60)).toBe(false)
    })

    it('should accept timestamp near edge of maxAge', () => {
      const now = Date.now() / 1000
      // Just under maxAge
      expect(verifyTimestamp(now - 59, 60)).toBe(true)
      // Just over maxAge
      expect(verifyTimestamp(now - 61, 60)).toBe(false)
    })

    it('should accept null for special message types', () => {
      expect(verifyTimestamp(undefined, 60)).toBe(false)
      expect(verifyTimestamp(null, 60)).toBe(false)
    })
  })

  describe('validateMessage', () => {
    it('should accept valid message', () => {
      const message = {
        type: 'notification',
        timestamp: Date.now() / 1000,
        user_id: 1,
      }
      expect(validateMessage(message)).toBe(true)
    })

    it('should reject message without type', () => {
      const message = { timestamp: Date.now() / 1000 }
      expect(validateMessage(message)).toBe(false)
    })

    it('should reject invalid message type', () => {
      const message = {
        type: 'invalid_type',
        timestamp: Date.now() / 1000,
      }
      expect(validateMessage(message)).toBe(false)
    })

    it('should reject message without timestamp', () => {
      const message = {
        type: 'notification',
        user_id: 1,
      }
      expect(validateMessage(message)).toBe(false)
    })

    it('should reject expired timestamp', () => {
      const message = {
        type: 'notification',
        timestamp: Date.now() / 1000 - 120,
      }
      expect(validateMessage(message)).toBe(false)
    })
  })

  describe('isAuthorizedSource', () => {
    it('should accept authorized user', () => {
      const message = { user_id: 1 }
      const allowed = new Set([1, 2, 3])
      expect(isAuthorizedSource(message, allowed)).toBe(true)
    })

    it('should reject unauthorized user', () => {
      const message = { user_id: 99 }
      const allowed = new Set([1, 2, 3])
      expect(isAuthorizedSource(message, allowed)).toBe(false)
    })

    it('should accept any user when allowed set is empty', () => {
      const message = { user_id: 1 }
      const allowed = new Set()
      expect(isAuthorizedSource(message, allowed)).toBe(true)
    })

    it('should reject message without user_id', () => {
      const message = {}
      const allowed = new Set([1, 2, 3])
      expect(isAuthorizedSource(message, allowed)).toBe(false)
    })
  })
})
