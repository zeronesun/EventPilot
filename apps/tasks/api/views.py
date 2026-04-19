from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Count
from django.utils import timezone

from apps.tasks.models import Task, TaskDependency, CommunicationTask
from .serializers import (
    TaskSerializer, TaskDependencySerializer, CommunicationTaskSerializer, TaskSimpleSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['status', 'task_type', 'assignee', 'event']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', '-due_date']
    
    def get_queryset(self):
        """获取任务查询集"""
        return Task.objects.select_related('assignee', 'event', 'created_by').prefetch_related('dependencies')
    
    def perform_create(self, serializer):
        """创建任务时的额外处理"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """标记任务为完成"""
        task = self.get_object()
        
        if task.status == 'completed':
            return Response(
                {'message': '任务已完成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'completed'
        task.progress = 100
        task.completed_at = timezone.now()
        task.save()
        
        # 触发依赖任务状态更新
        self._update_dependent_tasks(task)
        
        return Response({'message': '任务已标记为完成'})
    
    @action(detail=True, methods=['post'])
    def dependencies(self, request, pk=None):
        """管理任务依赖关系"""
        task = self.get_object()
        depends_on_ids = request.data.get('depends_on', [])
        
        # 删除现有依赖
        task.dependencies.all().delete()
        
        # 创建新依赖
        for dep_id in depends_on_ids:
            try:
                dep_task = Task.objects.get(id=dep_id, event=task.event)
                TaskDependency.objects.create(task=task, depends_on=dep_task)
            except Task.DoesNotExist:
                return Response(
                    {'message': f'依赖任务 {dep_id} 不存在'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({'message': '依赖关系已更新'})
    
    @action(detail=False, methods=['get'])
    def kanban_data(self, request):
        """获取看板数据"""
        event_id = request.query_params.get('event')
        if not event_id:
            return Response(
                {'message': '需要指定event参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取活动的所有任务
        from apps.events.models import Event
        event = Event.objects.get(id=event_id)
        tasks = event.prefetch_related('dependencies')
        
        # 按状态分组任务
        columns = {
            'pending': {'id': 'pending', 'name': '待办', 'tasks': []},
            'ready': {'id': 'ready', 'name': '就绪', 'tasks': []},
            'in_progress': {'id': 'in_progress', 'name': '进行中', 'tasks': []},
            'completed': {'id': 'completed', 'name': '已完成', 'tasks': []},
        }
        
        # 简化任务数据
        for task in tasks:
            task_data = TaskSimpleSerializer(task).data
            columns[task.status]['tasks'].append(task_data)
        
        # 统计信息
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        
        return Response({
            'data': {
                'columns': list(columns.values()),
                'statistics': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': tasks.filter(status='in_progress').count(),
                    'pending_tasks': tasks.filter(status='pending').count(),
                    'completion_rate': round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
                }
            }
        })
    
    def _update_dependent_tasks(self, task):
        """更新依赖的后续任务状态"""
        dependents = TaskDependency.objects.filter(depends_on=task)
        for dep in dependents:
            dependent_task = dep.task
            
            # 检查所有依赖是否都完成
            dependencies = dependent_task.dependencies.all()
            all_completed = all(d.depends_on.status == 'completed' for d in dependencies)
            
            if all_completed and dependent_task.status == 'pending':
                dependent_task.status = 'ready'
                dependent_task.save()