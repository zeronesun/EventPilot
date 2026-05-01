#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

# 创建测试用户
user, _ = User.objects.get_or_create(
    username='testuser',
    defaults={'password': 'testpass123'}
)
client = APIClient()
client.force_authenticate(user=user)

# 创建必要的数据
from apps.events.models import Event
from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate
from apps.checklists.services.checklist_service import ChecklistService

event = Event.objects.create(
    name='测试活动',
    type='conference',
    start_date=timezone.now(),
    end_date=timezone.now() + timezone.timedelta(days=1),
    owner=user
)

template = ChecklistTemplate.objects.create(
    name='测试模板',
    description='测试描述',
    checklist_type='custom',
    event_types=['conference'],
    version='1.0.0',
    created_by=user
)

# 添加模板项
ChecklistItemTemplate.objects.create(
    template=template,
    title='测试项',
    required=True,
    order=1,
    weight=1
)

# 创建实例
data = {
    'event_id': str(event.id),
    'template_id': str(template.id),
    'name': '测试实例'
}

instance, errors = ChecklistService.create_instance(data, user)
print(f"实例创建成功: {instance.id}")
print(f"实例项数量: {instance.items.count()}")

# 完成所有项
for item in instance.items.all():
    url = f'/api/checklists/items/{item.id}/check/'
    item_data = {
        'status': 'passed',
        'notes': f'完成项 {item.title}'
    }
    response = client.post(url, item_data, format='json')
    print(f"完成项 {item.id}: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"  响应数据: {response.data}")

# 再次检查实例
instance.refresh_from_db()
print(f"实例状态: {instance.status}")
print(f"实例完成度: {instance.completion_rate}")

required_items = instance.items.filter(required=True)
completed_required = required_items.filter(status__in=['passed', 'failed']).count()
print(f"必选项: {required_items.count()}, 已完成: {completed_required}")

# 尝试完成实例
url = f'/api/checklists/instances/{instance.id}/complete/'
print(f"\n调用完成API: {url}")
response = client.post(url)
print(f"响应状态码: {response.status_code}")
if hasattr(response, 'data'):
    print(f"响应数据: {response.data}")
else:
    print(f"响应内容: {response.content}")

instance.refresh_from_db()
print(f"\n最终实例状态: {instance.status}")
