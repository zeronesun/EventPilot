from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义API异常处理器
    """
    # 调用DRF默认异常处理
    response = exception_handler(exc, context)
    
    # 如果已经有响应，添加格式化信息
    if response is not None:
        api_format = {
            "error": {
                "code": get_error_code(exc),
                "message": str(exc),
                "request_id": get_request_id(context),
                "timestamp": get_timestamp(),
            }
        }
        
        # 添加详细错误信息
        if hasattr(response, 'data'):
            if isinstance(response.data, dict):
                api_format["error"]["details"] = response.data
            else:
                api_format["error"]["message"] = response.data
        
        response.data = api_format
        response.status_code = get_status_code(exc, response.status_code)
        
        # 记录错误日志
        logger.error(
            f"API Error: {get_error_code(exc)} - {str(exc)}",
            extra={
                'request_id': get_request_id(context),
                'context': context,
                'traceback': traceback.format_exc()
            }
        )
    
    else:
        #处理DRF未捕获的异常
        logger.critical(
            f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
            extra={
                'context': context,
                'traceback': traceback.format_exc()
            }
        )
        
        response = Response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "内部服务器错误",
                    "request_id": get_request_id(context),
                    "timestamp": get_timestamp(),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def get_error_code(exc):
    """将异常映射为错误代码"""
    error_mapping = {
        'ValidationError': 'VALIDATION_ERROR',
        'AuthenticationFailed': 'AUTHENTICATION_ERROR',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotFound': 'NOT_FOUND',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'ParseError': 'PARSE_ERROR',
        'Throttled': 'RATE_LIMIT_EXCEEDED',
    }
    
    for error_class, code in error_mapping.items():
        if error_class in type(exc).__name__:
            return code
    
    if hasattr(exc, 'default_code'):
        return exc.default_code.upper().replace(' ', '_')
    
    return 'INTERNAL_ERROR'


def get_status_code(exc, default_status):
    """根据异常类型返回适当的HTTP状态码"""
    if hasattr(exc, 'status_code'):
        return exc.status_code
    
    # 基于异常类型的默认状态码映射
    if 'NotFound' in type(exc).__name__:
        return status.HTTP_404_NOT_FOUND
    elif 'PermissionDenied' in type(exc).__name__:
        return status.HTTP_403_FORBIDDEN
    elif 'ValidationError' in type(exc).__name__:
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    elif 'AuthenticationFailed' in type(exc).__name__:
        return status.HTTP_401_UNAUTHORIZED
    
    return default_status


def get_request_id(context):
    """获取请求ID（需要在中间件中设置）"""
    request = context.get('request')
    if request and hasattr(request, 'id'):
        return request.id
    import uuid
    return str(uuid.uuid4())


def get_timestamp():
    """获取当前ISO格式时间戳"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + 'Z'