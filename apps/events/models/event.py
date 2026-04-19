from django.db import models
from django.conf import settings
import uuid


class Event(models.Model):
    """活动项目"""
    class Status(models.TextChoices):
        PLANNING = 'planning', '策划中'
        EXECUTING = 'executing', '执行中'
        COMPLETED = 'completed', '已完成'
        REVIEWED = 'reviewed', '已复盘'
        CANCELLED = 'cancelled', '已取消'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="活动名称")
    type = models.CharField(max_length=50, verbose_name="活动类型")
    description = models.TextField(blank=True, verbose_name="描述")
    
    # 时间信息
    start_date = models.DateTimeField(verbose_name="开始时间")
    end_date = models.DateTimeField(verbose_name="结束时间")
    
    # 客户信息
    client = models.CharField(max_length=255, blank=True, verbose_name="客户")
    client_contact = models.CharField(max_length=100, blank=True, verbose_name="客户联系人")
    
    # 预算信息
    estimated_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="预估预算"
    )
    actual_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="实际预算"
    )
    budget_variance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="预算偏差"
    )
    
    # 状态和归属
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PLANNING,
        verbose_name="状态"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='owned_events',
        verbose_name="负责人"
    )
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        db_table = 'events'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['owner']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = '活动'
        verbose_name_plural = '活动'
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class BudgetItem(models.Model):
    """预算明细"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        'Event', 
        on_delete=models.CASCADE, 
        related_name='budget_items',
        verbose_name="活动"
    )
    category_name = models.CharField(max_length=100, verbose_name="预算科目")
    name = models.CharField(max_length=255, verbose_name="预算项名称")
    
    # 预算金额
    estimated_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="预估金额"
    )
    actual_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="实际金额"
    )
    variance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="偏差"
    )
    
    # 责任和状态
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="负责人"
    )
    status = models.CharField(max_length=20, default='pending', verbose_name="状态")
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'budget_items'
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['status']),
        ]
        verbose_name = '预算明细'
        verbose_name_plural = '预算明细'

    def __str__(self):
        return f"{self.event.name} - {self.name}"