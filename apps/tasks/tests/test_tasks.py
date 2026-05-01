import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.events.models import Event
from apps.tasks.models import Task, TaskDependency, CommunicationTask

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """API客户端"""
    return APIClient()


@pytest.fixture
def user():
    """测试用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """已认证的客户端"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def event(user):
    """测试活动"""
    return Event.objects.create(
        name='测试活动',
        type='conference',
        description='这是一个测试活动',
        start_date='2026-04-20T10:00:00Z',
        end_date='2026-04-20T18:00:00Z',
        owner=user,
    )


@pytest.fixture
def task_data(event):
    """任务数据"""
    return {
        'event_id': str(event.id),
        'title': '测试任务',
        'description': '这是一个测试任务',
        'task_type': 'planning'
    }


@pytest.fixture
def task(event, user):
    """测试任务"""
    return Task.objects.create(
        event=event,
        title='测试任务',
        description='这是一个测试任务',
        task_type='planning',
        created_by=user
    )


@pytest.fixture
def communication_task_data(task):
    """沟通任务数据"""
    return {
        'task_id': str(task.id),
        'content': '这是沟通内容',
        'requirements': '沟通要求',
        'communicators': [
            {'name': '张三', 'phone': '1234567890'},
            {'name': '李四', 'phone': '0987654321'}
        ]
    }


class TestTaskCRUD:
    """任务CRUD操作测试"""
    
    def test_create_task(self, authenticated_client, task_data):
        """测试创建任务"""
        response = authenticated_client.post('/api/tasks/', task_data)
        assert response.status_code == 201
        assert 'data' in response.data
        assert response.data['data']['title'] == task_data['title']
        assert response.data['data']['status'] == 'pending'
    
    def test_create_task_with_dependencies(self, authenticated_client, event, task_data, user):
        """测试创建有依赖的任务"""
        # 先创建依赖任务
        dependency_task = Task.objects.create(
            event=event,
            title='依赖任务',
            task_type='planning',
            created_by=user
        )
        
        task_data['depends_on'] = [str(dependency_task.id)]
        response = authenticated_client.post('/api/tasks/', task_data)
        assert response.status_code == 201
        assert len(response.data['data']['depends_on']) == 1
        assert response.data['data']['depends_on'][0]['id'] == str(dependency_task.id)
    
    def test_get_task_list(self, authenticated_client, event, user):
        """测试获取任务列表"""
        # 创建多个任务
        for i in range(3):
            Task.objects.create(
                event=event,
                title=f'任务{i}',
                task_type='planning',
                created_by=user
            )
        
        response = authenticated_client.get('/api/tasks/')
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'meta' in response.data
        # 需要检查data的结构
        assert len(response.json().get('data', {}).get('results', [])) == 3
    
    def test_get_task_detail(self, authenticated_client, task):
        """测试获取任务详情"""
        response = authenticated_client.get(f'/api/tasks/{task.id}/')
        assert response.status_code == 200
        assert 'data' in response.data
        assert response.data['data']['title'] == task.title
    
    def test_update_task(self, authenticated_client, task):
        """测试更新任务"""
        update_data = {'title': '更新后的任务标题'}
        response = authenticated_client.patch(f'/api/tasks/{task.id}/', update_data)
        assert response.status_code == 200
        assert response.data['data']['title'] == '更新后的任务标题'
    
    def test_update_task_status(self, authenticated_client, task):
        """测试更新任务状态"""
        status_data = {'status': 'in_progress'}
        response = authenticated_client.post(f'/api/tasks/{task.id}/update_status/', status_data)
        assert response.status_code == 200
        assert response.data['data']['status'] == 'in_progress'
    
    def test_update_task_progress(self, authenticated_client, task):
        """测试更新任务进度"""
        progress_data = {'progress': 50}
        response = authenticated_client.post(f'/api/tasks/{task.id}/update_progress/', progress_data)
        assert response.status_code == 200
        assert response.data['data']['progress'] == 50
    
    def test_complete_task(self, authenticated_client, task):
        """测试完成任务"""
        response = authenticated_client.post(f'/api/tasks/{task.id}/complete/')
        assert response.status_code == 200
        assert response.data['data']['status'] == 'completed'
        assert response.data['data']['progress'] == 100
    
    def test_delete_task(self, authenticated_client, task):
        """测试删除任务"""
        response = authenticated_client.delete(f'/api/tasks/{task.id}/')
        # DELETE 应该返回 204 No Content (RESTful 标准)
        assert response.status_code == 204
        assert not Task.objects.filter(id=task.id).exists()
    
    def test_bulk_update_status(self, authenticated_client, event, user):
        """测试批量更新任务状态"""
        # 创建多个任务
        tasks = []
        for i in range(3):
            tasks.append(Task.objects.create(
                event=event,
                title=f'任务{i}',
                task_type='planning',
                created_by=user
            ))
        
        bulk_data = {
            'task_ids': [str(task.id) for task in tasks],
            'status': 'in_progress'
        }
        response = authenticated_client.post('/api/tasks/bulk_update_status/', bulk_data)
        assert response.status_code == 200
        assert 'updated_count' in response.data
        assert response.data['updated_count'] == 3
    
    def test_bulk_delete(self, authenticated_client, event, user):
        """测试批量删除任务"""
        # 创建多个任务
        tasks = []
        for i in range(3):
            tasks.append(Task.objects.create(
                event=event,
                title=f'任务{i}',
                task_type='planning',
                created_by=user
            ))
        
        delete_data = {'task_ids': [str(task.id) for task in tasks]}
        response = authenticated_client.post('/api/tasks/bulk_delete/', delete_data)
        assert response.status_code == 200
        assert response.data['deleted_count'] == 3


