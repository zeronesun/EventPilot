"""
Repository Layer - 数据访问层抽象
将数据访问逻辑从Service层分离，支持未来切换ORM或数据库
"""
from typing import List, Optional, TypeVar, Generic
from django.db import models
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=models.Model)


class BaseRepository(Generic[T]):
    """
    基础仓储实现
    提供通用的CRUD操作和缓存支持
    """
    
    model_class: type[T]
    cache_timeout: int = 300
    
    def __init__(self, model_class: type[T], cache_timeout: int = 300):
        self.model_class = model_class
        self.cache_timeout = cache_timeout
    
    def get_by_id(self, id: int, use_cache: bool = True) -> Optional[T]:
        """
        根据ID获取对象
        
        Args:
            id: 对象ID
            use_cache: 是否使用缓存
            
        Returns:
            模型实例或None
        """
        cache_key = f'{self.model_class.__name__.lower()}:id:{id}'
        
        if use_cache:
            cached_obj = cache.get(cache_key)
            if cached_obj is not None:
                return cached_obj
        
        try:
            obj = self.model_class.objects.get(id=id)
            if use_cache:
                cache.set(cache_key, obj, self.cache_timeout)
            return obj
        except self.model_class.DoesNotExist:
            return None
    
    def get_all(self, use_cache: bool = True) -> List[T]:
        """
        获取所有对象
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            模型实例列表
        """
        cache_key = f'{self.model_class.__name__.lower()}:all'
        
        if use_cache:
            cached_objs = cache.get(cache_key)
            if cached_objs is not None:
                return list(cached_objs)
        
        objs = self.model_class.objects.all().order_by('-id')
        
        if use_cache:
            cache.set(cache_key, list(objs), self.cache_timeout)
        
        return list(objs)
    
    def filter(self, **kwargs) -> models.QuerySet:
        """
        过滤对象
        
        Args:
            **kwargs: 过滤条件
            
        Returns:
            QuerySet
        """
        return self.model_class.objects.filter(**kwargs)
    
    def create(self, **kwargs) -> T:
        """
        创建对象
        
        Args:
            **kwargs: 对象字段
            
        Returns:
            创建的模型实例
        """
        obj = self.model_class.objects.create(**kwargs)
        logger.info(f"创建 {obj.__class__.__name__}: id={obj.id}")
        
        # 清除相关缓存
        self._clear_cache()
        
        return obj
    
    def update(self, obj: T, **kwargs) -> T:
        """
        更新对象
        
        Args:
            obj: 模型实例
            **kwargs: 更新的字段
            
        Returns:
            更新后的模型实例
        """
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        obj.save()
        logger.info(f"更新 {obj.__class__.__name__}: id={obj.id}")
        
        # 清除缓存
        cache_key = f'{self.model_class.__name__.lower()}:id:{obj.id}'
        cache.delete(cache_key)
        self._clear_cache()
        
        return obj
    
    def delete(self, obj: T) -> bool:
        """
        删除对象
        
        Args:
            obj: 模型实例
            
        Returns:
            是否成功
        """
        obj_id = obj.id
        obj.delete()
        logger.info(f"删除 {obj.__class__.__name__}: id={obj_id}")
        
        # 清除缓存
        cache_key = f'{self.model_class.__name__.lower()}:id:{obj_id}'
        cache.delete(cache_key)
        self._clear_cache()
        
        return True
    
    def delete_by_id(self, id: int) -> bool:
        """
        根据ID删除对象
        
        Args:
            id: 对象ID
            
        Returns:
            是否成功
        """
        obj = self.get_by_id(id, use_cache=False)
        if obj:
            return self.delete(obj)
        return False
    
    def exists(self, **kwargs) -> bool:
        """
        检查对象是否存在
        
        Args:
            **kwargs: 过滤条件
            
        Returns:
            是否存在
        """
        return self.model_class.objects.filter(**kwargs).exists()
    
    def count(self, **kwargs) -> int:
        """
        统计对象数量
        
        Args:
            **kwargs: 过滤条件
            
        Returns:
            数量
        """
        return self.model_class.objects.filter(**kwargs).count()
    
    def _clear_cache(self):
        """清除所有相关缓存"""
        cache_key = f'{self.model_class.__name__.lower()}:all'
        cache.delete(cache_key)


class EventRepository(BaseRepository):
    """事件仓储"""
    
    def __init__(self):
        from apps.events.models import Event
        super().__init__(Event, cache_timeout=300)
    
    def get_by_owner(self, owner_id: int) -> List:
        """获取所有者的事件"""
        return self.filter(owner_id=owner_id).order_by('-created_at')
    
    def get_upcoming(self, owner_id: int, limit: int = 10) -> List:
        """获取即将到来的事件"""
        from django.utils import timezone
        now = timezone.now()
        return self.filter(
            owner_id=owner_id,
            end_date__gt=now
        ).order_by('start_date')[:limit]


class TaskRepository(BaseRepository):
    """任务仓储"""
    
    def __init__(self):
        from apps.tasks.models import Task
        super().__init__(Task, cache_timeout=180)
    
    def get_by_owner(self, owner_id: int, status: Optional[str] = None) -> List:
        """获取所有者的任务"""
        queryset = self.filter(owner_id=owner_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    def get_by_checklist(self, checklist_id: int) -> List:
        """获取检查清单的任务"""
        return self.filter(checklist_id=checklist_id).order_by('-created_at')
    
    def get_overdue(self, owner_id: int) -> List:
        """获取过期任务"""
        from django.utils import timezone
        now = timezone.now()
        return self.filter(
            owner_id=owner_id,
            due_date__lt=now
        ).exclude(status='done').order_by('due_date')


class ChecklistRepository(BaseRepository):
    """检查清单仓储"""
    
    def __init__(self):
        from apps.checklists.models import Checklist
        super().__init__(Checklist, cache_timeout=300)
    
    def get_by_owner(self, owner_id: int) -> List:
        """获取所有者的检查清单"""
        return self.filter(owner_id=owner_id).order_by('-created_at')


class UserRepository(BaseRepository):
    """用户仓储"""
    
    def __init__(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        super().__init__(User, cache_timeout=600)
    
    def get_by_username(self, username: str) -> Optional:
        """根据用户名获取用户"""
        return self.filter(username=username).first()
    
    def get_by_email(self, email: str) -> Optional:
        """根据邮箱获取用户"""
        return self.filter(email=email).first()
