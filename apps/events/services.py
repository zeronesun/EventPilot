"""
Events Service Layer - 业务逻辑层
将复杂的业务逻辑从Views分离，提高代码可测试性和可维护性
"""
from typing import List, Optional, Tuple
from datetime import datetime
import logging
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.events.models import Event
from apps.core.event_bus import EventBus, event_bus

logger = logging.getLogger(__name__)
User = get_user_model()


class EventService:
    """事件服务类 - 封装事件相关的业务逻辑"""

    EVENT_CACHE_TIMEOUT = 300  # 5分钟缓存

    def __init__(self):
        self.bus: EventBus = event_bus

    def create_event(
        self,
        name: str,
        event_type: str,
        start_date: str,
        end_date: str,
        description: str = "",
        location: str = "",
        owner_id: int = None,
        owner: User = None
    ) -> Tuple[Optional[Event], List[str]]:
        """
        创建新事件
        
        Args:
            name: 事件名称
            event_type: 事件类型
            start_date: 开始日期(ISO格式)
            end_date: 结束日期(ISO格式)
            description: 事件描述
            location: 事件地点
            owner_id: 所有者ID（兼容旧接口）
            owner: 所有者User对象（优先使用）
            
        Returns:
            (Event对象, 错误消息列表)
        """
        errors = []
        
        # 参数验证
        if not name or not name.strip():
            errors.append("事件名称不能为空")
        
        if not start_date:
            errors.append("开始日期不能为空")
            
        if not end_date:
            errors.append("结束日期不能为空")
        
        if errors:
            return None, errors
        
        # 解析日期
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                errors.append("结束日期必须晚于开始日期")
                return None, errors
        except ValueError as e:
            errors.append(f"日期格式错误: {str(e)}")
            return None, errors
        
        # 确定所有者
        if owner is None and owner_id is not None:
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                errors.append("指定的用户不存在")
                return None, errors
        
        if owner is None:
            from django.conf import settings
            owner = User.objects.get(username='admin')  # 默认管理员
        
        # 创建事件
        try:
            with transaction.atomic():
                event = Event.objects.create(
                    name=name,
                    type=event_type,
                    description=description,
                    location=location,
                    start_date=start_dt,
                    end_date=end_dt,
                    owner=owner
                )
                
                # 发布事件创建消息到事件总线
                self.bus.publish('event.created', {
                    'event_id': event.id,
                    'event_name': event.name,
                    'owner_id': owner.id,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"事件创建成功: {event.name} (ID: {event.id})")
                
                # 清除相关缓存
                self._clear_events_cache(owner.id)
                
                return event, []
                
        except Exception as e:
            logger.error(f"创建事件失败: {str(e)}")
            errors.append(f"创建事件失败: {str(e)}")
            return None, errors

    def update_event(
        self,
        event_id: int,
        **kwargs
    ) -> Tuple[Optional[Event], List[str]]:
        """
        更新事件信息
        
        Args:
            event_id: 事件ID
            **kwargs: 要更新的字段
            
        Returns:
            (Event对象, 错误消息列表)
        """
        errors = []
        
        try:
            event = Event.objects.select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            errors.append("事件不存在")
            return None, errors
        
        # 如果更新了日期，验证日期有效性
        if 'start_date' in kwargs and 'end_date' in kwargs:
            try:
                start_dt = datetime.fromisoformat(kwargs['start_date'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(kwargs['end_date'].replace('Z', '+00:00'))
                
                if end_dt <= start_dt:
                    errors.append("结束日期必须晚于开始日期")
                    return None, errors
                    
                kwargs['start_date'] = start_dt
                kwargs['end_date'] = end_dt
            except ValueError as e:
                errors.append(f"日期格式错误: {str(e)}")
                return None, errors
        
        # 更新事件
        try:
            with transaction.atomic():
                for key, value in kwargs.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                
                event.save()
                
                # 发布事件更新消息
                self.bus.publish('event.updated', {
                    'event_id': event.id,
                    'event_name': event.name,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"事件更新成功: {event.name} (ID: {event.id})")
                
                # 清除缓存
                self._clear_events_cache(event.owner.id)
                
                return event, []
                
        except Exception as e:
            logger.error(f"更新事件失败: {str(e)}")
            errors.append(f"更新事件失败: {str(e)}")
            return None, errors

    def delete_event(self, event_id: int) -> Tuple[bool, List[str]]:
        """
        删除事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            (是否成功, 错误消息列表)
        """
        errors = []
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            errors.append("事件不存在")
            return False, errors
        
        try:
            with transaction.atomic():
                event_name = event.name
                owner_id = event.owner.id if event.owner else None
                event.delete()
                
                # 发布事件删除消息
                self.bus.publish('event.deleted', {
                    'event_id': event_id,
                    'event_name': event_name,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"事件删除成功: {event_name} (ID: {event_id})")
                
                # 清除缓存
                if owner_id:
                    self._clear_events_cache(owner_id)
                
                return True, []
                
        except Exception as e:
            logger.error(f"删除事件失败: {str(e)}")
            errors.append(f"删除事件失败: {str(e)}")
            return False, errors

    def get_user_events(self, user_id: int, use_cache: bool = True) -> List[Event]:
        """
        获取用户的所有事件
        
        Args:
            user_id: 用户ID
            use_cache: 是否使用缓存
            
        Returns:
            事件列表
        """
        cache_key = f'events:user:{user_id}'
        
        if use_cache:
            cached_events = cache.get(cache_key)
            if cached_events is not None:
                return list(cached_events)
        
        events = Event.objects.filter(owner_id=user_id).order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, list(events), self.EVENT_CACHE_TIMEOUT)
        
        return list(events)

    def get_event_stats(self, user_id: int) -> dict:
        """
        获取用户的事件统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        cache_key = f'events:stats:{user_id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats is not None:
            return cached_stats
        
        events = self.get_user_events(user_id, use_cache=False)
        
        stats = {
            'total': len(events),
            'by_type': {},
            'upcoming': 0,
            'past': 0
        }
        
        now = timezone.now()
        for event in events:
            # 按类型统计
            event_type = event.type or 'other'
            stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1
            
            # 按时间统计
            if event.end_date and event.end_date > now:
                stats['upcoming'] += 1
            else:
                stats['past'] += 1
        
        cache.set(cache_key, stats, self.EVENT_CACHE_TIMEOUT)
        
        return stats

    def _clear_events_cache(self, user_id: int):
        """
        清除事件相关的缓存
        
        Args:
            user_id: 用户ID
        """
        cache_keys_to_delete = [
            f'events:user:{user_id}',
            f'events:stats:{user_id}'
        ]
        
        for key in cache_keys_to_delete:
            cache.delete(key)


# 全局服务实例
event_service = EventService()