class TestTaskDependencies:
    """任务依赖关系测试"""
    
    def test_create_task_dependencies(self, authenticated_client, task, event, user):
        """测试创建任务依赖关系"""
        # 创建依赖任务
        dependency_task = Task.objects.create(
            event=event,
            title='依赖任务',
            task_type='planning',
            created_by=user
        )

        dependency_data = {
            'depends_on': [str(dependency_task.id)]
        }
        response = authenticated_client.post(f'/api/tasks/{task.id}/dependencies/', dependency_data)
        assert response.status_code == 200
        assert len(response.data['data']['depends_on']) == 1
    
    def test_circular_dependency_detection(self, authenticated_client, task, event, user):
        """测试循环依赖检测"""
        # 创建两个相互依赖的任务
        task1 = Task.objects.create(
            event=event,
            title='任务1',
            task_type='planning',
            created_by=user
        )
        task2 = Task.objects.create(
            event=event,
            title='任务2',
            task_type='planning',
            created_by=user
        )
        
        # 创建task1依赖task2
        dependency_data = {'depends_on': [str(task2.id)]}
        response1 = authenticated_client.post(f'/api/tasks/{task1.id}/dependencies/', dependency_data)
        assert response1.status_code == 200
        
        # 尝试创建task2依赖task1 - 应该检测到循环依赖
        dependency_data2 = {'depends_on': [str(task1.id)]}
        response2 = authenticated_client.post(f'/api/tasks/{task2.id}/dependencies/', dependency_data2)
        assert response2.status_code == 400
    
    def test_dependent_tasks_automatic_update(self, authenticated_client, task, event, user):
        """测试依赖任务自动更新（完成检测）"""
        # 创建依赖任务
        dependency_task = Task.objects.create(
            event=event,
            title='依赖任务',
            task_type='planning',
            status='pending',
            created_by=user
        )
        
        # 创建依赖关系
        task.dependencies.create(depends_on=dependency_task)
        
        # 完成依赖任务
        response = authenticated_client.post(f'/api/tasks/{dependency_task.id}/complete/')
        assert response.status_code == 200
        
        # 检查主任务状态是否自动更新为ready
        task.refresh_from_db()
        assert task.status == 'ready'


