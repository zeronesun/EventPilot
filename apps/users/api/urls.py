from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from . import jwt_views

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT认证端点
    path('auth/login/', jwt_views.jwt_login, name='jwt-login'),
    path('auth/refresh/', jwt_views.jwt_refresh, name='jwt-refresh'),
    path('auth/verify/', jwt_views.jwt_verify, name='jwt-verify'),
    # 用户管理端点
    path('', include(router.urls)),
]