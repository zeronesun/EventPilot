"""
首页统计数据视图
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.events.models import Event
from apps.tasks.models import Task


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    获取首页统计数据
    
    统计项:
    - 活动总数
    - 进行中活动
    - 待处理任务
    - 已完成任务
    """
    # 活动统计
    total_events = Event.objects.count()
    executing_events = Event.objects.filter(status='executing').count()
    
    # 任务统计
    pending_tasks = Task.objects.filter(status='pending').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    return Response({
        'total_events': total_events,
        'executing_events': executing_events,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
    })
