"""
通知WebSocket Consumer

处理通知相关的WebSocket连接和消息推送

注意：当前项目使用统一的 EventPilotConsumer 处理所有WebSocket连接
此类保留用于多环境兼容和未来扩展
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    通知WebSocket消费者

    每个用户会连接到'user_{user_id}'频道
    """

    async def connect(self):
        """
        WebSocket连接
        """
        # 获取用户ID（从认证信息中）
        from channels.db import database_sync_to_async
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # 这里需要根据实际的认证方式获取用户
        # 简化版本：从query params或headers获取
        user_id = self.scope.get('user_id')

        if not user_id:
            # 如果没有用户ID，拒绝连接
            await self.close()
            return

        # 用户频道名称
        self.user_channel_name = f'user_{user_id}'

        # 添加到用户频道组
        await self.channel_layer.group_add(
            self.user_channel_name,
            self.channel_name
        )

        # 接受连接
        await self.accept()

        logger.info(f"用户 {user_id} 连接到通知WebSocket")

    async def disconnect(self, close_code):
        """
        WebSocket断开
        """
        if hasattr(self, 'user_channel_name'):
            await self.channel_layer.group_discard(
                self.user_channel_name,
                self.channel_name
            )

        logger.info(f"WebSocket断开连接: close_code={close_code}")

    async def send_notification(self, event):
        """
        发送通知消息

        此方法由channel_layer.group_send触发
        """
        message = event['message']

        # 发送JSON消息到客户端
        await self.send(text_data=json.dumps(message))

    async def receive(self, text_data):
        """
        接收客户端消息（如标记已读等操作）
        """
        try:
            data = json.loads(text_data)

            action = data.get('action')

            if action == 'mark_read':
                await self.handle_mark_read(data)
            elif action == 'bulk_mark_read':
                await self.handle_bulk_mark_read(data)
            elif action == 'delete':
                await self.handle_delete(data)
            else:
                logger.warning(f"未知的WebSocket操作: {action}")

        except json.JSONDecodeError:
            logger.error("无效的JSON消息")
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {str(e)}")

    async def handle_mark_read(self, data):
        """
        处理标记已读
        """
        notification_id = data.get('notification_id')
        user_id = self.scope.get('user_id')

        if not notification_id:
            return

        from apps.notifications.services import NotificationService
        from channels.db import database_sync_to_async

        # 需要包装同步代码
        success = await database_sync_to_async(NotificationService.mark_as_read)(notification_id)

        if success:
            # 发送确认
            await self.send(text_data=json.dumps({
                'type': 'notification.marked_read',
                'notification_id': notification_id,
                'success': True
            }))

    async def handle_bulk_mark_read(self, data):
        """
        处理批量标记已读
        """
        notification_ids = data.get('notification_ids')
        user_id = self.scope.get('user_id')

        from apps.notifications.services import NotificationService
        from channels.db import database_sync_to_async
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # 获取用户对象
        try:
            user = await database_sync_to_async(User.objects.get)(id=user_id)

            # 批量标记已读
            count = await database_sync_to_async(NotificationService.bulk_mark_as_read)(
                user, notification_ids
            )

            # 发送确认
            await self.send(text_data=json.dumps({
                'type': 'notification.bulk_marked_read',
                'count': count,
                'success': True
            }))

        except User.DoesNotExist:
            logger.error(f"用户不存在: {user_id}")

    async def handle_delete(self, data):
        """
        处理删除通知
        """
        notification_id = data.get('notification_id')

        from apps.notifications.services import NotificationService
        from channels.db import database_sync_to_async

        success = await database_sync_to_async(NotificationService.delete_notification)(notification_id)

        if success:
            # 发送确认
            await self.send(text_data=json.dumps({
                'type': 'notification.deleted',
                'notification_id': notification_id,
                "success": True
            }))
