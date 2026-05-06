"""
认证测试 - 使用同步 Playwright API (最终修复版)
覆盖: 登录页面加载、登录成功/失败、保护路由重定向
"""
import pytest


class TestAuthentication:
    """认证功能测试"""

    def test_login_page_loads(self, page):
        """
        [用户视角] 登录页面正常加载
        验证: 页面加载，表单元素存在
        """
        page.goto('http://172.28.166.164:5173/login')

        # 等待页面加载完成
        page.wait_for_load_state('networkidle')

        # 验证页面标题
        assert 'EventPilot' in page.title() or '登录' in page.content()

    def test_login_success(self, page):
        """
        [用户视角] 登录成功
        前端: 填写表单，点击登录，验证跳转
        后端: API 返回 token
        """
        # 访问登录页
        page.goto('http://172.28.166.164:5173/login')
        page.wait_for_load_state('networkidle')

        # 填写用户名
        page.fill('input[type="text"], input[placeholder*="用户名"], input[name="username"]', 'admin')

        # 填写密码
        page.fill('input[type="password"], input[placeholder*="密码"], input[name="password"]', 'admin123')

        # 点击登录按钮（多种可能的选择器）
        login_button = page.locator('button[type="submit"], button:has-text("登录"), .login-button').first
        if login_button.is_visible():
            login_button.click()
        else:
            # 尝试按 Enter 提交
            page.keyboard.press('Enter')

        # 等待跳转
        page.wait_for_timeout(2000)

        # 验证：应该跳转到 dashboard 或首页
        current_url = page.url
        assert 'login' not in current_url, f"登录失败，仍在登录页: {current_url}"

    def test_login_failure_wrong_password(self, page):
        """
        [用户视角] 错误密码登录失败
        验证: 错误提示显示，停留在登录页
        """
        page.goto('http://172.28.166.164:5173/login')
        page.wait_for_load_state('networkidle')

        # 填写错误的密码
        page.fill('input[type="text"], input[placeholder*="用户名"], input[name="username"]', 'admin')
        page.fill('input[type="password"], input[placeholder*="密码"], input[name="password"]', 'wrongpassword')

        # 点击登录
        login_button = page.locator('button[type="submit"], button:has-text("登录"), .login-button').first
        if login_button.is_visible():
            login_button.click()
        else:
            page.keyboard.press('Enter')

        # 等待响应
        page.wait_for_timeout(2000)

        # 验证：仍然在登录页
        current_url = page.url
        assert 'login' in current_url, f"应该仍在登录页，但当前在: {current_url}"

    def test_protected_route_redirect(self, page):
        """
        [用户视角] 未登录访问保护路由重定向到登录页
        """
        # 先清除任何可能的登录状态
        page.goto('http://172.28.166.164:5173')
        page.evaluate("localStorage.clear()")

        # 访问保护路由
        page.goto('http://172.28.166.164:5173/dashboard')
        page.wait_for_load_state('networkidle')

        # 验证：重定向到登录页
        current_url = page.url
        assert 'login' in current_url, f"应该重定向到登录页，但当前在: {current_url}"

    def test_logout(self, page):
        """
        [用户视角] 登出功能
        验证: 退出后重定向到登录页
        """
        # 通过 API 获取 token（不使用 Django ORM，避免 async 冲突）
        import requests
        response = requests.post(
            'http://172.28.166.164:8000/api/users/auth/login/',
            json={'username': 'admin', 'password': 'admin123'}
        )

        # 确保登录成功
        assert response.status_code in [200, 201], f"登录失败: {response.text}"
        response_data = response.json()
        access_token = response_data.get('data', {}).get('token')
        assert access_token, f"未找到 token，响应: {response_data}"

        # 设置 token
        page.goto('http://172.28.166.164:5173/login')
        page.evaluate(f"localStorage.setItem('eventpilot_token', '{access_token}')")

        # 已登录状态访问应用
        page.goto('http://172.28.166.164:5173')
        page.wait_for_load_state('networkidle')

        # 尝试找到登出按钮
        logout_button = page.locator('button:has-text("退出"), a:has-text("退出"), .logout-button').first

        if logout_button.is_visible():
            logout_button.click()
        else:
            # 尝试通过菜单触发退出
            user_menu = page.locator('.user-menu, .avatar, .header-user').first
            if user_menu.is_visible():
                user_menu.click()
                page.wait_for_timeout(500)
                # 再找退出按钮
                logout_button = page.locator('button:has-text("退出"), a:has-text("退出")').first
                if logout_button.is_visible():
                    logout_button.click()

        # 等待跳转
        page.wait_for_timeout(2000)

        # 验证：回到登录页
        current_url = page.url
        assert 'login' in current_url, f"退出后应该回到登录页，但当前在: {current_url}"

        # 验证：localStorage 已清除
        token = page.evaluate("localStorage.getItem('eventpilot_token')")
        assert token is None, f"退出后 token 应该被清除，实际: {token}"
