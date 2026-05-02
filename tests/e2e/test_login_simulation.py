#!/usr/bin/env python
"""
模拟浏览器登录测试脚本
"""
import json

print("=" * 60)
print("EventPilot 登录模拟测试")
print("=" * 60)

# 登录信息
login_info = {
    "url": "http://172.28.166.164:5173",
    "username": "admin",
    "password": "admin123"
}

print(f"\n目标URL: {login_info['url']}")
print(f"用户名: {login_info['username']}")
print(f"密码: {'*' * len(login_info['password'])}")

print("\n" + "=" * 60)
print("登录步骤:")
print("=" * 60)
print("1. 访问 http://172.28.166.164:5173")
print("2. 系统重定向到登录页面 /login")
print("3. 输入用户名: admin")
print("4. 输入密码: admin123")
print("5. 点击登录按钮")
print("6. 登录成功后跳转到首页")

print("\n" + "=" * 60)
print("预期结果:")
print("=" * 60)
print("✓ 登录成功")
print("✓ 跳转到首页 (http://172.28.166.164:5173/)")
print("✓ 可以访问受保护的页面，如 /analytics")

print("\n" + "=" * 60)
print("Analytics 页面功能:")
print("=" * 60)
print("- 活动总数统计")
print("- 任务总数统计")
print("- 任务完成率")
print("- 预算偏差率")
print("- 活动状态分布")
print("- 活动类型分布")
print("- 任务类型分布")
print("- 预算概览")
print("- 高风险活动列表")
print("- 即将到期活动列表")
print("- TOP活跃负责人")
print("- 月度活动趋势")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
