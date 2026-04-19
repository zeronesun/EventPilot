import uuid
import logging
from django.utils.deprecation import RemovedInDjango40Warning
from django.utils.functional import SimpleLazyObject

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """
    请求ID中间件
    为每个请求生成唯一的请求ID，便于日志追踪和问题排查
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 生成请求ID
        request.id = str(uuid.uuid4())
        request.start_time = __import__('time').time()
        
        response = self.get_response(request)
        
        # 添加请求ID到响应头
        response['X-Request-ID'] = request.id
        response['X-Process-Time'] = f"{__import__('time').time() - request.start_time:.3f}s"
        
        return response


class OperationLoggingMiddleware:
    """
    操作日志中间件
    记录用户的关键操作
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 只对认证用户记录操作日志
        if request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            logger.info(
                f"User ID: {getattr(request.user, 'id', 'unknown')} - "
                f"Method: {request.method} - "
                f"Path: {request.path} - "
                f"IP: {self._get_client_ip(request)}"
            )
        
        return self.get_response(self)(request)
    
    def _get_client_ip(self, request):
        """
        获取客户端IP地址
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# 中间件配置定义
MIDDLEWARE_CLASSES = []