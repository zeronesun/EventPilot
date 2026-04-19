from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer, UserSimpleSerializer, ChangePasswordSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """用户视图集"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        """获取用户查询集"""
        return User.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # 验证旧密码
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'message': '旧密码不正确'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 设置新密码
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # 可选：删除旧token强制重新登录
        Token.objects.filter(user=user).delete()
        
        return Response({'message': '密码修改成功'})