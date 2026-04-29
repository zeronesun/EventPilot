#!/usr/bin/env python3
"""
Profiles高级功能API测试（调试版）
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=== Profiles高级功能测试 ===\n")

# 登录获取token
login_resp = requests.post(f"{BASE_URL}/users/auth/login/", json={"username": "admin", "password": "admin123"})
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
r = requests.post(f"{BASE_URL}/profiles/profiles/", headers=headers, json=create_data)
print(f"   状态: {r.status_code}")
response_data = r.json()
print(f"   响应keys: {list(response_data.keys())}")
print(f"   id字段: {response_data.get('id', 'Not found')}")

# 直接使用现有档案进行测试
print("\n获取现有档案:")
r = requests.get(f"{BASE_URL}/profiles/profiles/", headers=headers)
print(f"   状态: {r.status_code}")
if r.status_code == 200 and len(r.json()) > 0:
    profiles = r.json()
    if isinstance(profiles, list):
        profile_id = profiles[0].get('id')
        print(f"   使用档案ID: {profile_id}")
    else:
        profile_id = None
        
    if profile_id:
        # 2. 测试contacts（列表）
        print(f"\n2. 测试 /profiles/profiles/{profile_id}/contacts/:")
        r = requests.get(f"{BASE_URL}/profiles/profiles/{profile_id}/contacts/", headers=headers)
        print(f"   状态: {r.status_code}")

        # 3. 测试add contact  
        print(f"\n3. 测试 /profiles/profiles/{profile_id}/contact/:")
        r = requests.post(f"{BASE_URL}/profiles/profiles/{profile_id}/contact/", headers=headers, json={
            "name": "李四",
            "phone": "13900139000",
            "email": "lisi@example.com"
        })
        print(f"   状态: {r.status_code}")

        # 4. 测试interactions
        print(f"\n4. 测试 /profiles/profiles/{profile_id}/interactions/:")
        r = requests.get(f"{BASE_URL}/profiles/profiles/{profile_id}/interactions/", headers=headers)
        print(f"   状态: {r.status_code}")

        # 5. 测试add interaction
        print(f"\n5. 测试 /profiles/profiles/{profile_id}/interaction/:")
        r = requests.post(f"{BASE_URL}/profiles/profiles/{profile_id}/interaction/", headers=headers, json={
            "interaction_type": "email",
            "content": "邮件沟通",
            "outcome": "pending"
        })
        print(f"   状态: {r.status_code}")

        # 6. 测试evaluations
        print(f"\n6. 测试 /profiles/profiles/{profile_id}/evaluations/:")
        r = requests.get(f"{BASE_URL}/profiles/profiles/{profile_id}/evaluations/", headers=headers)
        print(f"   状态: {r.status_code}")

        # 7. 测试add evaluation
        print(f"\n7. 测试 /profiles/profiles/{profile_id}/evaluation/:")
        r = requests.post(f"{BASE_URL}/profiles/profiles/{profile_id}/evaluation/", headers=headers, json={
            "category": "quality",
            "score": 85,
            "period": "q1",
            "comments": "质量良好"
        })
        print(f"   状态: {r.status_code}")

        # 8. 测试综合评估
        print(f"\n8. 测试 /profiles/profiles/{profile_id}/comprehensive_assessment/:")
        r = requests.get(f"{BASE_URL}/profiles/profiles/{profile_id}/comprehensive_assessment/", headers=headers)
        print(f"   状态: {r.status_code}")

print("\n=== 测试完成 ===")
