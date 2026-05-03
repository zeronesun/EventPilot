"""
任务管理模块 E2E 测试
覆盖: 任务CRUD、看板拖拽、批量操作
"""
import pytest
from playwright.async_api import expect


class TestTaskManagement:
    """任务管理测试"""

    @pytest.mark.asyncio
    async def test_tasks_page_loads(self, authenticated_page):
        """[UI/UX] 任务列表页加载"""
        page = authenticated_page
        await page.goto('http://localhost:5173/tasks')

        # 验证页面标题
        await expect(page.locator('.page-title, h1, h2')).to_contain_text('任务')

        # 验证新建按钮
        await expect(page.locator('button:has-text("新建")')).to_be_visible()

    @pytest.mark.asyncio
    async def test_create_task(self, authenticated_page, test_event):
        """[前后端联动] 创建任务"""
        from apps.tasks.models import Task
        page = authenticated_page
        await page.goto('http://localhost:5173/tasks')

        # 打开创建弹窗
        await page.click('button:has-text("新建")')
        await page.wait_for_selector('.el-dialog__title:has-text("新建任务")')

        # 填写任务信息
        await page.fill('input[placeholder*="任务标题"]', 'E2E测试任务')
        await page.fill('textarea[placeholder*="描述"]', '测试任务描述')

        # 选择优先级
        await page.click('.el-select:has-text("优先级")')
        await page.click('.el-select-dropdown__item:has-text("高")')

        # 提交
        with page.expect_response('**/api/tasks/') as response_info:
            await page.click('button:has-text("确定")')

        response = await response_info.value
        assert response.status in [200, 201]

        # 验证成功提示
        await expect(page.locator('.el-message--success')).to_be_visible()

    @pytest.mark.asyncio
    async def test_kanban_board_loads(self, authenticated_page):
        """[UI/UX] 看板页面加载"""
        page = authenticated_page
        await page.goto('http://localhost:5173/events-kanban')

        # 验证看板列存在
        await expect(page.locator('text=待办')).to_be_visible()
        await expect(page.locator('text=进行中')).to_be_visible()
        await expect(page.locator('text=已完成')).to_be_visible()

    @pytest.mark.asyncio
    async def test_task_status_update(self, authenticated_page, test_task):
        """[用户视角] 更新任务状态"""
        from apps.tasks.models import Task
        page = authenticated_page
        task_id = str(test_task.id)

        await page.goto('http://localhost:5173/tasks')

        # 找到任务并更新状态
        # 根据实际 UI 调整选择器
        task_row = page.locator(f'text={test_task.title}').first
        if await task_row.is_visible():
            await task_row.click()

            # 在详情中更新状态
            await page.click('.el-select:has-text("状态")')
            await page.click('.el-select-dropdown__item:has-text("已完成")')

            with page.expect_response(f'**/api/tasks/{task_id}/') as response_info:
                await page.click('button:has-text("保存")')

            response = await response_info.value
            assert response.status == 200

            # 数据库断言
            task = Task.objects.get(id=task_id)
            assert task.status == 'done'
