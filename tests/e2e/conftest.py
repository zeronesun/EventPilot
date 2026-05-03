"""
EventPilot E2E 测试配置
结合 Playwright (前端) + Django ORM (后端数据库断言)
"""
import os
import sys
import pytest
import django

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
os.environ.setdefault('DJANGO_DEBUG', 'True')

django.setup()

from django.contrib.auth import get_user_model
from apps.events.models import Event, EventParticipant
from apps.tasks.models import Task

User = get_user_model()


# ============================================================
# Django ORM Fixtures (数据库准备)
# ============================================================

@pytest.fixture(scope='session')
def django_db_setup():
    """确保测试数据库可用"""
    from django.conf import settings
    # 测试时使用 SQLite 内存数据库或独立测试库
    settings.DATABASES['default']['NAME'] = 'eventpilot_test'


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='user',
        is_active=True
    )
    return user


@pytest.fixture
def admin_user(db):
    """创建管理员用户"""
    user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin',
        is_active=True
    )
    return user


@pytest.fixture
def test_event(db, test_user):
    """创建测试活动"""
    from datetime import datetime, timedelta
    event = Event.objects.create(
        name='测试活动-产品发布会',
        type='conference',
        description='这是一个测试活动',
        start_date=datetime.now() + timedelta(days=7),
        end_date=datetime.now() + timedelta(days=8),
        client='测试客户',
        client_contact='张三',
        estimated_budget=50000.00,
        status=Event.Status.PLANNING,
        owner=test_user
    )
    return event


@pytest.fixture
def test_task(db, test_event, test_user):
    """创建测试任务"""
    task = Task.objects.create(
        title='测试任务-场地预订',
        description='预订活动场地',
        status='todo',
        priority='high',
        event=test_event,
        assignee=test_user,
        due_date=test_event.start_date
    )
    return task


# ============================================================
# Playwright Fixtures (浏览器)
# ============================================================

@pytest.fixture(scope='session')
def browser_context_args(browser_context_args):
    """浏览器上下文配置"""
    return {
        **browser_context_args,
        'viewport': {'width': 1920, 'height': 1080},
        'record_video_dir': 'tests/e2e/videos/',
    }


@pytest.fixture
async def authenticated_page(page, admin_user):
    """已登录的页面（通过 API 获取 JWT Token）"""
    import requests

    # 通过后端 API 登录获取 token
    response = requests.post(
        'http://localhost:8000/api/users/auth/login/',
        json={'username': 'admin', 'password': 'admin123'}
    )

    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access')

        # 在浏览器中设置 localStorage
        await page.goto('http://localhost:5173/login')
        await page.evaluate(f"""
            localStorage.setItem('eventpilot_token', '{access_token}');
        """)

    yield page


# ============================================================
# API 客户端 Fixtures
# ============================================================

@pytest.fixture
def api_client(admin_user):
    """DRF APIClient"""
    from rest_framework.test import APIClient
    from apps.users.api.jwt_views import generate_tokens

    client = APIClient()
    tokens = generate_tokens(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client
