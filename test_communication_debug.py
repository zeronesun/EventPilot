"""
调试 CommunicationTask 测试
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.events.models import Event
from apps.tasks.models import Task, CommunicationTask
import logging

User = get_user_model()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_db():
    """临时数据库"""
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.core.management import call_command

    setup_test_environment()
    # 使用内存数据库
    from django.conf import settings
    test_db = settings.DATABASES['default']
    test_db['NAME'] = ':memory:'

    # 运行迁移
    call_command('migrate', '--run-syncdb', verbosity=0)

    yield

    teardown_test_environment()


def test_debug_communication_task(temp_db):
    """调试沟通任务创建"""

    # 禁用所有信号
    from django.db.models.signals import post_save, post_delete
    from apps.websocket import signals
    signals.event_updated.disconnect(sender=None)

    # 创建测试数据
    user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
    event = Event.objects.create(
        name='测试活动',
        type='conference',
        description='这是一个测试活动',
        start_date='2026-04-20T10:00:00Z',
        end_date='2026-04-20T18:00:00Z',
        owner=user,
    )
    task = Task.objects.create(
        event=event,
        title='测试任务',
        description='这是一个测试任务',
        task_type='planning',
        created_by=user
    )

    client = APIClient()
    client.force_authenticate(user=user)

    # 测试创建沟通任务
    data = {
        'task_id': str(task.id),
        'content': '这是沟通内容',
        'requirements': '沟通要求',
        'communicators': [
            {'name': '张三', 'phone': '1234567890'},
            {'name': '李四', 'phone': '0987654321'}
        ]
    }

    print(f"Task ID: {task.id}")
    print(f"Request data: {data}")

    response = client.post('/api/tasks/communications/', data, format='json')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.data if hasattr(response, \"data\") else response.content.decode()}')

    if response.status_code != 201:
        print("\n=== 错误详情 ===")
        if hasattr(response, 'data'):
            print(f"Response data: {response.data}")

    assert response.status_code == 201, f"Expected 201, got {response.status_code}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
