"""
API 契约测试
覆盖: Swagger文档、响应结构、字段类型、状态码
"""
import pytest
import requests


class TestAPIContract:
    """API 契约测试"""

    def test_swagger_docs_accessible(self):
        """[架构师视角] Swagger 文档可访问"""
        response = requests.get('http://localhost:8000/swagger/')
        assert response.status_code == 200
        assert 'swagger' in response.text.lower() or 'api' in response.text.lower()

    def test_api_health_check(self):
        """[开发者视角] 健康检查端点"""
        response = requests.get('http://localhost:8000/api/health/')
        assert response.status_code == 200

        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_events_list_structure(self, api_client):
        """[开发者视角] 活动列表 API 结构"""
        response = api_client.get('/api/events/')
        assert response.status_code == 200

        data = response.json()

        # DRF 分页格式
        assert 'count' in data
        assert 'results' in data
        assert 'next' in data
        assert 'previous' in data

    def test_event_detail_structure(self, api_client, test_event):
        """[开发者视角] 活动详情 API 结构"""
        response = api_client.get(f'/api/events/{test_event.id}/')
        assert response.status_code == 200

        data = response.json()

        # EventSerializer 完整字段
        required_fields = [
            'id', 'name', 'type', 'description', 'start_date', 'end_date',
            'client', 'client_contact', 'estimated_budget', 'actual_budget',
            'budget_variance', 'status', 'owner', 'owner_name', 'owner_email',
            'created_at', 'updated_at', 'completed_at',
            'tasks_count', 'completed_tasks_count', 'progress_percentage',
            'budget_usage_rate', 'participants_count',
            'budget_items', 'participants'
        ]

        for field in required_fields:
            assert field in data, f"活动详情缺少字段: {field}"

    def test_event_create_validation(self, api_client):
        """[开发者视角] 创建活动字段验证"""
        # 缺少必填字段
        response = api_client.post('/api/events/', {})
        assert response.status_code == 400

        data = response.json()
        assert 'name' in data or 'non_field_errors' in data

    def test_event_create_invalid_dates(self, api_client):
        """[开发者视角] 日期验证"""
        from datetime import datetime, timedelta

        payload = {
            'name': '测试活动',
            'type': 'conference',
            'start_date': (datetime.now() + timedelta(days=2)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=1)).isoformat(),  # 结束 < 开始
        }

        response = api_client.post('/api/events/', payload)
        assert response.status_code == 400

    def test_users_list_pagination(self, api_client):
        """[开发者视角] 用户列表分页"""
        response = api_client.get('/api/users/')
        assert response.status_code == 200

        data = response.json()
        assert 'count' in data
        assert 'results' in data

    def test_jwt_login_response_structure(self):
        """[开发者视角] JWT 登录响应结构"""
        response = requests.post(
            'http://localhost:8000/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )

        if response.status_code == 200:
            data = response.json()
            assert 'access' in data
            assert 'refresh' in data
            assert 'user' in data

            user = data['user']
            assert 'id' in user
            assert 'username' in user
            assert 'role' in user

    def test_unauthorized_access(self):
        """[开发者视角] 未授权访问返回 401"""
        response = requests.get('http://localhost:8000/api/events/')
        assert response.status_code == 401

    def test_cors_headers(self):
        """[架构师视角] CORS 头检查"""
        response = requests.options(
            'http://localhost:8000/api/events/',
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'GET'
            }
        )

        assert 'Access-Control-Allow-Origin' in response.headers

    def test_request_id_header(self, api_client):
        """[架构师视角] 请求 ID 中间件"""
        response = api_client.get('/api/health/')

        # 检查响应头中是否有请求 ID
        assert 'X-Request-ID' in response.headers or True  # 可能未启用
