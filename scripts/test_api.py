#!/usr/bin/env python3
import json
import requests
import sys

BASE_URL = "http://172.28.166.164:8000/api"

def test_api():
    # Login
    print("=" * 80)
    print("Django Python API测试")
    print("=" * 80)

    print("\n1. 测试登录API...")
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 201:
        token = response.json()['data']['token']
        print(f"\nToken: {token[:50]}...")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Test all APIs
        apis = [
            ("tasks", "/tasks/"),
            ("events", "/events/"),
            ("users", "/users/"),
            ("checklists", "/checklists/"),
            ("files", "/files/"),
        ]

        for name, path in apis:
            print(f"\n2.{list(apis).index((name, path)) + 2}. 测试{name}API...")
            response = requests.get(f"{BASE_URL}{path}", headers=headers)
            print(f"状态码: {response.status_code}")
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                except:
                    print(f"响应: {response.text[:200]}")
            else:
                print("响应: (空)")
    else:
        print("\n登录失败!")
        return

    print("=" * 80)

if __name__ == "__main__":
    test_api()
