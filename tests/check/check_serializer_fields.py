#!/usr/bin/env python3
"""
打印serializer的field定义
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.checklists.api.serializers import ChecklistInstanceSerializer

print("=== Serializer Fields ===")
for field_name, field_obj in ChecklistInstanceSerializer().fields.items():
    print(f"{field_name}: {type(field_obj).__name__}")
    if hasattr(field_obj, 'source'):
        print(f"  - source: {field_obj.source}")
