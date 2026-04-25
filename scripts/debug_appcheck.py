from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

print("INSTALLED_APPS check:")
if 'apps.checklists' in settings.INSTALLED_APPS:
    print("✓ apps.checklists in INSTALLED_APPS")
else:
    print("✗ apps.checklists NOT in INSTALLED_APPS")
    print("  INSTALLED_APPS:", settings.INSTALLED_APPS)

print("\nApps config check:")
from django.apps import apps
try:
    config = apps.get_app_config('checklists')
    print(f"✓ checklists app loaded: {config.name}")
except Exception as e:
    print(f"✗ checklists app NOT loaded: {e}")

print("\nURL conf check:")
from django.urls import get_resolver
resolver = get_resolver()
checklist_urls_found = []
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'checklist' in pattern_str.lower() or 'list' in pattern_str.lower():
        checklist_urls_found.append(pattern.pattern)
        print(f"  {pattern.pattern}")

if not checklist_urls_found:
    print("  No Checklist URLs with 'list' found!")
