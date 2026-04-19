from django.urls import re_path

# 延迟导入以避免初始化问题
def get_websocket_urlpatterns():
    """获取WebSocket URL模式，延迟导入消费者"""
    from .consumer import EventPilotConsumer
    
    return [
        re_path(r'ws/events/$', EventPilotConsumer.as_asgi()),
        re_path(r'ws/tasks/$', EventPilotConsumer.as_asgi()),
        re_path(r'ws/notifications/$', EventPilotConsumer.as_asgi()),
        re_path(r'ws/status/$', EventPilotConsumer.as_asgi()),
    ]

# 提供兼容接口
websocket_urlpatterns = []

# 在需要时动态获取URL模式
def load_websocket_urlpatterns():
    """加载WebSocket URL模式"""
    global websocket_urlpatterns
    if not websocket_urlpatterns:
        websocket_urlpatterns = get_websocket_urlpatterns()
    return websocket_urlpatterns