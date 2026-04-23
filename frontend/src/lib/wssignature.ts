/**
 * WebSocket 消息签名模块
 * 用于生成和验证 WebSocket 消息签名，防止消息伪造和重放攻击
 */

// SHA-256 哈希函数实现
async function sha256(message: string): Promise<string> {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}

// HMAC-SHA256 实现
async function hmacSha256(key: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  
  const keyBuffer = encoder.encode(key);
  const messageBuffer = encoder.encode(message);
  
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyBuffer,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signature = await crypto.subtle.sign(
    'HMAC',
    cryptoKey,
    messageBuffer
  );
  
  // 转换为十六进制字符串
  const hashArray = Array.from(new Uint8Array(signature));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * MessageSigner 类
 * 负责生成 WebSocket 消息签名
 */
export class MessageSigner {
  private signatureKey: string;
  
  constructor(signatureKey: string) {
    this.signatureKey = signatureKey;
  }
  
  /**
   * 为消息添加签名
   * 
   * @param message - 原始消息对象
   * @param userId - 当前用户ID（可选）
   * @returns 已签名的消息副本
   */
  async signMessage(
    message: Record<string, unknown>,
    userId?: number
  ): Promise<Record<string, unknown>> {
    // 不修改原始消息，创建副本
    const signedMessage = { ...message };
    
    // 确保 timestamp 存在
    if (!signedMessage.timestamp) {
      signedMessage.timestamp = Math.floor(Date.now() / 1000); // Unix 时间戳
    }
    
    // 添加用户ID（如果提供）
    if (userId !== undefined && !signedMessage.user_id) {
      signedMessage.user_id = userId;
    }
    
    // 提取需要签名的字段（不包括 signature 本身）
    const payload = { ...signedMessage };
    delete (payload as any).signature;
    
    // 生成签名
    const jsonString = JSON.stringify(payload);
    const signature = await hmacSha256(this.signatureKey, jsonString);
    signedMessage.signature = signature;
    
    return signedMessage;
  }
  
  /**
   * 获取签名密钥
   */
  getSignatureKey(): string {
    return this.signatureKey;
  }
  
  /**
   * 设置签名密钥
   */
  setSignatureKey(key: string): void {
    this.signatureKey = key;
  }
}

/**
 * MessageValidator 类
 * 负责验证 WebSocket 消息签名（可选，用于接收到的消息）
 */
export class MessageValidator {
  private signatureKey: string;
  private maxMessageLatency: number; // 消息最大延迟时间（秒）
  private timestampTolerance: number; // 时间戳容差（秒）
  
  constructor(
    signatureKey: string,
    maxMessageLatency: number = 30,
    timestampTolerance: number = 60
  ) {
    this.signatureKey = signatureKey;
    this.maxMessageLatency = maxMessageLatency;
    this.timestampTolerance = timestampTolerance;
  }
  
  /**
   * 验证消息内容
   * 
   * @param message - 收到的消息
   * @param clientUserId - 客户端用户ID（可选，用于验证）
   * @returns 验证通过返回 true
   * @throws 验证失败抛出错误对象 { code, message }
   */
  async validateMessage(
    message: Record<string, unknown>,
    clientUserId?: number
  ): Promise<boolean> {
    // 1. 检查必需字段
    const requiredFields = ['type', 'timestamp'];
    for (const field of requiredFields) {
      if (!(field in message)) {
        throw new Error(
          `Missing required field '${field}'`,
          { cause: { code: 'MISSING_FIELD', field } }
        );
      }
    }
    
    // 2. 验证时间戳（防止重放攻击）
    const timestamp = message.timestamp as number;
    if (typeof timestamp !== 'number' || !Number.isFinite(timestamp)) {
      throw new Error(
        `Invalid timestamp format: ${timestamp}`,
        { cause: { code: 'INVALID_TIMESTAMP', timestamp } }
      );
    }
    
    const currentTime = Math.floor(Date.now() / 1000);
    const timeDiff = Math.abs(currentTime - timestamp);
    
    if (timeDiff > this.maxMessageLatency) {
      throw new Error(
        `Message too old (age: ${timeDiff}s, max: ${this.maxMessageLatency}s)`,
        { cause: { 
          code: 'MESSAGE_TOO_OLD',
          message_age: timeDiff,
          max_age: this.maxMessageLatency
        }}
      );
    }
    
    // 3. 验证消息签名（如果存在）
    const signature = (message as any).signature;
    if (signature && typeof signature === 'string') {
      // 提取需要签名的字段（不包括 signature 本身）
      const payload = { ...message };
      delete (payload as any).signature;
      
      const jsonString = JSON.stringify(payload);
      const expectedSig = await hmacSha256(this.signatureKey, jsonString);
      
      // 使用恒定时间比较来防止时序攻击
      if (!this.constantTimeCompare(expectedSig, signature)) {
        throw new Error(
          'Invalid message signature',
          { cause: { code: 'INVALID_SIGNATURE' } }
        );
      }
    } else {
      // 对于非关键消息，签名可以是可选的
      // 但对于协作类的消息，要求必须有签名
      const criticalMessageTypes = [
        'collaboration',
        'task_status_change',
        'task_update',
        'event_update',
        'edit_lock'
      ];
      
      const messageType = message.type as string;
      if (criticalMessageTypes.includes(messageType)) {
        throw new Error(
          `Critical message '${messageType}' requires signature`,
          { cause: { code: 'SIGNATURE_REQUIRED', type: messageType } }
        );
      }
    }
    
    // 4. 可选：验证用户ID（如果消息中包含）
    if (clientUserId !== undefined && 'user_id' in message) {
      const messageUserId = message.user_id as number;
      if (messageUserId !== clientUserId) {
        throw new Error(
          `User ID mismatch (message: ${messageUserId}, client: ${clientUserId})`,
          { cause: { 
            code: 'USER_ID_MISMATCH',
            message_user_id: messageUserId,
            client_user_id: clientUserId
          }}
        );
      }
    }
    
    return true;
  }
  
  /**
   * 恒定时间字符串比较，防止时序攻击
   */
  private constantTimeCompare(a: string, b: string): boolean {
    if (a.length !== b.length) {
      return false;
    }
    
    let result = 0;
    for (let i = 0; i < a.length; i++) {
      result |= (a.charCodeAt(i) ^ b.charCodeAt(i));
    }
    
    return result === 0;
  }
}

/**
 * 创建全局签名器实例
 */
let messageSigner: MessageSigner | null = null;
let messageValidator: MessageValidator | null = null;

/**
 * 获取或创建全局签名器
 * 
 * @param signatureKey - 签名密钥（可选，首次调用时设置）
 * @returns MessageSigner 实例
 */
export function getMessageSigner(signatureKey?: string): MessageSigner {
  if (!messageSigner) {
    // 从 localStorage 读取签名密钥（如果存在）
    const storedKey = localStorage.getItem('ws_signature_key');
    const key = signatureKey || storedKey || 'default-signature-key-change-in-production';
    
    messageSigner = new MessageSigner(key);
    
    // 如果提供了新密钥，保存到 localStorage
    if (signatureKey) {
      localStorage.setItem('ws_signature_key', signatureKey);
    }
  }
  return messageSigner;
}

/**
 * 获取或创建全局验证器
 * 
 * @param signatureKey - 签名密钥（可选）
 * @returns MessageValidator 实例
 */
export function getMessageValidator(signatureKey?: string): MessageValidator {
  if (!messageValidator) {
    // 从 localStorage 读取签名密钥
    const storedKey = localStorage.getItem('ws_signature_key');
    const key = signatureKey || storedKey || 'default-signature-key-change-in-production';
    
    messageValidator = new MessageValidator(
      key,
      30, // maxMessageLatency: 30 秒
      60  // timestampTolerance: 60 秒
    );
  }
  return messageValidator;
}

/**
 * 重置签名器和验证器实例
 * 用于测试或需要重新创建的场景
 */
export function resetMessageSecurity(): void {
  messageSigner = null;
  messageValidator = null;
  localStorage.removeItem('ws_signature_key');
}

/**
 * 自动签名的辅助函数
 * 
 * 对消息自动添加时间戳和签名
 * 
 * @param message - 原始消息
 * @param userId - 用户ID（可选）
 * @returns 已签名的消息
 */
export async function autoSignMessage(
  message: Record<string, unknown>,
  userId?: number
): Promise<Record<string, unknown>> {
  const signer = getMessageSigner();
  return await signer.signMessage(message, userId);
}

/**
 * 自动验证消息的辅助函数
 * 
 * 验证接收到的消息的完整性
 * 
 * @param message - 收到的消息
 * @param clientUserId - 客户端用户ID（可选）
 * @returns 验证成功返回 true
 */
export async function autoValidateMessage(
  message: Record<string, unknown>,
  clientUserId?: number
): Promise<boolean> {
  const validator = getMessageValidator();
  return await validator.validateMessage(message, clientUserId);
}

// 导出常量
export const SECURITY_CONSTANTS = {
  MAX_MESSAGE_LATENCY: 30,     // 消息最大延迟（秒）
  TIMESTAMP_TOLERANCE: 60,     // 时间戳容差（秒）
  SIGNATURE_ALGORITHM: 'HMAC-SHA256'
} as const;
