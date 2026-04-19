from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from typing import Dict, Any
from apps.users.models import UserRole, UserActivity
from apps.users.services.user_service import UserService

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """用户角色序列化器"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'role', 'role_display', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserActivitySerializer(serializers.ModelSerializer):
    """用户活动序列化器"""
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'ip_address', 'user_agent', 'details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserCreationSerializer(serializers.ModelSerializer):
    """用户创建序列化器（内部使用）"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="至少8位，包含大小写字母、数字和特殊字符"
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=UserRole.ROLE_CHOICES,
        default='executor',
        help_text="用户角色"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone', 'avatar_url',
            'department', 'position', 'role', 'is_active'
        ]
        extra_kwargs = {
            'username': {'required': True, 'min_length': 3},
            'email': {'required': True},
            'is_active': {'default': True}
        }
    
    def validate_username(self, value: str) -> str:
        """验证用户名"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("用户名只能包含字母、数字和下划线")
        return value
    
    def validate_email(self, value: str) -> str:
        """验证邮箱"""
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("邮箱已被注册")
        return value
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        # 验证密码确认
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("密码和确认密码不匹配")
        
        # 验证密码强度
        is_valid, errors = UserService.validate_password_strength(data.get('password'))
        if not is_valid:
            raise serializers.ValidationError({"password": errors})
        
        # 验证手机号格式
        if data.get('phone') and not re.match(r'^[0-9+\-\s()]+$', data['phone']):
            raise serializers.ValidationError({"phone": "手机号格式不正确"})
        
        return data
    
    def create(self, validated_data: Dict[str, Any]) -> User:
        """创建用户"""
        validated_data.pop('confirm_password')
        
        request = self.context.get('request')
        
        # 使用服务层创建用户
        user, errors = UserService.create_user(validated_data, request)
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    role = serializers.ChoiceField(
        choices=UserRole.ROLE_CHOICES,
        required=False,
        help_text="用户角色"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'avatar_url', 'department', 'position', 'role', 'is_active',
            'email_verified', 'profile_completed'
        ]
        read_only_fields = ['email_verified']
    
    def validate_email(self, value: str) -> str:
        """验证邮箱"""
        value = value.lower().strip()
        instance = self.instance
        if User.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("邮箱已被使用")
        return value
    
    def validate_username(self, value: str) -> str:
        """验证用户名"""
        instance = self.instance
        if User.objects.filter(username=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("用户名已存在")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("用户名只能包含字母、数字和下划线")
        return value
    
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """更新用户"""
        request = self.context.get('request')
        
        # 使用服务层更新用户
        success, errors = UserService.update_user(instance, validated_data, request)
        
        if not success:
            raise serializers.ValidationError(errors)
        
        return instance


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """管理员用户更新序列化器（包含敏感操作）"""
    role = serializers.ChoiceField(
        choices=UserRole.ROLE_CHOICES,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'avatar_url', 'department', 'position', 'role', 'is_active',
            'email_verified', 'profile_completed', 'force_password_change',
            'failed_login_attempts', 'locked_until'
        ]
        read_only_fields = ['email_verified']
    
    def validate_username(self, value: str) -> str:
        """验证用户名"""
        instance = self.instance
        if User.objects.filter(username=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("用户名已存在")
        return value
    
    def validate_email(self, value: str) -> str:
        """验证邮箱"""
        value = value.lower().strip()
        instance = self.instance
        if User.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("邮箱已被使用")
        return value
    
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """更新用户（管理员版本）"""
        request = self.context.get('request')
        
        # 使用服务层更新用户
        success, errors = UserService.update_user(instance, validated_data, request)
        
        if not success:
            raise serializers.ValidationError(errors)
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        help_text="至少8位，包含大小写字母、数字和特殊字符"
    )
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("新密码和确认密码不匹配")
        
        # 验证新密码强度
        is_valid, errors = UserService.validate_password_strength(data['new_password'])
        if not is_valid:
            raise serializers.ValidationError({"new_password": errors})
        
        return data


class AdminPasswordResetSerializer(serializers.Serializer):
    """管理员密码重置序列化器"""
    user_id = serializers.UUIDField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8
    )
    confirm_password = serializers.CharField(required=True, write_only=True)
    force_change = serializers.BooleanField(
        default=True,
        help_text="是否强制用户修改密码"
    )
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("新密码和确认密码不匹配")
        
        # 验证新密码强度
        is_valid, errors = UserService.validate_password_strength(data['new_password'])
        if not is_valid:
            raise serializers.ValidationError({"new_password": errors})
        
        # 验证用户存在
        if not User.objects.filter(pk=data['user_id']).exists():
            raise serializers.ValidationError("用户不存在")
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """用户详情序列化器"""
    role = RoleSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_locked = serializers.SerializerMethodField()
    days_since_last_login = serializers.SerializerMethodField()
    account_age_days = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'phone', 'avatar_url', 'department', 'position', 'role',
            'is_active', 'email_verified', 'profile_completed', 'is_locked',
            'last_login', 'created_at', 'updated_at', 'days_since_last_login',
            'account_age_days'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']
    
    def get_is_locked(self, obj: User) -> bool:
        """检查账户是否被锁定"""
        return UserService.check_account_lockout(obj)
    
    def get_days_since_last_login(self, obj: User) -> int:
        """获取距离上次登录的天数"""
        if not obj.last_login:
            return 365  # 从未登录
        return (timezone.now() - obj.last_login).days
    
    def get_account_age_days(self, obj: User) -> int:
        """获取账户创建天数"""
        return (timezone.now() - obj.created_at).days


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器"""
    role_data = RoleSerializer(source='role', read_only=True)
    role = serializers.CharField(source='role.role', read_only=True)
    role_display = serializers.CharField(source='role.get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_locked = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'department',
            'position', 'role', 'role_display', 'is_active',
            'is_locked', 'last_login', 'created_at'
        ]
    
    def get_is_locked(self, obj: User) -> bool:
        """检查账户是否被锁定"""
        return UserService.check_account_lockout(obj)


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简化序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar_url', 'full_name']
        read_only_fields = fields


