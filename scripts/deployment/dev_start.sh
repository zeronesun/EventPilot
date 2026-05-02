#!/bin/bash
# 开发环境启动脚本

echo "🚀 EventPilot 开发环境启动..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3.11 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查Python依赖..."
pip list --outdated || echo "依赖检查完毕"

# 运行数据库迁移（如果需要）
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "📦 运行数据库迁移..."
    python manage.py migrate --noinput
fi

# 创建超级用户（如果不存在）
echo "👤 检查管理员用户..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())" | grep -q True || python manage.py createsuperuser --noinput

# 收集静态文件
echo "📂 收集静态文件..."
python manage.py collectstatic --noinput

# 启动开发服务器
echo "🌐 启动开发服务器..."
python manage.py runserver 0.0.0.0:8000