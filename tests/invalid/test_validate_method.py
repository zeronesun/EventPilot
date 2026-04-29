#!/usr/bin/env python3
"""
在service内部添加调试，找到实际错误位置
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import sys
from apps.events.models import Event
from apps.checklists.services.checklist_service import ChecklistService

event = Event.objects.get(id="08f5a543-a686-4d41-8f9b-9dd19badd2b5")

# 找到validate_instance_data可能的错误
test_data = {"event": event}  # 直接传入Event对象

is_valid, errors = ChecklistService.validate_instance_data(test_data)
print(f"Valid: {is_valid}, Errors: {errors}")
