"""
Tasks app测试配置
"""
import os
import pytest

# 确保测试环境允许testserver
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

import django
django.setup()


@pytest.fixture(autouse=True)
def configure_django():
    """自动配置Django用于测试"""
    # 确保每次测试前ALLOWED_HOST都包含testserver
    from django.conf import settings
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    if 'testserver' not in settings.CSRF_TRUSTED_ORIGINS:
        settings.CSRF_TRUSTED_ORIGINS.append('http://testserver')
