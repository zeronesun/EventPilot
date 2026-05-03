from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

from ..authentication import generate_jwt_token, decode_jwt_token
from .serializers import UserSerializer, ChangePasswordSerializer

User = get_user_model()


# @csrf_exempt  # Django CSRF decorator (disabled when admin is disabled)
@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    """
    JWT登录端点
    验证用户凭据并返回JWT token
    """
    from django.contrib.auth import authenticate
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'message': '需要提供用户名和密码'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 认证用户
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'message': '用户名或密码错误'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'message': '用户已被禁用'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # 生成JWT token
    token = generate_jwt_token(user)
    
    # 确保用户有UserRole，如果没有则创建
    if not hasattr(user, 'role'):
        from ..models import UserRole
        UserRole.objects.create(user=user, role='executor')
    
    # 获取用户序列化数据
    serializer = UserSerializer(user, context={'request': request})
    
    return Response({
        'data': {
            'user': serializer.data,
            'token': token,
            'expires_in': int(900)  # 15分钟（与配置一致）
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh(request):
    """
    JWT刷新端点
    刷新过期或即将过期的token
    允许使用过期的 access token 进行刷新（宽容模式）
    """
    from ..authentication import decode_jwt_token as decode_token
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = None
    
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
    
    # 尝试解码 token（即使过期也尝试获取用户信息）
    user = None
    if token:
        try:
            import jwt as jwt_lib
            payload = jwt_lib.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256'],
                options={'verify_exp': False}  # 不验证过期时间
            )
            user_id = payload.get('user_id')
            if user_id:
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                except User.DoesNotExist:
                    pass
        except Exception as e:
            logger.error(f"Refresh token decode failed: {e}")
    
    if not user or not user.is_authenticated:
        return Response(
            {'message': '无法验证用户身份，请重新登录'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        token = generate_jwt_token(user)
    except Exception as e:
        return Response(
            {'message': '生成token失败', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'data': {
            'token': token,
            'expires_in': int(settings.JWT_ACCESS_TOKEN_EXPIRY)
        }
    })


@api_view(['POST'])
def jwt_verify(request):
    """
    JWT验证端点
    验证当前JWT token是否有效
    """
    if not request.user or not request.user.is_authenticated:
        return Response(
            {'message': 'Token无效或已过期'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Token验证在中间件中完成，这里只是确认
    return Response({
        'data': {
            'valid': True,
            'user_id': str(request.user.id),
            'username': request.user.username,
            'is_staff': request.user.is_staff
        }
    })