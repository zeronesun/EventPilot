#!/usr/bin/env python3
"""
Tasks 拖拽功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def test_tasks_drag_functionality():
    """测试Tasks拖拽功能"""

    print("="*60)
    print("Tasks 拖拽功能测试")
    print("="*60)

    # 1. 登录
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text}")
        return False
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    if not token:
        print("❌ 无法获取Token")
        return False
    
    print(f"✅ Token获取成功")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取活动
    print("\n2. 获取测试活动:")
    r = requests.get(f"{BASE_URL}/events/events/", headers=headers)
    if r.status_code != 200:
        print("❌ 无法获取活动")
        return False
    
    events_data = r.json()
    results = events_data['results'] if 'results' in events_data else events_data
    if results:
        event = results[0]
        event_id = event.get('id')
        print(f"✅ 使用活动: {event_id}")
    else:
        print("❌ 没有可用活动")
        return False

    # 3. 创建不同状态的任务
    print("\n3. 创建测试任务:")
    tasks_by_status = {
        'pending': None,
        'in_progress': None,
        'completed': None
    }

    for status, task_id in tasks_by_status.items():
        payload = {
            "event_id": str(event_id),
            "title": f"拖拽测试-{status}",
            "description": f"测试{status}状态的任务",
            "task_type": "planning"
        }
        r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/", json=payload, headers=headers)
        if r.status_code == 201:
            task_data = r.json()
            task = task_data if 'data' not in task_data else task_data['data']
            tasks_by_status[status] = task.get('id')
            print(f"✅ 创建 {status} 任务: {task.get('id')[:8]}...")
        else:
            print(f"❌ 创建失败: {r.text}")

    # 4. 获取看板数据
    print("\n4. 获取看板数据:")
    r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/kanban_data/?event={event_id}", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        kanban_data = r.json()
        print(f"✅ 看板数据: {json.dumps(kanban_data, indent=2, ensure_ascii=False)[:300]}...")
    else:
        print(f"❌ 看板数据获取失败: {r.text}")
        return False

    # 5. 测试拖拽：将任务从 pending 拖到 in_progress
    print("\n5. 测试拖拽 (pending -> in_progress):")
    if not tasks_by_status['pending']:
        print("❌ pending任务未创建")
        return False

    r = requests.put(
        f"{BASE_URL}/tasks/tasks/tasks/{tasks_by_status['pending']}/",
        json={"status": "in_progress"},
        headers=headers
    )
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ 拖拽成功")
    else:
        print(f"❌ 拖拽失败: {r.text}")

    # 6. 再次获取看板数据验证拖拽结果
    print("\n6. 验证拖拽结果:")
    r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/kanban_data/?event={event_id}", headers=headers)
    if r.status_code == 200:
        kanban_data = r.json()
        # 检查in_progress列是否有任务
        in_progress_tasks = kanban_data.get('in_progress', [])
        if in_progress_tasks:
            print(f"✅ in_progress列有 {len(in_progress_tasks)} 个任务")
        else:
            print("❌ in_progress列没有任务")

    # 7. 测试批量拖拽（批量更新状态）
    print("\n7. 测试批量拖拽（批量更新状态）:")
    valid_task_ids = [t for t in tasks_by_status.values() if t]
    if len(valid_task_ids) >= 2:
        bulk_payload = {
            "task_ids": valid_task_ids,
            "status": "completed"
        }
        r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/bulk_update_status/", json=bulk_payload, headers=headers)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ 批量拖拽成功")
        else:
            print(f"❌ 批量拖拽失败: {r.text}")

    # 清理
    print("\n8. 清理测试任务:")
    for task_id in tasks_by_status.values():
        if task_id:
            requests.delete(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)

    print("\n" + "="*60)
    print("✅ Tasks 拖拽功能测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_tasks_drag_functionality()
