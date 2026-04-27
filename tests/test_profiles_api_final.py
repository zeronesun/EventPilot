#!/usr/bin/env python3
"""
Profiles高级功能API测试（完整版）
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=== Profiles高级功能测试 ===\n")

# 登录获取token
login_resp = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
token = login_resp.json()['data']['token']

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. 创建测试档案
print("1. 创建测试档案:")
create_data = {
    "name": "测试供应商",
    "profile_type": "supplier",
    "contact_info": {
        "name": "张三",
        "phone": "13800138000",
        "email": "test@example.com"
    }
}
r = requests.post(f"{BASE_URL}/profiles/", headers=headers, json=create_data)
print(f"   状态: {r.status_code}")
if r.status_code in [200, 201]:
    data = r.json()
    profile_id = data.get('id')
    print(f"   档案ID: {profile_id}")
else:
    print(f"   错误: {r.text[:200]}")
    profile_id = None

# 如果创建成功，继续测试
if profile_id:
    # 2. 测试contacts（列表）
    print("\n2. 测试 /profiles/{id}/contacts/:")
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/contacts/", headers=headers)
    print(f"   状态: {r.status_code}")

    # 3. 测试add contact  
    print("\n3. 测试 /profiles/{id}/contact/:")
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/contact/", headers=headers, json={
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com"
    })
    print(f"   状态: {r.status_code}")

    # 4. 测试interactions
    print("\n4. 测试 /profiles/{id}/interactions/:")
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/interactions/", headers=headers)
    print(f"   状态: {r.status_code}")

    # 5. 测试add interaction
    print("\n5. 测试 /profiles/{id}/interaction/:")
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/interaction/", headers=headers, json={
        "interaction_type": "email",
        "content": "邮件沟通",
        "outcome": "pending"
    })
    print(f"   状态: {r.status_code}")

    # 6. 测试evaluations
    print("\n6. 测试 /profiles/{id}/evaluations/:")
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/evaluations/", headers=headers)
    print(f"   状态: {r.status_code}")

    # 7. 测试add evaluation
    print("\n7. 测试 /profiles/{id}/evaluation/:")
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/evaluation/", headers=headers, json={
        "category": "quality",
        "score": 85,
        "period": "q1",
        "comments": "质量良好"
    })
    print(f"   状态: {r.status_code}")

    # 8. 测试综合评估
    print("\n8. 测试 /profiles/{id}/comprehensive_assessment/:")
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/comprehensive_assessment/", headers=headers)
    print(f"   状态: {r.status_code}")
    if r.status_code == 200:
        print(f"   结果: {r.json()}")

print("\n=== 测试完成 ===")