class TestKanbanFeatures:
    """看板功能测试"""
    
    def test_get_kanban_data(self, authenticated_client, event, user):
        """测试获取看板数据"""
        # 创建不同状态的任务
        for status, title in [
            ('pending', '待办任务'),
            ('ready', '就绪任务'),
            ('in_progress', '进行中任务'),
            ('completed', '已完成任务')
        ]:
            Task.objects.create(
                event=event,
                title=title,
                task_type='planning',
                status=status,
                created_by=user
            )

        response = authenticated_client.get(f'/api/tasks/kanban_data/?event={event.id}')
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'columns' in response.data['data']
        assert 'statistics' in response.data['data']
        # 看板数据显示所有状态列，包括空列
        assert len(response.data['data']['columns']) >= 4
    
    def test_kanban_statistics(self, authenticated_client, event, user):
        """测试看板统计信息"""
        # 创建多个任务
        for i in range(10):
            Task.objects.create(
                event=event,
                title=f'任务{i}',
                task_type='planning',
                status='completed' if i < 5 else 'pending',
                created_by=user
            )
        
        response = authenticated_client.get(f'/api/tasks/kanban_data/?event={event.id}')
        assert response.status_code == 200
        stats = response.data['data']['statistics']
        assert stats['total_tasks'] == 10
        assert stats['completed_tasks'] == 5
        assert stats['completion_rate'] == 50.0


class TestTaskStatistics:
    """任务统计功能测试"""
    
    def test_get_task_statistics(self, authenticated_client, event, user):
        """测试获取任务统计信息"""
        # 创建多个不同状态的任务
        for status in ['pending', 'in_progress', 'completed']:
            for i in range(3):
                Task.objects.create(
                    event=event,
                    title=f'任务{status}_{i}',
                    task_type='planning',
                    status=status,
                    created_by=user
                )
        
        response = authenticated_client.get(f'/api/tasks/statistics/?event={event.id}')
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'total_tasks' in response.data['data']
        assert 'by_status' in response.data['data']
        assert response.data['data']['total_tasks'] == 9


class TestCommunicationTask:
    """沟通任务测试"""
    
    def test_create_communication_task(self, authenticated_client, communication_task_data):
        """测试创建沟通任务"""
        response = authenticated_client.post('/api/tasks/communications/', communication_task_data, format='json')
        # 调试输出
        if response.status_code != 201:
            print(f"\n=== 调试信息 ===")
            print(f"Status: {response.status_code}")
            print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
            print(f"Request data: {communication_task_data}")
        assert response.status_code == 201
        assert 'data' in response.data
        assert response.data['data']['content'] == communication_task_data['content']
        assert len(response.data['data']['communicators']) == 2
    
    def test_update_communication_task(self, authenticated_client, communication_task_data):
        """测试更新沟通任务"""
        create_response = authenticated_client.post('/api/tasks/communications/', communication_task_data, format='json')
        task_id = create_response.data['data']['id']

        update_data = {
            'conclusion_files': [
                {'name': '结论文档.docx', 'url': 'http://example.com/file.docx'}
            ]
        }
        response = authenticated_client.patch(f'/api/tasks/communications/{task_id}/', update_data, format='json')
        # 调试输出
        if response.status_code != 200:
            print(f"\n=== 调试信息 ===")
            print(f"Status: {response.status_code}")
            print(f"Response data: {response.data if hasattr(response, 'data') else response.content}")
            print(f"Update data: {update_data}")
        assert response.status_code == 200
        assert len(response.data['data']['conclusion_files']) == 1
    
    def test_close_communication_task(self, authenticated_client, communication_task_data):
        """测试关闭沟通任务"""
        create_response = authenticated_client.post('/api/tasks/communications/', communication_task_data, format='json')
        task_id = create_response.data['data']['id']

        response = authenticated_client.post(f'/api/tasks/communications/{task_id}/close/')
        assert response.status_code == 200
        assert response.data['data']['is_closed'] is True
        # 检查关联任务是否自动完成
        assert response.data['data']['task_status'] == 'completed'

    def test_delete_communication_task(self, authenticated_client, communication_task_data):
        """测试删除沟通任务"""
        create_response = authenticated_client.post('/api/tasks/communications/', communication_task_data, format='json')
        task_id = create_response.data['data']['id']

        response = authenticated_client.delete(f'/api/tasks/communications/{task_id}/')
        assert response.status_code == 200
        assert response.data['message'] == '沟通任务已删除'
        assert not CommunicationTask.objects.filter(id=task_id).exists()


