"""
关联方档案管理API路由
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.profiles.api.views import (
    ContactProfileViewSet,
    RecommendationsViewSet,
    SearchViewSet,
    AnalyticsViewSet
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'profiles', ContactProfileViewSet, basename='profile')

# 注册功能视图
router.register(r'recommendations', RecommendationsViewSet, basename='recommendation')
router.register(r'search', SearchViewSet, basename='search')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

# URL模式
urlpatterns = [
    path('', include(router.urls)),
]