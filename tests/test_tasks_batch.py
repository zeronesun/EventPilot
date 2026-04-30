#!/usr/bin/env python3
"""
Tasks 批量操作测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def test_tasks_batch_operations():
    """测试Tasks批量操作功能"""

    print("="*60)
    print("Tasks 批量操作测试")
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

    # 3. 批量创建任务（通过多次调用）
    print("\n3. 批量创建任务:")
    created_task_ids = []
    for i in range(3):
        payload = {
            "event_id": str(event_id),
            "title": f"批量测试任务{i+1}",
            "description": f"这是批量创建的第{i+1}个测试任务",
            "task_type": "planning"
        }
        r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/", json=payload, headers=headers)
        if r.status_code == 201:
            task_data = r.json()
            task = task_data if 'data' not in task_data else task_data['data']
            task_id = task.get('id')
            created_task_ids.append(task_id)
            print(f"✅ 任务{i+1}创建成功: {task_id}")
        else:
            print(f"❌ 任务{i+1}创建失败: {r.text}")
            continue

    if not created_task_ids:
        print("❌ 批量创建任务失败")
        return False

    print(f"\n✅ 成功创建 {len(created_task_ids)} 个任务")

    # 4. 测试批量更新状态
    print("\n4. 批量更新任务状态为in_progress:")
    bulk_update_payload = {
        "task_ids": created_task_ids,
        "status": "in_progress"
    }
    r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/bulk_update_status/", json=bulk_update_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ 批量更新成功: {r.json()}")
    else:
        print(f"❌ 批量更新失败: {r.text}")

    # 5. 验证批量更新结果
    print("\n5. 验证批量更新结果:")
    for task_id in created_task_ids:
        r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)
        if r.status_code == 200:
            task = r.json()
            task_data = task['data'] if 'data' in task else task
            status = task_data.get('status')
            print(f"   任务 {task_id[:8]}... 状态: {status}")
        else:
            print(f"   ❌ 无法验证任务 {task_id}")

    # 6. 批量删除任务
    print("\n6. 批量删除任务:")
    bulk_delete_payload = {
        "task_ids": created_task_ids[:2]  # 只删除前2个
    }
    r = requests.post(f"{BASE_URL}/tasks/tasks/tasks/bulk_delete/", json=bulk_delete_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"✅ 批量删除成功: {result}")
    else:
        print(f"❌ 批量删除失败: {r.text}")

    # 7. 验证批量删除结果
    print("\n7. 验证批量删除结果:")
    for task_id in created_task_ids[:2]:
        r = requests.get(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)
        if r.status_code == 404:
            print(f"✅ 任务 {task_id[:8]}... 已成功删除")
        else:
            print(f"❌ 任务 {task_id[:8]}... 仍然存在")

    # 清理创建的剩余任务
    print("\n8. 清理剩余测试任务:")
    for task_id in created_task_ids[2:]:
        requests.delete(f"{BASE_URL}/tasks/tasks/tasks/{task_id}/", headers=headers)

    print("\n" + "="*60)
    print("✅ Tasks 批量操作测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_tasks_batch_operations()
