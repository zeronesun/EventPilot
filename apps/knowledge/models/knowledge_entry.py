from django.db import models
from django.conf import settings
import uuid


class KnowledgeEntry(models.Model):
    """知识条目"""
    class EntryType(models.TextChoices):
        ISSUE = 'issue', '问题'
        EXPERIENCE = 'experience', '经验'
        BEST_PRACTICE = 'best_practice', '最佳实践'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        verbose_name="条目类型"
    )
    
    # 内容
    title = models.CharField(max_length=255, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    
    # 标签和分类
    tags = models.JSONField(default=list, verbose_name="标签")
    category = models.CharField(max_length=100, blank=True, verbose_name="分类")
    
    # 关联
    related_events = models.JSONField(default=list, verbose_name="关联活动")
    related_tasks = models.JSONField(default=list, verbose_name="关联任务")
    
    # 状态和属性
    is_public = models.BooleanField(default=False, verbose_name="是否公开")
    is_verified = models.BooleanField(default=False, verbose_name="是否验证")
    popularity = models.PositiveIntegerField(default=0, verbose_name="流行度")
    
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
        db_table = 'knowledge_entries'
        indexes = [
            models.Index(fields=['entry_type']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['-popularity']),
        ]
        verbose_name = '知识条目'
        verbose_name_plural = '知识条目'
    
    def __str__(self):
        return self.title