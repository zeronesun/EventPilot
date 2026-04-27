#!/usr/bin/env python3
"""
测试JWT登录和权限
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=== JWT认证测试 ===\n")

# 登录获取token
login_resp = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
print(f"登录状态: {login_resp.status_code}")

if login_resp.status_code == 200:
    data = login_resp.json()
    print(f"Token类型: {type(data.get('access'))}")
    print(f"Token前50字符: {data.get('access', '')[:50] if data.get('access') else 'N/A'}")
    
    # 尝试访问profiles
    token = data.get('access')
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/profiles/", headers=headers)
    print(f"\nGET /profiles/ 状态: {r.status_code}")
    
    # 尝试创建
    r2 = requests.post(f"{BASE_URL}/profiles/", headers=headers, json={
        "name": "测试",
        "role": "supplier"
    })
    print(f"POST /profiles/ 状态: {r2.status_code}")
    if r2.status_code != 201:
        print(f"响应: {r2.text[:200]}")
else:
    print(f"登录失败: {login_resp.text[:200]}")
