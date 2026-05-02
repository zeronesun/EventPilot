#!/usr/bin/env python
import os
import sys
import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.events.models import Event
from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate, ChecklistItem
from apps.checklists.services.checklist_service import ChecklistService
from django.utils import timezone

@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=['testserver', '*'])
def test_complete_instance():
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
    print(f"Instance items: {instance.items.count()}")

    # 标记所有项为完成
    for item in instance.items.all():
        item.status = 'passed'
        item.checked_by = user
        item.checked_at = timezone.now()
        item.save()

    print("All items marked as passed")
    print(f"Instance status before API: {instance.status}")

    # 测试API
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(f'/api/checklists/instances/{instance.id}/complete/')
    print(f"API Response status: {response.status_code}")
    print(f"API Response data: {response.data if hasattr(response, 'data') else response.content}")

    instance.refresh_from_db()
    print(f"Instance status after API: {instance.status}")

if __name__ == '__main__':
    test_complete_instance()
