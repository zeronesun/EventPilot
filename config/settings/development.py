# -*- coding: utf-8 -*-
"""
Django settings for development environment.
"""
from .base import *

# 开发环境覆盖配置
DEBUG = True

# 允许的本地开发域名
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*', 'testserver']

# 开发环境 JWT Token 有效期延长（8小时）
JWT_ACCESS_TOKEN_EXPIRY = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRY', '28800'))

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

# 开发环境使用 Redis 缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# 开发环境使用 Redis Channel Layer (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    }
}