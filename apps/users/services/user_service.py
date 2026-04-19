import logging
import re
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Q, Count, Sum, F, QuerySet
from django.utils import timezone
from django.conf import settings

# 避免循环导入
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir.parent))

from apps.users.models import User, UserRole, UserActivity, ResourceAccess

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务层 - 处理用户CRUD操作的业务逻辑"""
    
    # 密码强度规则
    PASSWORD_STRENGTH = dict(
        min_length=8,
        require_uppercase=True,
        require_lowercase=True,
        require_digit=True,
        require_special=True,
        special_chars='!@#$%^&*()_+-=[]{}|;:,.<>?'
    )
    
    # 账户安全配置
    SECURITY_CONFIG = dict(
        max_failed_attempts=5,
        lockout_duration=30,  # 分钟
        password_expiry_days=90,
    )
    
    # 用户状态逻辑映射
    STATUS_LOGIC = {
        'active': lambda u: u.is_active and not u.is_deleted,
        'inactive': lambda u: not u.is_active and not u.is_deleted,
        'locked': lambda u: u.locked_until and u.locked_until > timezone.now(),
        'deleted': lambda u: u.is_deleted,
        'all': lambda u: True,
    }
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """验证密码强度"""
        errors = []
        
        if len(password) < UserService.PASSWORD_STRENGTH['min_length']:
            errors.append(f'密码长度至少{UserService.PASSWORD_STRENGTH["min_length"]}位')
        
        if UserService.PASSWORD_STRENGTH['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append('密码必须包含大写字母')
        
        if UserService.PASSWORD_STRENGTH['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append('密码必须包含小写字母')
        
        if UserService.PASSWORD_STRENGTH['require_digit'] and not re.search(r'\d', password):
            errors.append('密码必须包含数字')
        
        special_chars = UserService.PASSWORD_STRENGTH['special_chars']
        if UserService.PASSWORD_STRENGTH['require_special'] and not re.search(f'[{re.escape(special_chars)}]', password):
            errors.append(f'密码必须包含特殊字符（{special_chars}）')
        
        # 检查常见弱密码
        weak_passwords = ['password', '123456', 'qwerty', 'admin', '12345678', 'password123']
        if password.lower() in weak_passwords:
            errors.append('密码太简单，请使用更复杂的密码')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_user_data(username: str, email: str, password: str = None, **kwargs) -> Tuple[bool, List[str]]:
        """验证用户数据"""
        errors = []
        
        # 用户名验证
        if not username or len(username) < 3:
            errors.append('用户名长度至少3位')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('用户名只能包含字母、数字和下划线')
        elif User.objects.filter(username=username).exists():
            errors.append('用户名已存在')
        
        # 邮箱验证
        if not email or not '@' in email:
            errors.append('请输入有效的邮箱地址')
        elif User.objects.filter(email=email).exists():
            errors.append('邮箱已被注册')
        
        # 密码验证
        if password:
            is_valid, password_errors = UserService.validate_password_strength(password)
            if not is_valid:
                errors.extend(password_errors)
        
        # 手机号验证
        phone = kwargs.get('phone')
        if phone and not re.match(r'^[0-9+\-\s()]+$', phone):
            errors.append('手机号格式不正确')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def log_user_activity(user: User, activity_type: str, ip_address: str = None, 
                          user_agent: str = None, details: Dict = None):
        """记录用户活动"""
        try:
            UserActivity.objects.create(
                user=user,
                activity_type=activity_type,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {}
            )
        except Exception as e:
            logger.error(f"记录用户活动失败: {e}")
    
    @staticmethod
    def get_client_info(request) -> Tuple[str, str]:
        """获取客户端信息"""
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return ip_address, user_agent
    
    @staticmethod
    def create_user(user_data: Dict, request=None) -> Tuple[User, List[str]]:
        """创建新用户"""
        errors = []
        
        try:
            with transaction.atomic():
                # 验证数据
                is_valid, validation_errors = UserService.validate_user_data(
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    password=user_data.get('password'),
                    phone=user_data.get('phone')
                )
                
                if not is_valid:
                    return None, validation_errors
                
                # 创建用户
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    phone=user_data.get('phone', ''),
                    avatar_url=user_data.get('avatar_url', ''),
                    department=user_data.get('department', ''),
                    position=user_data.get('position', ''),
                    email_verified=False,
                )
                
                # 设置密码修改时间
                user.password_changed_at = timezone.now()
                user.save()
                
                # 分配角色
                role = user_data.get('role', 'executor')
                UserRole.objects.create(user=user, role=role)
                
                # 记录活动
                if request:
                    ip_address, user_agent = UserService.get_client_info(request)
                    UserService.log_user_activity(
                        user=user,
                        activity_type='profile_update',  # 用户创建
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={'created_by': request.user.username if hasattr(request, 'user') else 'system'}
                    )
                
                logger.info(f"用户创建成功: {user.username}")
                return user, []
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            errors.append(f"创建用户失败: {str(e)}")
            return None, errors
    
    @staticmethod
    def update_user(user: User, update_data: Dict, request=None) -> Tuple[bool, List[str]]:
        """更新用户信息"""
        errors = []
        
        try:
            with transaction.atomic():
                # 角色更新
                if 'role' in update_data:
                    try:
                        user_role, created = UserRole.objects.get_or_create(user=user)
                        user_role.role = update_data['role']
                        user_role.save()
                        
                        # 记录角色变更活动
                        if request:
                            ip_address, user_agent = UserService.get_client_info(request)
                            UserService.log_user_activity(
                                user=user,
                                activity_type='role_change',
                                ip_address=ip_address,
                                user_agent=user_agent,
                                details={
                                    'new_role': update_data['role'],
                                    'changed_by': request.user.username
                                }
                            )
                    except Exception as e:
                        errors.append(f"角色更新失败: {str(e)}")
                        return False, errors
                    
                    del update_data['role']
                
                # 密码更新逻辑在 change_password 方法中处理
                if 'password' in update_data:
                    del update_data['password']
                
                # 状态更新
                if 'is_active' in update_data:
                    user.is_active = update_data['is_active']
                    del update_data['is_active']
                
                # 更新用户信息
                for field, value in update_data.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                
                user.save()
                
                # 记录活动
                if request:
                    ip_address, user_agent = UserService.get_client_info(request)
                    UserService.log_user_activity(
                        user=user,
                        activity_type='profile_update',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={
                            'updated_fields': list(update_data.keys()),
                            'updated_by': request.user.username
                        }
                    )
                
                logger.info(f"用户更新成功: {user.username}")
                return True, []
                
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            errors.append(f"更新用户失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str, 
                        force_change: bool = False, request=None) -> Tuple[bool, List[str]]:
        """修改密码"""
        errors = []
        
        try:
            # 验证旧密码（如果不是强制修改）
            if not force_change:
                if not user.check_password(old_password):
                    errors.append('旧密码不正确')
                    # 记录失败的密码更改尝试
                    UserService.log_user_activity(
                        user=user,
                        activity_type='failed_login',
                        details={'reason': 'incorrect_old_password'}
                    )
                    return False, errors
            
            # 验证新密码强度
            is_valid, password_errors = UserService.validate_password_strength(new_password)
            if not is_valid:
                errors.extend(password_errors)
                return False, errors
            
            # 修改密码
            user.set_password(new_password)
            user.password_changed_at = timezone.now()
            user.force_password_change = False
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save()
            
            # 记录活动
            if request:
                ip_address, user_agent = UserService.get_client_info(request)
                UserService.log_user_activity(
                    user=user,
                    activity_type='password_change',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        'changed_by': 'self' if not force_change else request.user.username,
                        'forced': force_change
                    }
                )
            
            logger.info(f"密码修改成功: {user.username}")
            return True, []
            
        except Exception as e:
            logger.error(f"修改密码失败: {e}")
            errors.append(f"修改密码失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def delete_user(user: User, soft_delete: bool = True, request=None) -> Tuple[bool, List[str]]:
        """删除用户"""
        errors = []
        
        try:
            if soft_delete:
                # 软删除
                with transaction.atomic():
                    user.is_active = False
                    user.is_deleted = True
                    user.deleted_at = timezone.now()
                    if request and hasattr(request, 'user'):
                        user.deleted_by = request.user
                    user.save()
                    
                    # 记录删除活动
                    if request:
                        ip_address, user_agent = UserService.get_client_info(request)
                        UserService.log_user_activity(
                            user=user,
                            activity_type='bulk_operation',  # 使用批量操作类型表示删除
                            ip_address=ip_address,
                            user_agent=user_agent,
                            details={
                                'action': 'soft_delete',
                                'deleted_by': request.user.username
                            }
                        )
                    
                    logger.info(f"用户软删除成功: {user.username}")
            else:
                # 硬删除 - 清理关联数据
                with transaction.atomic():
                    # 记录删除前的信息
                    user_id = str(user.id)
                    username = user.username
                    
                    # 删除关联数据
                    UserRole.objects.filter(user=user).delete()
                    ResourceAccess.objects.filter(user=user).delete()
                    UserActivity.objects.filter(user=user).delete()
                    
                    # 删除用户
                    user.delete()
                    
                    # 记录删除活动（通过系统用户记录）
                    if request:
                        ip_address, user_agent = UserService.get_client_info(request)
                        # 创建一个系统活动记录
                        UserService.log_user_activity(
                            user=request.user if hasattr(request, 'user') else user,
                            activity_type='bulk_operation',
                            ip_address=ip_address,
                            user_agent=user_agent,
                            details={
                                'action': 'hard_delete',
                                'deleted_user': username,
                                'deleted_user_id': user_id,
                                'deleted_by': request.user.username if hasattr(request, 'user') else 'system'
                            }
                        )
                    
                    logger.info(f"用户硬删除成功: {username}")
            
            return True, errors
            
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            errors.append(f"删除用户失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def bulk_update_users_status(user_ids: List[str], is_active: bool, request=None) -> Tuple[int, List[str]]:
        """批量更新用户状态"""
        errors = []
        updated_count = 0
        
        try:
            with transaction.atomic():
                users = User.objects.filter(id__in=user_ids)
                updated_count = users.update(is_active=is_active)
                
                # 记录批量操作
                for user in users:
                    if request:
                        ip_address, user_agent = UserService.get_client_info(request)
                        UserService.log_user_activity(
                            user=user,
                            activity_type='bulk_operation',
                            ip_address=ip_address,
                            user_agent=user_agent,
                            details={
                                'action': 'status_update',
                                'new_status': is_active,
                                'updated_by': request.user.username
                            }
                        )
                
                logger.info(f"批量状态更新成功: {updated_count}个用户")
                
        except Exception as e:
            logger.error(f"批量状态更新失败: {e}")
            errors.append(f"批量状态更新失败: {str(e)}")
        
        return updated_count, errors
    
    @staticmethod
    def bulk_assign_roles(user_ids: List[str], role: str, request=None) -> Tuple[int, List[str]]:
        """批量分配角色"""
        errors = []
        updated_count = 0
        
        try:
            with transaction.atomic():
                for user_id in user_ids:
                    user = User.objects.filter(id=user_id).first()
                    if user:
                        UserRole.objects.update_or_create(
                            user=user,
                            defaults={'role': role}
                        )
                        updated_count += 1
                        
                        # 记录活动
                        if request:
                            ip_address, user_agent = UserService.get_client_info(request)
                            UserService.log_user_activity(
                                user=user,
                                activity_type='role_change',
                                ip_address=ip_address,
                                user_agent=user_agent,
                                details={
                                    'new_role': role,
                                    'changed_by': request.user.username
                                }
                            )
                
                logger.info(f"批量角色分配成功: {updated_count}个用户")
                
        except Exception as e:
            logger.error(f"批量角色分配失败: {e}")
            errors.append(f"批量角色分配失败: {str(e)}")
        
        return updated_count, errors
    
    @staticmethod
    def bulk_delete_users(user_ids: List[str], soft_delete: bool = True, request=None) -> Tuple[int, List[str]]:
        """批量删除用户"""
        errors = []
        deleted_count = 0
        
        try:
            with transaction.atomic():
                users = User.objects.filter(id__in=user_ids)
                
                if soft_delete:
                    users.update(
                        is_active=False,
                        is_deleted=True,
                        deleted_at=timezone.now()
                    )
                    
                    if request and hasattr(request, 'user'):
                        users.update(deleted_by=request.user)
                    
                    deleted_count = users.count()
                    
                    # 记录活动
                    for user in users:
                        if request:
                            ip_address, user_agent = UserService.get_client_info(request)
                            UserService.log_user_activity(
                                user=user,
                                activity_type='bulk_operation',
                                ip_address=ip_address,
                                user_agent=user_agent,
                                details={
                                    'action': 'bulk_soft_delete',
                                    'deleted_by': request.user.username
                                }
                            )
                else:
                    # 硬删除
                    user_ids_list = list(users.values_list('id', flat=True))
                    deleted_count = len(user_ids_list)
                    
                    # 删除关联数据
                    UserRole.objects.filter(user_id__in=user_ids_list).delete()
                    ResourceAccess.objects.filter(user_id__in=user_ids_list).delete()
                    UserActivity.objects.filter(user_id__in=user_ids_list).delete()
                    
                    users.delete()
                    
                    if request:
                        ip_address, user_agent = UserService.get_client_info(request)
                        UserService.log_user_activity(
                            user=request.user,
                            activity_type='bulk_operation',
                            ip_address=ip_address,
                            user_agent=user_agent,
                            details={
                                'action': 'bulk_hard_delete',
                                'deleted_count': deleted_count,
                                'deleted_by': request.user.username
                            }
                        )
                
                logger.info(f"批量删除成功: {deleted_count}个用户")
                
        except Exception as e:
            logger.error(f"批量删除失败: {e}")
            errors.append(f"批量删除失败: {str(e)}")
        
        return deleted_count, errors
    
    @staticmethod
    def check_account_lockout(user: User) -> bool:
        """检查账户是否被锁定"""
        if user.locked_until and user.locked_until > timezone.now():
            return True
        return False
    
    @staticmethod
    def increment_failed_login(user: User, ip_address: str = None):
        """增加失败登录次数"""
        user.failed_login_attempts += 1
        
        # 检查是否需要锁定账户
        max_attempts = UserService.SECURITY_CONFIG['max_failed_attempts']
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = timezone.now() + timedelta(
                minutes=UserService.SECURITY_CONFIG['lockout_duration']
            )
        
        user.save()
        
        # 记录失败的登录尝试
        UserService.log_user_activity(
            user=user,
            activity_type='failed_login',
            ip_address=ip_address,
            details={'attempts': user.failed_login_attempts}
        )
    
    @staticmethod
    def unlock_account(user: User, request=None) -> Tuple[bool, List[str]]:
        """解锁账户"""
        errors = []
        
        try:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save()
            
            # 记录解锁活动
            if request:
                ip_address, user_agent = UserService.get_client_info(request)
                UserService.log_user_activity(
                    user=user,
                    activity_type='account_unlocked',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={'unlocked_by': request.user.username}
                )
            
            logger.info(f"账户解锁成功: {user.username}")
            return True, errors
            
        except Exception as e:
            logger.error(f"解锁账户失败: {e}")
            errors.append(f"解锁账户失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def calculate_user_activity_score(user: User, days: int = 30) -> int:
        """计算用户活跃度分数"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        activities = UserActivity.objects.filter(
            user=user,
            created_at__gte=cutoff_date
        )
        
        # 基础分数
        score = 0
        
        # 登录分数（每次登录+5分）
        login_count = activities.filter(activity_type='login').count()
        score += login_count * 5
        
        # 操作分数（每次操作+2分）
        operation_count = activities.exclude(
            activity_type__in=['login', 'logout']
        ).count()
        score += operation_count * 2
        
        # 活跃日期数（每个活跃日期+3分）
        active_dates = activities.values('created_at__date').distinct().count()
        score += active_dates * 3
        
        # 最近登录奖励
        if user.last_login and (timezone.now() - user.last_login).days <= 7:
            score += 10
        
        return min(score, 100)  # 最大100分
    
    @staticmethod
    def get_inactive_users(threshold_days: int = 60) -> QuerySet:
        """获取不活跃用户"""
        threshold_date = timezone.now() - timedelta(days=threshold_days)
        return User.objects.filter(
            Q(last_login__lt=threshold_date) | Q(last_login__isnull=True),
            is_active=True,
            is_deleted=False
        )
    
    @staticmethod
    def get_user_statistics(days: int = 30) -> Dict[str, Any]:
        """获取用户统计信息"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        total_users = User.objects.filter(is_deleted=False).count()
        active_users = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).count()
        inactive_users = total_users - active_users
        new_users = User.objects.filter(
            created_at__gte=cutoff_date,
            is_deleted=False
        ).count()
        
        # 活跃度统计
        active_last_week = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'new_users': new_users,
            'active_last_week': active_last_week,
            'total_activities': UserActivity.objects.filter(
                created_at__gte=cutoff_date
            ).count()
        }