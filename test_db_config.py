import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.conf import settings

# 检查数据库配置
print(f"DATABASES: {settings.DATABASES}")
print(f"\nDATABASE_ROUTERS: {settings.DATABASE_ROUTERS}")
print(f"\nTEST database: {settings.DATABASES.get('default', {}).get('TEST', {})}")

# 检查是否是测试环境
print(f"\nIs test: {hasattr(settings, '_TEST')}")
