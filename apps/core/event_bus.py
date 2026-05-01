"""
Event Bus - 事件总线系统
实现发布-订阅模式，用于模块间解耦通信
"""
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import logging
import threading
import json

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线实现
    支持同步和异步事件发布，支持日志记录和错误处理
    """
    
    def __init__(self):
        # 订阅者字典: {事件名称: [处理函数列表]}
        self._subscribers: Dict[str, List[Callable]] = {}
        # 锁用于线程安全
        self._lock = threading.Lock()
        # 事件历史记录（用于调试）
        self._event_history: List[Dict] = []
        self._max_history = 100
    
    def subscribe(
        self,
        event_name: str,
        handler: Callable
    )-> Callable:
        """
        订阅事件
        
        Args:
            event_name: 事件名称
            handler: 处理函数
            
        Returns:
            取消订阅的函数
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            
            # 避免重复订阅
            if handler not in self._subscribers[event_name]:
                self._subscribers[event_name].append(handler)
                logger.debug(f"订阅事件: {event_name}, 处理函数: {handler.__name__}")
        
        def unsubscribe():
            self.unsubscribe(event_name, handler)
        
        return unsubscribe
    
    def unsubscribe(
        self,
        event_name: str,
        handler: Callable
    ):
        """
        取消订阅
        
        Args:
            event_name: 事件名称
            handler: 处理函数
        """
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(handler)
                    logger.debug(f"取消订阅: {event_name}, 处理函数: {handler.__name__}")
                except ValueError:
                    pass
    
    def publish(
        self,
        event_name: str,
        data: Optional[dict] = None
    ):
        """
        发布事件（同步）
        
        Args:
            event_name: 事件名称
            data: 事件数据
        """
        if data is None:
            data = {}
        
        # 记录事件历史
        self._record_event(event_name, data)
        
        # 获取订阅者
        with self._lock:
            handlers = self._subscribers.get(event_name, []).copy()
        
        if not handlers:
            logger.debug(f"事件 {event_name} 没有订阅者")
            return
        
        logger.info(f"发布事件: {event_name}, 触发 {len(handlers)} 个处理函数")
        
        # 调用所有处理函数
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(
                    f"事件处理失败 - 事件: {event_name}, "
                    f"处理函数: {handler.__name__}, 错误: {str(e)}",
                    exc_info=True
                )
    
    def publish_async(
        self,
        event_name: str,
        data: Optional[dict] = None
    ):
        """
        发布事件（异步）
        
        Args:
            event_name: 事件名称
            data: 事件数据
        """
        def async_publish():
            self.publish(event_name, data)
        
        # 在新线程中发布
        thread = threading.Thread(target=async_publish, daemon=True)
        thread.start()
    
    def emit(
        self,
        event_name: str,
        data: Optional[dict] = None
    ):
        """
        发布事件的别名方法
        """
        self.publish(event_name, data)
    
    def on(self, event_name: str):
        """
        装饰器方式订阅事件
        
        Example:
            @bus.on('task.created')
            def handle_task_created(data):
                print(f"任务创建: {data}")
        """
        def decorator(handler: Callable):
            self.subscribe(event_name, handler)
            return handler
        return decorator
    
    def _record_event(self, event_name: str, data: dict):
        """记录事件历史"""
        event_record = {
            'event': event_name,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'data_size': len(json.dumps(data))
        }
        
        self._event_history.append(event_record)
        
        # 保持历史记录数量限制
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def get_event_history(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的事件历史
        
        Args:
            limit: 返回的最大数量
            
        Returns:
            事件历史列表
        """
        return self._event_history[-limit:]
    
    def get_subscribers_count(self, event_name: str) -> int:
        """
        获取事件的订阅者数量
        
        Args:
            event_name: 事件名称
            
        Returns:
            订阅者数量
        """
        with self._lock:
            return len(self._subscribers.get(event_name, []))
    
    def clear_subscribers(self, event_name: Optional[str] = None):
        """
        清除订阅者
        
        Args:
            event_name: 事件名称，为None时清除所有订阅
        """
        with self._lock:
            if event_name:
                self._subscribers[event_name] = []
                logger.info(f"清除事件订阅者: {event_name}")
            else:
                self._subscribers.clear()
                logger.info("清除所有事件订阅者")


# 全局事件总线实例
event_bus = EventBus()


# 预定义的事件名称常量
class Events:
    """事件名称常量"""
    
    # 任务事件
    TASK_CREATED = 'task.created'
    TASK_UPDATED = 'task.updated'
    TASK_DELETED = 'task.deleted'
    TASK_DRAGGED = 'task.dragged'
    TASK_STATUS_CHANGED = 'task.status_changed'
    
    # 事件事件
    EVENT_CREATED = 'event.created'
    EVENT_UPDATED = 'event.updated'
    EVENT_DELETED = 'event.deleted'
    
    # 用户事件
    USER_LOGIN = 'user.login'
    USER_LOGOUT = 'user.logout'
    USER_REGISTERED = 'user.registered'
    
    # 检查清单事件
    CHECKLIST_CREATED = 'checklist.created'
    CHECKLIST_UPDATED = 'checklist.updated'
    CHECKLIST_DELETED = 'checklist.deleted'
    CHECKLIST_INSTANCE_CREATED = 'checklist.instance.created'
    
    # WebSocket事件
    WEBSOCKET_CONNECTED = 'websocket.connected'
    WEBSOCKET_DISCONNECTED = 'websocket.disconnected'
    WEBSOCKET_MESSAGE_SENT = 'websocket.message.sent'
    WEBSOCKET_MESSAGE_RECEIVED = 'websocket.message.received'
    
    # WebSocket协作事件
    TASK_DRAG_CONFLICT = 'task.drag.conflict'
    TASK_REALTIME_UPDATE = 'task.realtime.update'


# 事件总线使用示例
if __name__ == '__main__':
    # 创建事件处理器
    def on_task_created(data):
        print(f"任务创建: {data.get('task_title', 'Unknown')}")
    
    def on_task_updated(data):
        print(f"任务更新: ID={data.get('task_id', 'Unknown')}")
    
    # 订阅事件
    event_bus.subscribe(Events.TASK_CREATED, on_task_created)
    event_bus.subscribe(Events.TASK_UPDATED, on_task_updated)
    
    # 发布事件
    event_bus.publish(Events.TASK_CREATED, {
        'task_id': 1,
        'task_title': '新建任务',
        'owner_id': 1
    })
    
    event_bus.publish(Events.TASK_UPDATED, {
        'task_id': 1,
        'task_title': '更新后的任务'
    })
    
    # 查看历史
    print("\n事件历史:")
    for event in event_bus.get_event_history():
        print(f"  {event['event']} at {event['timestamp']}")
