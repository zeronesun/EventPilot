from rest_framework import authentication, permissions, exceptions
from rest_framework.response import Response
from rest_framework import status
import jwt
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_user_class():
    """延迟加载User模型以避免循环导入"""
    return get_user_model()

User = get_user_class()  # 定义User类


class JWTAuthentication(authentication.BaseAuthentication):
    """JWT认证类"""
    
    def authenticate(self, request):
        """
        JWT认证
        """
        auth_header = self.get_header(request)
        if not auth_header:
            return None
        
        # 提取token
        try:
            payload = self.decode_jwt_token(auth_header)
            user = self.get_user_from_payload(payload)
            return (user, payload)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token已过期')
        except jwt.InvalidSignatureError:
            raise exceptions.AuthenticationFailed('Token无效')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('用户不存在')
        except Exception as e:
            logger.error(f"JWT认证失败: {str(e)}")
            raise exceptions.AuthenticationFailed('认证失败')
    
    def get_header(self, request):
        """
        从请求头中获取JWT token
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        # 支持 "Bearer <token>" 格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]
    
    def decode_jwt_token(self, token):
        """
        解码JWT token并验证
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )

            # PyJWT 自动验证 exp 和 iat，无需手动验证

            return payload

        except jwt.ExpiredSignatureError:
            logger.info("JWT token已过期")
            raise
        except jwt.InvalidSignatureError:
            logger.error(f"JWT解码失败: {str(e)}")
            raise
    
    def get_user_from_payload(self, payload):
        """
        从JWT payload中获取用户
        """
        User = get_user_class()  # 延迟加载
        user_id = payload.get('user_id')

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('用户不存在或已禁用')

        # 获取用户角色
        if 'role' in payload:
            # 验证role是否正确（可选择加验证逻辑）
            pass

        return user


class JWTPermission(permissions.BasePermission):
    """JWT权限类"""
    
    def has_permission(self, request, view):
        """检查JWT用户权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 检查用户帐户是否激活
        if not request.user.is_active:
            return False
        
        return True


def generate_jwt_token(user):
    """
    生成JWT token
    """
    User = get_user_class()  # 延迟加载
    access_token_expiry = int(settings.JWT_ACCESS_TOKEN_EXPIRY)

    now = timezone.now()
    # 使用timestamp(PKR)int)确保跨版本兼容性
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': getattr(getattr(user, 'role', None), 'role', 'executor') if hasattr(user, 'role') and hasattr(user.role, 'role') else 'executor',
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(seconds=access_token_expiry)).timestamp()),
        'type': 'access'
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    return token


def decode_jwt_token(token):
    """
    解码JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token已过期')
    except jwt.InvalidSignatureError:
        raise exceptions.AuthenticationFailed('Token无效')


def refresh_jwt_token():
    """
    刷新JWT token（简化版本，实际应使用refresh token机制）
    """
    # 暂时实现：返回空
    return None