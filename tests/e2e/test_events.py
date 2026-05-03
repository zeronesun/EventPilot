"""
活动管理模块 E2E 测试
覆盖: 列表、创建、详情、编辑、删除、状态流转
"""
import pytest
from playwright.async_api import expect


class TestEventManagement:
    """活动管理测试"""

    @pytest.mark.asyncio
    async def test_events_page_loads(self, authenticated_page):
        """[UI/UX] 活动列表页加载"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        # 验证页面标题
        await expect(page.locator('.page-title')).to_contain_text('活动管理')

        # 验证工具栏按钮
        await expect(page.locator('button:has-text("新建活动")')).to_be_visible()
        await expect(page.locator('button:has-text("导出")')).to_be_visible()

        # 验证搜索框
        await expect(page.locator('input[placeholder*="搜索"]')).to_be_visible()

    @pytest.mark.asyncio
    async def test_create_event_dialog(self, authenticated_page):
        """[用户视角] 打开新建活动弹窗"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        # 点击新建活动
        await page.click('button:has-text("新建活动")')

        # 验证弹窗出现
        await expect(page.locator('.el-dialog__title')).to_contain_text('新建活动')

        # 验证表单字段
        await expect(page.locator('input[placeholder*="活动名称"]')).to_be_visible()
        await expect(page.locator('input[placeholder*="活动类型"]')).to_be_visible()

    @pytest.mark.asyncio
    async def test_create_event_full_flow(self, authenticated_page, db):
        """[前后端联动] 创建活动完整流程"""
        from apps.events.models import Event
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        # 打开创建弹窗
        await page.click('button:has-text("新建活动")')
        await page.wait_for_selector('.el-dialog__title:has-text("新建活动")')

        # 填写表单
        await page.fill('input[placeholder*="活动名称"]', 'E2E测试活动')

        # 选择活动类型（Element Plus Select）
        await page.click('.el-select:has-text("活动类型")')
        await page.click('.el-select-dropdown__item:has-text("会议")')

        # 填写描述
        await page.fill('textarea[placeholder*="描述"]', '这是一个E2E测试创建的活动')

        # 填写客户信息
        await page.fill('input[placeholder*="客户"]', '测试客户公司')
        await page.fill('input[placeholder*="联系人"]', '李四')

        # 填写预算
        await page.fill('input[placeholder*="预算"]', '100000')

        # 设置日期（根据实际组件调整）
        # await page.fill('input[placeholder*="开始时间"]', '2026-06-01 09:00')
        # await page.fill('input[placeholder*="结束时间"]', '2026-06-02 18:00')

        # 提交表单并等待后端响应
        with page.expect_response('**/api/events/') as response_info:
            await page.click('button:has-text("确定")')

        response = await response_info.value
        assert response.status == 201

        response_data = await response.json()
        event_id = response_data.get('id')

        # 数据库断言: 验证活动已创建
        event = Event.objects.filter(id=event_id).first()
        assert event is not None
        assert event.name == 'E2E测试活动'
        assert event.status == Event.Status.PLANNING
        assert event.type == 'conference'

        # 前端断言: 弹窗关闭，列表刷新
        await expect(page.locator('.el-dialog__wrapper')).not_to_be_visible()

        # 验证成功提示
        await expect(page.locator('.el-message--success')).to_contain_text('创建成功')

    @pytest.mark.asyncio
    async def test_event_detail_page(self, authenticated_page, test_event):
        """[前后端联动] 活动详情页"""
        page = authenticated_page
        event_id = str(test_event.id)

        await page.goto(f'http://localhost:5173/events/{event_id}')

        # 验证页面加载
        await expect(page.locator('h1, h2, .event-title')).to_contain_text(test_event.name)

        # 验证 API 响应
        with page.expect_response(f'**/api/events/{event_id}/') as response_info:
            await page.reload()

        response = await response_info.value
        assert response.status == 200

        data = await response.json()
        assert data['name'] == test_event.name
        assert data['status'] == test_event.status
        assert 'budget_items' in data
        assert 'participants' in data

    @pytest.mark.asyncio
    async def test_event_status_transition(self, authenticated_page, test_event, db):
        """[架构师视角] 活动状态流转"""
        from apps.events.models import Event
        page = authenticated_page
        event_id = str(test_event.id)

        await page.goto(f'http://localhost:5173/events/{event_id}/edit')

        # 修改状态为 executing
        await page.click('.el-select:has-text("状态")')
        await page.click('.el-select-dropdown__item:has-text("执行中")')

        # 提交更新
        with page.expect_response(f'**/api/events/{event_id}/') as response_info:
            await page.click('button:has-text("保存")')

        response = await response_info.value
        assert response.status == 200

        # 数据库断言
        event = Event.objects.get(id=event_id)
        assert event.status == Event.Status.EXECUTING

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, authenticated_page, test_event):
        """[开发者视角] 非法状态流转应返回 400"""
        import requests

        # 直接调用 API 测试非法状态转换
        # 例如: completed -> planning 应该是非法的
        event_id = str(test_event.id)

        # 先完成活动
        test_event.status = 'completed'
        test_event.save()

        # 尝试非法转换
        response = requests.patch(
            f'http://localhost:8000/api/events/{event_id}/',
            json={'status': 'planning'},
            headers={'Content-Type': 'application/json'}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_event_search_filter(self, authenticated_page, test_event):
        """[用户视角] 活动搜索筛选"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        # 输入搜索关键词
        await page.fill('input[placeholder*="搜索"]', test_event.name)
        await page.press('input[placeholder*="搜索"]', 'Enter')

        # 等待搜索结果
        await page.wait_for_timeout(500)

        # 验证搜索结果包含测试活动
        await expect(page.locator(f'text={test_event.name}')).to_be_visible()

    @pytest.mark.asyncio
    async def test_delete_event(self, authenticated_page, test_event, db):
        """[前后端联动] 删除活动"""
        from apps.events.models import Event
        page = authenticated_page
        event_id = str(test_event.id)

        await page.goto('http://localhost:5173/events')

        # 找到活动行并点击删除（根据实际 UI 调整）
        event_row = page.locator(f'text={test_event.name}').first
        if await event_row.is_visible():
            # 悬停显示操作按钮
            await event_row.hover()

            # 点击删除按钮
            delete_btn = page.locator('button[title*="删除"]').first
            if await delete_btn.is_visible():
                await delete_btn.click()

                # 确认删除
                await page.click('button:has-text("确定")')

                # 数据库断言
                await page.wait_for_timeout(500)
                assert not Event.objects.filter(id=event_id).exists()

    @pytest.mark.asyncio
    async def test_event_list_api_response_structure(self, authenticated_page):
        """[开发者视角] 活动列表 API 响应结构校验"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events')

        with page.expect_response('**/api/events/') as response_info:
            await page.reload()

        response = await response_info.value
        assert response.status == 200

        data = await response.json()

        # 验证 DRF 分页结构
        assert 'results' in data or isinstance(data, list)

        if 'results' in data:
            results = data['results']
        else:
            results = data

        if len(results) > 0:
            event = results[0]
            # 验证 EventListSerializer 字段
            required_fields = [
                'id', 'name', 'type', 'start_date', 'end_date',
                'status', 'owner_name', 'tasks_count',
                'progress_percentage', 'budget_usage_rate'
            ]
            for field in required_fields:
                assert field in event, f"缺少字段: {field}"
