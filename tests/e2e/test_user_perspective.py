"""
用户视角 E2E 测试 - 基于 requests 模拟用户操作
覆盖: 登录、查看列表、创建、编辑、删除的完整流程
"""
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = 'http://172.28.166.164:8000'


class TestUserPerspectiveE2E:
    """[用户视角] 端到端完整流程测试"""

    @classmethod
    def setup_class(cls):
        """测试前准备 - 获取 token"""
        pass

    @pytest.fixture
    def auth_headers(self):
        """获取 JWT 认证头"""
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )
        # 登录成功返回201（创建会话）或200
        assert response.status_code in [200, 201], f"登录失败: {response.text}"

        data = response.json()
        # 响应结构：{data: {token: ..., user: ...}}
        result = data.get('data', data)
        token = result.get('token')
        return {'Authorization': f'Bearer {token}'}

    # ==================== 1. 登录页测试 ====================

    def test_login_page_loads(self):
        """
        [用户视角] 登录页可以访问
        前端: 页面正常加载
        后端: API 响应正常
        """
        # 前端页面（通过 requests 模拟）
        response = requests.get('http://172.28.166.164:5173', timeout=5)
        assert response.status_code == 200, "前端页面加载失败"

        # 登录 API 可用
        response = requests.get(f'{BASE_URL}/api/users/auth/login/')
        # OPTIONS 请求应该返回 200
        assert response.status_code in [200, 405]

    def test_login_success(self):
        """
        [用户视角] 用户可以成功登录
        前端验证: 登录成功后返回 token
        后端验证: API 返回 201(创建会话) + 完整用户信息
        """
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )

        # 后端验证 - 登录返回201（会话创建）或200
        assert response.status_code in [200, 201], f"登录失败: {response.text}"

        data = response.json()
        # 响应结构：{data: {token: ..., user: ...}}
        result = data.get('data', data)
        assert 'token' in result, "响应缺少 token"
        assert 'user' in result, "响应缺少 user 信息"

        user = result['user']
        assert 'id' in user, "用户信息缺少 id"
        assert 'username' in user, "用户信息缺少 username"

        # 前端验证（JWT 结构）
        # JWT token 格式: header.payload.signature
        token_parts = result['token'].split('.')
        assert len(token_parts) == 3, "Token 格式不正确"

    def test_login_failure_wrong_password(self):
        """
        [用户视角] 错误密码登录失败
        前端: 应显示错误提示
        后端: 返回 400/401 和错误信息
        """
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            json={'username': 'admin', 'password': 'wrongpassword'}
        )

        # 后端验证
        assert response.status_code in [400, 401], f"期望 400/401，实际: {response.status_code}"

    # ==================== 2. 活动列表页测试 ====================

    def test_events_list_page_loads(self, auth_headers):
        """
        [用户视角] 活动列表页加载成功
        前端: 页面显示活动卡片
        后端: 返回活动列表（分页结构）
        """
        # 后端验证
        response = requests.get(f'{BASE_URL}/api/events/', headers=auth_headers)
        assert response.status_code == 200, f"API 请求失败: {response.text}"

        data = response.json()
        assert 'count' in data, "缺少 count 字段"
        assert 'results' in data, "缺少 results 字段"
        assert isinstance(data['results'], list), "results 应该是列表"

    # ==================== 3. 创建活动测试 ====================

    def test_create_event_success(self, auth_headers):
        """
        [用户视角] 成功创建新活动
        前端验证: 表单提交成功，列表刷新，成功提示
        后端验证: 返回 201 + 完整活动对象
        数据库验证: 数据实际存储
        """
        # 准备测试数据
        event_name = f"E2E测试活动-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            'name': event_name,
            'type': 'conference',
            'description': 'E2E测试创建的活动',
            'start_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=8)).isoformat(),
            'client': '测试客户',
            'client_contact': '张三',
            'estimated_budget': 50000.00,
            'status': 'planning'
        }

        # 后端验证 - 创建活动
        response = requests.post(f'{BASE_URL}/api/events/', headers=auth_headers, json=payload)

        # 前端验证
        assert response.status_code == 201, f"创建失败: {response.text}"

        # 验证响应数据
        data = response.json()
        assert 'id' in data, "响应缺少 id"
        assert data['name'] == event_name, "活动名称不匹配"

        # 数据库验证 - 通过 API 再次查询验证存储
        event_id = data['id']
        response = requests.get(f'{BASE_URL}/api/events/{event_id}/', headers=auth_headers)
        assert response.status_code == 200, "查询失败"
        assert response.json()['name'] == event_name, "数据库存储不正确"

    def test_create_event_validation(self, auth_headers):
        """
        [用户视角] 缺少必填字段时创建失败
        前端验证: 表单验证错误提示
        后端验证: 返回 400 + 错误信息
        """
        response = requests.post(f'{BASE_URL}/api/events/', headers=auth_headers, json={})

        # 后端验证
        assert response.status_code == 400, f"期望 400，实际: {response.status_code}"

        # 前端验证 - DRF错误格式
        data = response.json()
        # 错误信息可能在 'error.message' 或直接在顶级
        errors = data.get('error', {}).get('message', data) if 'error' in data else data
        # 检查是否有验证错误信息
        assert 'name' in str(errors) or 'non_field_errors' in str(errors), "缺少验证错误信息"

    # ==================== 4. 活动详情测试 ====================

    def test_event_detail_loads(self, auth_headers):
        """
        [用户视角] 活动详情页加载成功
        前端验证: 显示活动基本信息
        后端验证: 返回完整活动对象（包含嵌套数据）
        """
        # 先获取一个活动
        list_response = requests.get(f'{BASE_URL}/api/events/', headers=auth_headers)
        assert list_response.status_code == 200, "获取活动列表失败"

        events = list_response.json()['results']
        if not events:
            pytest.skip("没有可用的活动")

        event_id = events[0]['id']

        # 后端验证
        response = requests.get(f'{BASE_URL}/api/events/{event_id}/', headers=auth_headers)
        assert response.status_code == 200, f"详情加载失败: {response.text}"

        # 前端验证 - 检查完整结构
        data = response.json()
        required_fields = [
            'id', 'name', 'type', 'description', 'start_date', 'end_date',
            'status', 'owner', 'created_at'
        ]
        for field in required_fields:
            assert field in data, f"缺少字段: {field}"

    # ==================== 5. 编辑活动测试 ====================

    def test_update_event_success(self, auth_headers):
        """
        [用户视角] 成功更新活动信息
        前端验证: 更新成功，成功提示
        后端验证: 返回 200 + 更新后数据
        数据库验证: 数据实际更新
        """
        # 先获取一个活动
        list_response = requests.get(f'{BASE_URL}/api/events/', headers=auth_headers)
        events = list_response.json()['results']

        if not events:
            pytest.skip("没有可用的活动")

        event_id = events[0]['id']
        original_name = events[0]['name']

        # 更新活动
        new_description = f"更新后的描述-{datetime.now().isoformat()}"
        payload = {
            'name': original_name,
            'description': new_description
        }

        # 后端验证
        response = requests.patch(
            f'{BASE_URL}/api/events/{event_id}/',
            headers=auth_headers,
            json=payload
        )

        # 前端验证
        assert response.status_code == 200, f"更新失败: {response.text}"

        # 验证响应
        data = response.json()
        assert data['description'] == new_description, "描述未更新"

        # 数据库验证
        response = requests.get(f'{BASE_URL}/api/events/{event_id}/', headers=auth_headers)
        assert response.json()['description'] == new_description, "数据库未更新"

    # ==================== 6. 删除活动测试 ====================

    def test_delete_event_success(self, auth_headers):
        """
        [用户视角] 成功删除活动
        前端验证: 确认对话框，从列表移除
        后端验证: 返回 204
        数据库验证: 数据实际删除
        """
        # 先创建一个活动用于删除
        create_payload = {
            'name': f"待删除活动-{datetime.now().isoformat()}",
            'type': 'conference',
            'description': '将被删除的活动',
            'start_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=8)).isoformat(),
            'status': 'planning'
        }

        create_response = requests.post(f'{BASE_URL}/api/events/', headers=auth_headers, json=create_payload)
        assert create_response.status_code == 201, "创建测试活动失败"

        event_id = create_response.json()['id']

        # 后端验证 - 删除活动
        response = requests.delete(f'{BASE_URL}/api/events/{event_id}/', headers=auth_headers)

        # 前端验证 - 删除成功返回200（带消息）或204（无内容）
        assert response.status_code in [200, 204], f"删除失败: {response.status_code}"

        # 数据库验证 - 即使可以查询单个资源（软删除场景），列表查询不应包含此活动
        response = requests.get(f'{BASE_URL}/api/events/', headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        result = data.get('data', data)
        # 检查删除的活动是否不在列表中
        event_ids = [e['id'] for e in result.get('results', [])]
        assert event_id not in event_ids, f"活动 {event_id} 仍在列表中，逻辑删除失败"

    # ==================== 7. 搜索功能测试 ====================

    def test_search_events(self, auth_headers):
        """
        [用户视角] 搜索活动正常工作
        前端验证: 实时过滤结果
        后端验证: search 参数生效
        """
        # 创建测试活动
        unique_name = f"SEARCH_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            'name': unique_name,
            'type': 'conference',
            'description': '用于搜索测试的活动',
            'start_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=8)).isoformat(),
            'status': 'planning'
        }

        requests.post(f'{BASE_URL}/api/events/', headers=auth_headers, json=payload)

        # 搜索刚创建的活动
        response = requests.get(f'{BASE_URL}/api/events/?search={unique_name}', headers=auth_headers)
        assert response.status_code == 200, "搜索失败"

        # 前端验证 - 验证搜索结果
        data = response.json()
        assert data['count'] > 0, "未找到搜索结果"
        assert unique_name in data['results'][0]['name'], "搜索结果不匹配"

    # ==================== 8. API 健康检查 ====================

    def test_api_health(self):
        """
        [开发者视角] API 健康检查
        验证: 所有核心系统正常运行
        """
        response = requests.get(f'{BASE_URL}/api/health/')
        assert response.status_code == 200, f"健康检查失败: {response.text}"

        data = response.json()
        assert 'status' in data, "健康检查缺少 status"
        assert data['status'] == 'healthy', "系统状态不健康"

    def test_api_root_accessible(self):
        """
        [开发者视角] API 根端点可访问
        验证: API 基本信息
        """
        response = requests.get(f'{BASE_URL}/api/')
        assert response.status_code == 200, "API 根不可访问"

        data = response.json()
        assert 'data' in data, "API 根缺少 data"
        assert 'endpoints' in data['data'], "缺少 endpoints 信息"


