#!/usr/bin/env python3
"""验证编辑功能 - 修改实际内容"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_edit_with_real_change():
    """测试活动编辑 - 修改描述来触发真正的更新"""
    print("=" * 60)
    print("EventPilot 编辑功能验证 (真实修改)")
    print("=" * 60)
    
    # 1. 登录
    print("\n[1] 登录...")
    login_resp = requests.post(f"{BASE_URL}/api/users/auth/login/", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_resp.status_code not in [200, 201]:
        print(f"❌ 登录失败: {login_resp.status_code}")
        return
    
    token = login_resp.json().get('data', {}).get('token', '')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ 登录成功")
    
    # 2. 获取活动列表
    print("\n[2] 获取活动列表...")
    events_resp = requests.get(f"{BASE_URL}/api/events/events/", headers=headers)
    events = events_resp.json().get('results', [])
    
    if not events:
        print("❌ 无活动数据")
        return
    
    # 找一个策划中或执行中的活动
    editable_event = None
    for event in events:
        if event['status'] in ['planning', 'executing']:
            editable_event = event
            break
    
    if not editable_event:
        print("⚠️ 使用第一个活动")
        editable_event = events[0]
    
    event_id = editable_event['id']
    original_desc = editable_event.get('description') or ''
    timestamp = int(time.time())
    
    print(f"✅ 选择活动: {editable_event['name']} (状态: {editable_event['status']})")
    print(f"   原始描述: {original_desc[:50] if original_desc else '(空)'}")
    
    # 3. 测试更新 - 修改描述以确保触发更新
    print("\n[3] 更新活动 (修改描述)...")
    new_desc = f"自动化验证-{timestamp}"
    update_data = {
        "name": editable_event['name'],
        "type": editable_event.get('type', 'conference'),
        "status": editable_event['status'],
        "start_date": editable_event.get('start_date'),
        "end_date": editable_event.get('end_date') or '2026-07-01T18:00:00',
        "estimated_budget": int(float(editable_event.get('estimated_budget', 1000) or 1000)) + 1,  # 微调预算
        "description": new_desc  # 修改描述
    }
    
    print(f"   新描述: {new_desc}")
    print(f"   结束时间: {update_data['end_date']}")
    print(f"   预算: ￥{update_data['estimated_budget']}")
    
    update_resp = requests.put(
        f"{BASE_URL}/api/events/events/{event_id}/",
        headers=headers,
        json=update_data
    )
    
    print(f"\n   状态码: {update_resp.status_code}")
    
    if update_resp.status_code == 200:
        result = update_resp.json()
        print("✅✅✅ 更新成功!")
        print(f"   活动名称: {result.get('name')}")
        print(f"   预算: ￥{result.get('estimated_budget', 'N/A')}")
        print(f"   描述: {result.get('description', '')[:50]}")
        
        # 验证 end_date 字段
        if result.get('end_date'):
            print(f"   ✅ 结束时间已保存: {result.get('end_date')}")
        else:
            print(f"   ⚠️ 结束时间为空")
            
    elif update_resp.status_code == 204:
        print("✅ 更新成功 (204 No Content)")
        
    elif update_resp.status_code == 400:
        error_data = update_resp.json()
        error_str = json.dumps(error_data, ensure_ascii=False)
        print(f"❌ 400 错误:")
        print(f"   {error_str}")
        
        # 详细分析错误原因
        if 'end_date' in error_str and ('required' in error_str or '必填' in error_str):
            print("\n   🔴 根本原因: end_date 字段缺失或格式错误")
            print("   💡 解决方案: 确保前端提交包含 end_date 字段")
        elif 'estimated_budget' in error_str or 'budget' in error_str:
            print("\n   🔴 根本原因: 预算字段名称不匹配")
            print("   💡 解决方案: 使用 estimated_budget 而非 budget")
        elif 'status' in error_str or 'UPDATE_ERROR' in error_str:
            print("\n   🟡 原因: 业务规则限制或数据未变化")
            print("   💡 这不是字段名问题，而是业务逻辑")
        else:
            print("\n   🟡 其他原因，需要进一步分析")
            
    else:
        print(f"❌ 更新失败: {update_resp.status_code}")
        print(f"   响应: {update_resp.text[:300]}")
    
    # 4. 恢复原始描述
    print("\n[4] 恢复原始数据...")
    restore_data = {
        "name": editable_event['name'],
        "type": editable_event.get('type', 'conference'),
        "status": editable_event['status'],
        "start_date": editable_event.get('start_date'),
        "end_date": editable_event.get('end_date'),
        "estimated_budget": editable_event.get('estimated_budget', 1000),
        "description": original_desc
    }
    
    restore_resp = requests.put(
        f"{BASE_URL}/api/events/events/{event_id}/",
        headers=headers,
        json=restore_data
    )
    
    if restore_resp.status_code in [200, 204]:
        print("✅ 已恢复原始数据")
    else:
        print("⚠️ 恢复失败（可手动恢复）")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_edit_with_real_change()