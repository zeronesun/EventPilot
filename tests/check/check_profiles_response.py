#!/usr/bin/env python3
"""
检查Profiles API响应结构
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

login_resp = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
token = login_resp.json()['data']['token']
headers = {"Authorization": f"Bearer {token}"}

print("=== 检查Profiles响应结构 ===\n")

# 创建
create_resp = requests.post(f"{BASE_URL}/profiles/", headers=headers, json={
    "name": "测试",
    "profile_type": "supplier"
})
print(f"Create响应keys: {list(create_resp.json().keys())}")
print(f"Create完整: {json.dumps(create_resp.json(), indent=2, ensure_ascii=False)}")

# 列表
list_resp = requests.get(f"{BASE_URL}/profiles/", headers=headers)
print(f"\nList响应: {list_resp.json()}")
