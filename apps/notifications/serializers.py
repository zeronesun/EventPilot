from rest_framework import serializers, fields
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    通知序列化器
    """
    relative_time = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'type',
            'title',
            'message',
            'data',
            'source',
            'related_object_type',
            'related_object_id',
            'read',
            'read_at',
            'created_at',
            'relative_time',
        ]
        read_only_fields = ['created_at', 'read_at', 'relative_time']

    def get_relative_time(self, obj):
        """获取相对时间（如"5分钟前"）"""
        from django.utils import timezone
        from datetime import timedelta

        if not obj.created_at:
            return ''

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return '刚刚'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() // 60)
            return f'{minutes}分钟前'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() // 3600)
            return f'{hours}小时前'
        elif diff < timedelta(days=7):
            days = diff.days
            return f'{days}天前'
        else:
            return obj.created_at.strftime('%Y-%m-%d')


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    创建通知的序列化器
    用于内部调用
    """
    class Meta:
        model = Notification
        fields = [
            'user',
            'type',
            'title',
            'message',
            'data',
            'source',
            'related_object_type',
            'related_object_id',
        ]


class NotificationListSerializer(serializers.Serializer):
    """
    通知列表查询参数序列化器
    """
    type = serializers.CharField(required=False, allow_blank=True)
    read = serializers.BooleanField(required=False, allow_null=True)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class NotificationUpdateSerializer(serializers.Serializer):
    """
    通知更新序列化器（标记已读等）
    """
    read = serializers.BooleanField(required=False)


class BulkMarkReadSerializer(serializers.Serializer):
    """
    批量标记已读序列化器
    """
    notification_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True
    )
