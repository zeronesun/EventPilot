from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    """管理员或只读权限"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.is_superuser:
            return True
        
        if obj == request.user:
            return True
        
        return False


class IsAdminOrSelf(permissions.BasePermission):
    """管理员或自己"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        return obj == request.user


class IsUserRoleAdmin(permissions.BasePermission):
    """管理员角色权限"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            self._is_admin(request.user)
        )
    
    def _is_admin(self, user):
        try:
            from apps.users.models import UserRole
            user_role = UserRole.objects.get(user=user)
            return user_role.role == 'admin'
        except Exception:
            return False


class IsUserOwnerOrAdmin(permissions.BasePermission):
    """资源所有者或管理员"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if isinstance(obj, User):
            return obj == request.user
        
        return getattr(obj, 'user', None) == request.user


class CanManageUsers(permissions.BasePermission):
    """用户管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            from apps.users.models import UserRole
            user_role = UserRole.objects.get(user=request.user)
            return user_role.role in ['admin', 'project_owner']
        except Exception:
            return False


class IsNotLocked(permissions.BasePermission):
    """账户未锁定权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            from apps.users.services.user_service import UserService
            return not UserService.check_account_lockout(request.user)
        except Exception:
            return True


class CanModifySelfOnly(permissions.BasePermission):
    """只能修改自己的信息"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj == request.user


class IsEmailVerified(permissions.BasePermission):
    """邮箱验证权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 管理员除外
        if request.user.is_superuser:
            return True
        
        try:
            from apps.users.models import UserRole
            user_role = UserRole.objects.get(user=request.user)
            if user_role.role == 'admin':
                return True
        except Exception:
            pass
        
        return request.user.email_verified