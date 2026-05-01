import pytest
from django.test import TestCase, override_settings, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate
from apps.checklists.services.checklist_service import ChecklistService
from apps.events.models import Event

User = get_user_model()


# Apply override_settings to all test classes
@override_settings(ALLOWED_HOSTS=['testserver', '*'])
class ChecklistTemplateTestCase(TestCase):
    """清单模板测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_checklist_template(self):
        """测试创建清单模板"""
        data = {
            'name': '活动前检查清单',
            'description': '活动开始前的检查项',
            'checklist_type': 'custom',
            'event_types': ['conference', 'exhibition'],
            'version': '1.0.0',
            'status': 'draft',
            'tags': ['活动', '检查'],
            'items': [
                {
                    'title': '场地检查',
                    'description': '检查场地是否满足要求',
                    'required': True,
                    'order': 1,
                    'weight': 1
                },
                {
                    'title': '设备检查',
                    'description': '检查设备是否正常工作',
                    'required': True,
                    'order': 2,
                    'weight': 1
                }
            ]
        }
        
        response = self.client.post('/api/checklists/templates/', data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n创建模板失败: {response.status_code}")
            print(f"响应数据: {getattr(response, 'data', response.content)}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '活动前检查清单')
        self.assertEqual(response.data['items_count'], 2)
    
    def test_create_template_invalid_data(self):
        """测试创建模板时无效数据"""
        data = {
            'name': 'ab',  # 名称太短
            'description': '正常描述',
            'checklist_type': 'invalid_type',  # 无效类型
            'event_types': []
        }
        
        response = self.client.post('/api/checklists/templates/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_template(self):
        """测试更新模板"""
        # 先创建一个模板
        template = self._create_test_template()
        
        # 更新数据
        update_data = {
            'name': '更新后的模板名称',
            'description': '更新后的描述',
            'status': 'published',
            'version': '2.0.0'
        }
        
        url = f'/api/checklists/templates/{template.id}/'
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新后的模板名称')
    
    def test_get_template_statistics(self):
        """测试获取模板统计"""
        template = self._create_test_template()
        
        url = f'/api/checklists/templates/{template.id}/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_instances', response.data)
        self.assertIn('average_completion_rate', response.data)
    
    def test_publish_template(self):
        """测试发布模板"""
        template = self._create_test_template()
        
        url = f'/api/checklists/templates/{template.id}/publish/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        template.refresh_from_db()
        self.assertEqual(template.status, 'published')
    
    def test_duplicate_template(self):
        """测试复制模板"""
        template = self._create_test_template()
        
        url = f'/api/checklists/templates/{template.id}/duplicate/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('副本', response.data['name'])
    
    def _create_test_template(self):
        """创建测试模板"""
        from apps.checklists.services.checklist_service import ChecklistService
        
        data = {
            'name': '测试模板',
            'description': '测试描述',
            'checklist_type': 'custom',
            'event_types': ['conference'],
            'version': '1.0.0',
            'status': 'draft',
            'items': [
                {
                    'title': '测试项1',
                    'required': True,
                    'order': 1,
                    'weight': 1
                }
            ]
        }
        
        template, _ = ChecklistService.create_template(data, self.user)
        return template


@override_settings(ALLOWED_HOSTS=['testserver', '*'])
class ChecklistInstanceTestCase(TestCase):
    """清单实例测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试活动和模板
        from apps.events.models import Event
        from apps.checklists.models import ChecklistTemplate
        
        self.event = Event.objects.create(
            name='测试活动',
            type='conference',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            owner=self.user
        )
        
        self.template = ChecklistTemplate.objects.create(
            name='测试模板',
            description='测试描述',
            checklist_type='custom',
            event_types=['conference'],
            version='1.0.0',
            created_by=self.user
        )
    
    def test_create_instance_from_template(self):
        """测试从模板创建实例"""
        data = {
            'template_id': str(self.template.id),
            'event_id': str(self.event.id),
            'name': '测试实例'
        }
        
        response = self.client.post('/api/checklists/instances/instantiate_from_template/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '测试实例')
    
    def test_get_instance_progress(self):
        """测试获取实例进度"""
        # 创建实例
        instance = self._create_test_instance()
        
        url = f'/api/checklists/instances/{instance.id}/progress/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_items', response.data)
        self.assertIn('completion_rate', response.data)
    
    def test_update_instance_status(self):
        """测试更新实例状态"""
        # 创建包含2个必选项的实例
        template = ChecklistTemplate.objects.create(
            name='测试模板2',
            description='测试',
            checklist_type='custom',
            event_types=['conference'],
            created_by=self.user
        )
        
        # 添加2个必选项
        ChecklistItemTemplate.objects.create(
            template=template,
            title='必选项1',
            required=True,
            order=1,
            weight=1
        )
        ChecklistItemTemplate.objects.create(
            template=template,
            title='必选项2',
            required=True,
            order=2,
            weight=1
        )
        
        instance, errors = ChecklistService.create_instance({
            'event_id': str(self.event.id),
            'template_id': str(template.id),
            'name': '测试实例'
        }, self.user)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(instance.items.count(), 2)
        
        # 只完成第一个必选项，实例状态变为 in_progress
        item = instance.items.filter(required=True).first()
        data = {
            'status': 'passed',
            'notes': f'完成项 {item.title}'
        }
        url = f'/api/checklists/items/{item.id}/check/'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 实例状态为 in_progress
        instance.refresh_from_db()
        self.assertEqual(instance.status, 'in_progress')
        
        # 手动调用complete应该失败（还有未完成的必选项）
        url = f'/api/checklists/instances/{instance.id}/complete/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 打印实际错误消息以调试
        if 'errors' in response.data:
            print(f"\n完成API错误: {response.data['errors']}")
        else:
            print(f"\n完成API响应: {response.data}")
        
        # 完成第二个必选项
        item = instance.items.filter(required=True).last()
        data = {
            'status': 'passed',
            'notes': f'完成项 {item.title}'
        }
        url = f'/api/checklists/items/{item.id}/check/'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 实例自动完成
        instance.refresh_from_db()
        self.assertEqual(instance.status, 'completed')
    
    def test_get_instance_report(self):
        """测试获取实例报告"""
        instance = self._create_test_instance()
        
        url = f'/api/checklists/instances/{instance.id}/report/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('instance', response.data)
        self.assertIn('items', response.data)
    
    def _create_test_instance(self):
        """创建测试实例"""
        from apps.checklists.services.checklist_service import ChecklistService
        from apps.checklists.models import ChecklistItemTemplate
        
        # 添加模板项
        ChecklistItemTemplate.objects.create(
            template=self.template,
            title='测试项',
            required=True,
            order=1,
            weight=1
        )
        
        data = {
            'event_id': str(self.event.id),
            'template_id': str(self.template.id),
            'name': '测试实例'
        }

        instance, errors = ChecklistService.create_instance(data, self.user)
        self.assertEqual(len(errors), 0)
        return instance


