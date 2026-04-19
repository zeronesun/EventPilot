from django.db import models
from django.conf import settings
import uuid


class ChecklistTemplate(models.Model):
    """核验清单模板"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="模板名称")
    description = models.TextField(blank=True, verbose_name="描述")
    
    # 清单类型
    checklist_type = models.CharField(
        max_length=50,
        default='custom',
        verbose_name="清单类型"
    )
    
    # 适用性
    event_types = models.JSONField(default=list, verbose_name="适用活动类型")
    is_default = models.BooleanField(default=False, verbose_name="是否默认")
    
    # 版本控制
    version = models.CharField(max_length=50, default='1.0.0', verbose_name="版本号")
    status = models.CharField(max_length=20, default='draft', verbose_name="状态")
    
    # 标签和分类
    tags = models.JSONField(default=list, verbose_name="标签")
    category = models.CharField(max_length=100, blank=True, verbose_name="分类")
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name="元数据")
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
        db_table = 'checklist_templates'
        verbose_name = '核验清单模板'
        verbose_name_plural = '核验清单模板'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name


class ChecklistItemTemplate(models.Model):
    """核验清单项模板"""
    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="模板"
    )
    
    title = models.CharField(max_length=255, verbose_name="标题")
    description = models.TextField(blank=True, verbose_name="描述")
    required = models.BooleanField(default=True, verbose_name="必填")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="排序")
    
    # 权重和重要性
    weight = models.IntegerField(default=1, verbose_name="权重")
    status = models.CharField(max_length=20, default='active', verbose_name="状态")
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_item_templates'
        ordering = ['order']
        verbose_name = '核验清单项模板'
        verbose_name_plural = '核验清单项模板'
    
    def __str__(self):
        return self.title


class ChecklistInstance(models.Model):
    """核验清单实例"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='checklists',
        verbose_name="活动"
    )
    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.PROTECT,
        verbose_name="模板"
    )
    
    # 实例信息
    name = models.CharField(max_length=255, verbose_name="实例名称")
    status = models.CharField(max_length=20, default='incomplete', verbose_name="状态")
    
    # 完成度统计
    completion_rate = models.FloatField(default=0.0, verbose_name="完成度")
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        db_table = 'checklist_instances'
        verbose_name = '核验清单实例'
        verbose_name_plural = '核验清单实例'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['template']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.event.name} - {self.name}"


class ChecklistItem(models.Model):
    """核验清单项"""
    class CheckStatus(models.TextChoices):
        PENDING = 'pending', '待检查'
        IN_PROGRESS = 'in_progress', '检查中'
        PASSED = 'passed', '通过'
        FAILED = 'failed', '未通过'
        SKIPPED = 'skipped', '跳过'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(
        ChecklistInstance,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="清单实例"
    )
    template_item = models.ForeignKey(
        ChecklistItemTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="模板项"
    )
    
    # 核验内容
    title = models.CharField(max_length=255, verbose_name="标题")
    description = models.TextField(blank=True, verbose_name="描述")
    required = models.BooleanField(default=True, verbose_name="必填")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="排序")
    
    # 权重
    weight = models.IntegerField(default=1, verbose_name="权重")
    
    # 状态和备注
    notes = models.TextField(blank=True, verbose_name="备注")
    status = models.CharField(
        max_length=20,
        choices=CheckStatus.choices,
        default=CheckStatus.PENDING,
        verbose_name="状态"
    )
    
    # 附件
    attachments = models.JSONField(default=list, verbose_name="附件")
    
    # 检查人信息
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="检查人"
    )
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="检查时间")
    location = models.JSONField(null=True, blank=True, verbose_name="位置(GPS)")
    
    # 离线支持
    offline_pending = models.BooleanField(default=False, verbose_name="待同步")
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'checklist_items'
        ordering = ['order']
        indexes = [
            models.Index(fields=['instance']),
            models.Index(fields=['status']),
            models.Index(fields=['offline_pending']),
        ]
        verbose_name = '核验清单项'
        verbose_name_plural = '核验清单项'
    
    def __str__(self):
        return self.title