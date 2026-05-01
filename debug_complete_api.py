#!/usr/bin/env python
import os
import sys
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.events.models import Event
from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate, ChecklistItem
from apps.checklists.services.checklist_service import ChecklistService
from django.utils import timezone
from rest_framework.test import APIClient

def test_complete_api():
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testuser', password='test123')

    # 创建必要的数据
    event = Event.objects.create(
        name='Test Event',
        type='conference',
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(hours=1),
        owner=user
    )

    template = ChecklistTemplate.objects.create(
        name='Test Template',
        checklist_type='custom',
        created_by=user
    )

    ChecklistItemTemplate.objects.create(
        template=template,
        title='Required Item',
        required=True,
        order=1,
        weight=1
    )

    instance, errors = ChecklistService.create_instance({
        'event_id': str(event.id),
        'template_id': str(template.id),
        'name': 'Test Instance'
    }, user)

    print(f"Instance created: {instance}")
    print(f"Instance id: {instance.id}")
    print(f"Instance items: {instance.items.count()}")
    print(f"Instance status: {instance.status}")

    # 标记所有项为完成
    for item in instance.items.all():
        item.status = 'passed'
        item.checked_by = user
        item.checked_at = timezone.now()
        item.save()
        print(f"Item {item.id} marked as passed")

    print("All items marked as passed")

    # 检查实例项
    instance.refresh_from_db()
    print(f"Instance items count after marking: {instance.items.count()}")

    # 检查必填项完成情况
    required_items = instance.items.filter(required=True)
    completed_required = required_items.filter(status__in=['passed', 'failed']).count()
    print(f"Required items: {required_items.count()}")
    print(f"Completed required items: {completed_required}")

    # 测试API
    client = APIClient()
    client.force_authenticate(user=user)

    print(f"Making API call to: /api/checklists/instances/{instance.id}/complete/")
    response = client.post(f'/api/checklists/instances/{instance.id}/complete/')
    print(f"API Response status: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"API Response data: {response.data}")
    else:
        print(f"API Response content: {response.content}")

    instance.refresh_from_db()
    print(f"Instance status after API: {instance.status}")

    # 直接调用service来验证逻辑
    instance2, errors = ChecklistService.create_instance({
        'event_id': str(event.id),
        'template_id': str(template.id),
        'name': 'Test Instance 2'
    }, user)

    for item in instance2.items.all():
        item.status = 'passed'
        item.checked_by = user
        item.checked_at = timezone.now()
        item.save()

    success, complete_errors = ChecklistService.complete_instance(instance2, user)
    print(f"\nDirect service call success: {success}")
    print(f"Direct service call errors: {complete_errors}")
    print(f"Direct service call instance status: {instance2.status}")

if __name__ == '__main__':
    test_complete_api()
