#!/usr/bin/env python3
"""
测试首页统计端点
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# 登录
login = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
data = login.json()
token = data.get('data', {}).get('token', data.get('token', ''))
headers = {"Authorization": f"Bearer {token}"}

print("=== 首页统计测试 ===")
r = requests.get(f"{BASE_URL}/dashboard/stats/", headers=headers)
print(f"状态码: {r.status_code}")
if r.status_code == 200:
    stats = r.json()
    print(f"✅ 成功: {json.dumps(stats, indent=2, ensure_ascii=False)}")
else:
    print(f"❌ 失败: {r.text}")
