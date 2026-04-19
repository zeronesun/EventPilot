from django.db import models
from django.conf import settings
import uuid


class Review(models.Model):
    """复盘"""
    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name="活动"
    )
    
    # 基本信息
    title = models.CharField(max_length=255, verbose_name="复盘标题")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="状态"
    )
    
    # 复盘维度
    goal_achievement = models.TextField(blank=True, verbose_name="目标达成")
    process_execution = models.TextField(blank=True, verbose_name="流程执行")
    cost_control = models.TextField(blank=True, verbose_name="成本控制")
    customer_feedback = models.TextField(blank=True, verbose_name="客户反馈")
    team_collaboration = models.TextField(blank=True, verbose_name="团队协作")
    
    # 总结和改进
    successes = models.TextField(blank=True, verbose_name="成功经验")
    improvements = models.TextField(blank=True, verbose_name="待改进项")
    action_items = models.TextField(blank=True, verbose_name="行动项")
    
    # 关联问题
    related_issues = models.JSONField(default=list, verbose_name="相关问题")
    
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
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    
    class Meta:
        db_table = 'reviews'
        verbose_name = '复盘'
        verbose_name_plural = '复盘'
    
    def __str__(self):
        return f"{self.event.name} - {self.title}"