#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth.models import User
from apps.profiles.models import ContactProfile

print("检查User和ContactProfile:")
print(f"User表数量: {User.objects.count()}")
print(f"ContactProfile表数量: {ContactProfile.objects.count()}")

# 检查User是否有username
if User.objects.exists():
    u = User.objects.first()
    print(f"第一个User: {u.username if hasattr(u, 'username') else 'N/A'}")
