import logging
from typing import Dict, Any
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    UserSerializer, UserListSerializer, UserSimpleSerializer,
    UserCreationSerializer, UserUpdateSerializer, AdminUserUpdateSerializer,
    ChangePasswordSerializer, AdminPasswordResetSerializer,
    BulkUserStatusUpdateSerializer, BulkRoleAssignSerializer,
    BulkDeleteUsersSerializer, UserImportSerializer, UserUnlockSerializer,
    RoleSerializer, UserActivitySerializer, UserStatisticsSerializer,
    InactiveUsersSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsAdminOrSelf, IsUserRoleAdmin,
    CanManageUsers, IsNotLocked, CanModifySelfOnly
)
from apps.users.models import UserRole, UserActivity
from apps.users.services.user_service import UserService
from apps.users.services.user_import_service import UserImportService

User = get_user_model()
logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集 - 完整的CRUD操作"""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'department']
    ordering_fields = ['username', 'email', 'created_at', 'last_login']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取用户查询集"""
        queryset = User.objects.filter(is_deleted=False).select_related('role')
        
        # 状态过滤
        status_filter = self.request.query_params.get('status', 'active')
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        # 其他状态保持原样
        
        return queryset
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreationSerializer
        elif self.action in ['update', 'partial_update']:
            if self.request.user.is_superuser or self._is_admin():
                return AdminUserUpdateSerializer
            return UserUpdateSerializer
        return UserSerializer
    
    def _is_admin(self):
        """检查是否为管理员"""
        try:
            user_role = UserRole.objects.get(user=self.request.user)
            return user_role.role == 'admin'
        except Exception:
            return False
    
    def create(self, request, *args, **kwargs):
        """创建新用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 记录创建用户的活动
        try:
            ip_address, user_agent = UserService.get_client_info(request)
            UserService.log_user_activity(
                user=user,
                activity_type='profile_update',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'created_by': request.user.username}
            )
        except Exception as e:
            logger.error(f"记录创建用户活动失败: {e}")
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """获取用户详情"""
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """更新用户信息"""
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        
        # 检查权限 - 非管理员只能修改自己的信息
        if not (request.user.is_superuser or self._is_admin()) and user != request.user:
            return Response(
                {'detail': '您没有权限修改其他用户的信息'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(UserSerializer(user).data)
    
    def destroy(self, request, *args, **kwargs):
        """删除用户"""
        user = self.get_object()
        
        # 不允许删除自己
        if user == request.user:
            return Response(
                {'detail': '不能删除自己的账户'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 执行软删除
        success, errors = UserService.delete_user(user, soft_delete=True, request=request)
        
        if not success:
            return Response(
                {'detail': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """获取当前用户信息"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # 检查账户锁定状态
        if UserService.check_account_lockout(user):
            return Response(
                {'detail': '账户已被锁定，请联系管理员'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 验证旧密码
        if not user.check_password(serializer.validated_data['old_password']):
            # 记录失败的密码更改尝试
            ip_address, user_agent = UserService.get_client_info(request)
            UserService.increment_failed_login(user, ip_address)
            
            return Response(
                {'detail': '旧密码不正确'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 修改密码
        success, errors = UserService.change_password(
            user,
            serializer.validated_data['old_password'],
            serializer.validated_data['new_password'],
            request=request
        )
        
        if not success:
            return Response({'detail': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': '密码修改成功'})
    
    @action(detail=True, methods=['post'], permission_classes=[CanManageUsers])
    def reset_password(self, request, pk=None):
        """管理员重置用户密码"""
        user = self.get_object()
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 只有管理员可以执行
        if not (request.user.is_superuser or self._is_admin()):
            return Response(
                {'detail': '需要管理员权限'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 重置密码
        success, errors = UserService.change_password(
            user,
            old_password=None,  # 管理员操作不需要验证旧密码
            new_password=serializer.validated_data['new_password'],
            force_change=True,
            request=request
        )
        
        if not success:
            return Response({'detail': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': f'用户 {user.username} 密码已重置'})
    
    @action(detail=True, methods=['post'], permission_classes=[CanManageUsers])
    def unlock(self, request, pk=None):
        """解锁用户账户"""
        user = self.get_object()
        serializer = UserUnlockSerializer(data={'user_id': str(user.id)})
        serializer.is_valid(raise_exception=True)
        
        success, errors = UserService.unlock_account(user, request)
        
        if not success:
            return Response({'detail': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': f'用户 {user.username} 账户已解锁'})
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """获取用户活动日志"""
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')
        
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取单个用户统计信息"""
        user = self.get_object()
        
        activity_score = UserService.calculate_user_activity_score(user, days=30)
        account_age_days = (timezone.now() - user.created_at).days
        login_count = user.login_count
        
        activities_breakdown = UserActivity.objects.filter(
            user=user
        ).values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'user_id': str(user.id),
            'username': user.username,
            'activity_score': activity_score,
            'account_age_days': account_age_days,
            'total_logins': login_count,
            'activities_breakdown': list(activities_breakdown),
            'status': 'locked' if UserService.check_account_lockout(user) else 'active',
            'profile_completed': user.profile_completed
        })


class BulkUpdateStatusView(generics.GenericAPIView):
    """批量更新用户状态视图"""
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = BulkUserStatusUpdateSerializer
    
    def post(self, request):
        """批量更新用户状态"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_count, errors = UserService.bulk_update_users_status(
            user_ids=serializer.validated_data['user_ids'],
            is_active=serializer.validated_data['is_active'],
            request=request
        )
        
        if errors:
            return Response(
                {'detail': errors, 'updated_count': updated_count},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': f'成功更新 {updated_count} 个用户状态',
            'updated_count': updated_count
        })


class BulkAssignRolesView(generics.GenericAPIView):
    """批量分配角色视图"""
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = BulkRoleAssignSerializer
    
    def post(self, request):
        """批量分配角色"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_count, errors = UserService.bulk_assign_roles(
            user_ids=serializer.validated_data['user_ids'],
            role=serializer.validated_data['role'],
            request=request
        )
        
        if errors:
            return Response(
                {'detail': errors, 'updated_count': updated_count},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': f'成功为 {updated_count} 个用户分配角色',
            'updated_count': updated_count,
            'role': serializer.validated_data['role']
        })


class BulkDeleteView(generics.GenericAPIView):
    """批量删除用户视图"""
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = BulkDeleteUsersSerializer
    
    def post(self, request):
        """批量删除用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 检查是否包含自己
        user_ids = [str(uid) for uid in serializer.validated_data['user_ids']]
        if str(request.user.id) in user_ids:
            return Response(
                {'detail': '不能删除自己的账户'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, errors = UserService.bulk_delete_users(
            user_ids=user_ids,
            soft_delete=serializer.validated_data['soft_delete'],
            request=request
        )
        
        if errors:
            return Response(
                {'detail': errors, 'deleted_count': deleted_count},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delete_type = '软删除' if serializer.validated_data['soft_delete'] else '硬删除'
        return Response({
            'message': f'成功{delete_type} {deleted_count} 个用户',
            'deleted_count': deleted_count,
            'delete_type': delete_type
        })


class UserImportView(generics.GenericAPIView):
    """用户批量导入视图"""
    serializer_class = UserImportSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]
    
    def post(self, request):
        """批量导入用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        results = UserImportService.import_users_from_list(
            users_data=serializer.validated_data['users'],
            send_welcome_email=serializer.validated_data['send_welcome_email'],
            force_password_change=serializer.validated_data['force_password_change']
        )
        
        return Response(results, status=status.HTTP_200_OK)


class UserStatisticsView(generics.GenericAPIView):
    """用户统计视图"""
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = UserStatisticsSerializer
    
    def get(self, request):
        """获取用户统计信息"""
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        days = serializer.validated_data['days']
        
        # 基础统计
        statistics = UserService.get_user_statistics(days)
        
        # 按角色统计
        role_stats = UserRole.objects.values(
            'role'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按部门统计
        department_stats = User.objects.filter(
            is_deleted=False
        ).values('department').annotate(
            count=Count('id')
        ).exclude(
            department=''
        ).order_by('-count')
        
        # 最新注册用户
        new_users = User.objects.filter(
            is_deleted=False,
            created_at__gte=timezone.now() - timezone.timedelta(days=days)
        ).order_by('-created_at')[:10]
        
        # 活跃用户（过去7天内登录）
        active_users = User.objects.filter(
            is_deleted=False,
            last_login__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return Response({
            **statistics,
            'role_distribution': list(role_stats),
            'department_distribution': list(department_stats),
            'active_users_week': active_users,
            'recent_registrations': UserListSerializer(new_users, many=True).data
        })


class InactiveUsersView(generics.ListAPIView):
    """不活跃用户视图"""
    permission_classes = [IsAuthenticated, CanManageUsers]
    serializer_class = UserListSerializer
    
    def get_queryset(self):
        """获取不活跃用户列表"""
        threshold_days = int(self.request.query_params.get('threshold_days', 60))
        return UserService.get_inactive_users(threshold_days)


class RoleListView(generics.ListAPIView):
    """角色列表视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = None
    
    def get(self, request):
        """获取所有可用角色"""
        roles = []
        for key, display in UserRole.ROLE_CHOICES:
            roles.append({
                'value': key,
                'label': display
            })
        return Response(roles)