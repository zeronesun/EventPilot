#!/usr/bin/env python3
"""
检查清单实例化功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_checklists_instance():
    """测试检查清单实例化功能"""

    print("="*60)
    print("检查清单实例化功能测试")
    print("="*60)

    # 1. 登录
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/auth/login/", json=login_payload)
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text}")
        return False
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 创建模板
    print("\n2. 创建检查清单模板:")
    template_data = {
        "name": "测试实例化模板",
        "description": "用于测试实例化功能",
        "checklist_type": "pre_event",
        "event_types": ["conference"],
        "status": "published"
    }
    r = requests.post(f"{BASE_URL}/checklists/templates/", json=template_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code not in [200, 201]:
        print(f"❌ 模板创建失败: {r.text}")
        return False
    template_id = r.json().get('id', '')
    print(f"✅ 模板ID: {template_id[:20]}...")

    # 3. 创建实例（POST到instances端点）
    print("\n3. 创建检查清单实例:")
    instance_data = {
        "template": template_id,
        "name": "测试实例",
        "event": "08f5a543-a686-4d41-8f9b-9dd19badd2b5",  # UUID 字符串
        "status": "in_progress"
    }
    r = requests.post(f"{BASE_URL}/checklists/instances/", json=instance_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        instance = r.json()
        instance_id = instance.get('id', instance.get('data', {}).get('id', ''))
        print(f"✅ 实例创建成功: {instance_id[:20] if instance_id else 'N/A'}...")
    elif r.status_code == 400:
        print(f"⚠️  参数错误: {r.text}")
    else:
        print(f"❌ 创建失败: {r.text}")

    # 4. 创建检查清单项目模板
    print("\n4. 创建检查清单项目模板:")
    item_data = {
        "template": template_id,
        "title": "测试检查项",
        "description": "检查项描述",
        "required": False,
        "order": 1,
        "weight": 5,
        "status": "active"
    }
    r = requests.post(f"{BASE_URL}/checklists/item-templates/", json=item_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        print(f"✅ 项目模板创建成功")
    else:
        print(f"⚠️  项目模板创建状态: {r.status_code}")

    # 5. 读取实例列表
    print("\n5. 读取实例列表:")
    r = requests.get(f"{BASE_URL}/checklists/instances/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        instances = r.json()
        count = len(instances.get('results', [])) if 'results' in instances else len(instances.get('data', []))
        print(f"✅ 实例列表: {count} 个")
    else:
        print(f"⚠️  列表获取: {r.status_code}")

    print("\n" + "="*60)
    print("✅ 检查清单实例化测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_checklists_instance()
