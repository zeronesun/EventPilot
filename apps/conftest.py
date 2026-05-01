"""pytest 配置文件"""
import os
import pytest


@pytest.fixture(scope='session', autouse=True)
def configure_test_settings():
    """为测试环境配置环境变量"""
    os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
    os.environ.setdefault('DJANGO_DEBUG', 'True')
    os.environ.setdefault('USE_SQLITE', 'True')
    os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')
