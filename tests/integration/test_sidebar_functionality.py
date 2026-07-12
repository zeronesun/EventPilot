#!/usr/bin/env python3
"""
测试左栏所有功能模块的API端点
验证每个功能模块的核心API是否正常工作
"""
import os
import sys
import requests
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api"

def test_login():
    """测试登录功能"""
    print("\n" + "="*60)
    print("测试1: 用户登录")
    print("="*60)
    
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
    print(f"状态码: {r.status_code}")
    
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text[:200]}")
        return None
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    
    if not token:
        print(f"❌ 无法获取Token: {data}")
        return None
    
    print(f"✅ 登录成功 (Token前50字符): {token[:50]}...")
    return token

def test_dashboard(token):
    """测试工作台/仪表盘"""
    print("\n" + "="*60)
    print("测试2: 工作台/仪表盘")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取当前用户信息
    r = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    print(f"GET /users/me/ 状态码: {r.status_code}")
    if r.status_code == 200:
        user = r.json()
        print(f"✅ 当前用户: {user.get('username', 'N/A')}")
    else:
        print(f"❌ 获取用户信息失败: {r.text[:100]}")
    
    # 获取活动统计
    r = requests.get(f"{BASE_URL}/events/", headers=headers, params={"limit": 5})
    print(f"GET /events/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 活动列表: {count} 个活动")
    else:
        print(f"❌ 获取活动列表失败")

