from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.views.decorators import csrf_exempt

from .authentication import generate_jwt_token, decode_jwt_token
from .serializers import UserSerializer, ChangePasswordSerializer

User = get_user_model()


@csrf_exempt
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
        from .models import UserRole
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh(request):
    """
    JWT刷新端点
    刷新过期或即将过期的token
    """
    # 简化版本：重新生成token
    # 生产环境应该使用refresh token机制
    
    if not request.user or not request.user.is_authenticated:
        return Response(
            {'message': '用户未认证'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        token = generate_jwt_token(request.user)
    except Exception as e:
        return Response(
            {'message': '生成token失败', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'data': {
            'token': token,
            'expires_in': int(900)
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