#!/usr/bin/env python3
"""
检查登录响应结构
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

login_resp = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
print(f"状态码: {login_resp.status_code}")
data = login_resp.json()
print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
