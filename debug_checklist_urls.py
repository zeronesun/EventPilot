from django.conf import settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.checklists.api import urls as checklist_urls

print("Checklist urls urlpatterns:", checklist_urls.urlpatterns)

print("\nRouter patterns:")
for pattern in checklist_urls.router.registry:
    print(f"  {pattern}")

print("\nRouter URLs:")
for url in checklist_urls.router.urls:
    print(f"  {url.pattern} -> {url.name}")