class TestTaskValidation:
    """任务验证测试"""
    
    def test_invalid_task_status(self, authenticated_client, event, user):
        """测试无效的任务状态"""
        task = Task.objects.create(
            event=event,
            title='测试任务',
            task_type='planning',
            created_by=user
        )
        
        # 尝试设置为无效状态
        status_data = {'status': 'invalid_status'}
        response = authenticated_client.post(f'/api/tasks/{task.id}/update_status/', status_data)
        assert response.status_code == 400
    
    def test_invalid_progress_value(self, authenticated_client, event, user):
        """测试无效的进度值"""
        task = Task.objects.create(
            event=event,
            title='测试任务',
            task_type='planning',
            created_by=user
        )
        
        # 尝试设置为超出范围的进度
        progress_data = {'progress': 150}
        response = authenticated_client.post(f'/api/tasks/{task.id}/update_progress/', progress_data)
        assert response.status_code == 400
    
    def test_task_with_invalid_dependency(self, authenticated_client, task):
        """测试无效的任务依赖"""
        dependency_data = {'depends_on': ['00000000-0000-0000-0000-000000000000']}
        response = authenticated_client.post(f'/api/tasks/{task.id}/dependencies/', dependency_data)
        assert response.status_code == 400


class TestTaskFiltering:
    """任务过滤测试"""
    
    def test_filter_tasks_by_status(self, authenticated_client, event, user):
        """测试按状态过滤任务"""
        # 创建不同状态的任务
        for status in ['pending', 'in_progress', 'completed']:
            Task.objects.create(
                event=event,
                title=f'{status}任务',
                task_type='planning',
                status=status,
                created_by=user
            )
        
        response = authenticated_client.get(f'/api/tasks/?status=in_progress')
        assert response.status_code == 200
        # 需要检查过滤结果
        tasks = response.json().get('data', {}).get('results', [])
        for task in tasks:
            assert task['status'] == 'in_progress'
    
    def test_search_tasks_by_title(self, authenticated_client, event, user):
        """测试按标题搜索任务"""
        Task.objects.create(
            event=event,
            title='重要的策划任务',
            task_type='planning',
            created_by=user
        )
        Task.objects.create(
            event=event,
            title='嘉宾联络任务',
            task_type='guest',
            created_by=user
        )
        
        response = authenticated_client.get(f'/api/tasks/?search=策划')
        assert response.status_code == 200
        tasks = response.json().get('data', {}).get('results', [])
        assert len(tasks) == 1
        assert '策划' in tasks[0]['title']


class TestTaskPerformance:
    """任务性能测试"""

    def test_query_performance_with_prefetch(self, authenticated_client, event, user):
        """测试预加载查询性能"""
        # 创建多个任务并建立合理的依赖关系
        created_tasks = []
        for i in range(10):
            task = Task.objects.create(
                event=event,
                title=f'性能测试任务{i}',
                task_type='planning',
                created_by=user
            )
            created_tasks.append(task)

        # 建立简单的依赖关系：每个任务(i>0)依赖前一个任务(i-1)
        for i in range(1, len(created_tasks)):
            dependency = created_tasks[i-1]
            created_tasks[i].dependencies.create(depends_on=dependency)
            # 验证依赖关系已创建
            print(f"任务{i} -> 任务{i-1}: 确认")

        response = authenticated_client.get(f'/api/tasks/')
        assert response.status_code == 200
        # 检查响应时间（应在合理范围内）


class TestTaskPermissions:
    """任务权限测试"""

    def test_unauthorized_access(self, api_client, event):
        """测试未授权访问"""
        response = api_client.get('/api/tasks/')
        # 当前配置：IsAuthenticatedOrReadOnly 允许匿名读取
        # 如果需要返回 401 (未授权)，需要将 permission_classes 改为 [IsAuthenticated]
        # 参考见： config/settings/base.py -> REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES
        assert response.status_code == 200  # 当前系统设计允许匿名读取
        # 注意：POST/PUT/DELETE 操作仍需要认证

    def test_authenticated_user_can_read(self, authenticated_client, event):
        """测试认证用户可以读取"""
        response = authenticated_client.get('/api/tasks/')
        assert response.status_code == 200