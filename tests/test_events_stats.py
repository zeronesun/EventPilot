#!/usr/bin/env python3
"""
Events 统计和完成功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_events_stats_and_complete():
    """测试Events统计和完成功能"""

    print("="*60)
    print("Events 统计和完成功能测试")
    print("="*60)

    # 1. 登录
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text}")
        return False
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取活动
    print("\n2. 获取测试活动:")
    r = requests.get(f"{BASE_URL}/events/events/", headers=headers)
    if r.status_code != 200:
        print("❌ 无法获取活动")
        return False
    
    events_data = r.json()
    results = events_data['results'] if 'results' in events_data else events_data
    if not results:
        print("❌ 没有可用活动")
        return False
    
    event = results[0]
    event_id = event.get('id')
    print(f"✅ 使用活动: {event_id}")

    # 3. 测试统计端点
    print("\n3. 测试活动统计端点:")
    r = requests.get(f"{BASE_URL}/events/events/{event_id}/statistics/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        stats = r.json()
        print(f"✅ 统计数据正常 (包含 {len(str(stats))} 字节)")
        print(f"   任务总数: {stats.get('tasks', {}).get('total', 0)}")
        print(f"   预算状态: {stats.get('budget', {}).get('status', 'unknown')}")
    else:
        print(f"❌ 统计端点失败: {r.text}")

    # 4. 测试风险评估端点
    print("\n4. 测试风险评估端点:")
    r = requests.get(f"{BASE_URL}/events/events/{event_id}/risk/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        risk = r.json()
        risk_level = risk.get('level', 'unknown')
        print(f"✅ 风险评估正常")
        print(f"   风险等级: {risk_level}")
        print(f"   影响因素: {len(risk.get('factors', []))} 个")
    else:
        print(f"❌ 风险评估失败: {r.text}")

    # 5. 查找一个非完成状态的活动测试完成功能
    print("\n5. 查找适合的测试活动（非已完成状态）:")
    r = requests.get(f"{BASE_URL}/events/events/", headers=headers)
    if r.status_code == 200:
        events = r.json()['results']
        candidate_event = None
        for ev in events:
            if ev.get('status') not in ['completed', 'cancelled']:
                candidate_event = ev
                break
        
        if candidate_event:
            test_event_id = candidate_event['id']
            print(f"✅ 找到活动: {test_event_id} (状态: {candidate_event.get('status')})")
            
            # 测试完成端点
            r = requests.post(f"{BASE_URL}/events/events/{test_event_id}/complete/", headers=headers)
            print(f"\n6. 测试活动完成端点:")
            print(f"   状态码: {r.status_code}")
            if r.status_code == 200:
                result = r.json()
                print(f"✅ 活动完成成功")
            else:
                print(f"⚠️  完成失败（可能状态不符合要求）: {str(r.text)[:100]}")
        else:
            print("⚠️  没有找到合适的活动（所有活动都已完成或取消）")

    print("\n" + "="*60)
    print("✅ Events 统计和完成功能测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_events_stats_and_complete()
