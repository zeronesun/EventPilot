#!/usr/bin/env python3
"""
直接API测试验证event字段问题
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 登录
login = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
data = login.json()
token = data.get('data', {}).get('token', data.get('token', ''))
headers = {"Authorization": f"Bearer {token}"}

# 1. 只发送event字段，不发送其他字段
minimal_data = {
    "event": "08f5a543-a686-4d41-8f9b-9dd19badd2b5"
}

print("=== 测试1: 只有event字段 ===")
r = requests.post(f"{BASE_URL}/instances/", json=minimal_data, headers=headers)
print(f"状态码: {r.status_code}")
if r.status_code != 200:
    print(f"响应: {r.text[:500]}")

# 2. 发送完整字段（原始测试）
full_data = {
    "template": "f2843499-016d-463a-a24e-6898389aacc9",
    "event": "08f5a543-a686-4d41-8f9b-9dd19badd2b5",
    "name": "测试实例",
    "status": "in_progress"
}

print("\n=== 测试2: 完整字段 ===")
r = requests.post(f"{BASE_URL}/instances/", json=full_data, headers=headers)
print(f"状态码: {r.status_code}")
if r.status_code != 200:
    print(f"响应: {r.text[:500]}")

# 3. 使用整数ID（如果存在）
print("\n=== 测试3: 测试用event_id ===")
data_with_id = {
    "event_id": "08f5a543-a686-4d41-8f9b-9dd19badd2b5"
}
r = requests.post(f"{BASE_URL}/instances/", json=data_with_id, headers=headers)
print(f"状态码: {r.status_code}")
if r.status_code != 200:
    print(f"响应: {r.text[:500]}")
