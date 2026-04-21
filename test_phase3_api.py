#!/usr/bin/env python3
"""
Phase 3 API端点完整性测试
验证所有API端点的功能正确性
"""

import os
import sys

# 设置Django环境 - 必须在任何Django相关导入之前
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import json


class Phase3APITest(TestCase):
    """Phase 3 API端点测试类"""
    
    def setUp(self):
        """测试初始化"""
        # 创建测试用户 - 使用随机时间戳避免重复
        import time
        from datetime import datetime
        timestamp = int(time.time())
        
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username=f'test_user_{timestamp}',
            email=f'test_{timestamp}@example.com',
            password='test_password123'
        )
        
        # 创建API客户端并设置认证
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        print("✅ 测试环境初始化完成")
    
    def test_profile_list_endpoint(self):
        """测试档案列表端点"""
        print("📝 测试档案列表端点 GET /api/profiles/")
        response = self.client.get('/api/profiles/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        print(f"✅ 档案列表端点测试通过 - 状态码: {response.status_code}")
    
    def test_profile_create_endpoint(self):
        """测试档案创建端点"""
        print("📝 测试档案创建端点 POST /api/profiles/")
        
        profile_data = {
            'name': 'Test Company',
            'company_name': 'Test Company Ltd',
            'profile_type': 'supplier',
            'status': 'active',
            'industry': 'Technology',
            'credit_score': 75,
            'quality_score': 80,
            'risk_level': 'low',
            'tags': 'test,supplier,technology'
        }
        
        response = self.client.post('/api/profiles/', profile_data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['name'], 'Test Company')
        print(f"✅ 档案创建端点测试通过 - 创建ID: {response.data['id']}")
    
    def test_profile_detail_endpoint(self):
        """测试档案详情端点"""
        print("📝 测试档案详情端点 GET /api/profiles/{id}/")
        
        # 先创建一个档案
        profile_data = {
            'name': 'Detail Test Company',
            'company_name': 'Detail Test Ltd',
            'profile_type': 'client',
            'status': 'active'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 获取详情
        response = self.client.get(f'/api/profiles/{profile_id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], profile_id)
        print(f"✅ 档案详情端点测试通过 - 档案ID: {profile_id}")
    
    def test_recommendation_endpoint(self):
        """测试智能推荐端点"""
        print("📝 测试智能推荐端点 POST /api/profiles/recommendations/suppliers/")
        
        request_data = {
            'event_type': '商务会议',
            'min_credit_score': 60,
            'max_risk_level': 'medium',
            'limit': 5
        }
        
        response = self.client.post('/api/profiles/recommendations/suppliers/', request_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('recommendations', response.data)
        print(f"✅ 智能推荐端点测试通过 - 推荐数量: {response.data.get('count', 0)}")
    
    def test_search_endpoint(self):
        """测试智能搜索端点"""
        print("📝 测试智能搜索端点 POST /api/profiles/search/profiles/")
        
        search_data = {
            'query': 'technology',
            'profile_type': 'supplier',
            'limit': 10
        }
        
        response = self.client.post('/api/profiles/search/profiles/', search_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        print(f"✅ 智能搜索端点测试通过 - 结果数量: {response.data.get('count', 0)}")
    
    def test_analytics_dashboard_endpoint(self):
        """测试分析仪表盘端点"""
        print("📝 测试分析仪表盘端点 GET /api/profiles/analytics/dashboard/")
        
        response = self.client.get('/api/profiles/analytics/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        print(f"✅ 分析仪表盘端点测试通过 - 数据响应正常")
    
    def test_profile_contacts_endpoint(self):
        """测试档案联系人端点"""
        print("📝 测试档案联系人端点 GET /api/profiles/{id}/contacts/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Contact Test Company',
            'company_name': 'Contact Test Ltd',
            'profile_type': 'partner'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 获取联系人
        response = self.client.get(f'/api/profiles/{profile_id}/contacts/')
        
        self.assertEqual(response.status_code, 200)
        print(f"✅ 档案联系人端点测试通过 - 联系人数量: {response.data.get('count', 0)}")
    
    def test_contact_creation_endpoint(self):
        """测试联系人创建端点"""
        print("📝 测试联系人创建端点 POST /api/profiles/{id}/contact/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Create Contact Company',
            'company_name': 'Create Contact Ltd',
            'profile_type': 'client'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 创建联系人
        contact_data = {
            'name': 'John Doe',
            'position': 'Manager',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'is_primary': True
        }
        
        response = self.client.post(f'/api/profiles/{profile_id}/contact/', contact_data, format='json')
        
        self.assertEqual(response.status_code, 201)
        print(f"✅ 联系人创建端点测试通过 - 联系人ID: {response.data.get('id')}")
    
    def test_interactions_endpoint(self):
        """测试交互历史端点"""
        print("📝 测试交互历史端点 GET /api/profiles/{id}/interactions/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Interaction Test Company',
            'company_name': 'Interaction Test Ltd',
            'profile_type': 'supplier'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 获取交互历史
        response = self.client.get(f'/api/profiles/{profile_id}/interactions/')
        
        self.assertEqual(response.status_code, 200)
        print(f"✅ 交互历史端点测试通过 - 交互记录数量: {response.data.get('count', 0)}")
    
    def test_interaction_creation_endpoint(self):
        """测试交互记录创建端点"""
        print("📝 测试交互记录创建端点 POST /api/profiles/{id}/interaction/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Create Interaction Company',
            'company_name': 'Create Interaction Ltd',
            'profile_type': 'partner'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 创建交互记录
        interaction_data = {
            'interaction_type': 'communication',
            'title': 'Test Meeting',
            'description': 'Test meeting description',
            'satisfaction_score': 4,
            'result_status': 'successful'
        }
        
        response = self.client.post(f'/api/profiles/{profile_id}/interaction/', interaction_data, format='json')
        
        self.assertEqual(response.status_code, 201)
        print(f"✅ 交互记录创建端点测试通过 - 交互ID: {response.data.get('id')}")
    
    def test_evaluations_endpoint(self):
        """测试评估记录端点"""
        print("📝 测试评估记录端点 GET /api/profiles/{id}/evaluations/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Evaluation Test Company',
            'company_name': 'Evaluation Test Ltd',
            'profile_type': 'supplier'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 获取评估记录
        response = self.client.get(f'/api/profiles/{profile_id}/evaluations/')
        
        self.assertEqual(response.status_code, 200)
        print(f"✅ 评估记录端点测试通过 - 评估记录数量: {response.data.get('count', 0)}")
    
    def test_evaluation_creation_endpoint(self):
        """测试评估记录创建端点"""
        print("📝 测试评估记录创建端点 POST /api/profiles/{id}/evaluation/")
        
        # 创建测试档案
        profile_data = {
            'name': 'Create Evaluation Company',
            'company_name': 'Create Evaluation Ltd',
            'profile_type': 'client'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data, format='json')
        profile_id = create_response.data['id']
        
        # 创建评估记录
        evaluation_data = {
            'service_quality_score': 4,
            'response_speed_score': 5,
            'professional_capability_score': 4,
            'overall_score': 4,
            'risk_assessment': 'low risk',
            'comments': 'Good performance'
        }
        
        response = self.client.post(f'/api/profiles/{profile_id}/evaluation/', evaluation_data, format='json')
        
        self.assertEqual(response.status_code, 201)
        print(f"✅ 评估记录创建端点测试通过 - 评估ID: {response.data.get('id')}")


def run_all_tests():
    """运行所有API端点测试"""
    print("🚀 开始Phase 3 API端点完整性测试")
    print("=" * 50)
    
    test_methods = [
        'test_profile_list_endpoint',
        'test_profile_create_endpoint', 
        'test_profile_detail_endpoint',
        'test_recommendation_endpoint',
        'test_search_endpoint',
        'test_analytics_dashboard_endpoint',
        'test_profile_contacts_endpoint',
        'test_contact_creation_endpoint',
        'test_interactions_endpoint',
        'test_interaction_creation_endpoint',
        'test_evaluations_endpoint',
        'test_evaluation_creation_endpoint'
    ]
    
    # 创建测试实例
    test_instance = Phase3APITest('setUp')
    test_instance.setUp()
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            # 为每个测试方法重新初始化
            test_instance.setUp()
            
            # 执行测试
            getattr(test_instance, test_method)()
            passed += 1
            
        except Exception as e:
            failed += 1
            print(f"❌ {test_method} - 失败: {str(e)}")
    
    print("=" * 50)
    print(f"📊 测试结果统计:")
    print(f"   通过: {passed}/{len(test_methods)}")
    print(f"   失败: {failed}/{len(test_methods)}")
    print(f"   成功率: {(passed/len(test_methods)*100):.1f}%")
    
    if failed == 0:
        print("🎉 所有API端点测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，需要修复")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)