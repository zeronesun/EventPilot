/**
 * WebSocket 客户端增强版本
 * 添加消息签名验证和时间戳检查
 */

import { WebSocketClient, WebSocketMessage } from './websocket-client';
import { signMessage, validateMessage, isAuthorizedSource, verifyTimestamp } from './crypto';
import { getAuthConfig } from './auth-config';

export class SecureWebSocketClient extends WebSocketClient {
  private secretKey: string;
  private userId: number | null = null;
  private enabledSignature: boolean = true;

  constructor(config: any, secretKey?: string) {
    super(config);
    this.secretKey = secretKey || getAuthConfig().websocketSecret || 'default-secret';
  }

  setUserId(userId: number) {
    this.userId = userId;
  }

  setEnableSignature(enabled: boolean) {
    this.enabledSignature = enabled;
  }

  // 重写 send 方法，添加签名
  send(message: WebSocketMessage): boolean {
    if (!this.enabledSignature) {
      return super.send(message);
    }

    // 克隆消息以避免修改原始对象
    const secureMessage = { ...message };

    // 添加时间戳（防止重放攻击）
    if (!secureMessage.timestamp) {
      secureMessage.timestamp = Math.floor(Date.now() / 1000);
    }

    // 添加用户ID
    if (this.userId !== null && !secureMessage.user_id) {
      secureMessage.user_id = this.userId;
    }

    // 添加签名
    if (!secureMessage.signature) {
      secureMessage.signature = signMessage(secureMessage, this.secretKey);
    }

    return super.send(secureMessage);
  }

  // 重写 handleMessage，添加验证
  protected handleMessage(message: WebSocketMessage): void {
    // 基础验证
    if (!validateMessage(message)) {
      console.error('[SecureWebSocket] Message validation failed:', message);
      this.triggerError(new Error('Message validation failed'));
      return;
    }

    // 验证来源（如果有用户ID）
    if (this.userId !== null && !isAuthorizedSource(message, new Set([this.userId]))) {
      console.error('[SecureWebSocket] Unauthorized message source:', message.user_id);
      this.triggerError(new Error('Unauthorized message source'));
      return;
    }

    // 调用父类处理
    super.handleMessage(message);
  }

  private triggerError(error: Error) {
    // 触发所有错误处理器
    this['errorHandlers']?.forEach((handler: any) => handler(error));
  }
}

export function getSecureWebSocketClient(): SecureWebSocketClient {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.host;
  const wsUrl = `${wsProtocol}//${wsHost}/ws/events/`;

  return new SecureWebSocketClient({
    url: wsUrl,
    autoReconnect: true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    heartbeatInterval: 30000,
  });
}
