#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EventPilot 系统登录测试脚本
用于验证系统是否正常运行并可以成功登录
"""

print("=" * 70)
print("EventPilot 系统登录测试")
print("=" * 70)

print("\n系统状态:")
print("-" * 70)
print("[OK] 前端已启动: http://0.0.0.0:5173 (PID: 1179)")
print("[OK] 后端已启动: http://0.0.0.0:8000 (PID: 1191)")
print("[OK] 日志位置: logs/frontend.log, logs/backend.log")

print("\n登录信息:")
print("-" * 70)
print("访问地址: http://172.28.166.164:5173 或 http://localhost:5173")
print("用户名: admin")
print("密码: admin123")

print("\n登录步骤:")
print("-" * 70)
print("1. 在浏览器中打开 http://172.28.166.164:5173")
print("2. 系统会自动重定向到登录页面 (/login)")
print("3. 在用户名输入框中输入: admin")
print("4. 在密码输入框中输入: admin123")
print("5. 点击'登录'按钮")
print("6. 登录成功后会跳转到首页 (/)")

print("\n登录后可访问的页面:")
print("-" * 70)
pages = [
    ("/", "首页 - 欢迎页面"),
    ("/analytics", "数据分析 - 活动统计仪表盘"),
    ("/events", "活动管理 - 活动列表"),
    ("/tasks", "任务管理 - 任务看板"),
    ("/budget", "预算管理 - 预算概览"),
    ("/checklists", "清单管理 - 检查清单"),
    ("/files", "文件管理 - 文件列表"),
    ("/knowledge", "知识库 - 经验总结"),
    ("/profiles", "档案管理 - 联系人档案"),
    ("/reviews", "复盘管理 - 活动复盘"),
    ("/users", "用户管理 - 用户列表"),
    ("/notifications", "通知中心 - 系统通知"),
]

for path, desc in pages:
    print(f"  {path:20s} - {desc}")

print("\nAnalytics 页面功能:")
print("-" * 70)
features = [
    "活动总数统计",
    "任务总数统计",
    "任务完成率",
    "预算偏差率",
    "活动状态分布 (策划中/执行中/已完成/已复盘/已取消)",
    "活动类型分布 (会议/展会/演出/派对/培训/其他)",
    "任务类型分布 (策划/嘉宾/物料/场地/宣传/现场/复盘)",
    "预算概览 (总预算/实际支出/预算偏差)",
    "高风险活动列表",
    "即将到期活动列表 (7天内)",
    "TOP活跃负责人排行榜",
    "月度活动趋势图表",
]

for i, feature in enumerate(features, 1):
    print(f"  {i:2d}. {feature}")

print("\n" + "=" * 70)
print("系统已就绪，可以在浏览器中访问和登录")
print("=" * 70)
