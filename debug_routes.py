from django.conf import settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()
user = User.objects.create_user(username='test', password='test')

client = Client()
client.force_login(user)

print("Listing URLs...")
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(f"  Pattern: {pattern.pattern}")
    if hasattr(pattern, 'url_patterns'):
        for sub in pattern.url_patterns:
            print(f"    Sub: {sub.pattern}")

print("\n\nTrying to access /api/checklists/templates/")
response = client.post('/api/checklists/templates/', json.dumps({
    'name': 'test',
    'checklist_type': 'pre_event',
    'event_types': []
}), content_type='application/json')
print(f"Status: {response.status_code}")
print(f"Content: {response.content[:200]}")
