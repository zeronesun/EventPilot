"""
EventPilot Phase 2 API端点测试脚本
测试基本的API功能和响应
"""

import os
import sys
import django

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone
import json

User = get_user_model()

def setup_test_data():
    """设置测试数据"""
    # 创建管理员用户
    try:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='AdminPass123!',
            is_superuser=True
        )
        from apps.users.models import UserRole
        UserRole.objects.create(user=admin_user, role='admin')
        print(f"✓ 创建管理员用户: {admin_user.username}")
    except:
        admin_user = User.objects.get(username='testadmin')
        print(f"✓ 使用现有管理员用户: {admin_user.username}")
    
    return admin_user

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("EventPilot Phase 2 API端点功能测试")
    print("=" * 60)
    
    # 设置测试数据
    admin_user = setup_test_data()
    
    # 创建API客户端
    client = APIClient()
    
    # 测试1: 用户登录（获取token）
    print("\n测试 1: 用户登录")
    response = client.post('/api/auth/login/', {
        'username': 'testadmin',
        'password': 'AdminPass123!'
    }, format='json')
    
    if response.status_code in [200, 201]:
        # 登录成功，提取token
        token = response.data.get('data', {}).get('token')
        username = response.data.get('data', {}).get('user', {}).get('username')
        if token:
            print(f"✓ 登录成功: {username}")
            print(f"  - Token: {str(token)[:20]}...")
            # 尝试不同的认证头格式
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        else:
            print(f"✓ 登录响应但未找到token: {username}")
            return False
    else:
        print(f"✗ 登录失败: {response.status_code}")
        print(f"  - 响应: {response.data}")
        return False
    
    # 测试2: 获取用户列表
    print("\n测试 2: 获取用户列表")
    response = client.get('/api/users/users/')
    
    if response.status_code == 200:
        print(f"✓ 成功获取用户列表: {len(response.data)} 个用户")
    else:
        print(f"✗ 获取用户列表失败: {response.status_code}")
        return False
    
    # 测试3: 创建新用户
    print("\n测试 3: 创建新用户")
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
    
    response = client.post('/api/users/users/', user_data, format='json')
    
    if response.status_code == 201:
        print(f"✓ 成功创建用户: {response.data.get('username')}")
        new_user_id = response.data.get('id')
    else:
        print(f"✗ 创建用户失败: {response.data}")
        return False
    
    # 测试4: 获取用户详情
    print("\n测试 4: 获取用户详情")
    response = client.get(f'/api/users/users/{new_user_id}/')
    
    if response.status_code == 200:
        print(f"✓ 成功获取用户详情: {response.data.get('username')}")
        print(f"  - 角色信息: {response.data.get('role', 'N/A')}")
        print(f"  - 部门: {response.data.get('department', 'N/A')}")
    else:
        print(f"✗ 获取用户详情失败: {response.status_code}")
        return False
    
    # 测试5: 更新用户信息
    print("\n测试 5: 更新用户信息")
    update_data = {
        'first_name': 'Updated',
        'last_name': 'User',
        'department': 'New Department',
        'position': 'Senior Developer'
    }
    
    response = client.patch(f'/api/users/users/{new_user_id}/', update_data, format='json')
    
    if response.status_code == 200:
        print(f"✓ 成功更新用户信息")
        print(f"  - 新部门: {response.data.get('department')}")
    else:
        print(f"✗ 更新用户信息失败: {response.data}")
        return False
    
    # 测试6: 测试密码强度验证
    print("\n测试 6: 测试密码强度验证")
    
    # 测试弱密码创建
    weak_data = {
        'username': 'weakuser',
        'email': 'weak@test.com',
        'password': 'weak',
        'confirm_password': 'weak',
        'role': 'executor'
    }
    
    response = client.post('/api/users/users/', weak_data, format='json')
    
    if response.status_code == 400:
        print(f"✓ 正确拒绝弱密码: weak")
    else:
        print(f"✗ 密码强度验证失败: 应该拒绝弱密码")
        return False
    
    # 测试7: 测试批量状态更新
    print("\n测试 7: 测试批量状态更新")
    
    # 首先创建几个用户用于批量操作
    batch_users = []
    for i in range(3):
        user_data = {
            'username': f'batchuser{i}',
            'email': f'batch{i}@test.com',
            'password': f'BatchPass{i}!',
            'confirm_password': f'BatchPass{i}!',
            'role': 'executor'
        }
        response = client.post('/api/users/users/', user_data, format='json')
        if response.status_code == 201:
            batch_users.append(response.data.get('id'))
    
    if len(batch_users) >= 2:
        bulk_data = {
            'user_ids': batch_users[:2],
            'is_active': False
        }
        
        response = client.post('/api/users/users/bulk/update-status/', bulk_data, format='json')
        
        if response.status_code == 200:
            print(f"✓ 成功批量更新状态: {response.data.get('updated_count')} 个用户")
        else:
            print(f"✗ 批量状态更新失败: {response.data}")
            return False
    else:
        print(f"✗ 没有足够的用户进行批量测试")
    
    # 测试8: 获取用户统计
    print("\n测试 8: 获取用户统计")
    response = client.get('/api/users/users/statistics/')
    
    if response.status_code == 200:
        print(f"✓ 成功获取用户统计")
        print(f"  - 总用户数: {response.data.get('total_users')}")
        print(f"  - 活跃用户数: {response.data.get('active_users')}")
        print(f"  - 新用户数(30天): {response.data.get('new_users')}")
    else:
        print(f"✗ 获取用户统计失败: {response.status_code}")
        return False
    
    # 测试9: 获取角色列表
    print("\n测试 9: 获取角色列表")
    response = client.get('/api/users/roles/')
    
    if response.status_code == 200:
        print(f"✓ 成功获取角色列表: {len(response.data)} 个角色")
        for role in response.data:
            print(f"  - {role.get('label')} ({role.get('value')})")
    else:
        print(f"✗ 获取角色列表失败: {response.status_code}")
        return False
    
    # 测试10: 删除用户（软删除）
    print("\n测试 10: 删除用户（软删除）")
    response = client.delete(f'/api/users/users/{new_user_id}/')
    
    if response.status_code == 204:
        print(f"✓ 成功软删除用户")
    else:
        print(f"✗ 删除用户失败: {response.status_code}")
        return False
    
    # 验证用户是否被软删除
    try:
        deleted_user = User.objects.get(id=new_user_id)
        if deleted_user.is_deleted:
            print(f"✓ 验证软删除成功: 用户已标记为删除")
        else:
            print(f"✗ 软删除验证失败: 用户未被标记为删除")
    except:
        print(f"✗ 找不到已删除的用户")
    
    print("\n" + "=" * 60)
    print("🎉 API端点功能测试完成")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_api_endpoints()
    
    if success:
        print("\n✅ 所有API端点测试通过！")
        print("Phase 2 用户管理CRUD功能实现完成。")
        sys.exit(0)
    else:
        print("\n❌ 部分API端点测试失败，请检查实现。")
        sys.exit(1)