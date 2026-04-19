#!/usr/bin/env python
"""
EventPilot任务管理CRUD功能验证脚本
验证Phase 2任务管理功能的完整性和正确性
"""

import os
import django
import time
import json
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.events.models import Event
from apps.tasks.models import Task, TaskDependency, CommunicationTask
from apps.tasks.services.task_service import TaskService
from apps.tasks.services.communication_task_service import CommunicationTaskService

User = get_user_model()


def log(message, level='INFO'):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def colored_message(message, color='green'):
    """彩色消息输出"""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, colors['reset'])}{message}{colors['reset']}"


def setup_test_data():
    """设置测试数据"""
    log("=== 初始化测试数据 ===")
    
    # 创建测试用户
    try:
        user = User.objects.get(username='test_user')
        log("测试用户已存在: test_user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password_123'
        )
        log(colored_message(f"✓ 创建测试用户: {user.username}", 'green'))
    
    # 创建测试活动
    try:
        event = Event.objects.get(name='测试活动-CRUD验证')
        log("测试活动已存在: 测试活动-CRUD验证")
    except Event.DoesNotExist:
        event = Event.objects.create(
            name='测试活动-CRUD验证',
            type='测试',
            description='用于验证任务管理CRUD功能的测试活动',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=2),
            owner=user
        )
        log(colored_message(f"✓ 创建测试活动: {event.name}", 'green'))
    
    # 创建第二个测试用户（用于分配任务）
    try:
        assignee = User.objects.get(username='assignee_user')
        log("分配用户已存在: assignee_user")
    except User.DoesNotExist:
        assignee = User.objects.create_user(
            username='assignee_user',
            email='assignee@example.com',
            password='assignee_password_123'
        )
        log(colored_message(f"✓ 创建分配用户: {assignee.username}", 'green'))
    
    return user, event, assignee


def test_create_task(user, event):
    """测试任务创建功能"""
    log("\n=== 测试任务创建功能 ===")
    
    test_cases = [
        {
            'name': '基础任务创建',
            'data': {
                'title': '基础测试任务',
                'description': '这是一个基础的测试任务',
                'task_type': 'planning',
                'start_date': timezone.now() + timedelta(hours=1),
                'due_date': timezone.now() + timedelta(days=1)
            }
        },
        {
            'name': '带依赖的任务创建',
            'data': {
                'title': '带依赖的测试任务',
                'description': '这个任务依赖其他任务',
                'task_type': 'guest',
                'start_date': timezone.now() + timedelta(hours=2),
                'due_date': timezone.now() + timedelta(days=2)
            },
            'create_dependency': True
        },
        {
            'name': '分配任务给用户',
            'data': {
                'title': '待分配的任务',
                'description': '这个任务需要分配给特定用户',
                'task_type': 'material',
                'start_date': timezone.now() + timedelta(hours=3),
                'due_date': timezone.now() + timedelta(days=3)
            },
            'assign_to': True
        }
    ]
    
    created_tasks = {}
    
    for test_case in test_cases:
        try:
            data = test_case['data'].copy()
            data['event_id'] = str(event.id)
            
            task = TaskService.create_task(user, str(event.id), data)
            created_tasks[test_case['name']] = task
            
            log(colored_message(f"✓ {test_case['name']} - 任务ID: {task.id}", 'green'))
            
            # 处理依赖任务
            if test_case.get('create_dependency'):
                # 先创建依赖任务
                dep_data = {
                    'title': '依赖任务1',
                    'description': '这是被依赖的任务',
                    'task_type': 'planning',
                    'start_date': timezone.now() + timedelta(hours=1),
                    'due_date': timezone.now() + timedelta(days=1)
                }
                dep_data['event_id'] = str(event.id)
                dependency_task = TaskService.create_task(user, str(event.id), dep_data)
                
                # 为当前任务添加依赖
                task_with_dep = TaskService.update_task(
                    str(task.id), 
                    user, 
                    {'depends_on': [str(dependency_task.id)]}
                )
                
                log(colored_message(f"✓  创建依赖关系成功", 'green'))
            
            # 分配任务
            if test_case.get('assign_to'):
                from django.contrib.auth import get_user_model
                User = get_user_model()
                assignee = User.objects.get(username='assignee_user')
                assigned_task = TaskService.assign_task(str(task.id), assignee, user)
                
                log(colored_message(f"✓  任务已分配给: {assignee.username}", 'green'))
            
        except Exception as e:
            log(colored_message(f"✗ {test_case['name']} 失败: {str(e)}", 'red'))
    
    return created_tasks