def test_events(token):
    """测试活动管理"""
    print("\n" + "="*60)
    print("测试3: 活动管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取活动列表
    r = requests.get(f"{BASE_URL}/events/", headers=headers)
    print(f"GET /events/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        results = data.get('results', data)
        print(f"✅ 活动列表: {len(results)} 个活动")
    else:
        print(f"❌ 获取活动列表失败: {r.text[:100]}")
    
    # 创建测试活动
    start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT10:00:00Z")
    end_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%dT18:00:00Z")
    
    event_payload = {
        "name": "测试活动-功能验证",
        "type": "conference",
        "description": "用于功能验证的测试活动",
        "start_date": start_date,
        "end_date": end_date,
        "status": "planning"
    }
    r = requests.post(f"{BASE_URL}/events/", json=event_payload, headers=headers)
    print(f"POST /events/ 状态码: {r.status_code}")
    if r.status_code == 201:
        event = r.json()
        print(f"✅ 活动创建成功: {event.get('name', 'N/A')}")
        return event.get('id')
    else:
        print(f"❌ 创建活动失败: {r.text[:100]}")
        return None

def test_tasks(token, event_id):
    """测试任务管理"""
    print("\n" + "="*60)
    print("测试4: 任务管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取任务列表
    r = requests.get(f"{BASE_URL}/tasks/", headers=headers)
    print(f"GET /tasks/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 任务列表: {count} 个任务")
    else:
        print(f"❌ 获取任务列表失败: {r.text[:100]}")
    
    # 创建测试任务
    if event_id:
        task_payload = {
            "event_id": event_id,
            "title": "测试任务-功能验证",
            "description": "用于功能验证的测试任务",
            "task_type": "planning"
        }
        r = requests.post(f"{BASE_URL}/tasks/", json=task_payload, headers=headers)
        print(f"POST /tasks/ 状态码: {r.status_code}")
        if r.status_code == 201:
            task = r.json()
            print(f"✅ 任务创建成功: {task.get('title', 'N/A')}")
            return task.get('id')
        else:
            print(f"❌ 创建任务失败: {r.text[:100]}")
    
    return None

def test_users(token):
    """测试用户管理"""
    print("\n" + "="*60)
    print("测试5: 用户管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取用户列表（测试搜索和分页）
    r = requests.get(f"{BASE_URL}/users/", headers=headers, params={"page": 1, "page_size": 20})
    print(f"GET /users/ (分页) 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get('count', len(data.get('results', [])))
        print(f"✅ 用户列表: {count} 个用户")
    else:
        print(f"❌ 获取用户列表失败: {r.text[:100]}")
    
    # 测试搜索功能
    r = requests.get(f"{BASE_URL}/users/", headers=headers, params={"search": "admin"})
    print(f"GET /users/?search=admin 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get('count', len(data.get('results', [])))
        print(f"✅ 搜索结果: {count} 个用户")
    else:
        print(f"❌ 搜索失败: {r.text[:100]}")

def test_checklists(token):
    """测试清单管理"""
    print("\n" + "="*60)
    print("测试6: 清单管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取模板列表
    r = requests.get(f"{BASE_URL}/checklists/templates/", headers=headers)
    print(f"GET /checklists/templates/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 模板列表: {count} 个模板")
    else:
        print(f"❌ 获取模板列表失败: {r.text[:100]}")
    
    # 获取实例列表
    r = requests.get(f"{BASE_URL}/checklists/instances/", headers=headers)
    print(f"GET /checklists/instances/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 实例列表: {count} 个实例")
    else:
        print(f"❌ 获取实例列表失败: {r.text[:100]}")
    
    # 创建测试模板
    template_payload = {
        "name": "测试清单模板-功能验证",
        "description": "用于功能验证的测试模板",
        "checklist_type": "pre_event",
        "event_types": ["conference"],
        "status": "draft"
    }
    r = requests.post(f"{BASE_URL}/checklists/templates/", json=template_payload, headers=headers)
    print(f"POST /checklists/templates/ 状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        template = r.json()
        print(f"✅ 模板创建成功: {template.get('name', 'N/A')}")
        return template.get('id')
    else:
        print(f"❌ 创建模板失败: {r.text[:100]}")
        return None

def test_files(token):
    """测试文件管理"""
    print("\n" + "="*60)
    print("测试7: 文件管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取文件列表
    r = requests.get(f"{BASE_URL}/files/", headers=headers)
    print(f"GET /files/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get('total', len(data.get('files', [])))
        print(f"✅ 文件列表: {count} 个文件")
    else:
        print(f"❌ 获取文件列表失败: {r.text[:100]}")
    
    # 获取文件统计
    r = requests.get(f"{BASE_URL}/files/stats/", headers=headers)
    print(f"GET /files/stats/ 状态码: {r.status_code}")
    if r.status_code == 200:
        stats = r.json()
        print(f"✅ 文件统计: {stats.get('total_files', 0)} 个文件")
    else:
        print(f"❌ 获取文件统计失败: {r.text[:100]}")

def test_budget(token, event_id):
    """测试预算管理"""
    print("\n" + "="*60)
    print("测试8: 预算管理")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if event_id:
        # 获取活动预算
        r = requests.get(f"{BASE_URL}/events/{event_id}/", headers=headers)
        print(f"GET /events/{event_id}/ 状态码: {r.status_code}")
        if r.status_code == 200:
            event = r.json()
            print(f"✅ 活动预算: 预计 {event.get('estimated_budget', 0)} 元")
        else:
            print(f"❌ 获取活动失败: {r.text[:100]}")
    else:
        print("⚠️  跳过预算测试（需要活动ID）")

def test_profiles(token):
    """测试关联方档案"""
    print("\n" + "="*60)
    print("测试9: 关联方档案")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取关联方列表
    r = requests.get(f"{BASE_URL}/profiles/", headers=headers)
    print(f"GET /profiles/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 关联方列表: {count} 个")
    else:
        print(f"❌ 获取关联方列表失败: {r.text[:100]}")
    
    # 创建测试关联方
    profile_payload = {
        "name": "测试关联方-功能验证",
        "profile_type": "supplier",
        "company_name": "测试公司"
    }
    r = requests.post(f"{BASE_URL}/profiles/", json=profile_payload, headers=headers)
    print(f"POST /profiles/ 状态码: {r.status_code}")
    if r.status_code == 201:
        profile = r.json()
        print(f"✅ 关联方创建成功: {profile.get('name', 'N/A')}")
    else:
        print(f"❌ 创建关联方失败: {r.text[:100]}")

def test_knowledge(token):
    """测试知识库"""
    print("\n" + "="*60)
    print("测试10: 知识库")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取知识条目列表
    r = requests.get(f"{BASE_URL}/knowledge/", headers=headers)
    print(f"GET /knowledge/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 知识条目: {count} 条")
    else:
        print(f"❌ 获取知识条目失败: {r.text[:100]}")

def test_reviews(token, event_id):
    """测试活动复盘"""
    print("\n" + "="*60)
    print("测试11: 活动复盘")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取复盘列表
    r = requests.get(f"{BASE_URL}/reviews/", headers=headers)
    print(f"GET /reviews/ 状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('results', [])) if 'results' in data else len(data)
        print(f"✅ 复盘列表: {count} 个")
    else:
        print(f"❌ 获取复盘列表失败: {r.text[:100]}")

def test_analytics(token):
    """测试数据分析"""
    print("\n" + "="*60)
    print("测试12: 数据分析")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取用户统计
    r = requests.get(f"{BASE_URL}/users/statistics/", headers=headers, params={"days": 30})
    print(f"GET /users/statistics/ 状态码: {r.status_code}")
    if r.status_code == 200:
        stats = r.json()
        print(f"✅ 用户统计: {stats.get('total_users', 0)} 个用户")
    else:
        print(f"❌ 获取用户统计失败: {r.text[:100]}")

def test_settings(token):
    """测试系统设置"""
    print("\n" + "="*60)
    print("测试13: 系统设置")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取当前用户信息（用于设置修改）
    r = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    print(f"GET /users/me/ 状态码: {r.status_code}")
    if r.status_code == 200:
        user = r.json()
        user_id = user.get('id')
        
        # 测试更新用户信息（系统设置中的保存功能）
        update_payload = {
            "email": user.get('email'),
            "first_name": user.get('first_name', '测试'),
            "last_name": user.get('last_name', '用户')
        }
        r = requests.patch(f"{BASE_URL}/users/{user_id}/", json=update_payload, headers=headers)
        print(f"PATCH /users/{user_id}/ 状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ 用户信息更新成功")
        else:
            print(f"❌ 更新用户信息失败: {r.text[:100]}")
    else:
        print(f"❌ 获取用户信息失败: {r.text[:100]}")

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("EventPilot 左栏功能完整性测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API基础URL: {BASE_URL}")
    print("="*60)
    
    # 1. 登录获取Token
    token = test_login()
    if not token:
        print("\n❌ 登录失败，测试无法继续")
        return
    
    # 2. 测试各功能模块
    test_dashboard(token)
    
    event_id = test_events(token)
    
    test_tasks(token, event_id)
    
    test_users(token)
    
    test_checklists(token)
    
    test_files(token)
    
    test_budget(token, event_id)
    
    test_profiles(token)
    
    test_knowledge(token)
    
    test_reviews(token, event_id)
    
    test_analytics(token)
    
    test_settings(token)
    
    print("\n" + "="*60)
    print("✅ 所有功能模块测试完成!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()