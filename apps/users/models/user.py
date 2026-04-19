from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
import hashlib


class User(AbstractUser):
    """扩展的用户模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True, verbose_name="手机号")
    avatar_url = models.URLField(blank=True, verbose_name="头像URL")
    department = models.CharField(max_length=100, blank=True, verbose_name="部门")
    position = models.CharField(max_length=100, blank=True, verbose_name="职位")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_phone_hash(self):
        """获取手机号码哈希（用于隐私查询）"""
        if self.phone:
            return hashlib.sha256(self.phone.encode()).hexdigest()
        return None


class UserRole(models.Model):
    """用户角色"""
    ROLE_CHOICES = [
        ('admin', '系统管理员'),
        ('project_owner', '项目负责人'),
        ('executor', '执行成员'),
        ('observer', '只读观察者'),
    ]
    
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='role', verbose_name="用户")
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='executor',
        verbose_name="角色"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'user_roles'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class ResourceAccess(models.Model):
    """资源级权限"""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='resource_accesses', verbose_name="用户")
    resource_type = models.CharField(max_length=50, verbose_name="资源类型")
    resource_id = models.UUIDField(verbose_name="资源ID")
    permission_level = models.PositiveSmallIntegerField(default=1, verbose_name="权限级别")
    granted_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='granted_permissions',
        verbose_name="授权人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    
    class Meta:
        db_table = 'resource_access'
        unique_together = ['user', 'resource_type', 'resource_id']
        indexes = [
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'created_at']),
        ]
        verbose_name = '资源权限'
        verbose_name_plural = '资源权限'

    def __str__(self):
        return f"{self.user.username} - {self.resource_type} - Level {self.permission_level}"