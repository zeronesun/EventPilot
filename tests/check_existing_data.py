#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.events.models import Event
from apps.checklists.models.checklist_template import ChecklistTemplate

print("=== Events in database ===")
for e in Event.objects.all()[:3]:
    print(f"ID: {e.id}, Name: {e.name}")

print("\n=== Templates in database ===")
for t in ChecklistTemplate.objects.all()[:3]:
    print(f"ID: {t.id}, Name: {t.name}")
