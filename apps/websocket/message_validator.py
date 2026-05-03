"""
WebSocket消息验证器
验证收到和发送的消息的完整性和安全性
"""

import time
import hmac
import hashlib
import logging
from typing import Dict, Any, Set, Optional
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class WebSocketMessageValidator:
    """
    WebSocket消息验证器
    
    功能：
    - 消息签名验证
    - 时间戳验证（防止重放攻击）
    - 消息类型验证
    - 来源验证
    """
    
    # 允许的消息类型
    ALLOWED_MESSAGE_TYPES = {
        'notification',
        'presence',
        'user_status',
        'collaboration',
        'event_update',
        'task_update',
        'ping',
        'pong',
        'connected',
        'error',
        'subscribe',
        'unsubscribe',
    }
    
    # 最大消息时间差（防止重放攻击），单位：秒
    MAX_TIMESTAMP_AGE = 60
    
    def __init__(self, secret: Optional[str] = None):
        """
        初始化验证器

        Args:
            secret: 用于签名的密钥，默认从settings获取
        """
        from apps.security.utils import WS_MESSAGE_SECRET
        self.secret = secret or getattr(settings, 'WEBSOCKET_MESSAGE_SECRET', WS_MESSAGE_SECRET)
        
    def validate_message(self, message: Dict[str, Any], user_id: Optional[int] = None) -> bool:
        """
        验证消息的完整性和安全性
        
        Args:
            message: 要验证的消息
            user_id: 发送者的用户ID（可选，用于验证来源）
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 基础结构验证
            if not self._validate_structure(message):
                return False
            
            # 时间戳验证
            if not self._validate_timestamp(message):
                return False
            
            # 消息类型验证
            if not self._validate_message_type(message):
                return False
            
            # 签名验证（如果存在）
            if 'signature' in message:
                if not self._validate_signature(message):
                    return False
            
            # 来源验证（如果提供了user_id）
            if user_id is not None:
                if not self._validate_source(message, user_id):
                    return False
            
            logger.debug(f"[WebSocket Validator] Message validated successfully: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"[WebSocket Validator] Validation error: {e}", exc_info=True)
            return False
    
    def _validate_structure(self, message: Dict[str, Any]) -> bool:
        """验证消息基础结构"""
        if not isinstance(message, dict):
            logger.error("[WebSocket Validator] Message is not a dictionary")
            return False
        
        if not message.keys():
            logger.error("[WebSocket Validator] Message is empty")
            return False
        
        return True
    
    def _validate_timestamp(self, message: Dict[str, Any]) -> bool:
        """验证时间戳（防止重放攻击）"""
        timestamp = message.get('timestamp')
        
        # 消息必须有时间戳
        if timestamp is None:
            # 特殊消息类型可以不需要时间戳
            if message.get('type') in ['pong', 'ping']:
                return True
            logger.warning("[WebSocket Validator] Message missing timestamp")
            return False
        
        # 验证时间戳是数字
        if not isinstance(timestamp, (int, float)):
            logger.error("[WebSocket Validator] Invalid timestamp format")
            return False
        
        # 验证时间戳在有效范围内
        current_time = time.time()
        message_time = float(timestamp)
        age = abs(current_time - message_time)
        
        if age > self.MAX_TIMESTAMP_AGE:
            logger.warning(f"[WebSocket Validator] Timestamp too old: {age:.2f}s > {self.MAX_TIMESTAMP_AGE}s")
            return False
        
        return True
    
    def _validate_message_type(self, message: Dict[str, Any]) -> bool:
        """验证消息类型"""
        message_type = message.get('type')
        
        if not message_type:
            logger.error("[WebSocket Validator] Message missing type field")
            return False
        
        if message_type not in self.ALLOWED_MESSAGE_TYPES:
            logger.error(f"[WebSocket Validator] Unrecognized message type: {message_type}")
            return False
        
        return True
    
    def _validate_signature(self, message: Dict[str, Any]) -> bool:
        """验证消息签名"""
        signature_from_message = message.get('signature')
        if not signature_from_message:
            logger.error("[WebSocket Validator] Message missing signature")
            return False
        
        # 计算预期签名
        message_copy = message.copy()
        
        # 移除签名字段，否则验证会失败
        message_copy.pop('signature', None)
        
        expected_signature = self._sign_message(message_copy)
        
        # 使用安全的比较方法防止时序攻击
        if not self._secure_compare(signature_from_message, expected_signature):
            logger.error("[WebSocket Validator] Invalid message signature")
            return False
        
        return True
    
    def _validate_source(self, message: Dict[str, Any], expected_user_id: int) -> bool:
        """验证消息来源"""
        message_user_id = message.get('user_id')
        
        if message_user_id is None:
            # 某些系统消息可能没有user_id
            if message.get('type') in ['connected', 'error']:
                return True
            logger.error("[WebSocket Validator] Message missing user_id")
            return False
        
        if message_user_id != expected_user_id:
            logger.error(
                f"[WebSocket Validator] Source mismatch: expected {expected_user_id}, got {message_user_id}"
            )
            return False
        
        return True
    
    def _sign_message(self, message: Dict[str, Any]) -> str:
        """对消息进行签名"""
        import json
        message_str = json.dumps(message, sort_keys=True, separators=(',', ':'))
        return hmac.new(
            self.secret.encode(),
            message_str.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _secure_compare(self, a: str, b: str) -> bool:
        """
        安全的字符串比较（防止时序攻击）
        """
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def add_signature(self, message: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        为消息添加签名、时间戳和user_id
        
        Args:
            message: 要签名的消息
            user_id: 发送者用户ID
            
        Returns:
            包含签名的消息副本
        """
        message_copy = message.copy()
        
        # 添加时间戳
        if 'timestamp' not in message_copy:
            message_copy['timestamp'] = int(time.time())
        
        # 添加user_id
        if user_id is not None and 'user_id' not in message_copy:
            message_copy['user_id'] = user_id
        
        # 添加签名
        signature = self._sign_message(message_copy)
        message_copy['signature'] = signature
        
        return message_copy


# 全局验证器实例
_validator: Optional[WebSocketMessageValidator] = None


def get_message_validator() -> WebSocketMessageValidator:
    """获取全局消息验证器实例"""
    global _validator
    if _validator is None:
        _validator = WebSocketMessageValidator()
    return _validator
