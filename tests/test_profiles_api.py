#!/usr/bin/env python3
"""
Profiles高级功能API测试
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 登录
print("=== Profiles高级功能测试 ===\n")
login_resp = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
token = login_resp.json().get('access')

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. 创建测试档案
print("1. 创建测试档案:")
create_data = {
    "name": "测试供应商",
    "role": "supplier",
    "contact": {
        "name": "张三",
        "phone": "13800138000",
        "email": "test@example.com"
    }
}
r = requests.post(f"{BASE_URL}/profiles/", headers=headers, json=create_data)
profile_id = r.json().get('id') if r.status_code == 201 else None
print(f"   状态: {r.status_code}")
if profile_id:
    print(f"   档案ID: {profile_id}")

# 2. 测试contacts（列表）
print("\n2. 测试 /profiles/{id}/contacts/:")
if profile_id:
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/contacts/", headers=headers)
    print(f"   状态: {r.status_code}")
    if r.status_code == 200:
        print(f"   联系人列表: {r.json()}")

# 3. 测试add contact
print("\n3. 测试 /profiles/{id}/contact/:")
if profile_id:
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/contact/", headers=headers, json={
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com"
    })
    print(f"   状态: {r.status_code}")
    contact_id = r.json().get('id') if r.status_code == 201 else None

# 4. 测试interactions
print("\n4. 测试 /profiles/{id}/interactions/:")
if profile_id:
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/interactions/", headers=headers)
    print(f"   状态: {r.status_code}")

# 5. 测试add interaction
print("\n5. 测试 /profiles/{id}/interaction/:")
if profile_id:
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/interaction/", headers=headers, json={
        "interaction_type": "email",
        "content": "邮件沟通",
        "outcome": "pending"
    })
    print(f"   状态: {r.status_code}")

# 6. 测试evaluations
print("\n6. 测试 /profiles/{id}/evaluations/:")
if profile_id:
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/evaluations/", headers=headers)
    print(f"   状态: {r.status_code}")

# 7. 测试add evaluation
print("\n7. 测试 /profiles/{id}/evaluation/:")
if profile_id:
    r = requests.post(f"{BASE_URL}/profiles/{profile_id}/evaluation/", headers=headers, json={
        "category": "quality",
        "score": 85,
        "period": "q1",
        "comments": "质量良好"
    })
    print(f"   状态: {r.status_code}")

# 8. 测试综合评估
print("\n8. 测试 /profiles/{id}/comprehensive_assessment/:")
if profile_id:
    r = requests.get(f"{BASE_URL}/profiles/{profile_id}/comprehensive_assessment/", headers=headers)
    print(f"   状态: {r.status_code}")
    if r.status_code == 200:
        print(f"   评估结果: {r.json()}")
