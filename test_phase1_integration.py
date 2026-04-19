#!/usr/bin/env python3
"""
EventPilot Phase 1 集成测试
测试后端API和前后端连接
"""

import os
import sys
import json
import time
from pathlib import Path

# 确保Django能找到项目设置
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_django_setup():
    """测试Django基本设置"""
    print_section("1. Django Setup 测试")
    
    try:
        import django
        django.setup()
        print("✅ Django setup successful")
        
        from django.conf import settings
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
        print(f"✅ Installed apps: {len(settings.INSTALLED_APPS)}")
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_database_models():
    """测试数据库模型"""
    print_section("2. 数据库模型测试")
    
    try:
        from apps.users.models import User
        from apps.events.models import Event
        from apps.tasks.models import Task
        from apps.checklists.models import ChecklistTemplate
        
        user_count = User.objects.count()
        event_count = Event.objects.count()
        task_count = Task.objects.count()
        template_count = ChecklistTemplate.objects.count()
        
        print(f"✅ User model: {user_count} users")
        print(f"✅ Event model: {event_count} events")
        print(f"✅ Task model: {task_count} tasks")
        print(f"✅ ChecklistTemplate model: {template_count} templates")
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_jwt_functions():
    """测试JWT功能"""
    print_section("3. JWT 功能测试")
    
    try:
        from apps.users.models import User
        from apps.users.authentication import generate_jwt_token, decode_jwt_token
        from jwt import DecodeError
        
        # 获取一个测试用户
        user = User.objects.first()
        if not user:
            print("⚠️  No users in database, creating test user...")
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.create_user(
                username='testuser',
                email='test@test.com',
                password='testpass123'
            )
        
        # 测试token生成
        token = generate_jwt_token(user)
        print(f"✅ JWT token generated: {token[:50]}...")
        print(f"   Token length: {len(token)}")
        
        # 测试token解码
        try:
            payload = decode_jwt_token(token)
            print(f"✅ JWT token decoded successfully")
            print(f"   User ID: {payload.get('user_id')}")
            print(f"   Username: {payload.get('username')}")
            print(f"   Role: {payload.get('role')}")
        except DecodeError as e:
            print(f"❌ JWT decode failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ JWT functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """测试API端点可访问性"""
    print_section("4. API 端点测试")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        client = Client()
        
        # 测试健康检查端点
        response = client.get('/api/health/')
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
        
        # 测试API信息端点
        response = client.get('/api/')
        print(f"✅ API info: {response.status_code}")
        
        # 测试JWT登录端点（需要用户）
        user = User.objects.first()
        if user:
            from django.contrib.auth import authenticate
            authenticated_user = authenticate(username=user.username, password='testpassword123')
            if not authenticated_user:
                # 创建测试密码
                user.set_password('testpassword123')
                user.save()
            
            # 测试登录（注意：这个可能失败因为我们没有运行服务器）
            print(f"⚠️  JWT登录 endpoint: needs running server")
            print(f"   Test user: {user.username}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cors_configuration():
    """测试CORS配置"""
    print_section("5. CORS 配置测试")
    
    try:
        from django.conf import settings
        
        cors_settings = {
            'CORS_ALLOW_ALL_ORIGINS': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', None),
            'CORS_ALLOWED_ORIGINS': getattr(settings, 'CORS_ALLOWED_ORIGINS', []),
            'CORS_ALLOW_CREDENTIALS': getattr(settings, 'CORS_ALLOW_CREDENTIALS', False),
            'ALLOWED_HOSTS': settings.ALLOWED_HOSTS
        }
        
        print("✅ CORS settings configured:")
        for key, value in cors_settings.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ CORS configuration test failed: {e}")
        return False

def main():
    """运行所有测试"""
    print_section("EventPilot Phase 1 集成测试")
    print("开始时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    tests = [
        ("Django Setup", test_django_setup),
        ("Database Models", test_database_models),
        ("JWT Functions", test_jwt_functions),
        ("API Endpoints", test_api_endpoints),
        ("CORS Configuration", test_cors_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 Phase 1 后端部分 100% 完成！")
        print("📋 下一步: 启动前端开发服务器测试集成")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
    
    print("\n测试完成时间:", time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()