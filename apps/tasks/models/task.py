from django.db import models
from django.conf import settings
import uuid


class Task(models.Model):
    """任务"""
    class Status(models.TextChoices):
        PENDING = 'pending', '待办'
        READY = 'ready', '就绪'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'
        CANCELLED = 'cancelled', '已取消'
        BLOCKED = 'blocked', '阻塞'
    
    class TaskType(models.TextChoices):
        PLANNING = 'planning', '策划'
        GUEST = 'guest', '嘉宾'
        MATERIAL = 'material', '物料'
        VENUE = 'venue', '场地'
        PROMOTION = 'promotion', '宣传'
        ONSITE = 'onsite', '现场'
        REVIEW = 'review', '复盘'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        'events.Event', 
        on_delete=models.CASCADE, 
        related_name='tasks',
        verbose_name="活动"
    )
    
    # 基本信息
    title = models.CharField(max_length=255, verbose_name="任务标题")
    description = models.TextField(blank=True, verbose_name="任务描述")
    task_type = models.CharField(
        max_length=20, 
        choices=TaskType.choices,
        verbose_name="任务类型"
    )
    
    # 责任和状态
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks',
        verbose_name="负责人"
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING,
        verbose_name="状态"
    )
    progress = models.PositiveSmallIntegerField(default=0, verbose_name="进度(%)")
    
    # 时间信息
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="截止日期")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="开始日期")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
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
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['status']),
            models.Index(fields=['task_type']),
            models.Index(fields=['assignee']),
            models.Index(fields=['due_date']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = '任务'
        verbose_name_plural = '任务'
    
    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    """任务依赖关系"""
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='dependencies',
        verbose_name="任务"
    )
    depends_on = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='dependents',
        verbose_name="依赖任务"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'task_dependencies'
        unique_together = ['task', 'depends_on']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['depends_on']),
        ]
        verbose_name = '任务依赖'
        verbose_name_plural = '任务依赖'

    def __str__(self):
        return f"{self.task.title} 依赖 {self.depends_on.title}"


class CommunicationTask(models.Model):
    """沟通任务"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        Task, 
        on_delete=models.CASCADE, 
        related_name='communication',
        verbose_name="任务"
    )
    
    # 沟通内容
    content = models.TextField(verbose_name="沟通内容")
    requirements = models.TextField(blank=True, verbose_name="要求")

    # 沟通对象
    communicators = models.JSONField(default=list, blank=True, verbose_name="联系人")

    # 结论性文件
    conclusion_files = models.JSONField(default=list, blank=True, verbose_name="结论文件")
    is_closed = models.BooleanField(default=False, verbose_name="已闭环")
    
    class Meta:
        db_table = 'communication_tasks'
        verbose_name = '沟通任务'
        verbose_name_plural = '沟通任务'
    
    def __str__(self):
        return f"{self.task.title} - 沟通任务"