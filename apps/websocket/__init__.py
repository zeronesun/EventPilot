# -*- coding: utf-8 -*-
"""
EventPilot WebSocket实时通讯基础设施
Phase 2 - WebSocket基础设施实现
"""

# 延迟导入以避免循环导入问题
__all__ = [
    'websocket_urlpatterns',
    'WebSocketAuthMiddleware', 
    'EventPilotConsumer',
    'ConnectionManager',
    'NotificationService',
    'StatusManager',
]

def get_websocket_components():
    """延迟导入WebSocket组件"""
    from .routing import websocket_urlpatterns
    from .middleware import WebSocketAuthMiddleware
    from .consumer import EventPilotConsumer
    from .connection_manager import ConnectionManager
    from .notification_service import NotificationService
    from .status_manager import StatusManager
    
    return {
        'websocket_urlpatterns': websocket_urlpatterns,
        'WebSocketAuthMiddleware': WebSocketAuthMiddleware,
        'EventPilotConsumer': EventPilotConsumer,
        'ConnectionManager': ConnectionManager,
        'NotificationService': NotificationService,
        'StatusManager': StatusManager,
    }