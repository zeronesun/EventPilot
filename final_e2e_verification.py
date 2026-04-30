#!/usr/bin/env python3
"""
EventPilot 端到端功能验证脚本
验证所有关键功能是否正常工作
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TOKEN = ""
HEADERS = {}
USER_ID = ""

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def test_login():
    print_section("1. 用户认证测试")
    print("登录 admin/admin123...")
    
    response = requests.post(
        f"{BASE_URL}/api/users/auth/login/",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        global TOKEN, USER_ID, HEADERS
        TOKEN = data['data']['token']
        USER_ID = data['data']['user']['id']
        HEADERS = {'Authorization': f'Bearer {TOKEN}'}
        print_success("登录成功")
        print(f"  获取Token: {TOKEN[:50]}...")
        return True
    else:
        print_error(f"登录失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return False

def test_checklists():
    print_section("2. 检查清单模板功能测试")
    
    # 创建检查清单模板
    print("创建检查清单模板...")
    template_data = {
        "name": "E2E测试检查清单",
        "description": "端到端功能验证测试",
        "checklist_type": "pre_event",
        "event_types": ["conference"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/checklists/templates/",
        json=template_data,
        headers=HEADERS
    )
    
    if response.status_code in [200, 201]:
        template = response.json()
        print_success(f"创建成功，响应: {str(template)[:100]}")
        
        # 读取检查清单模板
        print("读取检查清单模板...")
        response = requests.get(f"{BASE_URL}/api/checklists/templates/", headers=HEADERS)
        if response.status_code in [200, 201]:
            templates = response.json()
            print_success(f"读取成功，响应内容: {str(templates)[:100]}")
            return True
        else:
            print_error(f"读取失败: {response.status_code}")
            return False
    else:
        print_error(f"创建失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return False

def test_tasks():
    print_section("3. 任务管理功能测试")
    
    # 首先创建一个事件来关联任务
    print("创建关联事件...")
    event_data = {
        "name": "E2E测试事件",
        "type": "conference",
        "description": "端到端功能验证测试事件",
        "start_date": "2024-12-01T00:00:00Z",
        "end_date": "2024-12-02T00:00:00Z",
        "status": "planning"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/events/events/",
        json=event_data,
        headers=HEADERS
    )

    event_id = None
    if response.status_code in [200, 201]:
        event_json = response.json()
        event_id = event_json.get('id') or (event_json.get('results', [{}])[0].get('id') if isinstance(event_json, dict) else None)
        print_success(f"事件创建成功，ID: {event_id}")
    else:
        print_error(f"事件创建失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        # 继续测试读取功能
    
    # 创建任务
    print("创建任务...")
    task_data = {
        "title": "E2E测试任务",
        "description": "端到端功能验证测试任务",
        "task_type": "planning"
    }
    
    if event_id:
        task_data["event_id"] = str(event_id)
    
    response = requests.post(
        f"{BASE_URL}/api/tasks/tasks/",
        json=task_data,
        headers=HEADERS
    )
    
    if response.status_code in [200, 201]:
        print_success("任务创建成功")
        
        # 读取任务列表
        print("读取任务列表...")
        response = requests.get(f"{BASE_URL}/api/tasks/tasks/", headers=HEADERS)
        if response.status_code in [200, 201]:
            tasks = response.json()
            print_success(f"读取成功，响应内容: {str(tasks)[:100]}")
            return True
        else:
            print_error(f"读取失败: {response.status_code}")
            return False
    else:
        print_error(f"创建失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return False

def test_events():
    print_section("4. 事件管理功能测试")
    
    # 创建事件
    print("创建事件...")
    event_data = {
        "name": "E2E测试事件",
        "type": "conference",
        "description": "端到端功能验证测试事件",
        "start_date": "2024-12-01T00:00:00Z",
        "end_date": "2024-12-02T00:00:00Z",
        "status": "planning"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/events/events/",
        json=event_data,
        headers=HEADERS
    )
    
    if response.status_code in [200, 201]:
        print_success("事件创建成功")
        
        # 读取事件列表
        print("读取事件列表...")
        response = requests.get(f"{BASE_URL}/api/events/events/", headers=HEADERS)
        if response.status_code in [200, 201]:
            events = response.json()
            print_success(f"读取成功，响应内容: {str(events)[:100]}")
            return True
        else:
            print_error(f"读取失败: {response.status_code}")
            return False
    else:
        print_error(f"创建失败: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return False

def test_health():
    print_section("5. 系统健康检查")
    
    print("检查健康端点...")
    response = requests.get(f"{BASE_URL}/api/health/")
    if response.status_code in [200, 201]:
        print_success("健康检查通过")
        print(f"  响应: {response.text[:100]}")
        return True
    else:
        print_error(f"健康检查失败: {response.status_code}")
        return False

def main():
    print("\n" + "="*60)
    print("  EventPilot 端到端功能验证")
    print("  开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = []
    
    # 测试1: 登录
    results.append(("用户认证", test_login()))
    
    if not results[-1][1]:
        print_error("登录失败，无法继续测试")
        sys.exit(1)
    
    # 测试2: 健康检查
    results.append(("健康检查", test_health()))
    
    # 测试3: 检查清单
    results.append(("检查清单功能", test_checklists()))
    
    # 测试4: 任务管理
    results.append(("任务管理功能", test_tasks()))
    
    # 测试5: 事件管理
    results.append(("事件管理功能", test_events()))
    
    # 总结
    print_section("测试结果总结")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  总测试数: {len(results)}")
    print(f"  通过数: {sum(1 for _, r in results if r)}")
    print(f"  失败数: {sum(1 for _, r in results if not r)}")
    print()
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    print()
    if all_passed:
        print_success("所有测试通过！ EventPilot 基础功能验证成功")
        print_success("可以进入下一阶段开发或部署")
    else:
        print_error("部分测试失败，需要进一步调试")
    
    print("="*60)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
