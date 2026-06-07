"""
BR-V0-R12 批量删除功能测试
测试场景：
1. 选中无任务关联的已取消活动，应能成功删除
2. 选中含进行中任务的活动，应拒绝删除并显示错误
"""
import pytest
import requests
from pytest import approx
from typing import Dict, Any


class TestBatchDeleteBRV0R12:
    """BR-V0-R12 批量删除 BUG 验收测试"""
    
    @pytest.fixture
    def auth_headers(self):
        """获取认证 token"""
        resp = requests.post(
            'http://172.28.166.164:8000/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )
        token = resp.json()['data']['token']
        return {'Authorization': f'Bearer {token}'}
    
    @pytest.fixture
    def test_events(self, auth_headers):
        """获取测试用的活动"""
        resp = requests.get(
            'http://172.28.166.164:8000/api/events/',
            headers=auth_headers
        )
        events = resp.json()
        
        # 获取已取消活动
        cancelled_events = [
            e for e in events.get('results', events)
            if e.get('status') == 'cancelled'
        ]
        
        return cancelled_events[:3]  # 返回前3个用于测试
    
    def test_delete_without_task(self, auth_headers, test_events):
        """
        场景1：删除无任务关联的已取消活动
        预期：删除成功，返回200
        """
        if not test_events:
            pytest.skip("没有可用的已取消活动进行测试")
        
        # 查找无任务关联的活动
        target = None
        for event in test_events:
            if event.get('tasks_c', 0) == 0 and not event.get('has_in_progress_tasks'):
                target = event
                break
        
        if not target:
            pytest.skip("没有找到无任务关联的已取消活动")
        
        event_id = target['id']
        print(f"\n测试活动: {target['name']}")
        print(f"  ID: {event_id}")
        print(f"  tasks数量: {target.get('tasks_c', 0)}")
        print(f"  has_in_progress_tasks: {target.get('has_in_progress_tasks')}")
        
        # 执行删除
        delete_resp = requests.delete(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
        
        print(f"删除响应状态码: {delete_resp.status_code}")
        print(f"删除响应: {delete_resp.text}")
        
        # 预期：删除成功
        assert delete_resp.status_code == 200, f"删除失败: {delete_resp.text}"
        
        # 验证活动已被删除
        get_resp = requests.get(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
        assert get_resp.status_code in [404, 200], "活动应该已被删除"
        if get_resp.status_code == 200:
            assert not get_resp.json().get('id'), "活动ID应该为空"
    
    def test_delete_with_in_progress_task_blocked(self, auth_headers, test_events):
        """
        场景2：尝试删除含进行中任务的活动
        预期：删除被拒绝，返回400错误
        """
        # 首先创建一个活动和任务
        create_resp = requests.post(
            'http://172.28.166.164:8000/api/events/',
            headers=auth_headers,
            json={
                'name': '批量删除测试活动-含进行中任务',
                'type': 'meeting',
                'start_date': '2026-06-01',
                'status': 'cancelled'
            }
        )
        assert create_resp.status_code == 201
        event_id = create_resp.json()['id']
        
        # 创建进行中任务
        task_resp = requests.post(
            'http://172.28.166.164:8000/api/tasks/',
            headers=auth_headers,
            json={
                'event': event_id,
                'name': '进行中任务',
                'status': 'in_progress'
            }
        )
        assert task_resp.status_code == 201
        
        print(f"\n测试活动: 批量删除测试活动-含进行中任务")
        print(f"  ID: {event_id}")
        print(f"  已创建进行中任务")
        
        # 刷新活动信息以获取 has_in_progress_tasks
        get_resp = requests.get(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
        event_info = get_resp.json()
        print(f"  has_in_progress_tasks: {event_info.get('has_in_progress_tasks')}")
        
        # 尝试删除
        delete_resp = requests.delete(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
        
        print(f"删除响应状态码: {delete_resp.status_code}")
        print(f"删除响应: {delete_resp.text}")
        
        # 预期：删除被拒绝
        assert delete_resp.status_code == 400, f"应该被拒绝删除: {delete_resp.text}"
        assert '进行中' in delete_resp.text or 'in_progress' in delete_resp.text, "错误消息应包含'进行中'"
        
        # 验证活动仍然存在
        verify_resp = requests.get(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
        assert verify_resp.status_code == 200, "活动应该仍然存在"
        
        # 清理：先删除任务，再删除活动
        # 删除所有关联任务
        tasks_resp = requests.get(
            f'http://172.28.166.164:8000/api/tasks/?event={event_id}',
            headers=auth_headers
        )
        for task in tasks_resp.json().get('results', []):
            requests.delete(
                f"http://172.28.166.164:8000/api/tasks/{task['id']}/",
                headers=auth_headers
            )
        
        # 删除活动
        requests.delete(
            f'http://172.28.166.164:8000/api/events/{event_id}/',
            headers=auth_headers
        )
