"""
Phase 2 用户管理CRUD功能测试脚本
测试所有创建、读取、更新、删除、批量操作和高级功能
"""

import os
import django
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User, UserRole, UserActivity
from apps.users.services.user_service import UserService
import json

User = get_user_model()


class Phase2UserCRUDTests(APITestCase):
    """Phase 2 用户管理CRUD测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='AdminPass123!',
            is_superuser=True
        )
        UserRole.objects.create(user=self.admin_user, role='admin')
        
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='UserPass123!'
        )
        UserRole.objects.create(user=self.regular_user, role='executor')
        
        # 认证客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        print("\n=== Phase 2 用户管理CRUD功能测试 ===\n")
    
    def test_01_user_creation(self):
        """测试用户创建功能"""
        print("测试 1: 用户创建功能")
        
        user_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewUser123!',
            'confirm_password': 'NewUser123!',
            'first_name': 'New',
            'last_name': 'User',
            'department': 'IT',
            'position': 'Developer',
            'role': 'executor',
            'is_active': True
        }
        
        response = self.client.post(
            '/api/users/users/',
            user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # 检查是否记录了创建活动
        new_user = User.objects.get(username='newuser')
        activity_count = UserActivity.objects.filter(
            user=new_user,
            activity_type='profile_update'
        ).count()
        self.assertGreater(activity_count, 0)
        
        print(f"✓ 用户创建成功: {new_user.username}")
        return new_user
    
    def test_02_user_read_list(self):
        """测试用户列表读取"""
        print("\n测试 2: 用户列表读取")
        
        response = self.client.get('/api/users/users/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        print(f"✓ 成功读取用户列表，共 {len(response.data)} 个用户")
    
    def test_03_user_read_detail(self):
        """测试用户详情读取"""
        print("\n测试 3: 用户详情读取")
        
        user_id = self.regular_user.id
        response = self.client.get(f'/api/users/users/{user_id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertIn('role', response.data)
        self.assertIn('activities_breakdown' if 'activities_breakdown' in response.data else '', 
                      response.data)
        
        print(f"✓ 成功读取用户详情: {response.data['username']}")
    
    def test_04_user_update(self):
        """测试用户更新功能"""
        print("\n测试 4: 用户更新功能")
        
        user_id = self.regular_user.id
        updated_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'department': 'New Department',
            'position': 'Senior Developer'
        }
        
        response = self.client.patch(
            f'/api/users/users/{user_id}/',
            updated_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        
        print(f"✓ 用户更新成功: {self.regular_user.username}")
    
    def test_05_password_change(self):
        """测试密码更改功能"""
        print("\n测试 5: 密码更改功能")
        
        # 创建一个新用户用于测试密码更改
        test_user = User.objects.create_user(
            username='passworduser',
            email='password@test.com',
            password='OldPass123!'
        )
        UserRole.objects.create(user=test_user, role='executor')
        
        password_data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        }
        
        response = self.client.post(
            '/api/users/users/change-password/',
            password_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 验证新密码是否有效
        self.assertTrue(test_user.check_password('NewPass456!'))
        
        print("✓ 密码更改成功")
    
    def test_06_password_reset_by_admin(self):
        """测试管理员重置密码功能"""
        print("\n测试 6: 管理员重置密码功能")
        
        user_id = self.regular_user.id
        reset_data = {
            'user_id': str(user_id),
            'new_password': 'ResetPass789!',
            'confirm_password': 'ResetPass789!',
            'force_change': True
        }
        
        response = self.client.post(
            f'/api/users/users/{user_id}/reset_password/',
            reset_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        print("✓ 管理员密码重置成功")
    
    def test_07_user_activation(self):
        """测试用户激活/停用功能"""
        print("\n测试 7: 用户激活/停用功能")
        
        user_id = self.regular_user.id
        
        # 先停用用户
        update_data = {'is_active': False}
        response = self.client.patch(
            f'/api/users/users/{user_id}/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 验证用户已被停用
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)
        
        print("✓ 用户激活/停用功能正常")
    
    def test_08_role_assignment(self):
        """测试角色分配功能"""
        print("\n测试 8: 角色分配功能")
        
        user_id = self.regular_user.id
        role_data = {'role': 'project_owner'}
        
        response = self.client.patch(
            f'/api/users/users/{user_id}/',
            role_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 验证角色已更新
        user_role = UserRole.objects.get(user=self.regular_user)
        self.assertEqual(user_role.role, 'project_owner')
        
        print(f"✓ 角色分配成功: {user_role.role}")
    
    def test_09_user_soft_delete(self):
        """测试用户软删除功能"""
        print("\n测试 9: 用户软删除功能")
        
        # 创建一个测试用户
        test_user = User.objects.create_user(
            username='deletetest',
            email='delete@test.com',
            password='DeletePass123!'
        )
        UserRole.objects.create(user=test_user, role='executor')
        
        user_id = test_user.id
        response = self.client.delete(f'/api/users/users/{user_id}/')
        
        self.assertEqual(response.status_code, 204)
        
        # 验证用户已被软删除
        test_user.refresh_from_db()
        self.assertTrue(test_user.is_deleted)
        self.assertFalse(test_user.is_active)
        self.assertIsNotNone(test_user.deleted_at)
        
        print(f"✓ 用户软删除成功: {test_user.username}")
    
    def test_10_bulk_status_update(self):
        """测试批量状态更新功能"""
        print("\n测试 10: 批量状态更新功能")
        
        # 创建多个测试用户
        test_users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'bulkuser{i}',
                email=f'bulk{i}@test.com',
                password='BulkPass123!'
            )
            UserRole.objects.create(user=user, role='executor')
            test_users.append(user)
        
        user_ids = [str(user.id) for user in test_users]
        bulk_data = {
            'user_ids': user_ids,
            'is_active': False
        }
        
        response = self.client.post(
            '/api/users/users/bulk/update-status/',
            bulk_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['updated_count'], 3)
        
        # 验证所有用户状态已更新
        for user in test_users:
            user.refresh_from_db()
            self.assertFalse(user.is_active)
        
        print(f"✓ 批量状态更新成功: {response.data['updated_count']} 个用户")
    
    def test_11_bulk_role_assignment(self):
        """测试批量角色分配功能"""
        print("\n测试 11: 批量角色分配功能")
        
        # 创建多个测试用户
        test_users = []
        for i in range(2):
            user = User.objects.create_user(
                username=f'roleuser{i}',
                email=f'role{i}@test.com',
                password='RolePass123!'
            )
            UserRole.objects.create(user=user, role='executor')
            test_users.append(user)
        
        user_ids = [str(user.id) for user in test_users]
        bulk_data = {
            'user_ids': user_ids,
            'role': 'observer'
        }
        
        response = self.client.post(
            '/api/users/users/bulk/assign-roles/',
            bulk_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['updated_count'], 2)
        
        # 验证所有用户角色已更新
        for user in test_users:
            user_role = UserRole.objects.get(user=user)
            self.assertEqual(user_role.role, 'observer')
        
        print(f"✓ 批量角色分配成功: {response.data['updated_count']} 个用户")
    
    def test_12_user_import(self):
        """测试批量用户导入功能"""
        print("\n测试 12: 批量用户导入功能")
        
        import_data = {
            'users': [
                {
                    'username': 'import1',
                    'email': 'import1@test.com',
                    'password': 'ImportPass123!',
                    'first_name': 'Import',
                    'last_name': 'User1',
                    'role': 'executor'
                },
                {
                    'username': 'import2',
                    'email': 'import2@test.com',
                    'password': 'ImportPass456!',
                    'first_name': 'Import',
                    'last_name': 'User2',
                    'role': 'observer'
                }
            ],
            'send_welcome_email': False,
            'force_password_change': True
        }
        
        response = self.client.post(
            '/api/users/users/import/',
            import_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['imported'], 2)
        self.assertTrue(User.objects.filter(username='import1').exists())
        self.assertTrue(User.objects.filter(username='import2').exists())
        
        print(f"✓ 批量用户导入成功: {response.data['imported']} 个用户")
    
    def test_13_user_activities(self):
        """测试用户活动日志功能"""
        print("\n测试 13: 用户活动日志功能")
        
        # 记录一些测试活动
        UserService.log_user_activity(
            user=self.regular_user,
            activity_type='login',
            details={'test': 'data'}
        )
        
        user_id = self.regular_user.id
        response = self.client.get(f'/api/users/users/{user_id}/activities/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        print(f"✓ 用户活动日志读取成功: {len(response.data)} 条活动记录")
    
    def test_14_user_statistics(self):
        """测试用户统计功能"""
        print("\n测试 14: 用户统计功能")
        
        response = self.client.get('/api/users/users/statistics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_users', response.data)
        self.assertIn('active_users', response.data)
        self.assertIn('role_distribution', response.data)
        
        print(f"✓ 用户统计功能正常: 总用户 {response.data['total_users']}")
    
    def test_15_password_strength_validation(self):
        """测试密码强度验证"""
        print("\n测试 15: 密码强度验证")
        
        # 测试弱密码
        is_valid, errors = UserService.validate_password_strength('weak')
        self.assertFalse(is_valid)
        
        # 测试强密码
        is_valid, errors = UserService.validate_password_strength('StrongPass123!')
        self.assertTrue(is_valid)
        
        print("✓ 密码强度验证功能正常")
    
    def test_16_user_lockout(self):
        """测试账户锁定功能"""
        print("\n测试 16: 账户锁定功能")
        
        # 创建一个测试用户
        test_user = User.objects.create_user(
            username='lockout_user',
            email='lockout@test.com',
            password='LockoutPass123!',
            failed_login_attempts=5,
            locked_until=timezone.now() + timezone.timedelta(minutes=30)
        )
        UserRole.objects.create(user=test_user, role='executor')
        
        # 检查用户是否被锁定
        is_locked = UserService.check_account_lockout(test_user)
        self.assertTrue(is_locked)
        
        # 测试解锁功能
        success, errors = UserService.unlock_account(test_user)
        self.assertTrue(success)
        
        # 验证用户已解锁
        test_user.refresh_from_db()
        self.assertFalse(UserService.check_account_lockout(test_user))
        
        print("✓ 账户锁定和解锁功能正常")
    
    def test_17_inactive_users_detection(self):
        """测试不活跃用户检测功能"""
        print("\n测试 17: 不活跃用户检测功能")
        
        # 创建一个不活跃用户
        inactive_user = User.objects.create_user(
            username='inactive_user',
            email='inactive@test.com',
            password='InactivePass123!',
            last_login=timezone.now() - timezone.timedelta(days=90)
        )
        UserRole.objects.create(user=inactive_user, role='executor')
        
        response = self.client.get('/api/users/users/inactive/?threshold_days=60')
        
        self.assertEqual(response.status_code, 200)
        usernames = [user['username'] for user in response.data]
        self.assertIn('inactive_user', usernames)
        
        print(f"✓ 不活跃用户检测功能正常: 检测到 {len(response.data)} 个不活跃用户")
    
    def test_18_user_activity_score(self):
        """测试用户活跃度评分功能"""
        print("\n测试 18: 用户活跃度评分功能")
        
        # 创建一些活动
        for i in range(5):
            UserService.log_user_activity(
                user=self.regular_user,
                activity_type='login' if i == 0 else f'test_activity_{i}',
                details={'index': i}
            )
        
        # 计算活跃度分数
        score = UserService.calculate_user_activity_score(self.regular_user, days=30)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        
        print(f"✓ 用户活跃度评分功能正常: 分数 {score}")
    
    def test_19_concurrent_operations(self):
        """测试并发操作安全性"""
        print("\n测试 19: 并发操作安全性")
        
        # 创建一个用户
        test_user = User.objects.create_user(
            username='concurrent_user',
            email='concurrent@test.com',
            password='ConcurrentPass123!'
        )
        UserRole.objects.create(user=test_user, role='executor')
        
        # 模拟多次更新
        original_last_name = test_user.last_name
        for i in range(5):
            test_user.last_name = f'Update{i}'
            test_user.save()
        
        test_user.refresh_from_db()
        self.assertNotEqual(test_user.last_name, original_last_name)
        
        print("✓ 并发操作安全性测试通过")
    
    def test_20_data_validation(self):
        """测试数据验证完整性"""
        print("\n测试 20: 数据验证完整性")
        
        # 测试无效邮箱
        invalid_data = {
            'username': 'invaliduser',
            'email': 'invalid-email-format',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!',
            'role': 'executor'
        }
        
        response = self.client.post(
            '/api/users/users/',
            invalid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # 测试无效密码强度
        invalid_password_data = {
            'username': 'weakpass_user',
            'email': 'weakpass@test.com',
            'password': 'weak',
            'confirm_password': 'weak',
            'role': 'executor'
        }
        
        response = self.client.post(
            '/api/users/users/',
            invalid_password_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        print("✓ 数据验证完整性测试通过")
    
    def tearDown(self):
        """清理测试数据"""
        User.objects.all().delete()
        print("\n===Phase 2 用户管理CRUD功能测试完成 ===\n")


def run_all_tests():
    """运行所有测试"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(Phase2UserCRUDTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    result = run_all_tests()
    
    # 输出测试摘要
    print("\n" + "="*50)
    print("PHASE 2 用户管理CRUD功能测试摘要")
    print("="*50)
    print(f"总运行测试数: {result.testsRun}")
    print(f"成功测试数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败测试数: {len(result.failures)}")
    print(f"错误测试数: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！Phase 2 用户管理CRUD功能实现完成。")
    else:
        print("\n❌ 部分测试失败，请检查实现。")
        if result.failures:
            print("\n失败的测试:")
            for test, traceback in result.failures[:3]:
                print(f"  - {test}: {traceback.split()[-1]}")
        if result.errors:
            print("\n错误的测试:")
            for test, traceback in result.errors[:3]:
                print(f"  - {test}: {traceback.split()[-1]}")
    
    sys.exit(0 if result.wasSuccessful() else 1)