from apps.events.models import Event
from apps.tasks.models import Task
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()

# 获取admin用户
admin_user = User.objects.get(username='admin')
print(f"✅ 找到用户: {admin_user.username} (ID: {admin_user.id})")

# 创建测试活动（owner必须是User实例）
events = [
    Event(
        name="年度技术大会",
        type="conference",
        description="公司年度技术创新大会",
        start_date=datetime.date(2026, 6, 15),
        end_date=datetime.date(2026, 6, 16),
        client="科大讯飞",
        estimated_budget=500000,
        actual_budget=0,
        owner=admin_user,
        status='planning'
    ),
    Event(
        name="新产品发布会",
        type="launch",
        description="新产品全球首发仪式",
        start_date=datetime.date(2026, 7, 20),
        end_date=datetime.date(2026, 7, 20),
        client="华为",
        estimated_budget=800000,
        actual_budget=0,
        owner=admin_user,
        status='planning'
    ),
    Event(
        name="客户答谢会",
        type="dinner",
        description="VIP客户答谢晚宴",
        start_date=datetime.date(2026, 8, 10),
        end_date=datetime.date(2026, 8, 10),
        client="中国移动",
        estimated_budget=200000,
        actual_budget=0,
        owner=admin_user,
        status='executing'
    ),
]

created_events = []
for event in events:
    event.save()
    created_events.append(event)
    print(f"✅ 创建活动: {event.name} (ID: {event.id})")

# 为每个活动创建任务
task_templates = [
    {
        "title": "场地预订确认",
        "task_type": "venue",
        "status": "completed",
        "progress": 100
    },
    {
        "title": "参会名单收集",
        "task_type": "guest",
        "status": "in_progress",
        "progress": 60
    },
    {
        "title": "物料采购",
        "task_type": "material",
        "status": "pending",
        "progress": 0
    },
    {
        "title": "嘉宾邀请",
        "task_type": "guest",
        "status": "in_progress",
        "progress": 40
    },
]

for event in created_events:
    for i, tpl in enumerate(task_templates):
        task = Task(
            event=event,  # 直接传event对象
            title=f"{tpl['title']}",
            description=tpl['title'],
            task_type=tpl['task_type'],
            status=tpl['status'],
            progress=tpl['progress'],
            assignee=admin_user  # assignee也是User实例
        )
        task.save()
        print(f"  ✅ 创建任务: {task.title}")

print(f"\n📊 数据创建完成!")
print(f"   - 活动数: {Event.objects.count()}")
print(f"   - 任务数: {Task.objects.count()}")
