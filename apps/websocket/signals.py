import json
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Model
from typing import Callable, Optional
from functools import wraps

from apps.websocket.notification_service import NotificationService
from apps.websocket.status_manager import StatusManager

logger = logging.getLogger(__name__)


# 延迟初始化以避免启动时的Redis配置问题
notification_service = None
status_manager = None

def get_notification_service():
    """延迟获取NotificationService实例"""
    global notification_service
    if notification_service is None:
        try:
            from apps.websocket.notification_service import NotificationService
            notification_service = NotificationService()
        except Exception as e:
            logger.error(f"Failed to create NotificationService: {str(e)}")
    return notification_service

def get_status_manager():
    """延迟获取StatusManager实例"""
    global status_manager
    if status_manager is None:
        try:
            from apps.websocket.status_manager import StatusManager
            status_manager = StatusManager()
        except Exception as e:
            logger.error(f"Failed to create StatusManager: {str(e)}")
    return status_manager


def websocket_notification(model_name: str, action: str = 'updated'):
    """
    WebSocket通知装饰器
    
    Args:
        model_name: 模型名称
        action: 动作类型
    """
    def decorator(signal_handler: Callable):
        @wraps(signal_handler)
        def wrapper(sender: Model, instance: Model, **kwargs):
            # 先执行原始信号处理器
            result = signal_handler(sender, instance, **kwargs)
            
            # 发送WebSocket通知（仅在 service 可用时）
            service = get_notification_service()
            if service:
                try:
                    _send_model_notification(instance, model_name, action)
                except Exception as e:
                    logger.error(f"Failed to send WebSocket notification: {str(e)}")
            
            return result
        
        return wrapper
    
    return decorator


def _send_model_notification(instance: Model, model_name: str, action: str):
    """
    发送模型变更的WebSocket通知
    
    Args:
        instance: 模型实例
        model_name: 模型名称
        action: 动作类型
    """
    service = get_notification_service()
    if service is None:
        logger.debug(f"Notification Service not available, skipping {model_name} notification")
        return
    
    try:
        if model_name == 'event':
            service.send_event_notification(
                event_id=instance.id,
                action=action,
                data=_serialize_model(instance, model_name)
            )
        elif model_name == 'task':
            if hasattr(instance, 'assignee_id') and instance.assignee_id:
                service.send_task_notification(
                    task_id=instance.id,
                    action=action,
                    user_id=instance.assignee_id,
                    data=_serialize_model(instance, model_name)
                )
    
    except Exception as e:
        logger.error(f"Error sending WebSocket notification: {str(e)}")


def _serialize_model(instance: Model, model_name: str) -> dict:
    """
    序列化模型实例
    
    Args:
        instance: 模型实例
        model_name: 模型名称
        
    Returns:
        序列化后的数据
    """
    if model_name == 'event':
        return {
            'id': instance.id,
            'title': instance.title,
            'status': instance.status,
            'start_date': instance.start_date.isoformat() if instance.start_date else None,
            'end_date': instance.end_date.isoformat() if instance.end_date else None,
            'organizer_id': instance.organizer_id
        }
    elif model_name == 'task':
        return {
            'id': instance.id,
            'title': instance.title,
            'status': instance.status,
            'event_id': instance.event_id,
            'assignee_id': instance.assignee_id,
            'due_date': instance.due_date.isoformat() if instance.due_date else None
        }
    
    return {}


# 活动模型信号
try:
    from apps.events.models import Event
    
    @receiver(post_save, sender=Event)
    @websocket_notification('event', 'updated')
    def event_updated(sender: Model, instance: Event, created: bool, **kwargs):
        """活动更新信号"""
        pass
    
    @receiver(post_delete, sender=Event)
    def event_deleted(sender: Model, instance: Event, **kwargs):
        """活动删除信号"""
        pass

# 任务模型信号
    from apps.tasks.models import Task
    
    @receiver(post_save, sender=Task)
    @websocket_notification('task', 'updated')
    def task_updated(sender: Model, instance: Task, created: bool, **kwargs):
        """任务更新信号"""
        if created:
            pass  # creation is handled by decorator
        # task status change notification is handled by decorator
        
        # Additional status change notification if needed
        if hasattr(instance, 'status') and instance.assignee_id:
            service = get_notification_service()
            if service:
                try:
                    service.send_task_notification(
                        task_id=instance.id,
                        action='status_changed',
                        user_id=instance.assignee_id,
                        data=_serialize_model(instance, 'task')
                    )
                except Exception as e:
                    logger.error(f"Failed to send task status notification: {str(e)}")
    
    @receiver(post_delete, sender=Task)
    def task_deleted(sender: Model, instance: Task, **kwargs):
        """任务删除信号"""
        service = get_notification_service()
        if service and instance.assignee_id:
            try:
                service.send_task_notification(
                    task_id=instance.id,
                    action='deleted',
                    user_id=instance.assignee_id,
                    data={'id': instance.id, 'title': instance.title}
                )
            except Exception as e:
                logger.error(f"Failed to send task deletion notification: {str(e)}")

except ImportError as e:
    logger.warning(f"Could not import models for WebSocket signals: {str(e)}")


# 定期清理任务
def start_cleanup_task():
    """启动定期清理任务"""
    from django.conf import settings
    import asyncio
    
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                await status_manager.cleanup_old_states()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
    
    # 在后台启动清理任务
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(cleanup_loop())
    except RuntimeError:
        logger.warning("Could not start cleanup task: no event loop")


# 心跳检测任务
def start_heartbeat_check():
    """启动心跳检测任务"""
    from apps.websocket.consumer import EventPilotConsumer
    import asyncio
    
    async def heartbeat_loop():
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                connection_manager = EventPilotConsumer.get_connection_manager()
                await connection_manager.check_timeouts()
            except Exception as e:
                logger.error(f"Error in heartbeat check loop: {str(e)}")
    
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(heartbeat_loop())
    except RuntimeError:
        logger.warning("Could not start heartbeat check task: no event loop")