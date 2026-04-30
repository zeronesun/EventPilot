#!/usr/bin/env python3
"""
EventPilot 测试数据生成器
生成各种类型的测试数据用于演示和测试
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import random

# API配置
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
TOKEN = ""
HEADERS = {}

def login():
    """登录获取Token"""
    global TOKEN, HEADERS
    print("登录中...")
    response = requests.post(f"{BASE_URL}/api/users/auth/login/", json=ADMIN_CREDENTIALS)
    if response.status_code in [200, 201]:
        TOKEN = response.json()['data']['token']
        HEADERS = {'Authorization': f'Bearer {TOKEN}'}
        print("✓ 登录成功")
        return True
    return False

# 事件类型和状态
EVENT_TYPES = ["conference", "exhibition", "festival", "corporate_event", "roadshow"]
EVENT_STATUSES = ["planning", "executing", "completed", "reviewed", "cancelled"]

# 任务类型
TASK_TYPES = ["planning", "guest", "material", "venue", "promotion", "onsite", "review"]
TASK_STATUSES = ["pending", "in_progress", "completed", "blocked"]

# 检查清单类型
CHECKLIST_TYPES = ["pre_event", "during_event", "post_event"]

# 测试数据模板
COMPANY_PREFIXES = ["北京", "上海", "广州", "深圳", "杭州"]
INDUSTRIES = ["科技", "制造", "金融", "医疗", "教育"]

PERSON_NAMES = ["张伟", "李娜", "王强", "刘敏", "陈刚", "杨雪", "黄磊", "周杰"]

DEPARTMENTS = ["市场部", "运营部", "技术部", "设计部", "公关部"]

def generate_events(count=15):
    """生成事件数据"""
    print(f"\n生成 {count} 个事件...")
    
    events_created = 0
    events_data = []
    
    base_date = datetime.now() + timedelta(days=60)  # 从60天后开始
    
    for i in range(count):
        event_date = base_date + timedelta(days=random.randint(0, 180))
        
        event_data = {
            "name": f"{random.choice(COMPANY_PREFIXES)}{random.choice(INDUSTRIES)}大会202{i % 2 + 1}",
            "type": random.choice(EVENT_TYPES),
            "description": f"{random.choice(COMPANY_PREFIXES)}{random.choice(INDUSTRIES)}行业年度盛会，预计{random.randint(500, 5000)}人参加",
            "start_date": event_date.strftime("%Y-%m-%dT09:00:00Z"),
            "end_date": (event_date + timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%dT18:00:00Z"),
            "status": EVENT_STATUSES[i % len(EVENT_STATUSES)],
            "client": f"{random.choice(COMPANY_PREFIXES)}{random.choice(INDUSTRIES)}有限公司",
            "client_contact": f"{random.choice(PERSON_NAMES)} (总监)",
            "estimated_budget": random.randint(100000, 1000000),
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/events/events/",
                json=event_data,
                headers=HEADERS
            )
            
            if response.status_code in [200, 201]:
                event = response.json()
                if 'id' in event:
                    events_data.append((event['id'], event_data))
                    events_created += 1
                    print(f"  ✓ 事件 {i+1}: {event_data['name']}")
                elif 'data' in event and 'id' in event['data']:
                    events_data.append((event['data']['id'], event_data))
                    events_created += 1
                    print(f"  ✓ 事件 {i+1}: {event_data['name']}")
            else:
                print(f"  ✗ 事件 {i+1} 失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 事件 {i+1} 错误: {e}")
    
    print(f"✓ 成功创建 {events_created} 个事件")
    return events_data

def generate_tasks(events_data, tasks_per_event=8):
    """生成任务数据"""
    print(f"\n为每个事件生成 {tasks_per_event} 个任务...")
    
    tasks_created = 0
    
    for event_id, event_data in events_data:
        event_date = datetime.strptime(event_data['start_date'], "%Y-%m-%dT%H:%M:%SZ")
        
        for i in range(tasks_per_event):
            task_date = event_date - timedelta(days=random.randint(30, 60))
            
            task_data = {
                "title": f"{event_data['type']}任务-{i+1}",
                "description": f"{event_data['name']}的{random.choice(TASK_TYPES)}相关工作",
                "task_type": random.choice(TASK_TYPES),
                "status": random.choice(TASK_STATUSES),
                "start_date": task_date.strftime("%Y-%m-%dT09:00:00Z"),
                "due_date": (task_date + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%dT18:00:00Z")
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/tasks/tasks/",
                    json=task_data,
                    headers=HEADERS
                )
                
                if response.status_code in [200, 201]:
                    tasks_created += 1
            except Exception as e:
                print(f"  ✗ 任务创建错误: {e}")
    
    print(f"✓ 成功创建 {tasks_created} 个任务")
    return tasks_created

def generate_checklists(count=10):
    """生成检查清单模板"""
    print(f"\n生成 {count} 个检查清单模板...")
    
    checklists_created = 0
    
    for i in range(count):
        template_data = {
            "name": f"标准{i+1}检查清单",
            "description": f"标准化检查流程模板，适用于{random.choice(EVENT_TYPES)}类型活动",
            "checklist_type": random.choice(CHECKLIST_TYPES),
            "event_types": random.sample(EVENT_TYPES, random.randint(1, 3))
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/checklists/templates/",
                json=template_data,
                headers=HEADERS
            )
            
            if response.status_code in [200, 201]:
                checklists_created += 1
                print(f"  ✓ 检查清单 {i+1}: {template_data['name']}")
        except Exception as e:
            print(f"  ✗ 检查清单 {i+1} 失败: {e}")
    
    print(f"✓ 成功创建 {checklists_created} 个检查清单模板")
    return checklists_created

def generate_budget_items():
    """为已有事件生成预算项目"""
    print("\n为事件生成预算项目...")
    
    budget_categories = [
        ("场地费", 50000),
        ("设备费", 30000),
        ("人员费", 20000),
        ("餐饮费", 15000),
        ("宣传费", 25000),
        ("差旅费", 10000),
        ("礼品费", 8000),
        ("其他", 5000)
    ]
    
    budgets_created = 0
    
    # 获取一些事件ID
    try:
        response = requests.get(f"{BASE_URL}/api/events/events/", headers=HEADERS)
        if response.status_code in [200, 201]:
            events = response.json()
            event_list = events.get('results', [])
            
            for event in event_list[:8]:  # 为前8个事件生成预算
                for category, base_amount in budget_categories[:5]:  # 每个事件5个预算项
                    budget_data = {
                        "event": event.get('id') if isinstance(event, dict) else event,
                        "category_name": category,
                        "name": f"{category}支出",
                        "estimated_amount": base_amount * random.randint(8, 15) / 10,
                        "status": "pending"
                    }
                    
                    try:
                        response = requests.post(
                            f"{BASE_URL}/api/events/budget-items/",
                            json=budget_data,
                            headers=HEADERS
                        )
                        
                        if response.status_code in [200, 201]:
                            budgets_created += 1
                    except Exception as e:
                        pass
            
            print(f"  ✓ 成功创建 {budgets_created} 个预算项目")
    except Exception as e:
        print(f"  ✗ 预算生成失败: {e}")
    
    return budgets_created

def main():
    print("="*60)
    print("  EventPilot 测试数据生成器")
    print("  开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # 登录
    if not login():
        print("✗ 登录失败，无法继续")
        return
    
    total_events = 0
    total_tasks = 0
    total_checklists = 0
    total_budgets = 0
    
    # 生成事件
    events_data = generate_events(15)
    if events_data:
        total_events = len(events_data)
    
    # 生成任务
    if events_data:
        total_tasks = generate_tasks(events_data, 8)
    
    # 生成检查清单
    total_checklists = generate_checklists(10)
    
    # 生成预算项目
    total_budgets = generate_budget_items()
    
    # 总结
    print("\n" + "="*60)
    print("  测试数据生成完成")
    print("="*60)
    print(f"  事件: {total_events} 个")
    print(f"  任务: {total_tasks} 个")
    print(f"  检查清单模板: {total_checklists} 个")
    print(f"  预算项目: {total_budgets} 个")
    print()
    print("✓ 测试数据生成完成！")
    print("✓ EventPilot系统现在有足够的数据用于演示和测试")
    print("="*60)

if __name__ == "__main__":
    main()
