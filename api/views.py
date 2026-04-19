from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from datetime import datetime, timedelta
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
        "environment": settings.DJANGO_SETTINGS_MODULE,
        "features": {
            "user_management": "complete",
            "event_management": "complete",
            "task_management": "complete",
            "checklist_management": "complete",
            "profile_management": "complete",
            "knowledge_base": "complete",
            "review_system": "complete"
        }
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