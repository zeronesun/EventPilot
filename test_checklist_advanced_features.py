"""
EventPilot 清单管理系统高级功能测试

测试清单管理系统的剩余5%功能，包括版本管理、导出导入和核验功能
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, '/mnt/d/projects/sourcecode/EventPilot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# 配置Django
import django
try:
    django.setup()
    print("✓ Django setup successfully")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

from django.utils import timezone
from django.contrib.auth import get_user_model

# 导入模型
from apps.checklists.models import (
    ChecklistTemplate, ChecklistItemTemplate, ChecklistInstance, ChecklistItem,
    ChecklistVersion, ChecklistVersionComparison,
    ChecklistExport, ChecklistImport,
    ChecklistVerification, ChecklistVerificationDetail, ChecklistVerificationException
)

# 导入服务
from apps.checklists.services import checklist_service
from apps.checklists.services.checklist_version_service import ChecklistVersionService
from apps.checklists.services.checklist_export_service import ChecklistExportService, ChecklistImportService
from apps.checklists.services.checklist_verification_service import ChecklistVerificationService

User = get_user_model()

def test_checklist_version_management():
    """测试清单版本管理功能"""
    print("\n=== 测试清单版本管理 ===")
    
    try:
        # 创建测试用户
        user, _ = User.objects.get_or_create(
            username='test_user',
            email='test@example.com',
            defaults={'is_active': True}
        )
        
        # 创建测试模板
        template_data = {
            'name': '测试清单模板-版本管理',
            'description': '测试版本管理功能',
            'checklist_type': 'custom',
            'event_types': ['test'],
            'version': '1.0.0',
            'items': [
                {'title': '测试项1', 'description': '描述1', 'required': True, 'order': 1, 'weight': 1},
                {'title': '测试项2', 'description': '描述2', 'required': False, 'order': 2, 'weight': 2},
            ]
        }
        
        template, errors = checklist_service.ChecklistService.create_template(template_data, user)
        if errors:
            print(f"✗ 创建模板失败: {errors}")
            return False
        
        print(f"✓ 创建模板成功: {template.name}")
        
        # 测试版本创建
        version1, errors = ChecklistVersionService.create_template_version(
            template, 'patch', '初始化版本', user
        )
        if errors:
            print(f"✗ 创建版本失败: {errors}")
            return False
        
        print(f"✓ 创建版本成功: v{version1.version_number}")
        
        # 更新模板
        update_data = {
            'description': '更新后的描述',
            'items': [
                {'title': '测试项1', 'description': '描述1', 'required': True, 'order': 1, 'weight': 1},
                {'title': '测试项2', 'description': '描述2-更新', 'required': False, 'order': 2, 'weight': 2},
                {'title': '测试项3', 'description': '描述3-新增', 'required': True, 'order': 3, 'weight': 3},
            ]
        }
        
        success, errors = checklist_service.ChecklistService.update_template(template, update_data, user)
        if not success:
            print(f"✗ 更新模板失败: {errors}")
            return False
        
        print(f"✓ 更新模板成功")
        
        # 创建新版本
        version2, errors = ChecklistVersionService.create_template_version(
            template, 'minor', '添加新项', user
        )
        if errors:
            print(f"✗ 创建版本失败: {errors}")
            return False
        
        print(f"✓ 创建版本成功: v{version2.version_number}")
        
        # 测试版本对比
        comparison, errors = ChecklistVersionService.compare_versions(version1, version2, user)
        if errors:
            print(f"✗ 版本对比失败: {errors}")
            return False
        
        print(f"✓ 版本对比成功: {comparison.summary}")
        
        # 测试版本历史查询
        history = ChecklistVersionService.get_version_history(template_id=str(template.id))
        print(f"✓ 获取版本历史: {len(history)} 个版本")
        
        # 测试版本回滚
        success, errors = ChecklistVersionService.rollback_to_version(version1, user)
        if not success:
            print(f"✗ 版本回滚失败: {errors}")
            return False
        
        print(f"✓ 版本回滚成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 版本管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_checklist_export_import():
    """测试清单导出导入功能"""
    print("\n=== 测试清单导出导入 ===")
    
    try:
        user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'is_active': True}
        )
        
        # 获取或创建测试模板
        template = ChecklistTemplate.objects.filter(name__contains='测试')).first()
        if not template:
            print("✗ 未找到测试模板")
            return False
        
        # 测试JSON导出
        export = ChecklistExportService.create_export_record(
            target=template,
            export_format='json',
            created_by=user,
            include_items=True,
            include_metadata=True
        )
        
        print(f"✓ 创建导出记录: {export.export_format}")
        
        # 执行导出
        success, errors = ChecklistExportService.export_to_json(template, export)
        if not success:
            print(f"✗ JSON导出失败: {errors}")
            return False
        
        print(f"✓ JSON导出成功: {export.file_size} bytes")
        
        # 测试CSV导出
        export_csv = ChecklistExportService.create_export_record(
            target=template,
            export_format='csv',
            created_by=user,
            include_items=True
        )
        
        success, errors = ChecklistExportService.export_to_csv(template, export_csv)
        if not success:
            print(f"✗ CSV导出失败: {errors}")
            return False
        
        print(f"✓ CSV导出成功: {export_csv.file_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ 导出导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_checklist_verification():
    """测试清单核验功能"""
    print("\n=== 测试清单核验 ===")
    
    try:
        from apps.events.models import Event
        
        user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'is_active': True}
        )
        
        # 获取或创建测试活动
        event, _ = Event.objects.get_or_create(
            name='测试活动-核验',
            owner=user,
            defaults={
                'type': 'test',
                'status': 'planned',
                'start_time': timezone.now(),
                'end_time': timezone.now() + timezone.timedelta(hours=1)
            }
        )
        
        # 获取或创建测试模板
        template = ChecklistTemplate.objects.filter(name__contains='测试').first()
        if not template:
            print("✗ 未找到测试模板")
            return False
        
        # 创建测试实例
        instance_data = {
            'event_id': str(event.id),
            'template_id': str(template.id),
            'name': '测试核验实例'
        }
        
        instance, errors = checklist_service.ChecklistService.create_instance(instance_data, user)
        if errors:
            print(f"✗ 创建实例失败: {errors}")
            return False
        
        print(f"✓ 创建实例成功: {instance.name}")
        
        # 测试创建核验计划
        verification_data = {
            'instance_id': str(instance.id),
            'planned_start_time': timezone.now().isoformat(),
            'planned_end_time': (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
            'requires_approval': False,
            'start_immediately': False
        }
        
        verification, errors = ChecklistVerificationService.create_verification_plan(
            verification_data, user
        )
        if errors:
            print(f"✗ 创建核验计划失败: {errors}")
            return False
        
        print(f"✓ 创建核验计划成功: {verification.status}")
        
        # 测试开始核验
        success, errors = ChecklistVerificationService.start_verification(
            str(verification.id), user
        )
        if not success:
            print(f"✗ 开始核验失败: {errors}")
            return False
        
        print(f"✓ 开始核验成功")
        
        # 测试记录核验详情
        for item in instance.items.all():
            success, errors = ChecklistVerificationService.record_verification_detail(
                verification_id=str(verification.id),
                item_id=str(item.id),
                result='passed',
                evidence=f'测试-{item.title}',
                verified_by=user
            )
            if not success:
                print(f"✗ 记录核验详情失败: {errors}")
                return False
        
        print(f"✓ 记录核验详情成功")
        
        # 测试完成核验
        success, errors = ChecklistVerificationService.complete_verification(
            str(verification.id), user
        )
        if not success:
            print(f"✗ 完成核验失败: {errors}")
            return False
        
        print(f"✓ 完成核验成功")
        
        # 测试获取核验统计
        stats = ChecklistVerificationService.get_verification_statistics(str(verification.id))
        print(f"✓ 获取核验统计: 通过率 {stats.get('pass_rate', 0)}%")
        
        # 测试获取核验报告
        report = ChecklistVerificationService.get_verification_report(str(verification.id))
        if report:
            print(f"✓ 获取核验报告: {len(report.get('details', []))} 条详情")
        
        return True
        
    except Exception as e:
        print(f"✗ 核验测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("开始 EventPilot 清单管理系统高级功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试版本管理
    results.append(('版本管理', test_checklist_version_management()))
    
    # 测试导出导入
    results.append(('导出导入', test_checklist_export_import()))
    
    # 测试核验功能
    results.append(('核验功能', test_checklist_verification()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 成功" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())