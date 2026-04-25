from django.conf import settings
import os, sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).parent))

import django
django.setup()

print("All loaded app configs:")
from django.apps import apps
for app in apps.get_app_configs():
    if 'checklist' in app.name.lower():
        print(f"  {app.name}")

print("\nURL patterns for api/ namespace:")
from django.urls import get_resolver
resolver = get_resolver('api')
print(f"Resolver namespace: api")
print(f"URL patterns count: {len(resolver.url_patterns)}")

print("\nDirect URL patterns:")
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    print(f"  {pattern_str}")
