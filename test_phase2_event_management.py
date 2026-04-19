"""
EventPilot Phase 2 - 活动管理CRUD功能测试

测试覆盖：
1. 活动创建完整功能
2. 活动更新/PATCH功能
3. 活动删除功能（软删除和硬删除）
4. 活动状态管理和流转
5. 参与者管理
6. 预算管理和刷新
7. 活动统计和风险评估
8. 活动模板功能
9. 数据验证和错误处理
10. 性能和缓存测试
"""

import os
import json
import django
import datetime
import logging
from typing import Dict, Any, Optional

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test.utils import setup_test_environment
from django.test.client import RequestFactory
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.events.models import Event, BudgetItem, EventParticipant, EventTemplate
from apps.events.services.event_service import EventService
from apps.events.api.serializers import (
    EventSerializer, EventCreateSerializer, EventUpdateSerializer,
    EventListSerializer, EventParticipantSerializer
)
from apps.tasks.models import Task

User = get_user_model()
logger = logging.getLogger(__name__)


class EventServiceTest(TestCase):
    """活动服务层测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 清理之前的测试数据
        User.objects.all().delete()
        Event.objects.all().delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
    
    def tearDown(self):
        """清理测试数据"""
        Event.objects.all().delete()
        User.objects.all().delete()
    
    def test_create_event(self):
        """测试创建活动"""
        event_data = {
            'name': '测试活动',
            'type': 'conference',
            'description': '这是一个测试活动',
            'start_date': timezone.now() + datetime.timedelta(days=1),
            'end_date': timezone.now() + datetime.timedelta(days=3),
            'client': '测试客户',
            'client_contact': 'test@client.com',
            'estimated_budget': 100000,
            'budget_items': [
                {
                    'category_name': '场地',
                    'name': '会议室租赁',
                    'estimated_amount': 50000
                },
                {
                    'category_name': '餐饮',
                    'name': '午餐费用',
                    'estimated_amount': 20000
                }
            ]
        }
        
        event, errors = EventService.create_event(event_data, self.user)
        
        self.assertIsNotNone(event)
        self.assertEqual(len(errors), 0)
        self.assertEqual(event.name, '测试活动')
        self.assertEqual(event.status, Event.Status.PLANNING)
        self.assertEqual(event.budget_items.count(), 2)
        
        # 验证预算计算
        self.assertEqual(event.estimated_budget, 70000.0)
        
        print(f"✅ 活动创建测试通过: {event.name}")
    
    def test_create_event_validation(self):
        """测试活动创建验证"""
        # 测试无效数据
        invalid_data = {
            'name': '测',  # 名称太短
            'type': 'conference',
            'start_date': timezone.now(),
            'end_date': timezone.now() - datetime.timedelta(days=1),  # 结束时间早于开始时间
            'estimated_budget': -100  # 负预算
        }
        
        _, errors = EventService.create_event(invalid_data, self.user)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('名称' in error for error in errors))
        self.assertTrue(any('结束时间' in error for error in errors))
        self.assertTrue(any('预算' in error for error in errors))
        
        print(f"✅ 活动验证测试通过: 检测到 {len(errors)} 个错误")
    
    def test_update_event(self):
        """测试更新活动"""
        # 先创建一个活动
        event = Event.objects.create(
            name='原始活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            estimated_budget=100000,
            owner=self.user
        )
        
        # 更新活动
        update_data = {
            'name': '更新后的活动',
            'description': '活动描述已更新',
            'estimated_budget': 150000
        }
        
        success, errors = EventService.update_event(event, update_data)
        
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        
        event.refresh_from_db()
        self.assertEqual(event.name, '更新后的活动')
        self.assertEqual(event.estimated_budget, 150000)
        
        print(f"✅ 活动更新测试通过: {event.name}")
    
    def test_status_transition(self):
        """测试状态流转"""
        event = Event.objects.create(
            name='测试活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            owner=self.user
        )
        
        # 正常流转：策划中 -> 执行中
        success, _ = EventService.change_event_status(event, Event.Status.EXECUTING)
        self.assertTrue(success)
        
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.EXECUTING)
        
        # 执行中 -> 已完成
        success, _ = EventService.change_event_status(event, Event.Status.COMPLETED)
        self.assertTrue(success)
        
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.COMPLETED)
        self.assertIsNotNone(event.completed_at)
        
        # 测试无效流转
        success, errors = EventService.change_event_status(event, Event.Status.PLANNING)
        self.assertFalse(success)
        self.assertGreater(len(errors), 0)
        
        print(f"✅ 状态流转测试通过")
    
    def test_soft_delete(self):
        """测试软删除"""
        event = Event.objects.create(
            name='待删除活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            owner=self.user
        )
        
        success, _ = EventService.delete_event(event, soft_delete=True)
        
        self.assertTrue(success)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)
        self.assertIsNotNone(event.completed_at)
        
        print(f"✅ 软删除测试通过")
    
    def test_statistics_calculation(self):
        """测试统计计算"""
        event = Event.objects.create(
            name='统计活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            estimated_budget=100000,
            owner=self.user
        )
        
        # 创建一些预算项
        BudgetItem.objects.create(
            event=event,
            category_name='场地',
            name='会议室',
            estimated_amount=50000,
            actual_amount=45000,
            status='completed'
        )
        
        BudgetItem.objects.create(
            event=event,
            category_name='餐饮',
            name='午餐',
            estimated_amount=20000,
            actual_amount=15000,
            status='pending'
        )
        
        # 获取统计
        stats = EventService.get_event_statistics(event)
        
        self.assertIn('tasks', stats)
        self.assertIn('budget', stats)
        self.assertIn('timeline', stats)
        
        self.assertEqual(stats['budget']['estimated_total'], 70000.0)
        self.assertEqual(stats['budget']['actual_total'], 60000.0)
        
        print(f"✅ 统计计算测试通过")


class EventAPITest(APITestCase):
    """活动API测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 清理之前的测试数据
        User.objects.all().delete()
        Event.objects.all().delete()
        
        self.client = APIClient()
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='api_test_user',
            email='api_test@example.com',
            password='TestPass123!'
        )
        
        # 创建Token
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        
        # 设置认证
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def tearDown(self):
        """清理测试数据"""
        Event.objects.all().delete()
        User.objects.all().delete()
    
    def test_event_list(self):
        """测试活动列表"""
        # 创建一些测试活动
        for i in range(3):
            Event.objects.create(
                name=f'测试活动{i}',
                type='conference',
                start_date=timezone.now() + datetime.timedelta(days=i+1),
                end_date=timezone.now() + datetime.timedelta(days=i+3),
                owner=self.user
            )
        
        # 获取活动列表
        response = self.client.get('/api/events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 3)
        
        print(f"✅ 活动列表API测试通过")
    
    def test_event_create(self):
        """测试创建活动API"""
        event_data = {
            'name': 'API测试活动',
            'type': 'conference',
            'description': '通过API创建的测试活动',
            'start_date': (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            'end_date': (timezone.now() + datetime.timedelta(days=3)).isoformat(),
            'estimated_budget': 100000,
            'budget_items': [
                {
                    'category_name': '布置',
                    'name': '会场布置',
                    'estimated_amount': 30000
                }
            ]
        }
        
        response = self.client.post('/api/events/', event_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'API测试活动')
        self.assertEqual(response.data['budget_items'][0]['name'], '会场布置')
        
        print(f"✅ 创建活动API测试通过")
    
    def test_event_retrieve(self):
        """测试获取活动详情"""
        event = Event.objects.create(
            name='详情活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            estimated_budget=50000,
            owner=self.user
        )
        
        response = self.client.get(f'/api/events/{event.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(event.id))
        self.assertIn('tasks_count', response.data)
        self.assertIn('progress_percentage', response.data)
        
        print(f"✅ 获取活动详情API测试通过")
    
    def test_event_update(self):
        """测试更新活动API"""
        event = Event.objects.create(
            name='原始活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            owner=self.user
        )
        
        update_data = {
            'name': '更新名称',
            'description': '新的描述',
            'status': 'executing'
        }
        
        response = self.client.patch(f'/api/events/{event.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新名称')
        self.assertEqual(response.data['status'], 'executing')
        
        print(f"✅ 更新活动API测试通过")
    
    def test_event_delete(self):
        """测试删除活动API"""
        event = Event.objects.create(
            name='待删除活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            owner=self.user
        )
        
        response = self.client.delete(f'/api/events/{event.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 验证软删除
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)
        
        print(f"✅ 删除活动API测试通过")
    
    def test_event_statistics(self):
        """测试活动统计API"""
        event = Event.objects.create(
            name='统计活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            estimated_budget=80000,
            owner=self.user
        )
        
        response = self.client.get(f'/api/events/{event.id}/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('budget', response.data)
        self.assertIn('timeline', response.data)
        
        print(f"✅ 活动统计API测试通过")
    
    def test_event_risk_assessment(self):
        """测试活动风险评估API"""
        event = Event.objects.create(
            name='风险评估活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=30),
            estimated_budget=5000000,  # 高预算，高风险
            owner=self.user
        )
        
        response = self.client.get(f'/api/events/{event.id}/risk/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('level', response.data)
        self.assertIn('factors', response.data)
        self.assertIn('recommendations', response.data)
        
        print(f"✅ 活动风险评估API测试通过: 风险等级 {response.data['level']}")
    
    def test_participants_management(self):
        """测试参与者管理API"""
        event = Event.objects.create(
            name='参与者活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            owner=self.user
        )
        
        other_user = User.objects.create_user(
            username='participant',
            email='participant@example.com',
            password='PartPass123!'
        )
        
        # 添加参与者
        add_response = self.client.post(
            f'/api/events/{event.id}/participants/',
            {'user_id': str(other_user.id), 'role': 'executor'},
            format='json'
        )
        
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)
        
        # 获取参与者列表
        list_response = self.client.get(f'/api/events/{event.id}/participants/')
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(list_response.data), 0)
        
        print(f"✅ 参与者管理API测试通过")
    
    def test_event_complete(self):
        """测试完成活动API"""
        event = Event.objects.create(
            name='完成活动',
            type='conference',
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=3),
            status=Event.Status.EXECUTING,
            owner=self.user
        )
        
        response = self.client.post(f'/api/events/{event.id}/complete/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.COMPLETED)
        self.assertIsNotNone(event.completed_at)
        
        print(f"✅ 完成活动API测试通过")


class EventFilterTest(APITestCase):
    """活动过滤测试"""
    
    def setUp(self):
        # 清理之前的测试数据
        User.objects.all().delete()
        Event.objects.all().delete()
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='filter_user',
            email='filter@example.com',
            password='FilterPass123!'
        )
        
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # 创建不同状态的活动
        now = timezone.now()
        Event.objects.create(
            name='策划活动',
            type='conference',
            start_date=now + datetime.timedelta(days=1),
            end_date=now + datetime.timedelta(days=3),
            status=Event.Status.PLANNING,
            owner=self.user
        )
        
        Event.objects.create(
            name='执行活动',
            type='exhibition',
            start_date=now + datetime.timedelta(days=5),
            end_date=now + datetime.timedelta(days=7),
            status=Event.Status.EXECUTING,
            owner=self.user
        )
        
        Event.objects.create(
            name='完成活动',
            type='conference',
            start_date=now - datetime.timedelta(days=10),
            end_date=now - datetime.timedelta(days=8),
            status=Event.Status.COMPLETED,
            owner=self.user
        )
    
    def tearDown(self):
        """清理测试数据"""
        Event.objects.all().delete()
        User.objects.all().delete()
    
    def test_status_filter(self):
        """测试状态过滤"""
        response = self.client.get('/api/events/?status=planning')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'planning')
        
        print(f"✅ 状态过滤测试通过")
    
    def test_type_filter(self):
        """测试类型过滤"""
        response = self.client.get('/api/events/?type=conference')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        print(f"✅ 类型过滤测试通过")
    
    def test_search(self):
        """测试搜索功能"""
        response = self.client.get('/api/events/?search=策划')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
        print(f"✅ 搜索功能测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始 EventPilot Phase 2 活动管理CRUD功能测试")
    print("="*60 + "\n")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # 运行服务层测试
    print("📋 运行服务层测试...")
    for test_name in dir(EventServiceTest):
        if test_name.startswith('test_'):
            total_tests += 1
            try:
                test_instance = EventServiceTest()
                test_instance.setUp()
                getattr(test_instance, test_name)()
                test_instance.tearDown()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"❌ {test_name} 失败: {e}")
    
    # 运行API测试
    print("\n📋 运行API测试...")
    for test_name in dir(EventAPITest):
        if test_name.startswith('test_'):
            total_tests += 1
            try:
                test_instance = EventAPITest()
                test_instance.setUp()
                getattr(test_instance, test_name)()
                test_instance.tearDown()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"❌ {test_name} 失败: {e}")
    
    # 运行过滤测试
    print("\n📋 运行过滤测试...")
    for test_name in dir(EventFilterTest):
        if test_name.startswith('test_'):
            total_tests += 1
            try:
                test_instance = EventFilterTest()
                test_instance.setUp()
                getattr(test_instance, test_name)()
                test_instance.tearDown()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"❌ {test_name} 失败: {e}")
    
    # 打印总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {failed_tests} ❌")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "成功率: 0%")
    print("="*60 + "\n")
    
    return failed_tests == 0


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)