#!/usr/bin/env python3
"""
侧边栏导航简单测试（通过HTTP检查）
"""
import requests
import time

BASE_URL = "http://localhost:3000"

routes = [
    ('/', '首页'),
    ('/events', '活动管理'),
    ('/tasks', '任务管理'),
    ('/users', '用户管理'),
    ('/checklists', '清单管理'),
    ('/files', '文件管理'),
    ('/profiles', '关联方档案'),
]

print("=== 侧边栏导航测试 ===\n")

results = []

for path, name in routes:
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, timeout=5)
        status = "✅" if r.status_code == 200 else "❌"
        print(f"{status} {name} ({path}): {r.status_code}")
        results.append((path, name, r.status_code == 200))
    except Exception as e:
        print(f"❌ {name} ({path}): 错误 - {str(e)[:50]}")
        results.append((path, name, False))
    time.sleep(0.3)

print(f"\n总计: {len(results)} 个路由")
print(f"通过: {sum(1 for r in results if r[2])}")
print(f"失败: {sum(1 for r in results if not r[2])}")
