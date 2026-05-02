#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.events.models import Event
import uuid

# 直接查询
event_id_str = "08f5a543-a686-4d41-8f9b-9dd19badd2b5"
print(f"String: {event_id_str}")

try:
    uuid_obj = uuid.UUID(event_id_str)
    print(f"UUID: {uuid_obj}")
    print(f"Type: {type(uuid_obj)}")
except Exception as e:
    print(f"UUID conversion error: {e}")

try:
    event = Event.objects.get(id=event_id_str)
    print(f"Event found: {event.name}")
except Exception as e:
    print(f"Query by string error: {e}")

try:
    event = Event.objects.get(id=uuid_obj)
    print(f"Event found: {event.name}")
except Exception as e:
    print(f"Query by UUID object error: {e}")
