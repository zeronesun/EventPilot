#!/usr/bin/env python3
"""
Phase 3 API端点简化测试
使用requests库测试所有API端点
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# 测试API基础URL
BASE_URL = "http://127.0.0.1:8000/api"

def test_health_check():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ 健康检查 - 状态码: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def get_auth_token():
    """获取认证token"""
    try:
        # 尝试登录获取token
        login_data = {
            "username": "admin",
            "password": "admin123"  # 使用测试环境的默认密码
        }
        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        
        if response.status_code == 200:
            token = response.json().get('access')
            print(f"✅ 获取token成功")
            return token
        else:
            print(f"⚠️ 登录失败，使用测试模式")
            return None
    except Exception as e:
        print(f"⚠️ 获取token失败: {e}，使用测试模式")
        return None

def test_profiles_list(token=None):
    """测试档案列表端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(f"{BASE_URL}/profiles/", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 档案列表端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 档案列表端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 档案列表端点失败: {e}")
        return False

def test_profile_create(token=None):
    """测试档案创建端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # 使用时间戳确保唯一性
        timestamp = int(time.time())
        profile_data = {
            'name': f'Test Company {timestamp}',
            'company_name': f'Test Company Ltd {timestamp}',
            'profile_type': 'supplier',
            'status': 'active',
            'industry': 'Technology',
            'credit_score': 75,
            'quality_score': 80,
            'risk_level': 'low',
            'tags': 'test,supplier,technology'
        }
        
        response = requests.post(f"{BASE_URL}/profiles/", json=profile_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ 档案创建端点 - 状态码: {response.status_code}")
            return response.json().get('id')
        else:
            print(f"❌ 档案创建端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"❌ 档案创建端点失败: {e}")
        return None

def test_recommendations(token=None):
    """测试智能推荐端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        request_data = {
            'event_type': '商务会议',
            'min_credit_score': 60,
            'max_risk_level': 'medium',
            'limit': 5
        }
        
        response = requests.post(f"{BASE_URL}/profiles/recommendations/suppliers/", json=request_data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 智能推荐端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 智能推荐端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 智能推荐端点失败: {e}")
        return False

def test_search(token=None):
    """测试智能搜索端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        search_data = {
            'query': 'technology',
            'profile_type': 'supplier',
            'limit': 10
        }
        
        response = requests.post(f"{BASE_URL}/profiles/search/profiles/", json=search_data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 智能搜索端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 智能搜索端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 智能搜索端点失败: {e}")
        return False

def test_analytics(token=None):
    """测试分析仪表盘端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(f"{BASE_URL}/profiles/analytics/dashboard/", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 分析仪表盘端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 分析仪表盘端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 分析仪表盘端点失败: {e}")
        return False

def test_profile_contacts(profile_id, token=None):
    """测试档案联系人端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(f"{BASE_URL}/profiles/{profile_id}/contacts/", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 档案联系人端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 档案联系人端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 档案联系人端点失败: {e}")
        return False

def test_contact_creation(profile_id, token=None):
    """测试联系人创建端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        contact_data = {
            'name': 'John Doe',
            'position': 'Manager',
            'email': f'john{int(time.time())}@example.com',
            'phone': '+1234567890',
            'is_primary': True
        }
        
        response = requests.post(f"{BASE_URL}/profiles/{profile_id}/contact/", json=contact_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ 联系人创建端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 联系人创建端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 联系人创建端点失败: {e}")
        return False

def test_interactions(profile_id, token=None):
    """测试交互历史端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(f"{BASE_URL}/profiles/{profile_id}/interactions/", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ 交互历史端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 交互历史端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 交互历史端点失败: {e}")
        return False

def test_interaction_creation(profile_id, token=None):
    """测试交互记录创建端点"""
    try:
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        timestamp = int(time.time())
        interaction_data = {
            'interaction_type': 'communication',
            'title': f'Test Meeting {timestamp}',
            'description': 'Test meeting description',
            'satisfaction_score': 4,
            'result_status': 'successful'
        }
        
        response = requests.post(f"{BASE_URL}/profiles/{profile_id}/interaction/", json=interaction_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ 交互记录创建端点 - 状态码: {response.status_code}")
            return True
        else:
            print(f"❌ 交互记录创建端点 - 状态码: {response.status_code}, 响应: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ 交互记录创建端点失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始Phase 3 API端点完整性测试")
    print("=" * 50)
    
    # 测试列表
    tests = []
    
    # 1. 健康检查
    print("\n📋 测试1: 健康检查")
    tests.append(("健康检查", test_health_check()))
    
    # 2. 获取认证token
    print("\n📋 获取认证token")
    token = get_auth_token()
    
    # 3. 测试档案列表
    print("\n📋 测试2: 档案列表端点")
    tests.append(("档案列表端点", test_profiles_list(token)))
    
    # 4. 测试档案创建
    print("\n📋 测试3: 档案创建端点")
    profile_id = test_profile_create(token)
    tests.append(("档案创建端点", profile_id is not None))
    
    # 5. 测试智能推荐
    print("\n📋 测试4: 智能推荐端点")
    tests.append(("智能推荐端点", test_recommendations(token)))
    
    # 6. 测试智能搜索
    print("\n📋 测试5: 智能搜索端点")
    tests.append(("智能搜索端点", test_search(token)))
    
    # 7. 测试分析仪表盘
    print("\n📋 测试6: 分析仪表盘端点")
    tests.append(("分析仪表盘端点", test_analytics(token)))
    
    # 如果有创建的档案，测试档案相关功能
    if profile_id:
        # 8. 测试档案联系人
        print("\n📋 测试7: 档案联系人端点")
        tests.append(("档案联系人端点", test_profile_contacts(profile_id, token)))
        
        # 9. 测试联系人创建
        print("\n📋 测试8: 联系人创建端点")
        tests.append(("联系人创建端点", test_contact_creation(profile_id, token)))
        
        # 10. 测试交互历史
        print("\n📋 测试9: 交互历史端点")
        tests.append(("交互历史端点", test_interactions(profile_id, token)))
        
        # 11. 测试交互记录创建
        print("\n📋 测试10: 交互记录创建端点")
        tests.append(("交互记录创建端点", test_interaction_creation(profile_id, token)))
    
    # 统计结果
    print("\n" + "=" * 50)
    print(f"📊 测试结果统计:")
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print(f"\n   通过: {passed}/{total}")
    print(f"   失败: {total - passed}/{total}")
    print(f"   成功率: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("🎉 所有API端点测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，需要修复")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)