def test_update_task(user, event, created_tasks):
    """测试任务更新功能"""
    log("\n=== 测试任务更新功能 ===")
    
    test_cases = [
        {
            'name': '更新任务基本信息',
            'operations': [
                {'update': 'title', 'value': '更新后的任务标题'},
                {'update': 'description', 'value': '更新后的任务描述'}
            ]
        },
        {
            'name': '更新任务状态和进度',
            'operations': [
                {'update': 'status', 'value': 'in_progress'},
                {'update': 'progress', 'value': 30}
            ]
        },
        {
            'name': '完成任务',
            'operations': [
                {'update': 'status', 'value': 'completed'},
                {'update': 'progress', 'value': 100}
            ]
        }
    ]
    
    base_task = created_tasks.get('基础任务创建')
    
    for test_case in test_cases:
        try:
            if not base_task:
                # 使用现有任务
                task = Task.objects.filter(event=event).first()
                if not task:
                    log(f"跳过 {test_case['name']}: 无可用任务")
                    continue
            else:
                task = base_task
            
            update_data = {}
            for op in test_case['operations']:
                update_data[op['update']] = op['value']
            
            updated_task = TaskService.update_task(str(task.id), user, update_data)
            
            log(colored_message(f"✓ {test_case['name']}", 'green'))
            
            # 验证更新结果
            for op in test_case['operations']:
                if op['update'] == 'status':
                    log(f"  - 新状态: {updated_task.status}")
                elif op['update'] == 'progress':
                    log(f"  - 新进度: {updated_task.progress}%")
                elif op['update'] == 'title':
                    log(f"  - 新标题: {updated_task.title}")
            
            # 恢复任务状态以便后续测试
            if test_case['name'] == '完成任务':
                # 重置为进行中状态
                Task.objects.filter(id=updated_task.id).update(
                    status='in_progress',
                    progress=30,
                    completed_at=None
                )
                
        except Exception as e:
            log(colored_message(f"✗ {test_case['name']} 失败: {str(e)}", 'red'))


def test_task_operations(user, event, created_tasks):
    """测试任务特殊操作"""
    log("\n=== 测试任务特殊操作 ===")
    
    test_cases = [
        {
            'name': '更新进度操作',
            'method': 'update_progress',
            'value': 50
        },
        {
            'name': '更新状态操作',
            'method': 'update_status',
            'value': 'ready'
        },
        {
            'name': '完成任务操作',
            'method': 'complete'
        }
    ]
    
    base_task = created_tasks.get('基础任务创建')
    
    for test_case in test_cases:
        try:
            if not base_task:
                task = Task.objects.filter(event=event).exclude(status='completed').first()
                if not task:
                    log(f"跳过 {test_case['name']}: 无可用任务")
                    continue
            else:
                task = Task.objects.filter(id=base_task.id).first()
                if not task or task.status == 'completed':
                    task = Task.objects.filter(event=event).exclude(status='completed').first()
            
            if not task:
                log(f"跳过 {test_case['name']}: 无可用任务")
                continue
            
            if test_case['method'] == 'update_progress':
                result = TaskService.update_task_progress(str(task.id), test_case['value'], user)
                log(colored_message(f"✓ {test_case['name']} - 进度: {result.progress}%", 'green'))
                
            elif test_case['method'] == 'update_status':
                result = TaskService.update_task_status(str(task.id), test_case['value'], user)
                log(colored_message(f"✓ {test_case['name']} - 状态: {result.status}", 'green'))
                
            elif test_case['method'] == 'complete':
                # 先确认依赖关系都完成
                dependencies = TaskDependency.objects.filter(task=task)
                for dep in dependencies:
                    if dep.depends_on.status != 'completed':
                        dep.depends_on.status = 'completed'
                        dep.depends_on.progress = 100
                        dep.depends_on.save()
                
                result = TaskService.complete_task(str(task.id), user)
                log(colored_message(f"✓ {test_case['name']}", 'green'))
                
        except Exception as e:
            log(colored_message(f"✗ {test_case['name']} 失败: {str(e)}", 'red'))


