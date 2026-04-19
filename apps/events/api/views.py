from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Count, Sum

from apps.events.models import Event, BudgetItem
from .serializers import EventSerializer, EventListSerializer, BudgetItemSerializer


class EventViewSet(viewsets.ModelViewSet):
    """活动视图集"""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['status', 'type', 'owner']
    search_fields = ['name', 'description', 'client']
    ordering_fields = ['created_at', 'start_date', 'name']
    
    def get_queryset(self):
        """获取活动查询集"""
        queryset = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items')
        return queryset
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def perform_create(self, serializer):
        """创建活动时的额外处理"""
        # 设置owner为当前用户
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取活动统计数据"""
        event = self.get_object()
        
        tasks_queryset = event.tasks
        budget_queryset = event.budget_items
        
        stats = {
            'tasks': {
                'total': tasks_queryset.count(),
                'by_status': dict(tasks_queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
                'by_type': dict(tasks_queryset.values('task_type').annotate(count=Count('id')).values_list('task_type', 'count')),
            },
            'budget': {
                'estimated_total': budget_queryset.aggregate(
                    total=Sum('estimated_amount')
                )['total'] or 0,
                'actual_total': budget_queryset.aggregate(
                    total=Sum('actual_amount')
                )['total'] or 0,
                'variance_total': budget_queryset.aggregate(
                    total=Sum('variance')
                )['total'] or 0,
                'items_count': budget_queryset.count(),
            }
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """标记活动为完成"""
        event = self.get_object()
        
        if event.status == 'completed':
            return Response(
                {'message': '活动已完成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        event.status = 'completed'
        event.completed_at = timezone.now()
        event.save()
        
        return Response({'message': '活动已标记为完成'})


class BudgetItemViewSet(viewsets.ModelViewSet):
    """预算明细视图集"""
    serializer_class = BudgetItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """获取预算明细查询集"""
        event_id = self.request.query_params.get('event')
        queryset = BudgetItem.objects.all()
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建预算明细时的额外处理"""
        serializer.save()
        # 触发预算重新计算（可以优化为异步）
        self._update_event_budget(serializer.instance.event)
    
    def perform_update(self, serializer):
        """更新预算明细时的额外处理"""
        serializer.save()
        self._update_event_budget(serializer.instance.event)
    
    def _update_event_budget(self, event):
        """更新活动的预算汇总"""
        budget_items = event.budget_items.all()
        
        event.estimated_budget = sum(
            item.estimated_amount for item in budget_items
        )
        event.actual_budget = sum(
            item.actual_amount for item in budget_items
        )
        event.budget_variance = event.estimated_budget - event.actual_budget
        event.save()