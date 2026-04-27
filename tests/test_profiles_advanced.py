#!/usr/bin/env python3
"""
Profiles高级功能API测试
"""
import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api"

# 登录
login = requests.post(f"{BASE_URL}/auth/login/", json={"username": "admin"...[truncated]