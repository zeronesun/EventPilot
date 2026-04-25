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
            
            # 验证有效期
            if 'exp' in payload:
                exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
                if exp_time < timezone.now():
                    raise jwt.ExpiredSignatureError('Token已过期')

            # 验证签发时间
            if 'iat' in payload:
                iat_time = datetime.fromtimestamp(payload['iat'], tz=timezone.utc)
                # Token签发时间不能早于服务器时间太多（防止时钟不同步）
                if iat_time < timezone.now() - timedelta(minutes=5):
                    raise jwt.InvalidSignatureError('Token签发时间无效')
            
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
    
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': getattr(getattr(user, 'role', None), 'role', 'executor') if hasattr(user, 'role') and hasattr(user.role, 'role') else 'executor',
        'iat': datetime.now(tz=timezone.utc),
        'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=access_token_expiry),
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