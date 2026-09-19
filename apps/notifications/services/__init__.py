"""通知服务层

统一导出通知相关服务：
- NotificationService  通知创建、查询、已读管理
"""

from .notification_service import NotificationService

__all__ = [
    'NotificationService',
]
