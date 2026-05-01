"""测试dependency API的调试脚本"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.events.models import Event
from apps.tasks.models import Task
from apps.tasks.services import TaskService

User = get_user_model()

# 创建数据
user = User.objects.get_or_create(username='testuser', defaults={'email': 'test@test.com'})[0]
event = Event.objects.get_or_create(
    name='测试活动',
    type='conference',
    description='测试',
    start_date='2026-04-20T10:00:00Z',
    end_date='2026-04-20T18:00:00Z',
    owner=user
)[0]

task = Task.objects.create(
    event=event,
    title='主任务',
    task_type='planning',
    created_by=user
)

dependency_task = Task.objects.create(
    event=event,
    title='依赖任务',
    task_type='planning',
    created_by=user
)

print(f"Task ID: {task.id}")
print(f"Dependency Task ID: {dependency_task.id}")

client = APIClient()
client.force_authenticate(user=user)

# 测试直接创建依赖关系
from apps.tasks.models import TaskDependency
try:
    td = TaskDependency.objects.create(task=task, depends_on=dependency_task)
    print(f"直接创建成功: {td}")
except Exception as e:
    print(f"直接创建失败: {e}")

# 测试 API
dependency_data = {'depends_on': [str(dependency_task.id)]}
print(f"发送的数据: {dependency_data}")

response = client.post(f'/api/tasks/{task.id}/dependencies/', dependency_data, format='json')
print(f"响应状态: {response.status_code}")
print(f"响应数据: {response.data if hasattr(response, 'data') else response.content}")
