"""
EventPilot 权限控制系统
包含：角色管理、权限定义、权限检查、装饰器
"""
from functools import wraps
from typing import List, Dict, Any, Optional, Set
from django.core.cache import cache
from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# 角色定义
class Roles:
    """系统角色定义"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    OPERATOR = 'operator'
    VIEWER = 'viewer'
    GUEST = 'guest'
    
    ALL_ROLES = [ADMIN, MANAGER, OPERATOR, VIEWER, GUEST]
    
    # 角色层级（数值越高权限越大）
    ROLE_HIERARCHY = {
        GUEST: 1,
        VIEWER: 2,
        OPERATOR: 3,
        MANAGER: 4,
        ADMIN: 5
    }


# 权限定义
class Permissions:
    """系统权限定义"""
    
    # 活动管理权限
    VIEW_EVENTS = 'view_events'
    CREATE_EVENT = 'create_event'
    EDIT_EVENT = 'edit_event'
    DELETE_EVENT = 'delete_event'
    MANAGE_PARTICIPANTS = 'manage_participants'
    
    # 任务管理权限
    VIEW_TASKS = 'view_tasks'
    CREATE_TASK = 'create_task'
    EDIT_TASK = 'edit_task'
    DELETE_TASK = 'delete_task'
    ASSIGN_TASK = 'assign_task'
    
    # 文件管理权限
    VIEW_FILES = 'view_files'
    UPLOAD_FILE = 'upload_file'
    DELETE_FILE = 'delete_file'
    
    # 系统管理权限
    VIEW_USERS = 'view_users'
    MANAGE_USERS = 'manage_users'
    VIEW_ROLES = 'view_roles'
    MANAGE_ROLES = 'manage_roles'
    MANAGE_SYSTEM = 'manage_system'
    
    # 审计日志权限
    VIEW_AUDIT_LOG = 'view_audit_log'


# 角色权限映射（简化版，生产环境可用数据库驱动）
ROLE_PERMISSIONS = {
    Roles.ADMIN: set(),  # 管理员拥有所有权限
    Roles.MANAGER: {
        Permissions.VIEW_EVENTS,
        Permissions.CREATE_EVENT,
        Permissions.EDIT_EVENT,
        Permissions.VIEW_TASKS,
        Permissions.CREATE_TASK,
        Permissions.EDIT_TASK,
        Permissions.ASSIGN_TASK,
        Permissions.VIEW_FILES,
        Permissions.UPLOAD_FILE,
        Permissions.VIEW_USERS,
        Permissions.VIEW_ROLES,
        Permissions.VIEW_AUDIT_LOG
    },
    Roles.OPERATOR: {
        Permissions.VIEW_EVENTS,
        Permissions.VIEW_TASKS,
        Permissions.CREATE_TASK,
        Permissions.EDIT_TASK,
        Permissions.VIEW_FILES,
        Permissions.UPLOAD_FILE,
        Permissions.VIEW_USERS
    },
    Roles.VIEWER: {
        Permissions.VIEW_EVENTS,
        Permissions.VIEW_TASKS,
        Permissions.VIEW_FILES,
    },
    Roles.GUEST: {
        Permissions.VIEW_EVENTS
    }
}


# 角色管理器
class RoleManager:
    """角色管理"""
    
    @staticmethod
    def get_user_roles(user: User) -> List[str]:
        """获取用户的所有角色"""
        cache_key = f'user_roles_{user.id}'
        roles = cache.get(cache_key)
        
        if roles is None:
            from .models import UserProfile
            try:
                profile = user.userprofile
                roles = [profile.role]
            except UserProfile.DoesNotExist:
                roles = [Roles.GUEST]
            
            cache.set(cache_key, roles, timeout=60 * 15)  # 缓存15分钟
        
        return roles
    
    @staticmethod
    def set_user_role(user: User, role: str) -> bool:
        """设置用户角色"""
        if role not in Roles.ALL_ROLES:
            logger.error(f"Invalid role: {role}")
            return False
        
        from .models import UserProfile
        
        try:
            profile = user.userprofile
            profile.role = role
            profile.save()
            
            # 清除缓存
            cache_key = f'user_roles_{user.id}'
            cache.delete(cache_key)
            
            return True
        except UserProfile.DoesNotExist:
            # 创建profile
            UserProfile.objects.create(user=user, role=role)
            return True
        except Exception as e:
            logger.error(f"Error setting user role: {e}")
            return False
    
    @staticmethod
    def has_role(user: User, role: str) -> bool:
        """检查用户是否拥有指定角色"""
        return role in RoleManager.get_user_roles(user)
    
    @staticmethod
    def get_role_hierarchy_value(role: str) -> int:
        """获取角色的层级值（用于比较权限）"""
        return Roles.ROLE_HIERARCHY.get(role, 0)


# 权限检查器
class PermissionChecker:
    """权限检查"""
    
    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        """检查用户是否拥有指定权限"""
        if not user.is_authenticated:
            return False
        
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 管理员拥有所有权限
        if RoleManager.has_role(user, Roles.ADMIN):
            return True
        
        # 获取用户角色
        roles = RoleManager.get_user_roles(user)
        
        # 检查每个角色的权限
        for role in roles:
            role_perms = ROLE_PERMISSIONS.get(role, set())
            
            # 管理员角色有所有权限
            if role == Roles.ADMIN:
                return True
            
            if permission in role_perms:
                return True
        
        return False
    
    @staticmethod
    def has_any_permission(user: User, permissions: List[str]) -> bool:
        """检查用户是否拥有任意一个指定权限"""
        return any(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user: User, permissions: List[str]) -> bool:
        """检查用户是否拥有所有指定权限"""
        return all(PermissionChecker.has_permission(user, perm) for perm in permissions)
    
    @staticmethod
    def can_access_resource(user: User, resource_type: str, resource_id: int) -> bool:
        """检查用户是否可以访问特定资源"""
        # 检查基础权限
        view_permission = f'view_{resource_type}'
        if not PermissionChecker.has_permission(user, view_permission):
            return False
        
        # 检查资源所有权（可根据业务逻辑定制）
        try:
            from django.apps import apps
            
            model = apps.get_model(app_label='events', model_name=resource_type[:-1] if resource_type.endswith('s') else resource_type)
            resource = model.objects.get(id=resource_id)
            
            # 创建者可以访问
            if hasattr(resource, 'created_by') and resource.created_by == user:
                return True
            
            # 管理员和经理可以访问所有资源
            if RoleManager.has_role(user, Roles.ADMIN) or RoleManager.has_role(user, Roles.MANAGER):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking resource access: {e}")
            return False


# 装饰器
def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not PermissionChecker.has_permission(request.user, permission):
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'You do not have permission to perform this action',
                    'required_permission': permission
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_any_permission(*permissions: str):
    """需要任意一个权限的装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not PermissionChecker.has_any_permission(request.user, list(permissions)):
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'You need at least one of these permissions: {", ".join(permissions)}',
                    'required_permissions': list(permissions)
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_role(role: str):
    """角色检查装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not RoleManager.has_role(request.user, role):
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'You need the role "{role}" to perform this action',
                    'required_role': role
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_or_higher_role(min_role: str):
    """需要指定角色或更高级别的装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user_roles = RoleManager.get_user_roles(request.user)
            
            min_hierarchy = Roles.ROLE_HIERARCHY.get(min_role, 0)
            
            for role in user_roles:
                role_hierarchy = Roles.ROLE_HIERARCHY.get(role, 0)
                if role_hierarchy >= min_hierarchy:
                    return view_func(request, *args, **kwargs)
            
            return JsonResponse({
                'error': 'Permission denied',
                'message': f'You need role "{min_role}" or higher to perform this action',
                'required_role': min_role
            }, status=403)
        return wrapped_view
    return decorator


