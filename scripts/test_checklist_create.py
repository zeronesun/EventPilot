import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

# 创建测试用户
user = User.objects.create_user(
    username='testuser',
    password='testpass123'
)

print(f"Created user: {user.id}")

# 使用 APIClient
client = APIClient()
client.force_authenticate(user=user)

# 测试创建清单模板
data = {
    'name': '活动前检查清单',
    'description': '活动开始前的检查项',
    'checklist_type': 'pre_event',
    'event_types': ['conference', 'exhibition'],
    'version': '1.0.0',
    'status': 'draft',
    'tags': ['活动', '检查'],
    'items': [
        {
            'title': '场地检查',
            'description': '检查场地是否满足要求',
            'required': True,
            'order': 1,
            'weight': 1
        },
        {
            'title': '设备检查',
            'description': '检查设备是否正常工作',
            'required': True,
            'order': 2,
            'weight': 1
        }
    ]
}

print(f"\nSending request to /api/checklists/templates/")
print(f"Data: {data}")

response = client.post('/api/checklists/templates/', data, format='json')

print(f"\nResponse status: {response.status_code}")
print(f"Response headers: {response.headers}")
print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
