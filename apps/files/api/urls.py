from rest_framework.routers import DefaultRouter
from .views import FileViewSet, FileShareViewSet, FileHealthViewSet

# 创建路由
router = DefaultRouter()

# 注册文件管理视图
router.register(r'', FileViewSet, basename='file')

# 文件分享和健康检查使用自定义URL
from django.urls import path, include

urlpatterns = [
    path('files/share/<str:share_id>/', FileShareViewSet.as_view({'get': 'retrieve'}), name='file-share'),
    path('files/health/', FileHealthViewSet.as_view({'get': 'health'}), name='file-health'),
    path('', include(router.urls)),
]