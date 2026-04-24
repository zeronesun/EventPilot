# -*- coding: utf-8 -*-
"""
Django settings for development environment.
"""
from .base import *

# 开发环境覆盖配置
DEBUG = True

# 允许的本地开发域名
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# 开发工具配置
INSTALLED_APPS += [
    # 'django.contrib.admin',  # 暂时禁用admin
    'debug_toolbar',
]

# 调试工具栏（可选）
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# 开发环境数据库配置
DATABASES['default']['CONN_MAX_AGE'] = 0

# 开发环境日志
LOGGING['handlers']['file']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'

# CORS开发配置
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://172.28.166.164:3000',
    'http://10.255.255.254:3000',
    'http://10.255.255.255:3000',
]
CORS_ALLOW_CREDENTIALS = True


# 安全配置关闭
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False