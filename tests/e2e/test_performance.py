"""
性能测试
覆盖: 页面加载时间、API响应时间、资源加载
"""
import pytest
import time
import requests


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_login_page_load_time(self, page):
        """[架构师视角] 登录页加载时间 < 2s"""
        start = time.time()
        await page.goto('http://localhost:5173/login')
        await page.wait_for_load_state('networkidle')
        elapsed = time.time() - start

        assert elapsed < 2.0, f"登录页加载时间: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_dashboard_load_time(self, authenticated_page):
        """[架构师视角] 首页加载时间 < 2s"""
        page = authenticated_page
        start = time.time()
        await page.goto('http://localhost:5173/dashboard')
        await page.wait_for_load_state('networkidle')
        elapsed = time.time() - start

        assert elapsed < 2.0, f"首页加载时间: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_events_list_api_response_time(self, authenticated_page):
        """[架构师视角] 活动列表 API 响应 < 500ms"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        with page.expect_response('**/api/events/') as response_info:
            await page.reload()

        response = await response_info.value
        # Playwright 不直接提供响应时间，可以通过 timing
        timing = await response.request.timing()
        total_time = timing.get('responseEnd', 0) - timing.get('startTime', 0)

        if total_time > 0:
            assert total_time < 500, f"API 响应时间: {total_time}ms"

    def test_api_response_time_direct(self, api_client):
        """[架构师视角] 直接 API 调用响应时间"""
        start = time.time()
        response = api_client.get('/api/events/')
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"活动列表 API 响应时间: {elapsed:.0f}ms"

    def test_dashboard_stats_api_time(self, api_client):
        """[架构师视角] 首页统计 API 响应时间"""
        start = time.time()
        response = api_client.get('/api/dashboard/stats/')
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 500, f"统计 API 响应时间: {elapsed:.0f}ms"

    @pytest.mark.asyncio
    async def test_large_list_pagination(self, authenticated_page):
        """[架构师视角] 大数据量列表分页性能"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        # 等待表格加载
        await page.wait_for_selector('.el-table__row')

        # 获取行数
        rows = page.locator('.el-table__row')
        row_count = await rows.count()

        # 验证分页控制存在
        pagination = page.locator('.el-pagination')
        if await pagination.is_visible():
            # 点击下一页
            next_btn = pagination.locator('button:has-text("下一页")')
            if await next_btn.is_visible() and await next_btn.is_enabled():
                start = time.time()
                await next_btn.click()
                await page.wait_for_load_state('networkidle')
                elapsed = time.time() - start

                assert elapsed < 1.0, f"分页加载时间: {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_js_bundle_size(self, page):
        """[架构师视角] JS 资源大小检查"""
        await page.goto('http://localhost:5173/login')

        # 获取所有 JS 资源
        resources = await page.evaluate("""
            () => performance.getEntriesByType('resource')
                .filter(r => r.name.endsWith('.js'))
                .map(r => ({name: r.name, size: r.transferSize}))
        """)

        for resource in resources:
            if resource['size'] > 0:
                # 单个 JS 文件不应超过 1MB
                assert resource['size'] < 1024 * 1024, \
                    f"JS 文件过大: {resource['name']} ({resource['size']} bytes)"
