#!/usr/bin/env python3
"""
检查validated_data
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.checklists.api.serializers import ChecklistInstanceSerializer
from apps.events.models import Event
from apps.checklists.models.checklist_template import ChecklistTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

event = Event.objects.get(id="08f5a543-a686-4d41-8f9b-9dd19badd2b5")
template = ChecklistTemplate.objects.get(id="f2843499-016d-463a-a24e-6898389aacc9")
user = User.objects.first()

test_data = {
    "event": "08f5a543-a686-4d41-8f9b-9dd19badd2b5",
    "template": "f2843499-016d-463a-a24e-6898389aacc9",
    "name": "测试",
    "status": "in_progress"
}

serializer = ChecklistInstanceSerializer(data=test_data, context={'request': type('obj', (object,), {'user': user})()})

print(f"Valid: {serializer.is_valid()}")
print(f"Validated_data: {serializer.validated_data}")
print(f"Type of event: {type(serializer.validated_data.get('event'))}")
print(f"Type of template: {type(serializer.validated_data.get('template'))}")