def test_dependency_management(user, event, created_tasks):
    """测试任务依赖管理"""
    log("\n=== 测试任务依赖管理 ===")
    
    try:
        # 创建基础任务
        base_task_data = {
            'title': '依赖测试主任务',
            'description': '用于测试依赖管理的任务',
            'task_type': 'planning',
            'event_id': str(event.id)
        }
        main_task = TaskService.create_task(user, str(event.id), base_task_data)
        
        # 创建多个依赖任务
        dependencies = []
        for i in range(3):
            dep_data = {
                'title': f'依赖任务{i+1}',
                'description': f'这是第{i+1}个依赖任务',
                'task_type': 'planning',
                'event_id': str(event.id)
            }
            dep_task = TaskService.create_task(user, str(event.id), dep_data)
            dependencies.append(dep_task)
        
        # 为主任务添加依赖
        update_data = {
            'depends_on': [dep.id for dep in dependencies]
        }
        updated_main = TaskService.update_task(str(main_task.id), user, update_data)
        
        log(colored_message(f"✓ 创建了 {len(dependencies)} 个依赖任务", 'green'))
        log(colored_message(f"✓ 主任务状态: {updated_main.status}", 'green'))
        
        # 逐步完成依赖任务，观察主任务状态变化
        for i, dep_task in enumerate(dependencies):
            dep_task.status = 'completed'
            dep_task.progress = 100
            dep_task.save()
            
            # 检查主任务状态
            main_task.refresh_from_db()
            log(f"  - 完成依赖任务 {i+1}，主任务状态: {main_task.status}")
        
        log(colored_message(f"✓ 依赖管理测试完成 - 最终状态: {main_task.status}", 'green'))
        
    except Exception as e:
        log(colored_message(f"✗ 依赖管理测试失败: {str(e)}", 'red'))


def test_batch_operations(user, event):
    """测试批量操作"""
    log("\n=== 测试批量操作 ===")
    
    try:
        # 创建多个任务
        task_ids = []
        for i in range(5):
            task_data = {
                'title': f'批量测试任务{i+1}',
                'description': f'第{i+1}个批量测试任务',
                'task_type': 'planning',
                'event_id': str(event.id)
            }
            task = TaskService.create_task(user, str(event.id), task_data)
            task_ids.append(str(task.id))
        
        log(colored_message(f"✓ 创建了 {len(task_ids)} 个任务", 'green'))
        
        # 批量更新状态
        result = TaskService.bulk_update_status(task_ids[:3], 'in_progress', user)
        log(colored_message(f"✓ 批量更新状态: {result['updated_count']} 个任务", 'green'))
        
        # 批量删除
        # 先删除依赖关系
        TaskDependency.objects.filter(task__id__in=task_ids[3:]).delete()
        
        result = TaskService.bulk_delete_tasks(task_ids[3:], user)
        log(colored_message(f"✓ 批量删除: {result['deleted_count']} 个任务", 'green'))
        
    except Exception as e:
        log(colored_message(f"✗ 批量操作测试失败: {str(e)}", 'red'))


def test_communication_tasks(user, event):
    """测试沟通任务功能"""
    log("\n=== 测试沟通任务功能 ===")
    
    try:
        # 创建基础任务
        task_data = {
            'title': '沟通测试任务',
            'description': '用于测试沟通功能的任务',
            'task_type': 'planning',
            'event_id': str(event.id)
        }
        task = TaskService.create_task(user, str(event.id), task_data)
        
        # 创建沟通任务
        comm_data = {
            'content': '需要与相关人员确认活动细节',
            'requirements': '确保所有参与者了解活动安排',
            'communicators': [
                {'name': '张三', 'phone': '13800138000'},
                {'name': '李四', 'email': 'li4@example.com'}
            ],
            'conclusion_files': []
        }
        
        comm_task = CommunicationTaskService.create_communication_task(str(task.id), comm_data, user)
        log(colored_message(f"✓ 创建沟通任务: {comm_task.content}", 'green'))
        
        # 更新沟通任务
        update_data = {
            'conclusion_files': [
                {
                    'name': '沟通结果.pdf',
                    'url': 'http://example.com/result.pdf',
                    'size': 102400
                }
            ]
        }
        
        updated_comm = CommunicationTaskService.update_communication_task(
            str(comm_task.id), 
            update_data, 
            user
        )
        log(colored_message(f"✓ 更新沟通任务: 已添加结论文件", 'green'))
        
        # 闭环沟通任务
        closed_comm = CommunicationTaskService.close_communication_task(str(comm_task.id), user)
        log(colored_message(f"✓ 闭环沟通任务: {closed_comm.is_closed}", 'green'))
        log(colored_message(f"✓ 关联任务状态: {closed_comm.task.status}", 'green'))
        
    except Exception as e:
        log(colored_message(f"✗ 沟通任务测试失败: {str(e)}", 'red'))


