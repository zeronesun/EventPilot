from django.db import models
from django.conf import settings
import uuid


class Profile(models.Model):
    """关联方档案"""
    class ProfileType(models.TextChoices):
        SPEAKER = 'speaker', '讲师'
        VENUE = 'venue', '场地'
        SUPPLIER = 'supplier', '供应商'
        CONTACT = 'contact', '联系人'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_type = models.CharField(
        max_length=20,
        choices=ProfileType.choices,
        verbose_name="档案类型"
    )
    
    # 基本信息
    name = models.CharField(max_length=255, verbose_name="名称")
    contact_info = models.JSONField(verbose_name="联系信息")
    
    # 合作历史
    cooperation_history = models.TextField(blank=True, verbose_name="合作历史")
    notes = models.TextField(blank=True, verbose_name="注意事项")
    
    # 标签和属性
    tags = models.JSONField(default=list, verbose_name="标签")
    rating = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="评分")
    
    # 元数据
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'profiles'
        indexes = [
            models.Index(fields=['profile_type']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = '关联方档案'
        verbose_name_plural = '关联方档案'
    
    def __str__(self):
        return f"{self.get_profile_type_display()} - {self.name}"


class ProfileEventAssociation(models.Model):
    """档案与活动的关联"""
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='event_associations',
        verbose_name="档案"
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='profile_associations',
        verbose_name="活动"
    )
    role = models.CharField(max_length=100, blank=True, verbose_name="角色")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'profile_event_associations'
        unique_together = ['profile', 'event']
        verbose_name = '档案-活动关联'
        verbose_name_plural = '档案-活动关联'