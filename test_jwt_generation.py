import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
try:
    admin_user = User.objects.get(username='admin')
except User.DoesNotExist:
    admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='admin')

from apps.users.authentication import generate_jwt_token
from django.conf import settings

print(f".JWT_SECRET_KEY: {settings.JWT_SECRET_KEY}")
print(f"JWT_ACCESS_TOKEN_EXPIRY: {settings.JWT_ACCESS_TOKEN_EXPIRY}")
print(f"JWT_REFRESH_TOKEN_EXPIRY: {settings.JWT_REFRESH_TOKEN_EXPIRY}")

token = generate_jwt_token(admin_user)
print(f"JWT Token: {token[:50]}..." if len(token) > 50 else f"JWT Token: {token}")
print("JWT generation successful!")
