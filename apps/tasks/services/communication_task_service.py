from typing import Optional, List
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

from apps.tasks.models import Task, CommunicationTask

logger = logging.getLogger(__name__)


class CommunicationTaskService:
    """沟通任务服务层 - 处理沟通任务相关的所有业务逻辑"""
    
    @staticmethod
    @transaction.atomic
    def create_communication_task(task_id: str, data: dict, user) -> CommunicationTask:
        """
        创建沟通任务
        
        Args:
            task_id: 关联的任务ID
            data: 沟通任务数据
            user: 创建用户
            
        Returns:
            CommunicationTask: 创建的沟通任务对象
        """
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        # 检查是否已存在沟通任务
        if CommunicationTask.objects.filter(task=task).exists():
            raise ValidationError(f"任务 {task_id} 已存在沟通任务")
        
        # 验证联系人列表
        communicators = data.get('communicators', [])
        if not communicators:
            raise ValidationError("联系人为必填项")
        
        communication_data = {
            'task': task,
            'content': data.get('content'),
            'requirements': data.get('requirements', ''),
            'communicators': communicators,
            'conclusion_files': data.get('conclusion_files', []),
            'is_closed': False,
        }
        
        communication_task = CommunicationTask.objects.create(**communication_data)
        
        logger.info(
            f"沟通任务创建成功: task_id={task_id}, "
            f"user_id={user.id if user else None}"
        )
        
        return communication_task
    
    @staticmethod
    @transaction.atomic
    def update_communication_task(communication_task_id: str, data: dict, user) -> CommunicationTask:
        """
        更新沟通任务
        
        Args:
            communication_task_id: 沟通任务ID
            data: 更新数据
            user: 操作用户
            
        Returns:
            CommunicationTask: 更新后的沟通任务对象
        """
        try:
            communication_task = CommunicationTask.objects.select_related('task').get(
                id=communication_task_id
            )
        except CommunicationTask.DoesNotExist:
            raise ValidationError(f"沟通任务 {communication_task_id} 不存在")
        
        # 允许更新的字段
        if 'content' in data:
            communication_task.content = data['content']
        if 'requirements' in data:
            communication_task.requirements = data['requirements']
        if 'conclusion_files' in data:
            communication_task.conclusion_files = data['conclusion_files']
        if 'is_closed' in data:
            communication_task.is_closed = data['is_closed']
        
        # 特殊处理联系人 - 替换而非追加
        if 'communicators' in data:
            communicators = data['communicators']
            if not communicators:
                raise ValidationError("联系人不能为空")
            communication_task.communicators = communicators
        
        # 如果标记为已闭环，且关联任务未完成，自动完成任务
        if data.get('is_closed', False) and not communication_task.is_closed:
            task = communication_task.task
            if task.status != 'completed':
                task.status = 'completed'
                task.progress = 100
                task.completed_at = timezone.now()
                task.save()
        
        communication_task.save()
        
        logger.info(
            f"沟通任务更新成功: communication_task_id={communication_task_id}, "
            f"user_id={user.id if user else None}"
        )
        
        return communication_task
    
    @staticmethod
    @transaction.atomic
    def delete_communication_task(communication_task_id: str, user) -> dict:
        """
        删除沟通任务
        
        Args:
            communication_task_id: 沟通任务ID
            user: 操作用户
            
        Returns:
            dict: 操作结果
        """
        try:
            communication_task = CommunicationTask.objects.get(id=communication_task_id)
        except CommunicationTask.DoesNotExist:
            raise ValidationError(f"沟通任务 {communication_task_id} 不存在")
        
        communication_task_id_str = str(communication_task.id)
        
        # 删除
        communication_task.delete()
        
        logger.info(
            f"沟通任务删除成功: communication_task_id={communication_task_id_str}, "
            f"user_id={user.id if user else None}"
        )
        
        return {'message': '沟通任务删除成功', 'communication_task_id': communication_task_id_str}
    
    @staticmethod
    @transaction.atomic
    def close_communication_task(communication_task_id: str, user) -> CommunicationTask:
        """
        标记沟通任务为已闭环
        
        Args:
            communication_task_id: 沟通任务ID
            user: 操作用户
            
        Returns:
            CommunicationTask: 闭环的沟通任务对象
        """
        try:
            communication_task = CommunicationTask.objects.select_related('task').get(
                id=communication_task_id
            )
        except CommunicationTask.DoesNotExist:
            raise ValidationError(f"沟通任务 {communication_task_id} 不存在")
        
        if communication_task.is_closed:
            raise ValidationError(f"沟通任务 {communication_task_id} 已经是已闭环状态")
        
        communication_task.is_closed = True
        
        # 自动完成关联任务
        task = communication_task.task
        if task.status != 'completed':
            task.status = 'completed'
            task.progress = 100
            task.completed_at = timezone.now()
            task.save()
        
        communication_task.save()
        
        logger.info(
            f"沟通任务已闭环: communication_task_id={communication_task_id}, "
            f"user_id={user.id if user else None}"
        )
        
        return communication_task
    
    @staticmethod
    def get_communication_by_task_id(task_id: str) -> Optional[CommunicationTask]:
        """
        根据任务ID获取沟通任务
        
        Args:
            task_id: 关联的任务ID
            
        Returns:
            CommunicationTask: 沟通任务对象，如果不存在返回None
        """
        try:
            return CommunicationTask.objects.select_related('task').get(task__id=task_id)
        except CommunicationTask.DoesNotExist:
            return None