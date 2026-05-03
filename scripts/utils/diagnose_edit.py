#!/usr/bin/env python3
"""详细诊断编辑功能"""
import requests
import json

BASE_URL = "http://localhost:8000"

def diagnose_update():
    """详细诊断活动更新问题"""
    print("=" * 60)
    print("EventPilot 编辑功能详细诊断")
    print("=" * 60)
    
    # 1. 登录
    print("\n[1] 登录...")
    login_resp = requests.post(f"{BASE_URL}/api/users/auth/login/", json={
        "username": "admin",
        "password": "admin123"
    })
    
    token = login_resp.json().get('data', {}).get('token', '')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Token: {token[:30]}...")
    
    # 2. 获取活动详情
    print("\n[2] 获取活动详情...")
    events_resp = requests.get(f"{BASE_URL}/api/events/events/", headers=headers)
    events = events_resp.json().get('results', [])
    
    if not events:
        print("❌ 无活动")
        return
    
    event = events[0]
    event_id = event['id']
    
    print(f"活动ID: {event_id}")
    print(f"活动名称: {event['name']}")
    print(f"当前状态: {event['status']}")
    print(f"开始时间: {event.get('start_date')}")
    print(f"结束时间: {event.get('end_date')}")
    print(f"预算: {event.get('estimated_budget')}")
    print(f"描述: {event.get('description', '(空)')[:50]}")
    
    # 3. 尝试更新 - 发送最小数据
    print("\n[3] 尝试更新 (只修改描述)...")
    
    update_data = {
        "description": f"测试描述-{__import__('time').time()}"
    }
    
    print(f"发送数据: {json.dumps(update_data, ensure_ascii=False)}")
    
    update_resp = requests.put(
        f"{BASE_URL}/api/events/events/{event_id}/",
        headers=headers,
        json=update_data
    )
    
    print(f"\n状态码: {update_resp.status_code}")
    print(f"响应头: {dict(update_resp.headers)}")
    print(f"响应内容:")
    try:
        resp_json = update_resp.json()
        print(json.dumps(resp_json, ensure_ascii=False, indent=2))
    except:
        print(update_resp.text)
    
    # 4. 再次获取详情，看是否真的没更新
    print("\n[4] 验证是否更新...")
    detail_resp = requests.get(
        f"{BASE_URL}/api/events/events/{event_id}/",
        headers=headers
    )
    updated_event = detail_resp.json()
    
    print(f"当前描述: {updated_event.get('description', '(空)')[:50]}")
    
    if updated_event.get('description') == update_data['description']:
        print("✅ 描述已更新!")
    else:
        print("❌ 描述未更新")
    
    # 5. 尝试完整字段更新
    print("\n[5] 尝试完整字段更新...")
    full_update = {
        "name": event['name'],
        "type": event.get('type', 'conference'),
        "status": event['status'],
        "start_date": event.get('start_date'),
        "end_date": event.get('end_date') or '2026-12-31T23:59:59',
        "estimated_budget": 9999,
        "description": "完整更新测试"
    }
    
    print(f"发送数据 (关键字段):")
    print(f"  - end_date: {full_update['end_date']}")
    print(f"  - estimated_budget: {full_update['estimated_budget']}")
    print(f"  - description: {full_update['description']}")
    
    full_resp = requests.put(
        f"{BASE_URL}/api/events/events/{event_id}/",
        headers=headers,
        json=full_update
    )
    
    print(f"\n状态码: {full_resp.status_code}")
    if full_resp.status_code == 200:
        result = full_resp.json()
        print("✅ 更新成功!")
        print(f"  返回的 end_date: {result.get('end_date')}")
        print(f"  返回的 estimated_budget: {result.get('estimated_budget')}")
    else:
        print("❌ 更新失败")
        try:
            print(f"  错误: {json.dumps(full_resp.json(), ensure_ascii=False)}")
        except:
            print(f"  响应: {full_resp.text[:200]}")

if __name__ == "__main__":
    diagnose_update()