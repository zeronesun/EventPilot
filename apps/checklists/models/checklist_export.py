from django.db import models
from django.conf import settings
import uuid


class ChecklistExport(models.Model):
    """清单导出记录"""
    class ExportFormat(models.TextChoices):
        CSV = 'csv', 'CSV格式'
        EXCEL = 'excel', 'Excel格式'
        PDF = 'pdf', 'PDF格式'
        JSON = 'json', 'JSON格式'
    
    class ExportStatus(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSING = 'processing', '处理中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 导出目标
    instance = models.ForeignKey(
        'ChecklistInstance',
        on_delete=models.CASCADE,
        related_name='exports',
        null=True,
        blank=True,
        verbose_name="实例"
    )
    template = models.ForeignKey(
        'ChecklistTemplate',
        on_delete=models.CASCADE,
        related_name='exports',
        null=True,
        blank=True,
        verbose_name="模板"
    )
    
    # 导出配置
    export_format = models.CharField(
        max_length=20,
        choices=ExportFormat.choices,
        verbose_name="导出格式"
    )
    include_items = models.BooleanField(default=True, verbose_name="包含清单项")
    include_attachments = models.BooleanField(default=False, verbose_name="包含附件")
    include_metadata = models.BooleanField(default=False, verbose_name="包含元数据")
    
    # 导出结果
    status = models.CharField(
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
        verbose_name="状态"
    )
    file_path = models.CharField(max_length=500, blank=True, verbose_name="文件路径")
    file_url = models.URLField(blank=True, verbose_name="文件URL")
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="文件大小")
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    
    # 元数据
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_exports'
        verbose_name = '清单导出'
        verbose_name_plural = '清单导出'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instance']),
            models.Index(fields=['template']),
            models.Index(fields=['status']),
            models.Index(fields=['export_format']),
        ]
    
    def __str__(self):
        target = self.instance.name if self.instance else self.template.name
        return f"{target} - {self.export_format}"


class ChecklistImport(models.Model):
    """清单导入记录"""
    class ImportStatus(models.TextChoices):
        PENDING = 'pending', '待处理'
        VALIDATING = 'validating', '验证中'
        PROCESSING = 'processing', '处理中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 导入配置
    import_format = models.CharField(max_length=20, verbose_name="导入格式")
    file_path = models.CharField(max_length=500, verbose_name="文件路径")
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="文件大小")
    
    # 导入选项
    create_template = models.BooleanField(default=False, verbose_name="创建模板")
    create_instance = models.BooleanField(default=False, verbose_name="创建实例")
    update_existing = models.BooleanField(default=False, verbose_name="更新现有")
    
    # 导入结果
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
        verbose_name="状态"
    )
    
    # 统计信息
    total_records = models.IntegerField(default=0, verbose_name="总记录数")
    processed_records = models.IntegerField(default=0, verbose_name="已处理记录数")
    success_records = models.IntegerField(default=0, verbose_name="成功记录数")
    failed_records = models.IntegerField(default=0, verbose_name="失败记录数")
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    validation_errors = models.JSONField(default=list, verbose_name="验证错误")
    
    # 元数据
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_imports'
        verbose_name = '清单导入'
        verbose_name_plural = '清单导入'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['import_format']),
        ]
    
    def __str__(self):
        return f"导入记录 - {self.import_format}"