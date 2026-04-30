/**
 * EventPilot 前端安全工具模块
 * 包含：WebSocket消息签名、请求防抖、错误处理、权限管理
 */

// 密码哈希工具
export class PasswordHasher {
  static async hashPassword(password: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

// WebSocket消息签名
export class WebSocketSigner {
  private secret: string;
  
  constructor(secret: string) {
    this.secret = secret;
  }
  
  async signMessage(message: Record<string, any>): Promise<{ message: Record<string, any>; signature: string }> {
    // 添加时间戳防止重放攻击
    const timestampedMessage = {
      ...message,
      _timestamp: Date.now()
    };
    
    // 创建签名字符串
    const messageString = JSON.stringify(timestampedMessage);
    const signature = await this.generateSignature(messageString + this.secret);
    
    return {
      message: timestampedMessage,
      signature
    };
  }
  
  async verifyMessage(message: Record<string, any>, signature: string, ttlSeconds: number = 60): Promise<boolean> {
    try {
      // 检查时间戳
      const currentTime = Date.now();
      const messageTime = message._timestamp || 0;
      
      if (currentTime - messageTime > ttlSeconds * 1000) {
        console.warn('WebSocket message expired');
        return false;
      }
      
      // 验证签名
      const messageString = JSON.stringify(message);
      const expectedSignature = await this.generateSignature(messageString + this.secret);
      
      return signature && signature === expectedSignature;
    } catch (error) {
      console.error('WebSocket signature verification error:', error);
      return false;
    }
  }
  
  private async generateSignature(data: string): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

// 输入清理
export class InputSanitizer {
  static sanitizeString(input: string, maxLength: number = 1000): string {
    if (!input) return '';
    
    // 移除危险字符
    const dangerousChars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r'];
    let sanitized = input;
    
    for (const char of dangerousChars) {
      sanitized = sanitized.split(char).join('');
    }
    
    // 限制长度
    if (sanitized.length > maxLength) {
      sanitized = sanitized.substring(0, maxLength);
    }
    
    return sanitized.trim();
  }
  
  static validateEmail(email: string): boolean {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
  }
  
  static sanitizeHTML(input: string): string {
    if (!input) return '';
    
    // 移除所有HTML标签
    return input.replace(/<[^>]*>/g, '');
  }
}

// XSS防护
export class XSSProtection {
  static escapeHTML(content: string): string {
    const div = document.createElement('div');
    div.textContent = content;
    return div.innerHTML;
  }
  
  static setHTMLSafely(element: HTMLElement, content: string): void {
    element.innerHTML = this.escapeHTML(content);
  }
}

// 请求防抖和节流
export class RequestUtils {
  private static pendingRequests = new Map<string, Promise<any>>();
  
  // 请求去重
  static async dedupeRequest<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!;
    }
    
    const promise = requestFn().finally(() => {
      this.pendingRequests.delete(key);
    });
    
    this.pendingRequests.set(key, promise);
    return promise;
  }
  
  // 防抖函数
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: number | null = null;
    
    return function(this: any, ...args: Parameters<T>) {
      if (timeout !== null) {
        clearTimeout(timeout);
      }
      
      timeout = setTimeout(() => {
        func.apply(this, args);
        timeout = null;
      }, wait);
    };
  }
  
  // 节流函数
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean;
    
    return function(this: any, ...args: Parameters<T>) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }
}

// 存储安全
export class StorageSecurity {
  private static prefix = 'eventpilot_secure_';
  
  static setItem(key: string, value: any): void {
    try {
      const data = JSON.stringify(value);
      // 简单的base64编码（生产环境应使用更安全的加密）
      const encoded = btoa(data);
      localStorage.setItem(this.prefix + key, encoded);
    } catch (error) {
      console.error('Storage set error:', error);
    }
  }
  
  static getItem<T>(key: string): T | null {
    try {
      const encoded = localStorage.getItem(this.prefix + key);
      if (!encoded) return null;
      
      const decoded = atob(encoded);
      return JSON.parse(decoded) as T;
    } catch (error) {
      console.error('Storage get error:', error);
      return null;
    }
  }
  
  static removeItem(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }
  
  static clearSecure(): void {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(this.prefix)) {
        localStorage.removeItem(key);
      }
    });
  }
}

// Content Security Policy helper
export class CSPHelper {
  static setNonce(nonce: string): void {
    // 为内联脚本添加nonce
    const scripts = document.querySelectorAll('script[nonce]');
    scripts.forEach(script => {
      script.setAttribute('nonce', nonce);
    });
  }
}

// 运行时环境检查
export class EnvironmentChecker {
  static isDevelopment(): boolean {
    return import.meta.env.DEV;
  }
  
  static isProduction(): boolean {
    return import.meta.env.PROD;
  }
  
  static getBaseUrl(): string {
    return import.meta.env.VITE_API_BASE_URL || '/api';
  }
}

// 安全配置
export const securityConfig = {
  maxMessageSize: 1024 * 1024, // 1MB
  requestTimeout: 30000, // 30秒
  rateLimit: {
    requests: 100,
    window: 60000 // 60秒
  },
  tokenTTL: 43200000, // 12小时
  websocket: {
    reconnectDelay: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000
  }
};

// 默认导出
export default {
  PasswordHasher,
  WebSocketSigner,
  InputSanitizer,
  XSSProtection,
  RequestUtils,
  StorageSecurity,
  CSPHelper,
  EnvironmentChecker,
  securityConfig
};