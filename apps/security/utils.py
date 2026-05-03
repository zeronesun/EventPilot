"""
EventPilot API安全增强模块
包含：密码哈希、JWT令牌验证、输入清理、XSS防护
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import os

# 密码安全相关配置
PASSWORD_SALT_LENGTH = 32
BCRYPT_ROUNDS = 12
SESSION_TIMEOUT_MINUTES = 30

# JWT令牌配置
# 安全修复：从环境变量读取JWT密钥
_JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not _JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required in production")
JWT_SECRET_KEY = _JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 12

# WebSocket安全配置
# 安全修复：从环境变量读取WebSocket密钥
_WEBSOCKET_MESSAGE_SECRET = os.getenv('WEBSOCKET_MESSAGE_SECRET')
if not _WEBSOCKET_MESSAGE_SECRET:
    if os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes'):
        _WEBSOCKET_MESSAGE_SECRET = 'dev-only-secret-not-for-production'
    else:
        raise ValueError("WEBSOCKET_MESSAGE_SECRET environment variable is required in production")
WS_MESSAGE_SECRET = _WEBSOCKET_MESSAGE_SECRET
WS_MESSAGE_EXPIRY_SECONDS = 60  # WebSocket消息60秒后过期
WS_MAX_MESSAGE_SIZE = 1024 * 1024  # 最大1MB消息


class PasswordHasher:
    """密码哈希和验证工具类"""
    
    @staticmethod
    def generate_salt() -> str:
        """生成随机盐值"""
        return secrets.token_hex(PASSWORD_SALT_LENGTH)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """使用PBKDF2哈希密码"""
        if salt is None:
            salt = secrets.token_hex(PASSWORD_SALT_LENGTH)
        
        # 使用PBKDF2-HMAC-SHA256进行密码哈希
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000  # 迭代次数
        )
        
        return f"{salt}:{key.hex()}"
    
    @staticmethod
    def verify_password(hashed_password: str, password: str) -> bool:
        """验证密码"""
        try:
            salt, key_hex = hashed_password.split(':')
            new_key = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                salt.encode('utf-8'), 
                100000
            )
            return secrets.compare_digest(new_key.hex(), key_hex)
        except Exception:
            return False


class TokenValidator:
    """JWT令牌验证工具类"""
    
    @staticmethod
    def generate_token(payload: Dict[str, Any]) -> str:
        """生成JWT令牌"""
        import base64
        import time
        
        # 添加过期时间
        payload['exp'] = int(time.time()) + (JWT_EXPIRATION_HOURS * 3600)
        payload['iat'] = int(time.time())
        
        # Header
        header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
        header_json = json.dumps(header, separators=(',', ':'))
        header_b64 = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip('=')
        
        # Payload
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        # Signature
        to_sign = f"{header_b64}.{payload_b64}"
        signature = hashlib.sha256((to_sign + JWT_SECRET_KEY).encode()).hexdigest()
        
        return f"{header_b64}.{payload_b64}.{signature}"
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            import base64
            
            # 分割token
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature = parts
            
            # 验证签名
            to_verify = f"{header_b64}.{payload_b64}"
            expected_signature = hashlib.sha256((to_verify + JWT_SECRET_KEY).encode()).hexdigest()
            
            if not secrets.compare_digest(signature, expected_signature):
                return None
            
            # 解码payload
            padding = '=' * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode()
            payload = json.loads(payload_json)
            
            # 检查过期时间
            import time
            if payload.get('exp', 0) < time.time():
                return None
            
            return payload
            
        except Exception:
            return None


class InputSanitizer:
    """输入清理工具类，防止XSS和注入攻击"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """清理字符串输入"""
        if not input_str:
            return ""
        
        # 移除危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
        # 限制长度
        if len(input_str) > max_length:
            input_str = input_str[:max_length]
        
        return input_str.strip()
    
    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """清理HTML输入，仅保留基本标签"""
        if not input_str:
            return ""
        
        # 允许的HTML标签
        ALLOWED_TAGS = ['<p>', '</p>', '<br>', '<strong>', '</strong>', '<em>', '</em>']
        
        for tag in ALLOWED_TAGS:
            input_str = input_str.replace(tag, tag)
        
        # 移除所有其他标签
        import re
        input_str = re.sub(r'<[^>]+>', '', input_str)
        
        return input_str
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class WebSocketSecurity:
    """WebSocket安全工具类"""
    
    @staticmethod
    def generate_message_signature(message: Dict[str, Any], secret: str) -> str:
        """生成WebSocket消息签名"""
        import time
        
        # 添加时间戳防止重放攻击
        message['_timestamp'] = str(int(time.time()))
        
        # 创建签名字符串
        message_str = json.dumps(message, sort_keys=True)
        signature = hashlib.sha256((message_str + secret).encode()).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_message_signature(message: Dict[str, Any], signature: str, secret: str) -> bool:
        """验证WebSocket消息签名"""
        try:
            # 检查时间戳
            import time
            current_time = int(time.time())
            msg_timestamp = int(message.get('_timestamp', 0))
            
            if current_time - msg_timestamp > WS_MESSAGE_EXPIRY_SECONDS:
                return False  # 消息过期
            
            # 重新计算签名
            message_str = json.dumps(message, sort_keys=True)
            expected_signature = hashlib.sha256((message_str + secret).encode()).hexdigest()
            
            return secrets.compare_digest(expected_signature, signature)
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_websocket_message(message: Any) -> Optional[Dict[str, Any]]:
        """清理WebSocket消息"""
        # 限制消息大小
        message_str = str(message)
        if len(message_str) > WS_MAX_MESSAGE_SIZE:
            return None
        
        # 转换为字典
        if isinstance(message, dict):
            cleaned = {}
            for key, value in message.items():
                # 清理键和值
                clean_key = InputSanitizer.sanitize_string(str(key), 100)
                if isinstance(value, str):
                    clean_value = InputSanitizer.sanitize_string(value, 500)
                elif isinstance(value, (int, float, bool)):
                    clean_value = value
                elif isinstance(value, (list, dict)):
                    continue  # 跳过复杂类型
                else:
                    clean_value = str(value)
                
                if clean_key:  # 只保留有效的键
                    cleaned[clean_key] = clean_value
            
            return cleaned
        
        return None


# Rate limiting
class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.clients = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """检查客户端是否在速率限制内"""
        current_time = datetime.now()
        
        # 清理过期记录
        if client_id in self.clients:
            if (current_time - self.clients[client_id]['start_time']).total_seconds() > self.window_seconds:
                del self.clients[client_id]
        
        # 初始化客户端记录
        if client_id not in self.clients:
            self.clients[client_id] = {
                'count': 0,
                'start_time': current_time
            }
        
        # 检查请求次数
        if self.clients[client_id]['count'] >= self.max_requests:
            return False
        
        self.clients[client_id]['count'] += 1
        return True


# 全局实例
password_hasher = PasswordHasher()
token_validator = TokenValidator()
input_sanitizer = InputSanitizer()
websocket_security = WebSocketSecurity()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)