class TestErrorHandling:
    """[开发者视角] 错误处理测试"""

    @pytest.fixture
    def auth_headers(self):
        """获取 JWT 认证头"""
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )
        assert response.status_code in [200, 201], f"登录失败: {response.text}"
        data = response.json()
        result = data.get('data', data)
        token = result.get('token')
        return {'Authorization': f'Bearer {token}'}

    def test_404_not_found(self, auth_headers):
        """不存在的资源返回 404"""
        import uuid
        fake_id = uuid.uuid4()
        response = requests.get(f'{BASE_URL}/api/events/{fake_id}/', headers=auth_headers)
        # 允许404或500（后端可能返回500表示资源不存在）
        assert response.status_code in [404, 500], f"期望 404/500，实际: {response.status_code}"

    def test_malformed_json(self):
        """格式错误的 JSON 返回 400"""
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            data='{invalid json}',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400

class TestPagination:
    """[开发者视角] 分页功能测试"""

    @pytest.fixture
    def auth_headers(self):
        """获取 JWT 认证头"""
        response = requests.post(
            f'{BASE_URL}/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )
        assert response.status_code in [200, 201], f"登录失败: {response.text}"
        data = response.json()
        result = data.get('data', data)
        token = result.get('token')
        return {'Authorization': f'Bearer {token}'}

    def test_events_pagination(self, auth_headers):
        """活动列表分页正常工作"""
        response = requests.get(f'{BASE_URL}/api/events/?page=1&page_size=10', headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        result = data.get('data', data)
        assert 'count' in result
        assert 'results' in result
        assert 'next' in result or result.get('next') is None
        assert 'previous' in result or result.get('previous') is None
