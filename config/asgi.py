import os
import logging
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 导入应用，确保models已注册
from django.conf import settings

# 导入WebSocket路由
from apps.websocket.routing import websocket_urlpatterns

# 导入JWT认证
from rest_framework_simplejwt.authentication import JWTAuthentication

# 配置ASGI应用
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

logger = logging.getLogger(__name__)

# 获取WebSocket URL路由
websocket_routing = URLRouter(websocket_urlpatterns)

# 配置中间件
def WebSocketMiddleware(inner):
    """
    WebSocket中间件包装器
    
    Args:
        inner: 内层应用
        
    Returns:
        包装后的应用
    """
    async def application(scope, receive, send):
        try:
            if scope['type'] == 'websocket':
                # WebSocket连接
                logger.info(f"WebSocket connection from {scope.get('client')}")
                
                # 应用WebSocket认证中间件
                from apps.websocket.middleware import WebSocketAuthMiddleware
                
                auth_app = WebSocketAuthMiddleware(inner)
                return await auth_app(dict(scope), receive, send)
            else:
                # HTTP连接
                return await inner(scope, receive, send)
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            raise
    
    return application

# 创建认证中间件
def AuthMiddlewareWrapper(inner):
    """
    JWT认证中间件包装器
    """
    async def application(scope, receive, send):
        if scope['type'] == 'websocket':
            # 添加JWT认证信息到scope
            from apps.websocket.middleware import WebSocketAuthMiddleware
            
            auth_middleware = WebSocketAuthMiddleware(inner)
            return await auth_middleware(dict(scope), receive, send)
        else:
            return await inner(scope, receive, send)
    
    return application

# 配置路由层
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareWrapper(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

logger.info("ASGI application configured with WebSocket support")