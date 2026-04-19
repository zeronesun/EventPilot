from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # 健康检查和系统信息
    path('health/', views.health_check, name='health'),
    path('', views.api_info, name='api-info'),
    
    # API文档（后续添加）
    # path('docs/', views.api_schema, name='api-docs'),
    
    # 应用API路由（后续添加）
]