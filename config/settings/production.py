# -*- coding: utf-8 -*-
"""
Django settings for production environment.
"""
from .base import *

# 生产环境配置
DEBUG = False

# 确保ALLOWED_HOSTS正确配置
if os.getenv('DJANGO_ALLOWED_HOSTS'):
    ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS').split(',')
else:
    raise ValueError("DJANGO_ALLOWED_HOSTS必须配置在生产环境中")

# 生产环境安全配置
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = TrueSESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 生产环境日志更严格
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['handlers']['console']['level'] = 'WARNING'

# 数据库连接优化
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'sslmode': 'require',
    'connect_timeout': 10,
}

# 缓存优化
CACHES['default']['TIMEOUT'] = 600
CACHES['default']['OPTIONS']['MAX_CONNECTIONS'] = 50

# 文件存储优化
if not USE_LOCAL_STORAGE:
    # 生产环境使用对象存储
    INSTALLED_APPS.append('storages')