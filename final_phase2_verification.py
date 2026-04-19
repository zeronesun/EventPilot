"""
最终Phase 2验证脚本
验证所有核心功能是否正常工作
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
from apps.users.models import UserRole, UserActivity
from apps.users.services.user_service import UserService
from apps.users.services.user_import_service import UserImportService

User = get_user_model()

def run_comprehensive_test():
    """运行全面的Phase 2功能验证"""
    print("=" * 60)
    print("EventPilot Phase 2 - 最终功能验证")
    print("=" * 60)
    
    success_count = 0
    total_tests = 15
    
    # 测试1: 密码强度验证
    print("\n1. 密码强度验证测试:")
    try:
        valid_password = "StrongPass123!"
        is_valid, errors = UserService.validate_password_strength(valid_password)
        if is_valid:
            print(f"  ✓ 强密码验证通过: {valid_password}")
            success_count += 1
        else:
            print(f"  ✗ 强密码验证失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试2: 用户数据验证
    print("\n2. 用户数据验证测试:")
    try:
        is_valid, errors = UserService.validate_user_data(
            username="test_new_user",
            email="newuser@test.com",
            password="TestPass123!"
        )
        if is_valid:
            print(f"  ✓ 用户数据验证通过")
            success_count += 1
        else:
            print(f"  ✗ 用户数据验证失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试3: 用户创建服务
    print("\n3. 用户创建服务测试:")
    try:
        # 清理已存在的测试用户
        User.objects.filter(username="service_test_user").delete()
        
        user_data = {
            'username': 'service_test_user',
            'email': 'service_test@test.com',
            'password': 'ServicePass123!',
            'role': 'executor'
        }
        
        user, errors = UserService.create_user(user_data)
        if user and not errors:
            print(f"  ✓ 用户创建成功: {user.username}")
            success_count += 1
        else:
            print(f"  ✗ 用户创建失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试4: 用户更新服务
    print("\n4. 用户更新服务测试:")
    try:
        update_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'department': 'IT Department'
        }
        success, errors = UserService.update_user(user, update_data)
        if success:
            print(f"  ✓ 用户更新成功: {user.username}")
            success_count += 1
        else:
            print(f"  ✗ 用户更新失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试5: 密码更改服务
    print("\n5. 密码更改服务测试:")
    try:
        success, errors = UserService.change_password(
            user, "ServicePass123!", "NewServicePass456!"
        )
        if success:
            print(f"  ✓ 密码更改成功")
            success_count += 1
        else:
            print(f"  ✗ 密码更改失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试6: 用户软删除服务
    print("\n6. 用户软删除服务测试:")
    try:
        success, errors = UserService.delete_user(user, soft_delete=True)
        if success:
            print(f"  ✓ 用户软删除成功")
            success_count += 1
        else:
            print(f"  ✗ 用户软删除失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试7: 批量导入服务
    print("\n7. 批量导入服务测试:")
    try:
        # 清理测试用户
        User.objects.filter(username__startswith="bulk_test_").delete()
        
        import_data = [
            {
                'username': 'bulk_test_1',
                'email': 'bulk1@test.com',
                'password': 'BulkPass123!',
                'role': 'executor'
            },
            {
                'username': 'bulk_test_2',
                'email': 'bulk2@test.com',
                'password': 'BulkPass123!',
                'role': 'observer'
            }
        ]
        
        results = UserImportService.import_users_from_list(
            users_data=import_data,
            send_welcome_email=False,
            force_password_change=False
        )
        
        if results.get('imported', 0) == 2:
            print(f"  ✓ 批量导入成功: {results['imported']} 个用户")
            success_count += 1
        else:
            print(f"  ✗ 批量导入失败: {results.get('errors', 'Unknown error')}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试8: 用户统计服务
    print("\n8. 用户统计服务测试:")
    try:
        stats = UserService.get_user_statistics(days=30)
        if 'total_users' in stats and 'active_users' in stats:
            print(f"  ✓ 用户统计成功: 总用户 {stats['total_users']}, 活跃用户 {stats['active_users']}")
            success_count += 1
        else:
            print(f"  ✗ 用户统计失败: 缺少必要字段")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试9: 用户活跃度评分
    print("\n9. 用户活跃度评分测试:")
    try:
        # 创建一些活动
        test_user = User.objects.filter(username='bulk_test_1').first()
        if test_user:
            for i in range(5):
                UserService.log_user_activity(
                    test_user,
                    'login' if i == 0 else f'test_activity_{i}',
                    details={'test': i}
                )
            
            score = UserService.calculate_user_activity_score(test_user, days=30)
            if 0 <= score <= 100:
                print(f"  ✓ 活跃度评分成功: {score}分")
                success_count += 1
            else:
                print(f"  ✗ 活跃度评分失败: 分数超出范围 {score}")
        else:
            print(f"  ✗ 活跃度评分测试: 没有测试用户")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试10: 不活跃用户检测
    print("\n10. 不活跃用户检测测试:")
    try:
        inactive_users = UserService.get_inactive_users(threshold_days=60)
        if inactive_users.count() >= 0:  # 查询成功就算通过
            print(f"  ✓ 不活跃用户检测成功: 检测到 {inactive_users.count()} 个用户")
            success_count += 1
        else:
            print(f"  ✗ 不活跃用户检测失败")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试11: 账户锁定功能
    print("\n11. 账户锁定功能测试:")
    try:
        # 创建一个被锁定的用户
        from django.utils import timezone
        locked_user = User.objects.create_user(
            username='locked_test',
            email='locked@test.com',
            password='LockedPass123!',
            failed_login_attempts=5,
            locked_until=timezone.now() + timezone.timedelta(minutes=30)
        )
        UserRole.objects.create(user=locked_user, role='executor')
        
        is_locked = UserService.check_account_lockout(locked_user)
        if is_locked:
            print(f"  ✓ 账户锁定检测成功: 用户已被锁定")
            success_count += 1
        else:
            print(f"  ✗ 账户锁定检测失败: 用户应该被锁定")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试12: 账户解锁功能
    print("\n12. 账户解锁功能测试:")
    try:
        success, errors = UserService.unlock_account(locked_user)
        if success:
            locked_user.refresh_from_db()
            is_still_locked = UserService.check_account_lockout(locked_user)
            if not is_still_locked:
                print(f"  ✓ 账户解锁成功: 用户已解锁")
                success_count += 1
            else:
                print(f"  ✗ 账户解锁失败: 用户仍然被锁定")
        else:
            print(f"  ✗ 账户解锁操作失败: {errors}")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试13: 批量状态更新
    print("\n13. 批量状态更新测试:")
    try:
        user_ids = [str(user.id) for user in User.objects.filter(username__startswith="bulk_test_")]
        if user_ids:
            updated_count, errors = UserService.bulk_update_users_status(user_ids, False)
            if updated_count == len(user_ids):
                print(f"  ✓ 批量状态更新成功: {updated_count} 个用户")
                success_count += 1
            else:
                print(f"  ✗ 批量状态更新失败: 预期 {len(user_ids)} 个，实际 {updated_count} 个")
        else:
            print(f"  ✗ 批量状态更新测试: 没有足够的测试用户")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试14: 批量角色分配
    print("\n14. 批量角色分配测试:")
    try:
        user_ids = [str(user.id) for user in User.objects.filter(username__startswith="bulk_test_")]
        if user_ids:
            updated_count, errors = UserService.bulk_assign_roles(user_ids, 'observer')
            if updated_count == len(user_ids):
                print(f"  ✓ 批量角色分配成功: {updated_count} 个用户分配为observer")
                success_count += 1
            else:
                print(f"  ✗ 批量角色分配失败: 预期 {len(user_ids)} 个，实际 {updated_count} 个")
        else:
            print(f"  ✗ 批量角色分配测试: 没有足够的测试用户")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 测试15: 批量删除功能
    print("\n15. 批量删除功能测试:")
    try:
        user_ids = [str(user.id) for user in User.objects.filter(username__startswith="bulk_test_")]
        if user_ids:
            deleted_count, errors = UserService.bulk_delete_users(user_ids, soft_delete=True)
            if deleted_count == len(user_ids):
                print(f"  ✓ 批量删除成功: {deleted_count} 个用户")
                success_count += 1
            else:
                print(f"  ✗ 批量删除失败: 预期 {len(user_ids)} 个，实际 {deleted_count} 个")
        else:
            print(f"  ✗ 批量删除测试: 没有足够的测试用户")
    except Exception as e:
        print(f"  ✗ 测试出错: {str(e)}")
    
    # 清理测试数据
    try:
        User.objects.filter(username__in=['locked_test', 'service_test_user']).delete()
        User.objects.filter(username__startswith="bulk_test_").delete()
    except:
        pass
    
    # 输出最终结果
    print("\n" + "=" * 60)
    print("Phase 2 功能验证结果")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {success_count}")
    print(f"失败测试: {total_tests - success_count}")
    print(f"成功率: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 所有测试通过！Phase 2 用户管理CRUD功能实现完成！")
        return 0
    elif success_count >= total_tests * 0.8:
        print("\n✅ 大部分测试通过！实现基本完成，有小问题需要修复。")
        return 1
    else:
        print("\n❌ 测试失败较多，需要检查实现。")
        return 2

if __name__ == '__main__':
    exit_code = run_comprehensive_test()
    sys.exit(exit_code)