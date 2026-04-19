import json
import logging
from typing import Optional
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from apps.users.models import User

logger = logging.getLogger(__name__)


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    WebSocket认证中间件
    实现基于JWT的WebSocket连接认证
    """
    
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        
        # 从查询参数或头部获取token
        token = self._get_token_from_scope(scope)
        
        if token:
            user = await self._get_user_from_token(token)
            scope['user'] = user
            scope['token'] = token
        else:
            scope['user'] = AnonymousUser()
            scope['token'] = None
            
            if self._require_auth(scope['path']):
                logger.warning(f"Unauthorized WebSocket connection attempt to {scope['path']}")
                await self._deny_connection(send)
                return
                
        return await super().__call__(scope, receive, send)
    
    def _get_token_from_scope(self, scope: dict) -> Optional[str]:
        """从scope中提取JWT token"""
        # 尝试从查询参数获取
        query_string = scope.get('query_string', b'').decode()
        if 'token=' in query_string:
            try:
                token = query_string.split('token=')[1].split('&')[0]
                return token
            except (IndexError, ValueError):
                pass
                
        # 尝试从headers获取
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', headers.get(b'Authorization', b'')).decode()
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
            
        return None
    
    @database_sync_to_async
    def _get_user_from_token(self, token: str):
        """使用JWT token获取用户"""
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # 预加载用户信息
            user.objects.current_user = user
            
            logger.info(f"WebSocket authenticated user: {user.username} (ID: {user.id})")
            return user
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid JWT token in WebSocket: {str(e)}")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {str(e)}")
            return AnonymousUser()
    
    def _require_auth(self, path: str) -> bool:
        """检查路径是否需要认证"""
        # 某些公共端点可能不需要认证
        public_paths = ['/ws/public/', '/ws/health/']
        return not any(public_path in path for public_path in public_paths)
    
    async def _deny_connection(self, send):
        """拒绝WebSocket连接"""
        await send({
            'type': 'websocket.close',
            'code': 4001,  # 自定义错误代码
            'reason': json.dumps({'error': 'Authentication required'})
        })


class WebSocketRateLimitMiddleware(BaseMiddleware):
    """
    WebSocket速率限制中间件
    防止连接滥用和DoS攻击
    """
    
    def __init__(self, inner):
        super().__init__(inner)
        self._connection_tracker = {}
        self._max_connections_per_ip = 5
        self._connection_timeout = 3600  # 1小时
        
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        client_ip = self._get_client_ip(scope)
        
        # 检查连接限制
        if client_ip and not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            await self._deny_connection(send)
            return
            
        return await super().__call__(scope, receive, send)
    
    def _get_client_ip(self, scope: dict) -> Optional[str]:
        """获取客户端IP地址"""
        client = scope.get('client')
        if client:
            return client[0]
            
        # 尝试从headers获取
        headers = dict(scope.get('headers', []))
        x_forwarded_for = headers.get(b'x-forwarded-for', b'').decode()
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
            
        x_real_ip = headers.get(b'x-real-ip', b'').decode()
        return x_real_ip if x_real_ip else None
    
    def _check_rate_limit(self, ip: str) -> bool:
        """检查IP的连接速率限制"""
        import time
        current_time = time.time()
        
        # 清理过期记录
        self._connection_tracker = {
            key: value for key, value in self._connection_tracker.items()
            if current_time - value.get('last_seen', 0) < self._connection_timeout
        }
        
        # 检查当前IP的连接数
        ip_connections = self._connection_tracker.get(ip, {})
        if not ip_connections:
            self._connection_tracker[ip] = {'count': 0, 'last_seen': current_time}
            return True
            
        if ip_connections.get('count', 0) >= self._max_connections_per_ip:
            return False
            
        ip_connections['count'] += 1
        ip_connections['last_seen'] = current_time
        return True
    
    async def _deny_connection(self, send):
        """拒绝连接"""
        await send({
            'type': 'websocket.close',
            'code': 4002,
            'reason': json.dumps({'error': 'Rate limit exceeded'})
        })