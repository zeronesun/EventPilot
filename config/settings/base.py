import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 构建路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 关键配置
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

#应用定义
INSTALLED_APPS = [
    # 'django.contrib.admin',  # 暂时禁用admin进行测试
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    #第三方应用
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    
    # 本地应用 - 核心模块
    'apps.users',
    'apps.events',
    'apps.tasks',
    'apps.checklists',
    # 'apps.profiles',  # 暂时禁用
    # 'apps.knowledge',  # 暂时禁用
    # 'apps.reviews',  # 暂时禁用
]

# 中间件
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS最早
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 静态文件处理
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# 数据库配置 (开发环境优先使用SQLite)
if os.getenv('USE_SQLITE', 'True').lower() in ('true', '1', 'yes'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.getenv('DB_NAME', 'eventpilot_dev.db'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'eventpilot'),
            'USER': os.getenv('DB_USER', 'eventpilot'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': 'prefer',
            },
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'eventpilot',
        'TIMEOUT': 300,
        'VERSION': 1,
    }
}

# 密码配置（使用argon2）
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件配置
USE_LOCAL_STORAGE = os.getenv('USE_LOCAL_STORAGE', 'True').lower() in ('true', '1', 'yes')
if USE_LOCAL_STORAGE:
    MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(BASE_DIR / 'public' / 'media'))
    MEDIA_URL = '/media/'
    STATIC_ROOT = os.getenv('STATIC_ROOT', str(BASE_DIR / 'public' / 'static'))
    STATIC_URL = '/static/'
else:
    MEDIA_ROOT = '/app/media'
    MEDIA_URL = '/media/'
    STATIC_ROOT = '/app/static'
    STATIC_URL = '/static/'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework基础配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# CORS配置
CORS_ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# 安全配置
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    SECURE_SSL_REDIRECT = False

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'logs' / 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        '': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# 确保日志目录存在
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# 自定义用户模型
AUTH_USER_MODEL = 'users.User'

# 认证配置
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Token认证（临时方案，后续替换为JWT）
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework.authentication.TokenAuthentication',
]
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.IsAuthenticatedOrReadOnly',
]