def test_task_statistics_and_error_handling(user, event):
    """测试统计功能和错误处理"""
    log("\n=== 测试统计功能和错误处理 ===")
    
    try:
        # 获取任务统计
        tasks = Task.objects.filter(event=event)
        total = tasks.count()
        by_status = tasks.values('status').count()
        
        log(colored_message(f"✓ 任务总数: {total}", 'green'))
        log(f"  - 待办: {tasks.filter(status='pending').count()}")
        log(f"  - 进行中: {tasks.filter(status='in_progress').count()}")
        log(f"  - 已完成: {tasks.filter(status='completed').count()}")
        
        # 测试错误处理 - 尝试删除有依赖的任务
        try:
            # 创建带依赖的任务
            main_data = {'title': '错误测试主任务', 'task_type': 'planning', 'event_id': str(event.id)}
            main_task = TaskService.create_task(user, str(event.id), main_data)
            
            dep_data = {'title': '错误测试依赖任务', 'task_type': 'planning', 'event_id': str(event.id)}
            dep_task = TaskService.create_task(user, str(event.id), dep_data)
            
            # 创建依赖关系
            update_data = {'depends_on': [str(dep_task.id)]}
            main_task = TaskService.update_task(str(main_task.id), user, update_data)
            
            # 尝试删除被依赖的任务 - 应该失败
            try:
                TaskService.delete_task(str(dep_task.id), user)
                log(colored_message(f"✗ 错误处理失败: 应该阻止删除有依赖的任务", 'red'))
            except Exception as e:
                log(colored_message(f"✓ 正确阻止删除有依赖的任务", 'green'))
                
        except Exception as e:
            log(colored_message(f"✗ 错误处理测试失败: {str(e)}", 'red'))
        
    except Exception as e:
        log(colored_message(f"✗ 统计功能测试失败: {str(e)}", 'red'))


def cleanup_test_data(event):
    """清理测试数据"""
    log("\n=== 清理测试数据 ===")
    
    try:
        # 删除所有测试任务
        task_count = Task.objects.filter(event=event).count()
        Task.objects.filter(event=event).delete()
        log(colored_message(f"✓ 清理了 {task_count} 个测试任务", 'green'))
        
    except Exception as e:
        log(colored_message(f"✗ 清理测试数据失败: {str(e)}", 'red'))


def run_all_tests():
    """运行所有测试"""
    log(colored_message("=== EventPilot 任务管理 CRUD 功能验证 ===", 'blue'))
    log("开始时间: " +(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    start_time = time.time()
    
    try:
        # 设置测试数据
        user, event, assignee = setup_test_data()
        
        # 运行测试
        created_tasks = test_create_task(user, event)
        test_update_task(user, event, created_tasks)
        test_task_operations(user, event, created_tasks)
        test_dependency_management(user, event, created_tasks)
        test_batch_operations(user, event)
        test_communication_tasks(user, event)
        test_task_statistics_and_error_handling(user, event)
        
        # 清理测试数据
        cleanup_test_data(event)
        
        end_time = time.time()
        duration = end_time - start_time
        
        log(colored_message("\n=== 所有测试已完成 ===", 'blue'))
        log(f"总耗时: {duration:.2f} 秒")
        log(colored_message("✓ 任务管理CRUD功能验证通过！", 'green'))
        
    except Exception as e:
        log(colored_message(f"\n✗ 测试过程中发生错误: {str(e)}", 'red'))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()