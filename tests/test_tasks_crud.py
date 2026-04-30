#!/usr/bin/env python3
"""
Tasks CRUD 完整测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def test_tasks_crud():
    """测试Tasks完整CRUD流程"""

    print("="*60)
    print("Tasks CRUD 完整测试")
    print("="*60)

    # 1. 登录获取token
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
    print(f"   状态码: {r.status_code}")

    if r.status_code not in [200, 201]:  # 200 OK 或 201 Created
        print(f"   ❌ 登录失败: {r.text}")
        return False

    data = r.json()
    # 后端返回嵌套结构 {data: {token: "...", user: {...}}}
    if 'data' in data:
        token = data['data'].get('token')
    else:
        token = data.get('token')

    if not token:
        print(f"   ❌ 无法获取Token，响应: {data}")
        return False

    print(f"   ✅ Token: {token[:50]}...")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取现有活动（必须先有活动才能创建任务）
    print("\n2. 获取现有活动 (Prerequisite):")
    r = requests.get(f"{BASE_URL}/events/events/", headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 200:
        events_data = r.json()
        results = events_data if isinstance(events_data, list) else events_data.get('results', [])

        # 尝试使用第一个活动，或者创建一个新活动
        if not results:
            # 创建一个至少持续1天的活动，类型必须是有效的（conference, exhibition, performance, party, training, other）
            start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT10:00:00Z")
            end_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%dT18:00:00Z")

            event_payload = {
                "name": "测试活动-CRUD测试",
                "type": "conference",  # 有效的活动类型
                "description": "用于Tasks CRUD测试的测试活动",
                "start_date": start_date,
                "end_date": end_date,
                "status": "planning"
            }
            r = requests.post(f"{BASE_URL}/events/events/", json=event_payload, headers=headers)
            print(f"   创建活动状态码: {r.status_code}")

            if r.status_code != 201:
                print(f"   ❌ 活动创建失败: {r.text}")
                print("   ⚠️  无法创建测试活动，测试必须停止")
                return False

            event = r.json()
            event_id = event.get('id')
            print(f"   ✅ 活动创建成功 (ID: {event_id})")
        else:
            event = results[0]
            event_id = event.get('id')
            print(f"   ✅ 使用现有活动: {event_id} - {event.get('name', '未知')}")
    else:
        print("   ❌ 无法获取活动列表")
        return False

    # 3. 创建任务（使用event_id而非event）
    print("\n3. 创建任务 (CREATE):")
    create_payload = {
        "event_id": str(event_id),  # note: 使用event_id
        "title": "测试任务1",
        "description": "这是一个测试任务",
        "task_type": "planning"
    }
    r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/", json=create_payload, headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code != 201:
        print(f"   ❌ 创建失败: {r.text}")
        print(f"   ⚠️  Payload: {create_payload}")
        return False

    response_data = r.json()
    # 后端返回 {data: {...}}
    task = response_data if 'data' not in response_data else response_data['data']
    task_id = task.get('id')
    print(f"   ✅ 任务创建成功 (ID: {task_id}, 标题: {task.get('title')})")

    # 4. 读取任务列表
    print("\n4. 读取任务列表 (LIST):")
    r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/", headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 200:
        tasks = r.json()
        results = tasks['results'] if 'results' in tasks else tasks
        count = len(results)
        print(f"   ✅ 任务列表: {count} 个任务")
    else:
        print(f"   ❌ 读取失败: {r.text}")

    # 5. 读取单个任务
    print("\n5. 读取任务详情 (RETRIEVE):")
    r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 200:
        task = r.json()
        print(f"   ✅ 任务详情: {task.get('title')}, 状态: {task.get('status')}")
    else:
        print(f"   ❌ 读取失败: {r.text}")

    # 6. 更新任务
    print("\n6. 更新任务 (UPDATE):")
    update_payload = {
        "title": "测试任务1（已更新）",
        "description": "任务描述已更新",
        "status": "in_progress"
    }
    r = requests.put(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", json=update_payload, headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 200:
        task = r.json()
        print(f"   ✅ 任务更新成功: {task.get('title')} (状态: {task.get('status')})")
    else:
        print(f"   ❌ 更新失败: {r.text}")

    # 7. 删除任务
    print("\n7. 删除任务 (DELETE):")
    r = requests.delete(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 204:
        print(f"   ✅ 任务删除成功")
    else:
        print(f"   ❌ 删除失败: {r.text}")

    # 8. 验证删除
    print("\n8. 验证删除 (RETRIEVE 删除后的任务):")
    r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)
    print(f"   状态码: {r.status_code}")

    if r.status_code == 404:
        print(f"   ✅ 任务已正确删除")
    else:
        print(f"   ❌ 删除验证失败: {r.text}")

    print("\n" + "="*60)
    print("✅ Tasks CRUD 测试完成 - 全部通过!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_tasks_crud()
