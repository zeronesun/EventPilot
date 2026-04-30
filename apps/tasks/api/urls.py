from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskDependencyViewSet, CommunicationTaskViewSet

app_name = 'tasks'
# 基础路由
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-dependencies', TaskDependencyViewSet, basename='taskdependency')
router.register(r'communication-tasks', CommunicationTaskViewSet, basename='communicationtask')

urlpatterns = [
    path('', include(router.urls)),
]