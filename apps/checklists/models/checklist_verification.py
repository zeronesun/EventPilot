from django.db import models
from django.conf import settings
import uuid


class ChecklistVerification(models.Model):
    """清单核验执行记录"""
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', '待核验'
        IN_PROGRESS = 'in_progress', '核验中'
        ON_HOLD = 'on_hold', '暂停'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
        CANCELLED = 'cancelled', '已取消'
    
    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = 'not_required', '无需审批'
        PENDING = 'pending', '待审批'
        APPROVED = 'approved', '已批准'
        REJECTED = 'rejected', '已拒绝'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(
        'ChecklistInstance',
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name="清单实例"
    )
    
    # 核验计划
    planned_start_time = models.DateTimeField(verbose_name="计划开始时间")
    planned_end_time = models.DateTimeField(verbose_name="计划结束时间")
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name="实际开始时间")
    actual_end_time = models.DateTimeField(null=True, blank=True, verbose_name="实际结束时间")
    
    # 核验状态
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name="核验状态"
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_REQUIRED,
        verbose_name="审批状态"
    )
    
    # 核验结果
    total_items = models.IntegerField(default=0, verbose_name="总项数")
    verified_items = models.IntegerField(default=0, verbose_name="已核验项数")
    passed_items = models.IntegerField(default=0, verbose_name="通过项数")
    failed_items = models.IntegerField(default=0, verbose_name="失败项数")
    
    # 核验人
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications',
        verbose_name="核验人"
    )
    
    # 审批信息
    requires_approval = models.BooleanField(default=False, verbose_name="需要审批")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approvals',
        verbose_name="审批人"
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="审批时间")
    rejection_reason = models.TextField(blank=True, verbose_name="拒绝原因")
    
    # 异常处理
    has_exceptions = models.BooleanField(default=False, verbose_name="有异常")
    exception_details = models.JSONField(default=list, verbose_name="异常详情")
    
    # 元数据
    notes = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_verifications'
        verbose_name = '清单核验'
        verbose_name_plural = '清单核验'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instance']),
            models.Index(fields=['status']),
            models.Index(fields=['approval_status']),
            models.Index(fields=['verified_by']),
            models.Index(fields=['requires_approval']),
        ]
    
    def __str__(self):
        return f"{self.instance.name} - 核验记录"


class ChecklistVerificationDetail(models.Model):
    """清单核验详情记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(
        ChecklistVerification,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name="核验记录"
    )
    
    # 关联的清单项
    checklist_item = models.ForeignKey(
        'ChecklistItem',
        on_delete=models.CASCADE,
        verbose_name="清单项"
    )
    
    # 核验详情
    status = models.CharField(max_length=20, verbose_name="状态")
    result = models.CharField(max_length=20, verbose_name="结果")
    evidence = models.TextField(blank=True, verbose_name="证据描述")
    
    # 附件
    attachments = models.JSONField(default=list, verbose_name="附件")
    
    # 位置和时间
    verified_at = models.DateTimeField(verbose_name="核验时间")
    location = models.JSONField(null=True, blank=True, verbose_name="位置(GPS)")
    
    # 核验人
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="核验人"
    )
    
    # 备注
    notes = models.TextField(blank=True, verbose_name="备注")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'checklist_verification_details'
        verbose_name = '清单核验详情'
        verbose_name_plural = '清单核验详情'
        ordering = ['verified_at']
        indexes = [
            models.Index(fields=['verification']),
            models.Index(fields=['checklist_item']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.checklist_item.title} - {self.result}"


class ChecklistVerificationException(models.Model):
    """清单核验异常处理记录"""
    class ExceptionType(models.TextChoices):
        MISSING_ITEM = 'missing_item', '缺失项'
        FAILED_VALIDATION = 'failed_validation', '验证失败'
        TIMEOUT = 'timeout', '超时'
        ACCESS_DENIED = 'access_denied', '访问拒绝'
        SYSTEM_ERROR = 'system_error', '系统错误'
        OTHER = 'other', '其他'
    
    class ExceptionStatus(models.TextChoices):
        OPEN = 'open', '待处理'
        IN_PROGRESS = 'in_progress', '处理中'
        RESOLVED = 'resolved', '已解决'
        IGNORED = 'ignored', '已忽略'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(
        ChecklistVerification,
        on_delete=models.CASCADE,
        related_name='exceptions',
        verbose_name="核验记录"
    )
    
    # 异常信息
    exception_type = models.CharField(
        max_length=30,
        choices=ExceptionType.choices,
        verbose_name="异常类型"
    )
    status = models.CharField(
        max_length=20,
        choices=ExceptionStatus.choices,
        default=ExceptionStatus.OPEN,
        verbose_name="状态"
    )
    
    # 异常描述
    title = models.CharField(max_length=255, verbose_name="异常标题")
    description = models.TextField(verbose_name="异常描述")
    checklist_item = models.ForeignKey(
        'ChecklistItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="相关清单项"
    )
    
    # 严重程度
    severity = models.CharField(max_length=20, verbose_name="严重程度")
    
    # 处理信息
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_exceptions',
        verbose_name="处理人"
    )
    resolution = models.TextField(blank=True, verbose_name="解决方案")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_exceptions',
        verbose_name="解决人"
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="解决时间")
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    
    class Meta:
        db_table = 'checklist_verification_exceptions'
        verbose_name = '清单核验异常'
        verbose_name_plural = '清单核验异常'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['verification']),
            models.Index(fields=['status']),
            models.Index(fields=['exception_type']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"