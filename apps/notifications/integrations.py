"""
通知集成模块

集成通知服务与WebSocket，实现实时通知推送
"""

import logging

logger = logging.getLogger(__name__)


def send_notification_via_websocket(channel_name, notification_data):
    """
    通过WebSocket发送通知

    参数:
        channel_name: WebSocket频道名称（如'user_{user_id}'）
        notification_data: 通知数据字典

    返回:
        bool: 是否发送成功
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()

        # 构建WebSocket消息
        message = {
            'type': 'notification.new',
            'data': notification_data
        }

        # 发送到指定频道
        async_to_sync(channel_layer.group_send)(
            channel_name,
            {
                'type': 'send_notification',
                'message': message
            }
        )

        logger.info(f"已通过WebSocket发送通知到频道: {channel_name}")
        return True

    except Exception as e:
        logger.error(f"通过WebSocket发送通知失败: {str(e)}")
        return False


def create_and_send_notification(
    user,
    type,
    title,
    message,
    source='system',
    related_object_type=None,
    related_object_id=None,
    data=None,
    send_ws=True
):
    """
    创建通知并通过WebSocket发送

    参数:
        send_ws: 是否通过WebSocket发送（默认True）

    返回:
        Notification对象
    """
    from .services import NotificationService
    from .models import Notification

    # 创建数据库中的通知
    notification = NotificationService.create_notification(
        user=user,
        type=type,
        title=title,
        message=message,
        source=source,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        data=data
    )

    # 通过WebSocket发送实时通知
    if send_ws and hasattr(user, 'id'):
        channel_name = f'user_{user.id}'

        notification_data = {
            'id': str(notification.id),
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'data': notification.data,
            'source': notification.source,
            'related_object_type': notification.related_object_type,
            'related_object_id': notification.related_object_id,
            'read': notification.read,
            'created_at': notification.created_at.isoformat()
        }

        send_notification_via_websocket(channel_name, notification_data)

    return notification


def notify_event_status_change(event, old_status, new_status):
    """
    通知活动状态变更
    """
    from apps.events.models import Event

    watchers = []  # 可以根据业务逻辑定义应该接收通知的用户列表

    if event.created_by:
        watchers.append(event.created_by)

    for user in set(watchers):  # 去重
        create_and_send_notification(
            user=user,
            type='info',
            title='活动状态已更新',
            message=f'活动"{event.name}"的状态已从 {old_status} 更新为 {new_status}',
            source='events',
            related_object_type='Event',
            related_object_id=str(event.id),
            data={
                'event_id': str(event.id),
                'event_name': event.name,
                'old_status': old_status,
                'new_status': new_status
            }
        )


def notify_task_assigned(task):
    """
    通知任务分配
    """
    if not task.assigned_to:
        return

    create_and_send_notification(
        user=task.assigned_to,
        type='info',
        title='新任务已分配',
        message=f'您被分配了新任务: {task.title}',
        source='tasks',
        related_object_type='Task',
        related_object_id=str(task.id),
        data={
            'task_id': str(task.id),
            'task_title': task.title,
            'due_date': task.due_date.isoformat() if task.due_date else None
        }
    )


def notify_task_completed(task):
    """
    通知任务完成
    """
    if task.created_by and task.created_by != task.assigned_to:
        create_and_send_notification(
            user=task.created_by,
            type='success',
            title='任务已完成',
            message=f'任务"{task.title}"已完成',
            source='tasks',
            related_object_type='Task',
            related_object_id=str(task.id),
            data={
                'task_id': str(task.id),
                'task_title': task.title,
                'completed_by': task.assigned_to.username if task.assigned_to else None
            }
        )