# 上下文处理器
def permissions_context(request):
    """向模板提供权限上下文"""
    if request.user.is_authenticated:
        user_roles = RoleManager.get_user_roles(request.user)
        user_permissions = set()
        
        for role in user_roles:
            role_perms = ROLE_PERMISSIONS.get(role, set())
            user_permissions.update(role_perms)
        
        return {
            'user_roles': user_roles,
            'user_permissions': user_permissions,
            'is_admin': Roles.ADMIN in user_roles,
            'is_manager': Roles.MANAGER in user_roles,
            'is_operator': Roles.OPERATOR in user_roles
        }
    
    return {}


# DRF权限类
from rest_framework import permissions

class EventPilotPermission:
    """自定义DRF权限类"""
    
    def has_permission(self, request, view):
        """检查是否有权限访问视图"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 基于视图方法的权限映射
        method_permission_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete'
        }
        
        action = view.action
        if not action:
            return True
        
        # 从view.action推断权限
        permission_name = f"{action}_events"
        return PermissionChecker.has_permission(request.user, permission_name)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """对象级权限：所有者可以编辑，其他人只读"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.created_by == request.user or request.user.is_superuser


# API响应工具
class PermissionResponseUtils:
    """权限相关响应工具"""
    
    @staticmethod
    def permission_denied_response(message: str = "权限不足") -> JsonResponse:
        """返回权限拒绝响应"""
        return JsonResponse({
            'error': 'permission_denied',
            'message': message
        }, status=403)
    
    @staticmethod
    def unauthorized_response() -> JsonResponse:
        """返回未授权响应"""
        return JsonResponse({
            'error': 'unauthorized',
            'message': '请先登录'
        }, status=401)
    
    @staticmethod
    def insufficient_roles_response(required_roles: List[str]) -> JsonResponse:
        """返回角色不足响应"""
        return JsonResponse({
            'error': 'insufficient_roles',
            'message': '角色权限不足',
            'required_roles': required_roles
        }, status=403)


# 初始化（创建admin用户）
def initialize_permissions():
    """初始化系统权限"""
    from .models import User
    
    try:
        admin_user = User.objects.get(username='admin')
        RoleManager.set_user_role(admin_user, Roles.ADMIN)
        print("Admin用户角色已设置为ADMIN")
    except User.DoesNotExist:
        print("Admin用户不存在，跳过角色设置")


if __name__ == '__main__':
    # 测试代码
    print("EventPilot Permission System initialized")
    print(f"Available roles: {Roles.ALL_ROLES}")
    print(f"Available permissions: { dir(Permissions) }")