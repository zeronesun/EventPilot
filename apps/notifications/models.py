from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Notification(models.Model):
    """
    通知模型
    用于系统向用户发送各类通知
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 用户关联
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )

    # 通知类型
    TYPE_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('success', '成功'),
    ]
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        db_index=True
    )

    # 通知内容
    title = models.CharField(max_length=200)
    message = models.TextField()

    # 附加数据（JSON格式）
    data = models.JSONField(default=dict, blank=True)

    # 系统模块来源
    source = models.CharField(
        max_length=50,
        help_text='通知来源系统模块',
        db_index=True
    )

    # 关联对象
    related_object_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='关联对象类型（Event, Task等）'
    )
    related_object_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='关联对象ID',
        db_index=True
    )

    # 阅读状态
    read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['read', 'created_at']),
            models.Index(fields=['source', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def mark_as_read(self):
        from django.utils import timezone
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])

    @classmethod
    def create_notification(cls, user, type, title, message, **kwargs):
        """
        创建通知的便捷方法
        """
        notification = cls.objects.create(
            user=user,
            type=type,
            title=title,
            message=message,
            **kwargs
        )
        return notification

    @classmethod
    def get_unread_count(cls, user):
        """获取用户未读通知数"""
        return cls.objects.filter(user=user, read=False).count()

    @classmethod
    def bulk_mark_as_read(cls, user, notification_ids=None):
        """
        批量标记已读
        如果 notification_ids 为 None，标记所有未读
        """
        queryset = cls.objects.filter(user=user, read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        from django.utils import timezone
        count = queryset.update(read=True, read_at=timezone.now())
        return count
