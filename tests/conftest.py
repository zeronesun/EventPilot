# -*- coding: utf-8 -*-
"""
测试配置和fixtures
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.events.models import Event
from apps.tasks.models import Task

User = get_user_model()


@pytest.fixture
def create_user(db):
    """创建测试用户"""
    def _create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    
    return _create_user


@pytest.fixture
def create_event(db, create_user):
    """创建测试活动"""
    def _create_event(**kwargs):
        defaults = {
            'title': 'Test Event',
            'description': 'Test Description',
            'status': 'planning',
            'start_date': None,
            'end_date': None
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)
    
    return _create_event


@pytest.fixture
def create_task(db, create_user):
    """创建测试任务"""
    def _create_task(**kwargs):
        defaults = {
            'title': 'Test Task',
            'description': 'Test Task Description',
            'status': 'pending',
            'event_id': None,
            'assignee_id': None
        }
        defaults.update(kwargs)
        return Task.objects.create(**defaults)
    
    return _create_task


@pytest.fixture
def create_jwt_token(create_user):
    """创建JWT token"""
    def _create_token(user=None):
        if user is None:
            user = create_user()
        token = RefreshToken.for_user(user)
        return str(token.access_token)
    
    return _create_token