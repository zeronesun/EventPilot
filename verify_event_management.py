"""
EventPilot Phase 2 - 活动管理CRUD功能验证脚本

简单的功能验证，不需要运行完整的测试套件
"""

import os
import sys
import django

# 配置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event, BudgetItem, EventParticipant, EventTemplate
from apps.events.services.event_service import EventService
from apps.users.models import User


def test_user_setup():
    """确保测试用户存在"""
    try:
        user = User.objects.get(username='test_admin')
        print(f"✅ 测试用户已存在: {user.username}")
        return user
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='Admin123!'
        )
        print(f"✅ 创建测试用户: {user.username}")
        return user


def test_event_creation():
    """测试活动创建"""
    print("\n📋 测试活动创建...")
    
    user = User.objects.first()
    if not user:
        user = test_user_setup()
    
    event_data = {
        'name': '2024年度技术大会',
        'type': 'conference',
        'description': '年度技术交流会议',
        'start_date': timezone.now() + timedelta(days=30),
        'end_date': timezone.now() + timedelta(days=32),
        'client': '科技公司',
        'client_contact': 'contact@tech.com',
        'estimated_budget': 500000,
        'owner_id': str(user.id),  # 使用owner_id
        'budget_items': [
            {
                'category_name': '场地',
                'name': '会议中心租赁',
                'estimated_amount': 200000
            },
            {
                'category_name': '服务',
                'name': '餐饮服务',
                'estimated_amount': 50000
            },
            {
                'category_name': '宣传',
                'name': '宣传材料',
                'estimated_amount': 30000
            }
        ]
    }
    
    event, errors = EventService.create_event(event_data, user)
    
    if errors:
        print(f"❌ 活动创建失败: {errors}")
        return None
    
    print(f"✅ 活动创建成功:")
    print(f"   - 名称: {event.name}")
    print(f"   - 类型: {event.type}")
    print(f"   - 状态: {event.get_status_display()}")
    print(f"   - 拥有者: {event.owner.username}")
    print(f"   - 预算项: {event.budget_items.count()}")
    print(f"   - 总预估预算: {event.estimated_budget}")
    
    return event


def test_event_update(event):
    """测试活动更新"""
    print("\n📋 测试活动更新...")
    
    update_data = {
        'name': '2024年度技术大会 - 更新版',
        'description': '年度技术交流会议（已更新）',
        'estimated_budget': 550000
    }
    
    success, errors = EventService.update_event(event, update_data)
    
    if not success:
        print(f"❌ 活动更新失败: {errors}")
        return False
    
    event.refresh_from_db()
    print(f"✅ 活动更新成功:")
    print(f"   - 新名称: {event.name}")
    print(f"   - 新预算: {event.estimated_budget}")
    
    return True


def test_status_transition(event):
    """测试状态流转"""
    print("\n📋 测试状态流转...")
    
    transitions = [
        ('planning', 'executing', '策划中 → 执行中'),
        ('executing', 'completed', '执行中 → 已完成'),
        ('completed', 'reviewed', '已完成 → 已复盘')
    ]
    
    for old_status, new_status, description in transitions:
        success, errors = EventService.change_event_status(event, new_status)
        
        if not success:
            print(f"❌ 状态流转失败: {description} - {errors}")
            return False
        
        event.refresh_from_db()
        print(f"✅ 状态流转成功: {description}")
    
    return True


def test_statistics(event):
    """测试统计功能"""
    print("\n📋 测试统计功能...")
    
    stats = EventService.get_event_statistics(event)
    
    print(f"✅ 活动统计数据:")
    print(f"   - 任务统计:")
    print(f"     * 总数: {stats['tasks']['total']}")
    print(f"     * 已完成: {stats['tasks']['completed']}")
    print(f"     * 进度: {stats['tasks']['progress_percentage']:.1f}%")
    print(f"   - 预算统计:")
    print(f"     * 预估: {stats['budget']['estimated_total']:.2f}")
    print(f"     * 实际: {stats['budget']['actual_total']:.2f}")
    print(f"     * 使用率: {stats['budget']['usage_rate']:.1f}%")
    print(f"   - 时间线:")
    print(f"     * 开始: {stats['timeline']['start_date']}")
    print(f"     * 结束: {stats['timeline']['end_date']}")
    print(f"     * 剩余天数: {stats['timeline']['days_remaining']}")
    
    return True


