#!/usr/bin/env python3
"""
EventPilot 快速测试数据生成
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def get_token():
    """获取访问token"""
    try:
        response = requests.post(f"{BASE_URL}/api/users/auth/login/", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code in [200, 201]:
            return response.json()['data']['token']
    except:
        pass
    return None

def create_sample_data():
    """创建示例数据"""
    token = get_token()
    if not token:
        print("✗ 无法获取token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    print("✓ 已获取访问token")
    
    # 1. 创建事件
    print("\n创建测试事件...")
    events = [
        {
            "name": "2024年度科技创新峰会",
            "type": "conference",
            "description": "一年一度的科技行业盛会",
            "start_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%dT09:00:00Z"),
            "end_date": (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%dT18:00:00Z"),
            "status": "planning"
        },
        {
            "name": "新产品发布会",
            "type": "corporate_event",
            "description": "公司季度产品发布会",
            "start_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT14:00:00Z"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT17:00:00Z"),
            "status": "executing"
        },
        {
            "name": "秋季客户答谢会",
            "type": "festival",
            "description": "VIP客户答谢活动",
            "start_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%dT10:00:00Z"),
            "end_date": (datetime.now() + timedelta(days=91)).strftime("%Y-%m-%dT16:00:00Z"),
            "status": "planning"
        }
    ]
    
    event_ids = []
    for i, event_data in enumerate(events):
        try:
            response = requests.post(f"{BASE_URL}/api/events/events/",
                                   json=event_data,
                                   headers=headers)
            if response.status_code in [200, 201]:
                result = response.json()
                event_id = result.get('id') or result.get('data', {}).get('id')
                if event_id:
                    event_ids.append(event_id)
                    print(f"✓ 创建事件: {event_data['name']}")
                else:
                    print(f"✗ 事件创建失败: {event_data['name']}")
            else:
                print(f"✗ 事件创建失败 (HTTP {response.status_code}): {event_data['name']}")
        except Exception as e:
            print(f"✗ 事件创建异常: {event_data['name']} - {e}")
    
    # 2. 创建任务
    print("\n创建测试任务...")
    if event_ids:
        task_types = ["planning", "guest", "material", "venue", "promotion"]
        
        for i in range(15):
            event_id = event_ids[i % len(event_ids)]
            task_type = task_types[i % len(task_types)]
            
            task_data = {
                "title": f"{task_type}任务-{i+1}",
                "description": "自动化生成的测试任务",
                "task_type": task_type,
                "start_date": (datetime.now() + timedelta(days=10+i)).strftime("%Y-%m-%dT09:00:00Z"),
                "due_date": (datetime.now() + timedelta(days=15+i)).strftime("%Y-%m-%dT18:00:00Z")
            }
            
            try:
                response = requests.post(f"{BASE_URL}/api/tasks/tasks/",
                                       json=task_data,
                                       headers=headers)
                if response.status_code in [200, 201]:
                    print(f"✓ 创建任务: {task_data['title']}")
                else:
                    print(f"✗ 任务创建失败 (HTTP {response.status_code})")
            except Exception as e:
                print(f"✗ 任务创建异常: {e}")
    
    # 3. 创建检查清单模板
    print("\n创建检查清单模板...")
    templates = [
        {
            "name": "活动现场标准检查清单",
            "description": "活动现场执行标准流程",
            "checklist_type": "during_event",
            "event_types": ["conference", "festival"]
        },
        {
            "name": "活动策划阶段检查",
            "description": "活动策划前期准备工作检查",
            "checklist_type": "pre_event",
            "event_types": ["conference", "corporate_event"]
        }
    ]
    
    for template_data in templates:
        try:
            response = requests.post(f"{BASE_URL}/api/checklists/templates/",
                                   json=template_data,
                                   headers=headers)
            if response.status_code in [200, 201]:
                print(f"✓ 创建检查清单: {template_data['name']}")
            else:
                print(f"✗ 检查清单创建失败")
        except Exception as e:
            print(f"✗ 检查清单创建异常: {e}")
    
    # 4. 显示数据统计
    print("\n" + "="*60)
    print("数据统计")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/events/events/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"事件总数: {data.get('count', 0)}")
    except:
        print("事件总数: 查询失败")
    
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/tasks/", headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if 'data' in data and 'count' in data['data']:
                count = data['data']['count']
            elif 'count' in data:
                count = data['count']
            else:
                count = len(data.get('results', []))
            print(f"任务总数: {count}")
    except:
        print("任务总数: 查询失败")
    
    print("\n✓ 测试数据生成完成！")

if __name__ == "__main__":
    print("="*60)
    print("EventPilot 快速测试数据生成器")
    print("="*60)
    create_sample_data()
