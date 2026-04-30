#!/usr/bin/env python3
"""
EventPilot 数据生成器 - 改进版
生成高质量的测试数据
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import random

# API配置
BASE_URL = "http://localhost:8000"

def login():
    """登录获取Token"""
    try:
        response = requests.post(f"{BASE_URL}/api/users/auth/login/", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code in [200, 201]:
            token = response.json()['data']['token']
            return {'Authorization': f'Bearer {token}'}
    except:
        pass
    return {}

def get_event_list(headers):
    """获取现有事件列表"""
    try:
        response = requests.get(f"{BASE_URL}/api/events/events/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            return data.get('results', [])
    except:
        pass
    return []

def create_tasks(headers, event_list, count=50):
    """为事件创建任务"""
    print(f"\n创建 {count} 个任务...")
    
    task_types = ["planning", "guest", "material", "venue", "promotion", "onsite", "review"]
    created = 0
    
    if not event_list:
        print("  ✗ 无可用事件")
        return 0
    
    for i in range(count):
        event = random.choice(event_list)
        event_id = event.get('id')
        
        # 计算任务日期
        start_date_str = event.get('start_date', '')
        if start_date_str:
            try:
                base_date = datetime.strptime(start_date_str[:19], "%Y-%m-%dT%H:%M:%S")
                task_date = base_date - timedelta(days=random.randint(30, 60))
            except:
                task_date = datetime.now() + timedelta(days=random.randint(10, 60))
        else:
            task_date = datetime.now() + timedelta(days=random.randint(10, 60))
        
        task_data = {
            "title": f"{random.choice(task_types)}任务-{i+1}",
            "description": "测试任务描述",
            "task_type": random.choice(task_types),
            "start_date": task_date.strftime("%Y-%m-%dT09:00:00Z"),
            "due_date": (task_date + timedelta(days=7)).strftime("%Y-%m-%dT18:00:00Z")
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/tasks/tasks/",
                json=task_data,
                headers=headers
            )
            if response.status_code in [200, 201]:
                created += 1
                if (i+1) % 10 == 0:
                    print(f"  已创建 {created} 个任务")
        except Exception as e:
            pass
    
    print(f"  ✓ 任务创建完成: {created} 个")
    return created

def create_budget_items(headers, event_list, count=30):
    """为事件创建预算项目"""
    print(f"\n创建 {count} 个预算项目...")
    
    categories = ["场地费", "设备费", "人员费", "餐饮费", "宣传费", "差旅费"]
    created = 0
    
    if not event_list:
        print("  ✗ 无可用事件")
        return 0
    
    for i in range(count):
        event = random.choice(event_list)
        event_id = event.get('id')
        
        budget_data = {
            "event": event_id,
            "category_name": random.choice(categories),
            "name": f"{random.choice(categories)}-{i+1}",
            "estimated_amount": random.randint(10000, 50000),
            "status": "pending"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/events/budget-items/",
                json=budget_data,
                headers=headers
            )
            if response.status_code in [200, 201]:
                created += 1
                if (i+1) % 10 == 0:
                    print(f"  已创建 {created} 个预算项目")
        except Exception as e:
            pass
    
    print(f"  ✓ 预算项目创建完成: {created} 个")
    return created

def show_statistics(headers):
    """显示系统统计信息"""
    print("\n" + "="*60)
    print("  当前系统数据统计")
    print("="*60)
    
    # 事件统计
    try:
        response = requests.get(f"{BASE_URL}/api/events/events/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            count = data.get('count', 0)
            print(f"  事件总数: {count}")
    except:
        print(f"  事件总数: 获取失败")
    
    # 任务统计
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/tasks/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if 'data' in data:
                count = data['data'].get('count', 0)
            else:
                count = len(data.get('results', []))
            print(f"  任务总数: {count}")
    except:
        print(f"  任务总数: 获取失败")
    
    # 检查清单统计
    try:
        response = requests.get(f"{BASE_URL}/api/checklists/templates/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            count = data.get('count', 0)
            print(f"  检查清单模板: {count}")
    except:
        print(f"  检查清单模板: 获取失败")

def main():
    print("="*60)
    print("  EventPilot 数据生成器 - 改进版")
    print("="*60)
    
    # 登录
    headers = login()
    if not headers:
        print("✗ 登录失败")
        return
    
    print("✓ 登录成功")
    
    # 获取现有事件
    event_list = get_event_list(headers)
    print(f"\n✓ 发现有 {len(event_list)} 个现有事件")
    
    if event_list:
        print(f"  示例事件: {event_list[0].get('name', '未知')[:30]}...")
    
    # 创建任务
    tasks_created = create_tasks(headers, event_list, 50)
    
    # 创建预算项目
    budgets_created = create_budget_items(headers, event_list, 30)
    
    # 显示统计
    show_statistics(headers)
    
    print("\n" + "="*60)
    print("  数据生成完成！")
    print(f"  新增任务: {tasks_created} 个")
    print(f"  新增预算: {budgets_created} 个")
    print("="*60)

if __name__ == "__main__":
    main()
