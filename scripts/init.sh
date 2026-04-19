#!/bin/bash
# EventPilot 项目初始化脚本

set -e

echo "🚀 EventPilot 项目初始化..."

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p logs public/static public/media storage/exports storage/temp cache

# 创建.env文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
else
    echo "ℹ️  .env 文件已存在"
fi

echo ""
echo "✅ 项目基础结构准备完成！"
echo ""
echo "📋 接下来的步骤:"
echo "1. python3.11 -m venv venv                # 创建虚拟环境"
echo "2. source venv/bin/activate               # 激活虚拟环境"
echo "3. pip install -r requirements.txt       # 安装Python依赖"
echo "4. python manage.py makemigrations      # 创建数据库迁移"
echo "5. python manage.py migrate              # 执行数据库迁移"
echo "6. python manage.py createsuperuser      # 创建超级用户"
echo "7. python manage.py runserver            # 启动开发服务器"