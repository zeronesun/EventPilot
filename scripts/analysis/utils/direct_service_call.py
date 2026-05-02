#!/usr/bin/env python3
"""
直接测试实例化，绕过validation
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.checklists.services.checklist_service import ChecklistService
from apps.events.models import Event
from apps.checklists.models.checklist_template import ChecklistTemplate

# 获取测试数据
event = Event.objects.get(id="08f5a543-a686-4d41-8f9b-9dd19badd2b5")
template = ChecklistTemplate.objects.get(id="f2843499-016d-463a-a24e-6898389aacc9")

print(f"Event: {event.name}, Template: {template.name}")

# 直接调用create_instance
test_data = {
    "event": str(event.id),
    "template": str(template.id),
    "name": "直接调用测试",
    "status": "in_progress"
}

instance, errors = ChecklistService.create_instance(test_data, None)

if instance:
    print(f"✅ 成功创建实例: {instance.name}")
else:
    print(f"❌ 失败: {errors}")