class ChecklistItemTestCase(TestCase):
    """清单项测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        from apps.events.models import Event
        from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate
        
        self.event = Event.objects.create(
            name='测试活动',
            type='conference',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            owner=self.user
        )
        
        self.template = ChecklistTemplate.objects.create(
            name='测试模板',
            description='测试描述',
            checklist_type='custom',
            event_types=['conference'],
            created_by=self.user
        )
        
        self.template_item = ChecklistItemTemplate.objects.create(
            template=self.template,
            title='测试项',
            required=True,
            order=1,
            weight=1
        )
        
        from apps.checklists.services.checklist_service import ChecklistService

        data = {
            'event_id': str(self.event.id),
            'template_id': str(self.template.id),
            'name': '测试实例'
        }

        self.instance, errors = ChecklistService.create_instance(data, self.user)
        self.assertEqual(len(errors), 0)
        self.item = self.instance.items.first()
    
    def test_update_item_status(self):
        """测试更新清单项状态"""
        url = f'/api/checklists/items/{self.item.id}/check/'
        data = {
            'status': 'passed',
            'notes': '检查通过'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'passed')
    
    def test_add_attachment(self):
        """测试添加附件"""
        attachment_data = {'name': 'test.jpg', 'url': 'http://example.com/test.jpg'}
        
        url = f'/api/checklists/items/{self.item.id}/attachment/'
        data = {'attachment': attachment_data}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.item.refresh_from_db()
        self.assertEqual(len(self.item.attachments), 1)


class ChecklistServiceTestCase(TestCase):
    """清单服务层测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_template_validation(self):
        """测试模板数据验证"""
        from apps.checklists.services.checklist_service import ChecklistService
        
        # 测试无效数据
        data = {
            'name': 'ab',  # 太短
            'checklist_type': 'invalid_type',  # 无效类型
            'event_types': []  # 空列表
        }
        
        is_valid, errors = ChecklistService.validate_template_data(data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_status_transition_validation(self):
        """测试状态流转验证"""
        from apps.checklists.services.checklist_service import ChecklistService
        
        # 测试无效流转
        is_valid, errors = ChecklistService.validate_status_transition('completed', 'incomplete')
        self.assertFalse(is_valid)
        
        # 测试有效流转
        is_valid, errors = ChecklistService.validate_status_transition('incomplete', 'in_progress')
        self.assertTrue(is_valid)
    
    def test_calculate_completion_rate(self):
        """测试完成度计算"""
        from apps.events.models import Event
        from apps.checklists.models import ChecklistTemplate, ChecklistInstance, ChecklistItem
        
        event = Event.objects.create(
            name='测试活动',
            type='conference',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
            owner=self.user
        )
        
        template = ChecklistTemplate.objects.create(
            name='测试模板',
            checklist_type='custom',
            event_types=['conference'],
            created_by=self.user
        )
        
        instance = ChecklistInstance.objects.create(
            event=event,
            template=template,
            name='测试实例',
            status='incomplete'
        )
        
        # 创建几个清单项
        for i in range(3):
            ChecklistItem.objects.create(
                instance=instance,
                title=f'测试项{i}',
                status='passed' if i < 2 else 'pending',
                weight=1
            )
        
        # 更新完成度
        from apps.checklists.services.checklist_service import ChecklistService
        ChecklistService._update_instance_completion(instance)
        
        self.assertAlmostEqual(instance.completion_rate, 66.67, places=1)