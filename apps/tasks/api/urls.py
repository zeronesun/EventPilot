from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskDependencyViewSet, CommunicationTaskViewSet

app_name = 'tasks'
# 基础路由 - 注意：在 config/urls.py 中路径前缀是 `api/tasks/`，所以这里不需要重复前缀
router = DefaultRouter()
# 必须先注册具体路径，最后注册泛型路径，避免路由冲突
router.register(r'dependencies', TaskDependencyViewSet, basename='taskdependency')
router.register(r'communications', CommunicationTaskViewSet, basename='communicationtask')
router.register(r'', TaskViewSet, basename='task')  # 放在最后，作为默认/捕获所有

urlpatterns = [
    path('', include(router.urls)),
]