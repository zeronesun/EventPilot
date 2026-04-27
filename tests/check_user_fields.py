#!/usr/bin/env python3
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.users.models import User

if User.objects.exists():
    u = User.objects.first()
    print(f"User: {u}")
    print(f"hasattr username: {hasattr(u, 'username')}")
    print(f"hasattr email: {hasattr(u, 'email')}")
    print(f"hasattr phone: {hasattr(u, 'phone')}")
    if hasattr(u, 'username'):
        print(f"username: {u.username}")