class BulkUserStatusUpdateSerializer(serializers.Serializer):
    """批量状态更新序列化器"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1,
        help_text="用户ID列表"
    )
    is_active = serializers.BooleanField(required=True)
    
    def validate_user_ids(self, value: list) -> list:
        """验证用户ID"""
        if len(value) > 100:
            raise serializers.ValidationError("一次最多更新100个用户")
        
        existing_count = User.objects.filter(
            id__in=value,
            is_deleted=False
        ).count()
        
        if existing_count != len(value):
            raise serializers.ValidationError("部分用户不存在或已被删除")
        
        return value


class BulkRoleAssignSerializer(serializers.Serializer):
    """批量角色分配序列化器"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1,
        help_text="用户ID列表"
    )
    role = serializers.ChoiceField(
        choices=UserRole.ROLE_CHOICES,
        required=True
    )
    
    def validate_user_ids(self, value: list) -> list:
        """验证用户ID"""
        if len(value) > 100:
            raise serializers.ValidationError("一次最多分配100个用户")
        
        return value


class BulkDeleteUsersSerializer(serializers.Serializer):
    """批量删除用户序列化器"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1,
        help_text="用户ID列表"
    )
    soft_delete = serializers.BooleanField(
        default=True,
        help_text="是否软删除"
    )
    
    def validate_user_ids(self, value: list) -> list:
        """验证用户ID"""
        if len(value) > 100:
            raise serializers.ValidationError("一次最多删除100个用户")
        
        return value


class UserImportSerializer(serializers.Serializer):
    """用户批量导入序列化器"""
    users = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1,
        max_length=1000,
        help_text="用户数据列表"
    )
    send_welcome_email = serializers.BooleanField(
        default=False,
        help_text="是否发送欢迎邮件"
    )
    force_password_change = serializers.BooleanField(
        default=True,
        help_text="是否强制修改密码"
    )
    
    def validate_users(self, value: list) -> list:
        """验证用户数据"""
        if not value:
            raise serializers.ValidationError("用户数据不能为空")
        
        return value


class UserUnlockSerializer(serializers.Serializer):
    """用户解锁序列化器"""
    user_id = serializers.UUIDField(required=True)
    
    def validate_user_id(self, value):
        """验证用户ID"""
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("用户不存在")
        return value


class UserStatisticsSerializer(serializers.Serializer):
    """用户统计序列化器"""
    days = serializers.IntegerField(
        default=30,
        min_value=1,
        max_value=365,
        help_text="统计天数"
    )


class InactiveUsersSerializer(serializers.Serializer):
    """不活跃用户查询序列化器"""
    threshold_days = serializers.IntegerField(
        default=60,
        min_value=7,
        max_value=365,
        help_text="不活跃天数阈值"
    )