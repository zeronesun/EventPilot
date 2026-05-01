"""
Tasks Service Layer - 业务逻辑层
处理任务相关的复杂业务逻辑，实现权限检查、数据验证等
"""
from typing import List, Optional, Tuple, Any
from datetime import datetime
import logging
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from apps.tasks.models import Task, TaskDragEvent
from apps.core.event_bus import EventBus, event_bus

logger = logging.getLogger(__name__)
User = get_user_model()


class TaskService:
    """任务服务类 - 封装任务相关的业务逻辑"""

    TASK_CACHE_TIMEOUT = 180  # 3分钟缓存

    def __init__(self):
        self.bus: EventBus = event_bus

    def create_task(
        self,
        title: str,
        description: str = "",
        status: str = "todo",
        priority: str = "medium",
        due_date: Optional[str] = None,
        checklist_id: Optional[int] = None,
        owner_id: Optional[int] = None,
        owner: Optional[User] = None
    ) -> Tuple[Optional[Task], List[str]]:
        """
        创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            status: 任务状态
            priority: 任务优先级
            due_date: 截止日期
            checklist_id: 关联的检查清单ID
            owner_id: 所有者ID
            owner: 所有者User对象
            
        Returns:
            (Task对象, 错误消息列表)
        """
        errors = []
        
        # 参数验证
        if not title or not title.strip():
            errors.append("任务标题不能为空")
            return None, errors
        
        # 验证status
        valid_statuses = ['todo', 'in_progress', 'review', 'done']
        if status not in valid_statuses:
            errors.append(f"无效的任务状态，必须是以下之一: {', '.join(valid_statuses)}")
            return None, errors
        
        # 验证priority
        valid_priorities = ['low', 'medium', 'high']
        if priority not in valid_priorities:
            errors.append(f"无效的优先级，必须是以下之一: {', '.join(valid_priorities)}")
            return None, errors
        
        # 解析截止日期
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError as e:
                errors.append(f"截止日期格式错误: {str(e)}")
                return None, errors
        
        # 确定所有者
        if owner is None:
            if owner_id:
                try:
                    owner = User.objects.get(id=owner_id)
                except User.DoesNotExist:
                    errors.append("指定的用户不存在")
                    return None, errors
            else:
                # 默认使用管理员用户
                try:
                    owner = User.objects.get(username='admin')
                except User.DoesNotExist:
                    owner = User.objects.first()
        
        if owner is None:
            errors.append("无法确定任务所有者")
            return None, errors
        
        # 创建任务
        try:
            with transaction.atomic():
                task = Task.objects.create(
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    due_date=due_date_obj,
                    checklist_id=checklist_id,
                    owner=owner
                )
                
                # 发布任务创建消息
                self.bus.publish('task.created', {
                    'task_id': task.id,
                    'task_title': task.title,
                    'owner_id': owner.id,
                    'checklist_id': checklist_id,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"任务创建成功: {task.title} (ID: {task.id})")
                
                # 清除缓存
                self._clear_tasks_cache(owner.id, checklist_id)
                
                return task, []
                
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            errors.append(f"创建任务失败: {str(e)}")
            return None, errors

    def update_task(
        self,
        task_id: int,
        **kwargs
    ) -> Tuple[Optional[Task], List[str]]:
        """
        更新任务信息
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
            
        Returns:
            (Task对象, 错误消息列表)
        """
        errors = []
        
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            errors.append("任务不存在")
            return None, errors
        
        # 验证字段
        if 'status' in kwargs:
            valid_statuses = ['todo', 'in_progress', 'review', 'done']
            if kwargs['status'] not in valid_statuses:
                errors.append(f"无效的任务状态")
                return None, errors
        
        if 'priority' in kwargs:
            valid_priorities = ['low', 'medium', 'high']
            if kwargs['priority'] not in valid_priorities:
                errors.append(f"无效的优先级")
                return None, errors
        
        # 更新任务
        try:
            with transaction.atomic():
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                task.save()
                
                # 发布任务更新消息
                self.bus.publish('task.updated', {
                    'task_id': task.id,
                    'task_title': task.title,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"任务更新成功: {task.title} (ID: {task.id})")
                
                # 清除缓存
                self._clear_tasks_cache(task.owner.id, task.checklist_id)
                
                return task, []
                
        except Exception as e:
            logger.error(f"更新任务失败: {str(e)}")
            errors.append(f"更新任务失败: {str(e)}")
            return None, errors

    def delete_task(self, task_id: int) -> Tuple[bool, List[str]]:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            (是否成功, 错误消息列表)
        """
        errors = []
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            errors.append("任务不存在")
            return False, errors
        
        try:
            with transaction.atomic():
                task_title = task.title
                owner_id = task.owner.id if task.owner else None
                checklist_id = task.checklist_id
                task.delete()
                
                # 发布任务删除消息
                self.bus.publish('task.deleted', {
                    'task_id': task_id,
                    'task_title': task_title,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"任务删除成功: {task_title} (ID: {task_id})")
                
                # 清除缓存
                if owner_id:
                    self._clear_tasks_cache(owner_id, checklist_id)
                
                return True, []
                
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            errors.append(f"删除任务失败: {str(e)}")
            return False, errors

    def batch_update_tasks(
        self,
        task_updates: List[Tuple[int, dict]]
    ) -> Tuple[int, List[str]]:
        """
        批量更新任务
        
        Args:
            task_updates: [(task_id, update_dict), ...]
            
        Returns:
            (成功数量, 错误消息列表)
        """
        success_count = 0
        errors = []
        
        with transaction.atomic():
            for task_id, update_data in task_updates:
                task, task_errors = self.update_task(task_id, **update_data)
                if task:
                    success_count += 1
                else:
                    errors.extend([f"Task {task_id}: " + err for err in task_errors])
        
        return success_count, errors

    def record_drag_event(
        self,
        task_id: int,
        old_status: str,
        new_status: str,
        user: User
    ) -> Tuple[bool, List[str]]:
        """
        记录任务拖拽事件用于协作冲突检测
        
        Args:
            task_id: 任务ID
            old_status: 旧状态
            new_status: 新状态
            user: 操作用户
            
        Returns:
            (是否成功, 错误消息列表)
        """
        errors = []
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            errors.append("任务不存在")
            return False, errors
        
        if task.status != old_status:
            errors.append(f"任务状态已变更，当前状态为 {task.status}")
            return False, errors
        
        try:
            with transaction.atomic():
                drag_event = TaskDragEvent.objects.create(
                    task=task,
                    old_status=old_status,
                    new_status=new_status,
                    user=user
                )
                
                # 发布任务拖拽消息
                self.bus.publish('task.dragged', {
                    'task_id': task_id,
                    'task_title': task.title,
                    'old_status': old_status,
                    'new_status': new_status,
                    'user_id': user.id,
                    'drag_event_id': drag_event.id,
                    'timestamp': timezone.now().isoformat()
                })
                
                logger.info(f"任务拖拽事件记录: {task.title} {old_status} -> {new_status}")
                
                return True, []
                
        except Exception as e:
            logger.error(f"记录拖拽事件失败: {str(e)}")
            errors.append(f"记录拖拽事件失败: {str(e)}")
            return False, errors

    def get_user_tasks(
        self,
        user_id: int,
        status: Optional[str] = None,
        checklist_id: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Task]:
        """
        获取用户的任务列表
        
        Args:
            user_id: 用户ID
            status: 筛选状态
            checklist_id: 筛选检查清单
            use_cache: 是否使用缓存
            
        Returns:
            任务列表
        """
        cache_key_parts = ['tasks:user', user_id]
        if status:
            cache_key_parts.append(f'status:{status}')
        if checklist_id:
            cache_key_parts.append(f'checklist:{checklist_id}')
        
        cache_key = ':'.join(map(str, cache_key_parts))
        
        if use_cache:
            cached_tasks = cache.get(cache_key)
            if cached_tasks is not None:
                return list(cached_tasks)
        
        queryset = Task.objects.filter(owner_id=user_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if checklist_id:
            queryset = queryset.filter(checklist_id=checklist_id)
        
        tasks = queryset.order_by('-created_at')
        
        if use_cache:
            cache.set(cache_key, list(tasks), self.TASK_CACHE_TIMEOUT)
        
        return list(tasks)

    def get_task_stats(self, user_id: int) -> dict:
        """
        获取用户的任务统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        cache_key = f'tasks:stats:{user_id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats is not None:
            return cached_stats
        
        tasks = self.get_user_tasks(user_id, use_cache=False)
        
        stats = {
            'total': len(tasks),
            'by_status': {},
            'by_priority': {},
            'overdue': 0
        }
        
        now = timezone.now()
        for task in tasks:
            # 按状态统计
            stats['by_status'][task.status] = stats['by_status'].get(task.status, 0) + 1
            
            # 按优先级统计
            stats['by_priority'][task.priority] = stats['by_priority'].get(task.priority, 0) + 1
            
            # 统计过期任务
            if task.due_date and task.due_date < now and task.status != 'done':
                stats['overdue'] += 1
        
        cache.set(cache_key, stats, self.TASK_CACHE_TIMEOUT)
        
        return stats

    def _clear_tasks_cache(self, user_id: int, checklist_id: Optional[int] = None):
        """
        清除任务相关的缓存
        
        Args:
            user_id: 用户ID
            checklist_id: 检查清单ID
        """
        # 清除该用户的任务缓存
        cache_keys_pattern = f'tasks:user:{user_id}:*'
        # 这里简单处理，清除所有相关缓存
        # 实际应用中可能需要使用django.core.cache.utils.make_template_fragment_key
        
        cache.delete(f'tasks:user:{user_id}')
        cache.delete(f'tasks:stats:{user_id}')
        
        if checklist_id:
            cache.delete(f'tasks:user:{user_id}:checklist:{checklist_id}')


# 全局服务实例
task_service = TaskService()
