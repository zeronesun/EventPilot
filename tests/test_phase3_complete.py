"""
Phase 3 完整系统测试套件
包含单元测试、集成测试和性能基准测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import time

# Django imports
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# Local imports
from apps.profiles.models import (
    ContactProfile, ContactPerson, 
    InteractionHistory, ProfileEvaluation
)
from apps.profiles.services import (
    ContactProfileService, InteractionService,
    EvaluationService, IntelligentRecommender,
    ProfileAnalytics
)

User = get_user_model()


class Phase3UnitTests(TestCase):
    """Phase 3 单元测试"""

    def setUp(self):
        """测试初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_contact_profile_creation(self):
        """测试档案创建"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Supplier',
            profile_type='supplier',
            company_name='Test Company Ltd',
            credit_score=75,
            quality_score=80,
            risk_level='low',
            status='active'
        )
        
        self.assertEqual(profile.name, 'Test Supplier')
        self.assertEqual(profile.profile_type, 'supplier')
        self.assertEqual(profile.credit_score, 75)
        self.assertTrue(profile.is_valid_credit_score())

    def test_contact_person_creation(self):
        """测试联系人创建"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Profile',
            profile_type='client',
            status='active'
        )
        
        contact = ContactPerson.objects.create(
            profile=profile,
            name='John Doe',
            position='Manager',
            email='john@example.com',
            phone='+1234567890',
            is_primary=True,
            is_active=True
        )
        
        self.assertEqual(contact.name, 'John Doe')
        self.assertTrue(contact.is_primary)
        self.assertTrue(contact.is_valid_email())

    def test_interaction_creation(self):
        """测试交互记录创建"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Profile',
            profile_type='client',
            status='active'
        )
        
        interaction = InteractionHistory.objects.create(
            profile=profile,
            interaction_type='communication',
            title='Test Meeting',
            description='Test meeting description',
            satisfaction_score=4,
            outcome_status='successful',
            interaction_date=datetime.now()
        )
        
        self.assertEqual(interaction.interaction_type, 'communication')
        self.assertEqual(interaction.satisfaction_score, 4)
        self.assertTrue(interaction.is_valid_score())

    def test_evaluation_creation(self):
        """测试评估记录创建"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Profile',
            profile_type='supplier',
            status='active'
        )
        
        evaluation = ProfileEvaluation.objects.create(
            profile=profile,
            evaluator=self.user,
            evaluation_date=datetime.now(),
            credit_score=85,
            quality_score=90,
            service_quality=4,
            response_speed=5,
            professional_ability=4,
            risk_level='low',
            recommendations='Good performance'
        )
        
        self.assertEqual(evaluation.credit_score, 85)
        self.assertEqual(evaluation.quality_score, 90)
        self.assertTrue(evaluation.is_valid_range())

    def test_profile_service_crud(self):
        """测试档案服务CRUD操作"""
        # 创建
        profile_data = {
            'name': 'Service Test Profile',
            'profile_type': 'supplier',
            'company_name': 'Service Test Ltd',
            'credit_score': 70,
            'quality_score': 75,
            'risk_level': 'low',
            'status': 'active'
        }
        
        profile = ContactProfileService.create_profile(
            owner=self.user,
            data=profile_data
        )
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, 'Service Test Profile')
        
        # 读取
        retrieved = ContactProfileService.get_profile(profile.id)
        self.assertEqual(retrieved.id, profile.id)
        
        # 更新
        updated = ContactProfileService.update_profile(
            profile_id=profile.id,
            data={'credit_score': 80}
        )
        self.assertEqual(updated.credit_score, 80)

    def test_interaction_service(self):
        """测试交互服务"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Profile',
            profile_type='client',
            status='active'
        )
        
        interaction_data = {
            'interaction_type': 'meeting',
            'title': 'Business Meeting',
            'description': 'Discussing project requirements',
            'satisfaction_score': 5,
            'outcome_status': 'successful'
        }
        
        interaction = InteractionService.record_interaction(
            profile=profile,
            data=interaction_data,
            user=self.user
        )
        
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.interaction_type, 'meeting')

    def test_evaluation_service(self):
        """测试评估服务"""
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Test Profile',
            profile_type='supplier',
            status='active'
        )
        
        evaluation_data = {
            'credit_score': 88,
            'quality_score': 92,
            'service_quality': 4,
            'response_speed': 5,
            'professional_ability': 5,
            'risk_level': 'low',
            'recommendations': 'Excellent work'
        }
        
        evaluation = EvaluationService.create_evaluation(
            profile=profile,
            data=evaluation_data,
            user=self.user
        )
        
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.credit_score, 88)

    def test_intelligent_recommender(self):
        """测试智能推荐引擎"""
        # 创建测试数据
        for i in range(10):
            profile = ContactProfile.objects.create(
                owner=self.user,
                name=f'Supplier {i}',
                profile_type='supplier',
                credit_score=60 + i * 4,  # 60-96
                quality_score=65 + i * 3,  # 65-92
                risk_level=['low', 'medium'][i % 2],
                status='active'
            )
            
            # 添加交互历史
            for j in range(i):  # 不同的交互次数
                InteractionHistory.objects.create(
                    profile=profile,
                    interaction_type='event',
                    title=f'Event {j}',
                    description='Test event',
                    satisfaction_score=4,
                    outcome_status='successful',
                    interaction_date=datetime.now() - timedelta(days=j*10)
                )
        
        # 测试推荐
        event_requirements = {
            'type': '商务会议',
            'min_credit_score': 70,
            'max_risk_level': 'medium',
            'limit': 5
        }
        
        recommendations = IntelligentRecommender.recommend_suppliers(
            event_requirements=event_requirements,
            limit=5
        )
        
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 5)
        
        # 验证推荐结果格式
        for rec in recommendations:
            self.assertIn('profile_id', rec)
            self.assertIn('score', rec)
            self.assertIn('reasons', rec)
            self.assertGreater(rec['score'], 0)

    def test_profile_analytics(self):
        """测试档案分析"""
        # 创建测试档案
        types = ['client', 'supplier', 'partner']
        for profile_type in types:
            ContactProfile.objects.create(
                owner=self.user,
                name=f'{profile_type.title()} {datetime.now().strftime("%H%M%S")}',
                profile_type=profile_type,
                credit_score=70,
                quality_score=75,
                risk_level='low',
                status='active'
            )
        
        # 获取统计数据
        stats = ProfileAnalytics.get_dashboard_stats(user=self.user)
        
        self.assertIn('total_profiles', stats)
        self.assertIn('by_type', stats)
        self.assertIn('average_scores', stats)
        self.assertGreater(stats['total_profiles'], 0)


class Phase3IntegrationTests(TestCase):
    """Phase 3 集成测试"""

    def setUp(self):
        """测试初始化"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_api_endpoints_integration(self):
        """测试API端点集成"""
        
        # 1. 创建档案
        profile_data = {
            'name': 'API Test Profile',
            'profile_type': 'client',
            'company_name': 'API Test Ltd',
            'credit_score': 75,
            'quality_score': 80,
            'risk_level': 'low',
            'status': 'active'
        }
        
        create_response = self.client.post('/api/profiles/', profile_data)
        self.assertEqual(create_response.status_code, 201)
        profile_id = create_response.data['id']
        
        # 2. 获取档案详情
        detail_response = self.client.get(f'/api/profiles/{profile_id}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['name'], 'API Test Profile')
        
        # 3. 添加联系人
        contact_data = {
            'name': 'API Contact',
            'position': 'Sales Manager',
            'email': 'api.contact@example.com',
            'phone': '+9876543210',
            'is_primary': True
        }
        
        contact_response = self.client.post(f'/api/profiles/{profile_id}/contact/', contact_data)
        self.assertEqual(contact_response.status_code, 201)
        
        # 4. 记录交互
        interaction_data = {
            'interaction_type': 'communication',
            'title': 'API Test Interaction',
            'description': 'Testing interaction API',
            'satisfaction_score': 4,
            'outcome_status': 'successful'
        }
        
        interaction_response = self.client.post(f'/api/profiles/{profile_id}/interaction/', interaction_data)
        self.assertEqual(interaction_response.status_code, 201)
        
        # 5. 创建评估
        evaluation_data = {
            'credit_score': 82,
            'quality_score': 85,
            'service_quality': 4,
            'response_speed': 4,
            'professional_ability': 4,
            'risk_level': 'low',
            'recommendations': 'Good API integration'
        }
        
        evaluation_response = self.client.post(f'/api/profiles/{profile_id}/evaluation/', evaluation_data)
        self.assertEqual(evaluation_response.status_code, 201)
        
        # 6. 获取推荐
        recommend_data = {
            'event_type': 'API Test',
            'min_credit_score': 70,
            'max_risk_level': 'low',
            'limit': 5
        }
        
        recommend_response = self.client.post('/api/profiles/recommendations/suppliers/', recommend_data)
        self.assertEqual(recommend_response.status_code, 200)
        self.assertIn('recommendations', recommend_response.data)

    def test_data_consistency(self):
        """测试数据一致性"""
        
        # 创建完整的数据链
        profile = ContactProfile.objects.create(
            owner=self.user,
            name='Consistency Test',
            profile_type='supplier',
            credit_score=60,
            quality_score=60,
            risk_level='low',
            status='active'
        )
        
        # 添加交互
        interaction = InteractionHistory.objects.create(
            profile=profile,
            interaction_type='event',
            title='Test Event',
            description='Testing consistency',
            satisfaction_score=5,
            outcome_status='successful'
        )
        
        # 创建评估
        evaluation = ProfileEvaluation.objects.create(
            profile=profile,
            evaluator=self.user,
            evaluation_date=datetime.now(),
            credit_score=85,
            quality_score=88,
            service_quality=5,
            response_speed=5,
            professional_ability=5,
            risk_level='low'
        )
        
        # 验证关系完整性
        self.assertEqual(profile.interactions.count(), 1)
        self.assertEqual(profile.evaluations.count(), 1)
        self.assertEqual(interaction.profile, profile)
        self.assertEqual(evaluation.profile, profile)
        
        # 验证综合评分计算
        assessment = ContactProfileService.assess_profile_comprehensive(profile)
        self.assertIn('aggregate_score', assessment)
        self.assertGreater(assessment['aggregate_score'], 0)


class Phase3PerformanceTests(TestCase):
    """Phase 3 性能基准测试"""

    def setUp(self):
        """测试初始化"""
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perfpass123'
        )

    def test_query_performance(self):
        """测试数据库查询性能"""
        
        # 创建100个档案
        start_time = time.time()
        for i in range(100):
            ContactProfile.objects.create(
                owner=self.user,
                name=f'Perf Test {i}',
                profile_type='supplier',
                credit_score=60 + (i % 40),
                quality_score=65 + (i % 35),
                risk_level=['low', 'medium', 'high'][i % 3],
                status=['active', 'potential', 'inactive'][i % 3]
            )
        create_time = time.time() - start_time
        
        print(f"创建100个档案耗时: {create_time:.2f}秒")
        self.assertLess(create_time, 5.0, "批量创建性能不达标")
        
        # 测试列表查询性能
        start_time = time.time()
        profiles = list(ContactProfile.objects.all()[:100])
        query_time = time.time() - start_time
        
        print(f"查询100个档案耗时: {query_time:.2f}秒")
        self.assertLess(query_time, 1.0, "列表查询性能不达标")

    def test_recommendation_performance(self):
        """测试推荐算法性能"""
        
        # 创建测试数据
        for i in range(20):
            profile = ContactProfile.objects.create(
                owner=self.user,
                name=f'Perf Supplier {i}',
                profile_type='supplier',
                credit_score=60 + i * 2,
                quality_score=65 + i * 1.5,
                risk_level=['low', 'medium'][i % 2],
                status='active'
            )
            
            # 添加交互历史
            for j in range(min(i * 2, 10)):
                InteractionHistory.objects.create(
                    profile=profile,
                    interaction_type='event',
                    title=f'Event {j}',
                    description='Performance test event',
                    satisfaction_score=4,
                    outcome_status='successful'
                )
        
        # 测试推荐性能
        event_requirements = {
            'type': 'Performance Test',
            'min_credit_score': 70,
            'max_risk_level': 'medium',
            'limit': 10
        }
        
        start_time = time.time()
        recommendations = IntelligentRecommender.recommend_suppliers(
            event_requirements=event_requirements,
            limit=10
        )
        recommend_time = time.time() - start_time
        
        print(f"推荐计算耗时: {recommend_time:.3f}秒")
        self.assertLess(recommend_time, 0.5, "推荐算法性能不达标")
        self.assertGreater(len(recommendations), 0)

    def test_concurrent_operations(self):
        """测试并发操作性能"""
        
        async def create_profile_async(index: int):
            """异步创建档案"""
            profile = ContactProfileService.create_profile(
                owner=self.user,
                data={
                    'name': f'Concurrent Test {index}',
                    'profile_type': 'client',
                    'credit_score': 70 + index % 30,
                    'quality_score': 75 + index % 25,
                    'risk_level': 'low',
                    'status': 'active'
                }
            )
            return profile
        
        # 模拟并发创建操作
        start_time = time.time()
        profiles = await asyncio.gather(*[
            create_profile_async(i) for i in range(50)
        ])
        concurrent_time = time.time() - start_time
        
        print(f"并发创建50个档案耗时: {concurrent_time:.2f}秒")
        self.assertLess(concurrent_time, 3.0, "并发性能不达标")
        self.assertEqual(len(profiles), 50)


def run_phase3_tests():
    """运行Phase 3完整测试套件"""
    pytest.main([
        __file__,
        '-v',  # 详细输出
        '--tb=short',  # 短格式错误信息
        '--no-header',  # 无页眉
        '-q'  # 安静模式
    ])


if __name__ == '__main__':
    run_phase3_tests()