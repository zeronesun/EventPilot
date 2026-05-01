import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver

resolver = get_resolver()
patterns = resolver.url_patterns

print(f"Found {len(patterns)} URL patterns")
print("\nChecking for checklist patterns...")

for pattern in patterns:
    pattern_str = str(pattern)
    if 'checklist' in pattern_str.lower():
        print(f"  - {pattern_str}")

print("\nListing all patterns:")
for i, pattern in enumerate(patterns[:20]):  # Show first 20
    print(f"  {i+1}. {pattern}")
