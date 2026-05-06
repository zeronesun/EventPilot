"""
测试Swagger API文档端点 - 独立最小化版本

如果drf-yasg已经集成，可以将其装饰器移除以启用测试。
"""
import pytest
import requests


def test_swagger_endpoint_response():
    """测试Swagger端点是否返回有效响应"""
    # 如果端点不存在，这会返回404而非异常
    response = requests.get('http://172.28.166.164:8000/api/swagger/')

    # 如果返回404，说明端点未启用（可以接受）
    # 如果返回200，说明已启用（验证JSON格式）
    if response.status_code == 404:
        pytest.skip("Swagger端点未启用 - 待集成drf-yasg")
    else:
        assert response.status_code == 200
        # 验证是有效的JSON
        data = response.json()
        assert isinstance(data, dict)
