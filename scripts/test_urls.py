import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# 创建测试用户
try:
    user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='test123'
    )
    print(f"Created user: {user.id}")
except Exception as e:
    print(f"User creation error: {e}")
    user = User.objects.filter(username='test_user').first()
    print(f"Found user: {user.id}")

# 创建客户端并登录
client = Client()
client.login(username='test_user', password='test123')

# 测试 URL 查找
try:
    url = reverse('checklist-template-list')
    print(f"✓ Found URL: {url}")
except Exception as e:
    print(f"✗ URL not found: {e}")

# 测试访问
response = client.get('/api/checklists/templates/')
print(f"Response status: {response.status_code}")
if hasattr(response, 'data'):
    print(f"Response data: {response.data}")
