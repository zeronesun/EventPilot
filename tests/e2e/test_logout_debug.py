"""
调试退出功能测试
"""
import pytest


def test_logout_debug(page):
    """
    [调试] 详细调查退出功能问题
    """
    import requests
    
    # 步骤1: 登录获取token
    print("=== 步骤1: 获取登录token ===")
    response = requests.post(
        'http://172.28.166.164:8000/api/users/auth/login/',
        json={'username': 'admin', 'password': 'admin123'}
    )
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    assert response.status_code in [200, 201]
    response_data = response.json()
    access_token = response_data.get('data', {}).get('token')
    print(f"获取到的token: {access_token[:50]}..." if access_token else "未获取到token")
    
    # 步骤2: 设置token并访问应用
    print("\n=== 步骤2: 设置token并访问应用 ===")
    page.goto('http://172.28.166.164:5173/login')
    page.evaluate(f"localStorage.setItem('eventpilot_token', '{access_token}')")
    
    # 验证token已设置
    set_token = page.evaluate("localStorage.getItem('eventpilot_token')")
    print(f"设置的token验证: {set_token[:50]}..." if set_token else "未设置token")
    
    # 访问首页
    page.goto('http://172.28.166.164:5173')
    page.wait_for_load_state('networkidle')
    print(f"访问首页后的URL: {page.url}")
    
    # 步骤3: 调查页面元素
    print("\n=== 步骤3: 调查页面元素 ===")
    
    # 截图
    page.screenshot(path='tests/e2e/screenshots/debug_step3_dashboard.png')
    print("已截图: tests/e2e/screenshots/debug_step3_dashboard.png")
    
    # 查找可能的退出相关按钮
    logout_selectors = [
        'button:has-text("退出")',
        'a:has-text("退出")', 
        'button:has-text("登出")',
        'a:has-text("登出")',
        '.logout-button',
        '.log-out',
        '.sign-out'
    ]
    
    found = False
    for selector in logout_selectors:
        elements = page.locator(selector)
        count = elements.count()
        if count > 0:
            print(f"找到选择器 '{selector}': {count}个元素")
            for i in range(min(count, 3)):
                element = elements.nth(i)
                try:
                    text = element.text_content()
                    visible = element.is_visible()
                    print(f"  元素{i}: text='{text}', visible={visible}")
                except:
                    pass
            found = True
    
    if not found:
        print("未找到明显的退出按钮")
    
    # 查找用户菜单相关元素
    menu_selectors = [
        '.user-menu',
        '.avatar',
        '.header-user',
        '.user-info',
        '.el-dropdown',
        '[class*="user"]',
        '[class*="avatar"]'
    ]
    
    print("\n查找用户菜单元素:")
    for selector in menu_selectors:
        elements = page.locator(selector)
        count = elements.count()
        if count > 0 and count < 10:
            print(f"找到 '{selector}': {count}个元素")
            for i in range(min(count, 3)):
                element = elements.nth(i)
                try:
                    visible = element.is_visible()
                    print(f"  元素{i}: visible={visible}")
                    if visible:
                        # 点击看看是否有dropdown
                        element.click()
                        page.wait_for_timeout(1000)
                        screenshot_name = f'tests/e2e/screenshots/debug_after_click_{selector.replace(".", "_")}.png'
                        page.screenshot(path=screenshot_name)
                        print(f"  已截图: {screenshot_name}")
                except Exception as e:
                    pass
    
    # 步骤4: 查看页面HTML结构
    print("\n=== 步骤4: 查看页面头部HTML ===")
    header_html = page.locator('header').inner_html() if page.locator('header').count() > 0 else "无header"
    print(f"Header HTML长度: {len(header_html)}")
    
    # 步骤5: 手动触发退出并验证
    print("\n=== 步骤5: 尝试手动退出 ===")
    
    # 清除localStorage
    page.evaluate("localStorage.clear()")
    print("已清除localStorage")
    
    # 刷新页面
    page.reload()
    page.wait_for_load_state('networkidle')
    
    current_url = page.url
    print(f"清除token并刷新后的URL: {current_url}")
    
    # 检查是否有登录相关元素
    login_elements = page.locator('input[type="password"], input[placeholder*="密码"], button:has-text("登录")')
    login_count = login_elements.count()
    print(f"找到登录相关元素: {login_count}个")


def test_logout_via_api(page):
    """
    [测试] 通过API调用退出
    """
    import requests
    
    # 登录
    response = requests.post(
        'http://172.28.166.164:8000/api/users/auth/login/',
        json={'username': 'admin', 'password': 'admin123'}
    )
    access_token = response.json().get('data', {}).get('token')
    
    # 设置token
    page.goto('http://172.28.166.164:5173/login')
    page.evaluate(f"localStorage.setItem('eventpilot_token', '{access_token}')")
    
    # 访问应用
    page.goto('http://172.28.166.164:5173')
    page.wait_for_load_state('networkidle')
    
    print(f"登录成功后URL: {page.url}")
    
    # 通过API调用退出（如果有的话）
    logout_response = requests.post(
        'http://172.28.166.164:8000/api/users/logout/',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    print(f"API退出响应: {logout_response.status_code}")
    
    # 清除本地token
    page.evaluate("localStorage.removeItem('eventpilot_token')")
    
    # 刷新
    page.reload()
    page.wait_for_load_state('networkidle')
    
    current_url = page.url
    print(f"清除token并刷新后的URL: {current_url}")
    
    # 如果前端没有正确重定向，我们检查是否有登录表单
    has_login = page.locator('input[type="password"]').count() > 0
    print(f"页面是否有登录表单: {has_login}")
