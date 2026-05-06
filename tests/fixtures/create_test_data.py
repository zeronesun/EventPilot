#!/usr/bin/env python
"""
EventPilot 测试数据准备脚本

根据 E2E_TEST_PROMPT.md 要求创建测试数据
"""
import os
import sys
import django

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.events.models import Event
from apps.tasks.models import Task
import random
from datetime import datetime, timedelta

User = get_user_model()


def create_test_users():
    """创建测试用户"""
    test_users = {
        'admin': {
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin',
            'email': 'admin@eventpilot.test'
        },
        'owner': {
            'username': 'owner',
            'password': 'owner123',
            'role': 'project_owner',
            'email': 'owner@eventpilot.test'
        },
        'executor': {
            'username': 'executor',
            'password': 'executor123',
            'role': 'executor',
            'email': 'executor@eventpilot.test'
        }
    }
    
    created_users = {}
    for key, user_data in test_users.items():
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'is_staff': key == 'admin',
                'is_superuser': key == 'admin',
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"✅ 创建用户: {user.username}")
        else:
            # 更新密码确保一致
            user.set_password(user_data['password'])
            user.save()
            print(f"✅ 用户已存在: {user.username}")
        created_users[key] = user
    
    return created_users


def create_test_events(users):
    """创建测试活动"""
    events_data = [
        {'name': '测试活动-策划中', 'status': 'planning', 'type': 'conference'},
        {'name': '测试活动-执行中', 'status': 'executing', 'type': 'seminar'},
        {'name': '测试活动-已完成', 'status': 'completed', 'type': 'workshop'},
    ]
    
    created_events = []
    for event_data in events_data:
        # 随机分配一个负责人
        owner = random.choice(list(users.values()))
        
        event, created = Event.objects.get_or_create(
            name=event_data['name'],
            defaults={
                'description': f"自动化测试用活动 - {event_data['status']}",
                'status': event_data['status'],
                'type': event_data['type'],
                'owner': owner,
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(hours=8),
            }
        )
        if created:
            print(f"✅ 创建活动: {event.name}")
        else:
            print(f"✅ 活动已存在: {event.name}")
        created_events.append(event)
    
    return created_events


def create_test_tasks(users, events):
    """创建测试任务"""
    tasks_data = [
        {'title': '测试任务-待办', 'status': 'todo', 'priority': 'high'},
        {'title': '测试任务-进行中', 'status': 'in_progress', 'priority': 'medium'},
        {'title': '测试任务-已完成', 'status': 'done', 'priority': 'low'},
    ]
    
    created_tasks = []
    for task_data in tasks_data:
        # 如果有活动，随机关联
        if events:
            event = random.choice(events)
        else:
            event = None
        
        # 随机分配负责人
        assignee = random.choice(list(users.values()))
        
        task, created = Task.objects.get_or_create(
            title=task_data['title'],
            defaults={
                'description': f"自动化测试用任务 - {task_data['status']}",
                'status': task_data['status'],
                'priority': task_data['priority'],
                'assignee': assignee,
                'event': event,
            }
        )
        if created:
            print(f"✅ 创建任务: {task.title}")
        else:
            print(f"✅ 任务已存在: {task.title}")
        created_tasks.append(task)
    
    return created_tasks


def main():
    """主函数"""
    print("=" * 60)
    print("EventPilot 测试数据准备")
    print("=" * 60)
    
    # 创建测试用户
    print("\n【1/3】创建测试用户...")
    users = create_test_users()
    print(f"   共 {len(users)} 个用户")
    
    # 创建测试活动
    print("\n【2/3】创建测试活动...")
    events = create_test_events(users)
    print(f"   共 {len(events)} 个活动")
    
    # 创建测试任务
    print("\n【3/3】创建测试任务...")
    tasks = create_test_tasks(users, events)
    print(f"   共 {len(tasks)} 个任务")
    
    # 统计信息
    print("\n" + "=" * 60)
    print("测试数据创建完成！")
    print("=" * 60)
    print(f"用户数: {User.objects.count()}")
    print(f"活动数: {Event.objects.count()}")
    print(f"任务数: {Task.objects.count()}")
    print("=" * 60)
    
    # 输出登录信息
    print("\n测试账号信息:")
    print("-" * 60)
    for key, user in users.items():
        pwd = 'admin123' if key == 'admin' else (key[:-1] + '123' if key.endswith('or') else key[:-1] + '123')
        if key == 'owner':
            pwd = 'owner123'
        elif key == 'executor':
            pwd = 'executor123'
        print(f"  {key:10} - 用户名: {user.username:10} 密码: {pwd}")
    print("-" * 60)


if __name__ == '__main__':
    main()
