#!/usr/bin/env python3
"""
测试JWT登录和权限
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=== JWT认证测试 ===\n")

# 登录获取token
login_resp = requests.post(f"{BASE_URL}/users/auth/login/", json={"username": "admin", "password": "admin123"})
print(f"登录状态: {login_resp.status_code}")

if login_resp.status_code in [200, 201]:
    data = login_resp.json()
    print(f"响应keys: {list(data.keys())}")
    
    # 尝试多种token结构
    token = None
    if 'access' in data:
        token = data['access']
    elif 'data' in data and 'access' in data['data']:
        token = data['data']['access']
    elif 'token' in data:
        token = data['token']
    
    print(f"Token: {'Found' if token else 'Not Found'}")
    if token:
        print(f"Token前50字符: {token[:50]}")
        
        # 尝试访问profiles
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/profiles/profiles/", headers=headers)
        print(f"\nGET /profiles/profiles/ 状态: {r.status_code}")
        if r.status_code == 200:
            print(f" profiles数量: {len(r.json())}")
        
        # 尝试创建
        r2 = requests.post(f"{BASE_URL}/profiles/profiles/", headers=headers, json={
            "name": "测试",
            "role": "supplier"
        })
        print(f"POST /profiles/profiles/ 状态: {r2.status_code}")
        if r2.status_code != 201:
            print(f"响应: {r2.text[:200]}")
else:
    print(f"登录失败: {login_resp.text[:200]}")
