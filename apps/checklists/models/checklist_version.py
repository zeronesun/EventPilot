from django.db import models
from django.conf import settings
import uuid


class ChecklistVersion(models.Model):
    """清单版本模型"""
    class VersionType(models.TextChoices):
        MAJOR = 'major', '重大更新'
        MINOR = 'minor', '次要更新'
        PATCH = 'patch', '补丁更新'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 关联的模板或实例
    template = models.ForeignKey(
        'ChecklistTemplate',
        on_delete=models.CASCADE,
        related_name='versions',
        null=True,
        blank=True,
        verbose_name="模板"
    )
    instance = models.ForeignKey(
        'ChecklistInstance',
        on_delete=models.CASCADE,
        related_name='versions',
        null=True,
        blank=True,
        verbose_name="实例"
    )
    
    # 版本信息
    version_number = models.CharField(max_length=50, verbose_name="版本号")
    version_type = models.CharField(
        max_length=20,
        choices=VersionType.choices,
        default=VersionType.PATCH,
        verbose_name="版本类型"
    )
    
    # 变更信息
    changelog = models.TextField(verbose_name="变更日志")
    changes = models.JSONField(default=dict, verbose_name="变更详情")
    
    # 版本数据快照
    snapshot = models.JSONField(default=dict, verbose_name="数据快照")
    
    # 生命周期
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_rollback = models.BooleanField(default=False, verbose_name="是否回滚版本")
    
    # 元数据
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_versions'
        verbose_name = '清单版本'
        verbose_name_plural = '清单版本'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template']),
            models.Index(fields=['instance']),
            models.Index(fields=['version_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        target = self.template.name if self.template else self.instance.name
        return f"{target} - v{self.version_number}"


class ChecklistVersionComparison(models.Model):
    """清单版本对比记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 对比的版本
    from_version = models.ForeignKey(
        ChecklistVersion,
        on_delete=models.CASCADE,
        related_name='comparisons_from',
        verbose_name="源版本"
    )
    to_version = models.ForeignKey(
        ChecklistVersion,
        on_delete=models.CASCADE,
        related_name='comparisons_to',
        verbose_name="目标版本"
    )
    
    # 对比结果
    differences = models.JSONField(default=dict, verbose_name="差异")
    summary = models.TextField(verbose_name="对比摘要")
    
    # 元数据
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'checklist_version_comparisons'
        verbose_name = '清单版本对比'
        verbose_name_plural = '清单版本对比'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"v{self.from_version.version_number} -> v{self.to_version.version_number}"