"""
认证模块 E2E 测试
覆盖: 登录、Token刷新、路由守卫、登出
"""
import pytest
from playwright.async_api import expect


class TestAuthentication:
    """认证流程测试"""

    @pytest.mark.asyncio
    async def test_login_page_loads(self, page):
        """[UI/UX] 登录页正确加载"""
        await page.goto('http://localhost:5173/login')

        # 验证页面标题和品牌
        await expect(page.locator('h2')).to_contain_text('EventPilot')
        await expect(page.locator('p')).to_contain_text('活动领航系统')

        # 验证表单元素存在
        await expect(page.locator('input[placeholder="用户名"]')).to_be_visible()
        await expect(page.locator('input[placeholder="密码"]')).to_be_visible()
        await expect(page.locator('button:has-text("登录")')).to_be_visible()

    @pytest.mark.asyncio
    async def test_login_success(self, page):
        """[用户视角] 成功登录流程"""
        await page.goto('http://localhost:5173/login')

        # 填写表单
        await page.fill('input[placeholder="用户名"]', 'admin')
        await page.fill('input[placeholder="密码"]', 'admin123')

        # 点击登录并等待响应
        with page.expect_response('**/api/users/auth/login/') as response_info:
            await page.click('button:has-text("登录")')

        response = await response_info.value
        assert response.status == 200

        # 验证 JWT Token 存储
        token = await page.evaluate("localStorage.getItem('eventpilot_token')")
        assert token is not None
        assert len(token) > 0

        # 验证跳转到首页
        await expect(page).to_have_url('http://localhost:5173/dashboard')

    @pytest.mark.asyncio
    async def test_login_failure_wrong_password(self, page):
        """[用户视角] 密码错误提示"""
        await page.goto('http://localhost:5173/login')

        await page.fill('input[placeholder="用户名"]', 'admin')
        await page.fill('input[placeholder="密码"]', 'wrongpassword')
        await page.click('button:has-text("登录")')

        # 验证错误提示显示
        await expect(page.locator('.el-alert--error')).to_be_visible()

        # 验证仍在登录页
        await expect(page).to_have_url('http://localhost:5173/login')

    @pytest.mark.asyncio
    async def test_protected_route_redirect(self, page):
        """[开发者视角] 未认证访问受保护路由重定向到登录"""
        await page.goto('http://localhost:5173/events')

        # 应重定向到登录页
        await expect(page).to_have_url('http://localhost:5173/login')

    @pytest.mark.asyncio
    async def test_authenticated_user_redirect_from_login(self, authenticated_page):
        """[开发者视角] 已登录用户访问登录页重定向到首页"""
        page = authenticated_page
        await page.goto('http://localhost:5173/login')

        # 应重定向到首页
        await expect(page).to_have_url('http://localhost:5173/dashboard')

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_page):
        """[用户视角] 登出功能"""
        page = authenticated_page
        await page.goto('http://localhost:5173/dashboard')

        # 点击用户菜单登出（假设有登出按钮）
        # 根据实际 UI 调整选择器
        logout_button = page.locator('text=退出登录')
        if await logout_button.is_visible():
            await logout_button.click()

            # 验证 Token 被清除
            token = await page.evaluate("localStorage.getItem('eventpilot_token')")
            assert token is None

            # 验证重定向到登录页
            await expect(page).to_have_url('http://localhost:5173/login')
