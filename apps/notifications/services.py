"""
通知服务模块

提供通知的创建、发送、查询等功能
"""

from .models import Notification
from .serializers import NotificationSerializer
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知服务
    """

    @staticmethod
    def create_notification(
        user,
        type,
        title,
        message,
        source='system',
        related_object_type=None,
        related_object_id=None,
        data=None,
        broadcast=False
    ):
        """
        创建通知

        参数:
            user: 接收通知的用户
            type: 通知类型 (info/warning/error/success)
            title: 通知标题
            message: 通知内容
            source: 通知来源模块
            related_object_type: 关联对象类型
            related_object_id: 关联对象ID
            data: 附加数据（字典）
            broadcast: 是否广播（当前版本保留）
        """
        try:
            if data is None:
                data = {}

            notification = Notification.objects.create(
                user=user,
                type=type,
                title=title,
                message=message,
                source=source,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                data=data
            )

            logger.info(f"通知已创建: {notification.id} for user {user.username}")

            # 触发WebSocket推送（需要集成到WebSocket模块）
            # 这部分在WebSocket集成时实现

            return notification

        except Exception as e:
            logger.error(f"创建通知失败: {str(e)}")
            raise

    @staticmethod
    def get_user_notifications(user, read=None, type=None, page=1, page_size=20):
        """
        获取用户通知列表

        参数:
            user: 用户
            read: 阅读状态筛选 (None=全部, True=已读, False=未读)
            type: 通知类型筛选
            page: 页码
            page_size: 每页大小

        返回:
            {
                'notifications': [...],
                'total': 总数,
                'page': 页码,
                'page_size': 每页大小
            }
        """
        try:
            queryset = Notification.objects.filter(user=user)

            if read is not None:
                queryset = queryset.filter(read=read)

            if type:
                queryset = queryset.filter(type=type)

            total = queryset.count()
            start = (page - 1) * page_size
            notifications = queryset[start:start + page_size]

            serializer = NotificationSerializer(notifications, many=True)

            return {
                'notifications': serializer.data,
                'total': total,
                'page': page,
                'page_size': page_size
            }

        except Exception as e:
            logger.error(f"获取通知列表失败: {str(e)}")
            raise

    @staticmethod
    def get_unread_count(user):
        """
        获取用户未读通知数
        """
        return Notification.get_unread_count(user)

    @staticmethod
    def mark_as_read(notification_id):
        """
        标记单个通知为已读
        """
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"通知不存在: {notification_id}")
            return False
        except Exception as e:
            logger.error(f"标记已读失败: {str(e)}")
            return False

    @staticmethod
    def bulk_mark_as_read(user, notification_ids=None):
        """
        批量标记已读

        参数:
            user: 用户
            notification_ids: 通知ID列表，如果为None则标记所有未读
        """
        try:
            count = Notification.bulk_mark_as_read(user, notification_ids)
            logger.info(f"批量标记已读: {count}条")
            return count
        except Exception as e:
            logger.error(f"批量标记已读失败: {str(e)}")
            raise

    @staticmethod
    def delete_notification(notification_id):
        """
        删除通知
        """
        try:
            count, _ = Notification.objects.filter(id=notification_id).delete()
            return count > 0
        except Exception as e:
            logger.error(f"删除通知失败: {str(e)}")
            return False

    @staticmethod
    def cleanup_old_notifications(days=90):
        """
        清理旧通知

        参数:
            days: 保留天数，超过此天数的通知将被删除
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)
        count, _ = Notification.objects.filter(created_at__lt=cutoff_date).delete()

        logger.info(f"清理旧通知: 删除了 {count} 条")
        return count