def test_risk_assessment(event):
    """测试风险评估"""
    print("\n📋 测试风险评估...")
    
    risk = EventService.assess_event_risk(event)
    
    print(f"✅ 风险评估结果:")
    print(f"   - 风险等级: {risk['level'].upper()}")
    print(f"   - 风险因素数: {len(risk['factors'])}")
    print(f"   - 建议数: {len(risk['recommendations'])}")
    
    if risk['factors']:
        print(f"   - 风险因素:")
        for factor in risk['factors']:
            print(f"     * {factor['type']}: {factor['message']}")
    
    if risk['recommendations']:
        print(f"   - 建议:")
        for rec in risk['recommendations'][:3]:
            print(f"     * {rec}")
    
    return True


def test_soft_delete(event):
    """测试软删除"""
    print("\n📋 测试软删除...")
    
    success, errors = EventService.delete_event(event, soft_delete=True)
    
    if not success:
        print(f"❌ 软删除失败: {errors}")
        return False
    
    event.refresh_from_db()
    print(f"✅ 软删除成功:")
    print(f"   - 状态: {event.get_status_display()}")
    print(f"   - 完成时间: {event.completed_at}")
    
    return True


def test_template_creation():
    """测试模板创建"""
    print("\n📋 测试模板创建...")
    
    user = User.objects.first()
    
    template = EventTemplate.objects.create(
        name="标准会议模板",
        category=EventTemplate.Category.CONFERENCE,
        description="用于标准化会议活动的模板",
        default_duration_days=3,
        default_budget=100000,
        task_templates=[
            {"name": "场地预订", "task_type": "preparation", "estimated_days": 2},
            {"name": "宣传推广", "task_type": "preparation", "estimated_days": 5},
            {"name": "现场执行", "task_type": "execution", "estimated_days": 1}
        ],
        budget_templates=[
            {"category_name": "场地", "name": "会场租赁", "estimated_amount": 50000},
            {"category_name": "餐饮", "name": "茶歇和午餐", "estimated_amount": 20000},
            {"category_name": "设备", "name": "音响投影设备", "estimated_amount": 15000}
        ],
        created_by=user,
        is_active=True
    )
    
    print(f"✅ 模板创建成功:")
    print(f"   - 名称: {template.name}")
    print(f"   - 分类: {template.get_category_display()}")
    print(f"   - 默认时长: {template.default_duration_days} 天")
    print(f"   - 默认预算: {template.default_budget:.2f}")
    print(f"   - 任务模板数: {len(template.task_templates)}")
    print(f"   - 预算模板数: {len(template.budget_templates)}")
    
    return template


def test_verification():
    """运行完整功能验证"""
    print("\n" + "="*80)
    print("EventPilot Phase 2 - 活动管理CRUD功能验证")
    print("="*80)
    
    results = []
    
    try:
        # 测试用户设置
        user = test_user_setup()
        results.append(('用户设置', True))
    except Exception as e:
        results.append(('用户设置', False, str(e)))
    
    try:
        # 测试活动创建
        event = test_event_creation()
        if not event:
            results.append(('活动创建', False, "活动创建失败"))
        else:
            results.append(('活动创建', True))
            
            try:
                # 测试活动更新
                if test_event_update(event):
                    results.append(('活动更新', True))
                else:
                    results.append(('活动更新', False))
            except Exception as e:
                results.append(('活动更新', False, str(e)))
            
            try:
                # 测试状态流转
                if test_status_transition(event):
                    results.append(('状态流转', True))
                else:
                    results.append(('状态流转', False))
            except Exception as e:
                results.append(('状态流转', False, str(e)))
            
            try:
                # 测试统计功能
                if test_statistics(event):
                    results.append(('统计功能', True))
                else:
                    results.append(('统计功能', False))
            except Exception as e:
                results.append(('统计功能', False, str(e)))
            
            try:
                # 测试风险评估
                if test_risk_assessment(event):
                    results.append(('风险评估', True))
                else:
                    results.append(('风险评估', False))
            except Exception as e:
                results.append(('风险评估', False, str(e)))
            
            try:
                # 测试软删除
                if test_soft_delete(event):
                    results.append(('软删除', True))
                else:
                    results.append(('软删除', False))
            except Exception as e:
                results.append(('软删除', False, str(e)))
    except Exception as e:
        results.append(('活动创建', False, str(e)))
    
    try:
        # 测试模板功能
        template = test_template_creation()
        if template:
            results.append(('模板创建', True))
        else:
            results.append(('模板创建', False))
    except Exception as e:
        results.append(('模板创建', False, str(e)))
    
    # 打印总结
    print("\n" + "="*80)
    print("验证结果总结")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for result in results:
        test_name = result[0]
        if result[1]:
            passed += 1
            print(f"✅ {test_name}")
        else:
            failed += 1
            error = result[2] if len(result) > 2 else "未知错误"
            print(f"❌ {test_name}: {error}")
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("="*80)
    print(f"总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌") 
    print(f"成功率: {success_rate:.1f}%")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = test_verification()
    sys.exit(0 if success else 1)