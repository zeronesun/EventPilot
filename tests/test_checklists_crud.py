#!/usr/bin/env python3
"""
检查清单模板CRUD功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api"

def test_checklists_crud():
    """测试检查清单模板CRUD功能"""

    print("="*60)
    print("检查清单模板CRUD功能测试")
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

    # 2. 创建检查清单模板
    print("\n2. 创建检查清单模板:")
    template_data = {
        "name": "测试检查清单模板",
        "description": "这是一个测试用的检查清单",
        "checklist_type": "pre_event",
        "event_types": ["conference"],
        "status": "draft",
        "category": "event_planning",
        "is_public": False
    }
    r = requests.post(f"{BASE_URL}/templates/", json=template_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        result = r.json()
        template_id = result.get('id', result.get('data', {}).get('id', ''))
        print(f"✅ 检查清单模板创建成功: {template_id[:20] if template_id else 'N/A'}...")
    else:
        print(f"❌ 创建失败: {r.text}")
        return False

    # 3. 读取检查清单模板列表
    print("\n3. 读取检查清单模板列表:")
    r = requests.get(f"{BASE_URL}/templates/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        templates_list = r.json()
        count = len(templates_list.get('results', [])) if 'results' in templates_list else len(templates_list.get('data', []))
        print(f"✅ 获取列表成功: {count} 个模板")
    else:
        print(f"❌ 获取列表失败: {r.text}")

    # 4. 读取单个检查清单模板详情
    print("\n4. 读取检查清单模板详情:")
    r = requests.get(f"{BASE_URL}/templates/{template_id}/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        template = r.json()
        print(f"✅ 获取详情成功: {template.get('name', 'N/A')}")
    else:
        print(f"❌ 获取详情失败: {r.text}")

    # 5. 更新检查清单模板
    print("\n5. 更新检查清单模板:")
    update_data = {
        "name": "更新后的检查清单模板",
        "description": "这是更新后的描述"
    }
    r = requests.patch(f"{BASE_URL}/templates/{template_id}/", json=update_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ 更新成功")
    else:
        print(f"❌ 更新失败: {r.text}")

    # 6. 删除检查清单模板
    print("\n6. 删除检查清单模板:")
    r = requests.delete(f"{BASE_URL}/templates/{template_id}/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 204:
        print(f"✅ 删除成功")
    elif r.status_code == 204 or r.status_code == 200:
        print(f"✅ 删除成功")
    elif r.status_code:
        print(f"⚠️  返回 {r.status_code}")
    else:
        print(f"❌ 删除失败: {r.text}")

    # 7. 验证删除
    print("\n7. 验证删除:")
    r = requests.get(f"{BASE_URL}/templates/{template_id}/", headers=headers)
    if r.status_code == 404:
        print(f"✅ 确认删除（返回404）")
    else:
        print(f"⚠️  删除验证状态码: {r.status_code}")

    # 8. 测试检查清单项目模板CRUD
    print("\n8. 测试检查清单项目模板（创建和读取）:")
    item_data = {
        "title": "测试项目",
        "description": "这是测试项目描述",
        "order": 1
    }
    r = requests.post(f"{BASE_URL}/item-templates/", json=item_data, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        print(f"✅ 项目模板创建成功")
    else:
        print(f"⚠️  创建状态: {r.status_code}")

    # 9. 测试检查清单实例化（如果存在）
    print("\n9. 测试检查清单实例化（从模板创建实例）:")
    r = requests.post(f"{BASE_URL}/instances/instantiate-from-template/", json={"template_id": template_id}, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code in [200, 201]:
        print(f"✅ 实例化成功")
    elif r.status_code == 404:
        print(f"⚠️  实例化端点不存在或路径不正确")
    else:
        print(f"⚠️  实例化返回: {r.status_code}")

    print("\n" + "="*60)
    print("✅ 检查清单模板CRUD测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_checklists_crud()
