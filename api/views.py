from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models import Count
from apps.events.models import Event
from apps.tasks.models import Task
# from drf_yasg import openapi, openapi_view
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg.inspectors import openapi


# @swagger_auto_schema(
#     operation_summary="API健康检查",
#     operation_description="检查API服务运行状态"
# )
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """健康检查端点"""
    return Response({
        "status": "healthy",
        "service": "EventPilot API",
        "version": "1.0.0-mvp",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "environment": "development",
        "features": {
            "user_management": "complete",
            "event_management": "complete",
            "task_management": "complete",
            "checklist_management": "complete",
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    })


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


# @swagger_auto_schema(
#     operation_summary="API信息",
#     operation_description="获取API系统信息和可用端点"
# )
@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API信息端点"""
    return Response({
        "data": {
            "name": "EventPilot API",
            "version": "1.0.0-mvp",
            "description": "活动领航系统 API 接口",
            "endpoints": {
                "health": "/api/health/",
                "docs": "/api/docs/",
                "users": "/api/users/",
                "events": "/api/events/",
                "tasks": "/api/tasks/",
                "checklists": "/api/checklists/",
                "profiles": "/api/profiles/",
                "knowledge": "/api/knowledge/",
                "reviews": "/api/reviews/"
            }
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    })