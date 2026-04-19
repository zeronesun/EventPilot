from typing import Optional, List
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

from apps.tasks.models import Task, TaskDependency, CommunicationTask
from apps.tasks.models.task import Task as TaskModel
from apps.events.models import Event

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务层 - 处理任务相关的所有业务逻辑"""
    
    @staticmethod
    @transaction.atomic
    def create_task(user, event_id: str, data: dict) -> Task:
        """
        创建任务
        
        Args:
            user: 创建用户
            event_id: 活动ID
            data: 任务数据字典
            
        Returns:
            Task: 创建的任务对象
        """
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ValidationError(f"活动 {event_id} 不存在")
        
        task_data = {
            'event': event,
            'title': data.get('title'),
            'description': data.get('description', ''),
            'task_type': data.get('task_type', 'planning'),
            'assignee': data.get('assignee'),
            'status': 'pending',
            'start_date': data.get('start_date'),
            'due_date': data.get('due_date'),
            'created_by': user,
        }
        
        task = Task.objects.create(**task_data)
        
        # 处理任务依赖关系
        depends_on_ids = data.get('depends_on', [])
        if depends_on_ids:
            TaskService._create_dependencies(task, depends_on_ids, event)
        
        # 如果有依赖，检查是否阻塞
        if depends_on_ids:
            TaskService._check_blocked_status(task)
        
        logger.info(
            f"任务创建成功: task_id={task.id}, title={task.title}, "
            f"event_id={event_id}, user_id={user.id}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def update_task(task_id: str, user, data: dict) -> Task:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            user: 更新用户
            data: 更新数据字典
            
        Returns:
            Task: 更新后的任务对象
        """
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        # 允许更新的字段
        allowed_fields = ['title', 'description', 'task_type', 'assignee', 
                        'start_date', 'due_date', 'status', 'progress']
        
        for field in allowed_fields:
            if field in data:
                setattr(task, field, data[field])
        
        # 验证截止日期
        if task.start_date and task.due_date:
            if task.due_date < task.start_date:
                raise ValidationError("截止日期不能早于开始日期")
        
        # 验证进度
        if task.progress is not None and (task.progress < 0 or task.progress > 100):
            raise ValidationError("进度必须在0-100之间")
        
        # 处理任务依赖关系更新
        if 'depends_on' in data:
            TaskDependency.objects.filter(task=task).delete()
            if data['depends_on']:
                TaskService._create_dependencies(task, data['depends_on'], task.event)
        
        # 检查是否阻塞
        TaskService._check_blocked_status(task)
        
        # 检查是否完成
        if task.status == 'completed' and task.progress != 100:
            task.progress = 100
            task.completed_at = timezone.now()
            TaskService._update_dependent_tasks(task)
        
        task.save()
        
        logger.info(
            f"任务更新成功: task_id={task.id}, "
            f"user_id={user.id if user else None}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def delete_task(task_id: str, user) -> dict:
        """
        删除任务（软删除）
        
        Args:
            task_id: 任务ID
            user: 删除用户
            
        Returns:
            dict: 操作结果
        """
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        # 检查是否有其他任务依赖于此任务
        dependents = TaskDependency.objects.filter(depends_on=task).count()
        if dependents > 0:
            raise ValidationError(f"无法删除: 有 {dependents} 个任务依赖于此任务")
        
        task_title = task.title
        task_id_str = str(task.id)
        
        # 删除依赖关系
        TaskDependency.objects.filter(task=task).delete()
        
        # 删除沟通任务（如果存在）
        CommunicationTask.objects.filter(task=task).delete()
        
        # 删除任务
        task.delete()
        
        logger.info(
            f"任务删除成功: task_id={task_id_str}, title={task_title}, "
            f"user_id={user.id if user else None}"
        )
        
        return {'message': '任务删除成功', 'task_id': task_id_str}
    
    @staticmethod
    @transaction.atomic
    def complete_task(task_id: str, user) -> Task:
        """
        标记任务为完成
        
        Args:
            task_id: 任务ID
            user: 操作用户
            
        Returns:
            Task: 完成的任务对象
        """
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        if task.status == 'completed':
            raise ValidationError(f"任务 {task_id} 已经是已完成状态")
        
        # 检查依赖是否都完成
        dependencies = TaskDependency.objects.filter(task=task)
        for dep in dependencies:
            if dep.depends_on.status != 'completed':
                raise ValidationError(
                    f"依赖任务 '{dep.depends_on.title}' 尚未完成，无法完成此任务"
                )
        
        # 标记为完成
        task.status = 'completed'
        task.progress = 100
        task.completed_at = timezone.now()
        task.save()
        
        # 触发依赖任务状态更新
        TaskService._update_dependent_tasks(task)
        
        logger.info(
            f"任务完成: task_id={task_id}, title={task.title}, "
            f"user_id={user.id if user else None}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def update_task_status(task_id: str, new_status: str, user) -> Task:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            new_status: 新状态
            user: 操作用户
            
        Returns:
            Task: 更新后的任务对象
        """
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if new_status not in valid_statuses:
            raise ValidationError(f"无效的状态: {new_status}")
        
        # 状态转换验证
        TaskService._validate_status_transition(task.status, new_status)
        
        old_status = task.status
        task.status = new_status
        
        # 如果标记为完成，设置完成时间和进度
        if new_status == 'completed':
            task.progress = 100
            task.completed_at = timezone.now()
            TaskService._update_dependent_tasks(task)
        elif new_status == 'in_progress':
            task.completed_at = None
        
        # 检查阻塞状态
        TaskService._check_blocked_status(task)
        
        task.save()
        
        logger.info(
            f"任务状态更新: task_id={task_id}, title={task.title}, "
            f"old_status={old_status}, new_status={new_status}, "
            f"user_id={user.id if user else None}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def update_task_progress(task_id: str, progress: int, user) -> Task:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            user: 操作用户
            
        Returns:
            Task: 更新后的任务对象
        """
        if progress < 0 or progress > 100:
            raise ValidationError("进度必须在0-100之间")
        
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        old_progress = task.progress
        task.progress = progress
        
        # 如果进度100%，自动标记为完成
        if progress == 100 and task.status != 'completed':
            task.status = 'completed'
            task.completed_at = timezone.now()
            TaskService._update_dependent_tasks(task)
        elif progress < 100 and task.status == 'completed':
            task.status = 'in_progress'
            task.completed_at = None
        
        task.save()
        
        logger.info(
            f"任务进度更新: task_id={task_id}, title={task.title}, "
            f"progress={old_progress}->{progress}, "
            f"user_id={user.id if user else None}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def assign_task(task_id: str, assignee, user) -> Task:
        """
        分配任务给用户
        
        Args:
            task_id: 任务ID
            assignee: 被分配的用户
            user: 操作用户
            
        Returns:
            Task: 更新后的任务对象
        """
        try:
            task = Task.objects.select_for_update().get(id=task_id)
        except Task.DoesNotExist:
            raise ValidationError(f"任务 {task_id} 不存在")
        
        task.assignee = assignee
        
        # 如果分配了负责人，且任务状态为pending，改为ready
        if assignee and task.status == 'pending':
            task.status = 'ready'
        
        task.save()
        
        logger.info(
            f"任务分配: task_id={task_id}, title={task.title}, "
            f"assignee_id={assignee.id if assignee else None}, "
            f"user_id={user.id if user else None}"
        )
        
        return task
    
    @staticmethod
    @transaction.atomic
    def bulk_update_status(task_ids: List[str], new_status: str, user) -> dict:
        """
        批量更新任务状态
        
        Args:
            task_ids: 任务ID列表
            new_status: 新状态
            user: 操作用户
            
        Returns:
            dict: 操作结果统计
        """
        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if new_status not in valid_statuses:
            raise ValidationError(f"无效的状态: {new_status}")
        
        updated_count = Task.objects.filter(id__in=task_ids).update(status=new_status)
        
        if new_status == 'completed':
            updated_count = Task.objects.filter(id__in=task_ids).update(
                progress=100,
                completed_at=timezone.now()
            )
        
        logger.info(
            f"批量更新任务状态: count={updated_count}, status={new_status}, "
            f"user_id={user.id if user else None}"
        )
        
        return {
            'message': f'成功更新 {updated_count} 个任务',
            'updated_count': updated_count
        }
    
    @staticmethod
    @transaction.atomic
    def bulk_delete_tasks(task_ids: List[str], user) -> dict:
        """
        批量删除任务
        
        Args:
            task_ids: 任务ID列表
            user: 操作用户
            
        Returns:
            dict: 操作结果统计
        """
        # 检查依赖关系
        dependents_count = TaskDependency.objects.filter(
            depends_on__id__in=task_ids
        ).count()
        
        if dependents_count > 0:
            raise ValidationError(
                f"无法删除: 有 {dependents_count} 个任务依赖于此任务列表"
            )
        
        deleted_count, _ = Task.objects.filter(id__in=task_ids).delete()
        
        logger.info(
            f"批量删除任务: count={deleted_count}, "
            f"user_id={user.id if user else None}"
        )
        
        return {
            'message': f'成功删除 {deleted_count} 个任务',
            'deleted_count': deleted_count
        }
    
    @staticmethod
    def _create_dependencies(task: Task, depends_on_ids: List[str], event: Event):
        """创建任务依赖关系"""
        for dep_id in depends_on_ids:
            try:
                dep_task = Task.objects.get(id=dep_id, event=event)
                
                # 防止循环依赖
                if TaskService._has_circular_dependency(task, dep_task):
                    raise ValidationError(f"检测到循环依赖: {task.title} -> {dep_task.title}")
                
                TaskDependency.objects.create(task=task, depends_on=dep_task)
            except Task.DoesNotExist:
                raise ValidationError(f"依赖任务 {dep_id} 不存在")
    
    @staticmethod
    def _has_circular_dependency(task: Task, potential_dep: Task) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        
        def dfs(current_task):
            if current_task.id in visited:
                return True
            visited.add(current_task.id)
            
            deps = TaskDependency.objects.filter(task=current_task)
            for dep in deps:
                if dep.depends_on.id == task.id:
                    return True
                if dfs(dep.depends_on):
                    return True
            return False
        
        return dfs(potential_dep)
    
    @staticmethod
    def _check_blocked_status(task: Task):
        """检查并更新任务阻塞状态"""
        dependencies = TaskDependency.objects.filter(task=task)
        
        all_completed = all(
            dep.depends_on.status == 'completed' 
            for dep in dependencies
        )
        
        if task.status == 'blocked' and all_completed and dependencies.exists():
            task.status = 'ready'
        elif task.status in ['pending', 'ready'] and not all_completed and dependencies.exists():
            task.status = 'blocked'
    
    @staticmethod
    def _update_dependent_tasks(task: Task):
        """更新依赖此任务的其他任务状态"""
        dependents = TaskDependency.objects.filter(depends_on=task)
        
        for dep in dependents:
            dependent_task = dep.task
            
            # 检查所有依赖是否都完成
            dependencies = dependent_task.dependencies.all()
            all_completed = all(
                d.depends_on.status == 'completed' 
                for d in dependencies
            )
            
            if all_completed and dependent_task.status in ['pending', 'blocked']:
                dependent_task.status = 'ready'
                dependent_task.save()
    
    @staticmethod
    def _validate_status_transition(current_status: str, new_status: str):
        """验证状态转换是否合法"""
        valid_transitions = {
            'pending': ['ready', 'in_progress', 'cancelled', 'blocked'],
            'ready': ['pending', 'in_progress', 'cancelled', 'blocked'],
            'in_progress': ['pending', 'ready', 'completed', 'cancelled', 'blocked'],
            'completed': ['in_progress', 'cancelled'],
            'cancelled': ['pending', 'ready', 'in_progress'],
            'blocked': ['pending', 'ready'],
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"无效的状态转换: {current_status} -> {new_status}"
            )