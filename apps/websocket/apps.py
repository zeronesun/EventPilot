# -*- coding: utf-8 -*-
"""
WebSocket应用配置
"""

from django.apps import AppConfig


class WebsocketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.websocket'
    verbose_name = 'WebSocket实时通讯'
    
    def ready(self):
        """应用启动时执行"""
        import apps.websocket.signals