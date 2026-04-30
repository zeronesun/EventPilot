#!/bin/bash

# EventPilot: 开发环境设置脚本
# 版本: 2026-04-30
# 用途: 一键设置完整的开发环境

set -e  # 遇到错误立即退出

echo "🚀 EventPilot 开发环境设置开始"
echo "===================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数定义
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# 检查是否在正确的目录
if [ ! -f "manage.py" ] && [ ! -d "frontend" ]; then
    print_error "请在EventPilot项目根目录运行此脚本"
    exit 1
fi

# 步骤1: 检查系统依赖
echo "📋 第一步: 检查系统依赖"
echo "------------------------------------"

# 检查Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未安装，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python版本: $PYTHON_VERSION"

# 检查Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js 未安装，请先安装Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js版本: $NODE_VERSION"

# 检查npm
if ! command -v npm &> /dev/null; then
    print_error "npm 未安装"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_success "npm版本: $NPM_VERSION"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 未安装"
    exit 1
fi

# 步骤2: 设置Python虚拟环境
echo ""
echo "📋 第二步: 设置Python虚拟环境"
echo "------------------------------------"

if [ ! -d "venv" ]; then
    print_info "创建Python虚拟环境..."
    python3 -m venv venv
    print_success "虚拟环境创建成功"
else
    print_success "虚拟环境已存在"
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source venv/bin/activate

# 升级pip
print_info "升级pip..."
pip install --upgrade pip setuptools wheel

print_success "Python虚拟环境准备完成"

# 步骤3: 安装Python依赖
echo ""
echo "📋 第三步: 安装Python依赖"
echo "------------------------------------"

# 安装requirements.txt中的依赖
print_info "安装Python包..."
pip install -r requirements.txt

print_success "Python依赖安装完成"

# 步骤4: 设置数据库
echo ""
echo "📋 第四步: 数据库设置"
echo "------------------------------------"

# 创建logs目录
mkdir -p logs

# 运行数据库迁移
print_info "运行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

print_success "数据库迁移完成"

# 步骤5: 初始化环境配置
echo ""
echo "📋 第五步: 初始化环境配置"
echo "------------------------------------"

# 创建.env文件（如果不存在）
if [ ! -f ".env" ]; then
    print_info "创建.env环境变量文件..."
    cat > .env << EOF
# Django配置
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,172.28.166.164

# 数据库配置
DATABASE_URL=postgresql://eventpilot:eventpilot@localhost:5432/eventpilot

# Redis配置
REDIS_URL=redis://localhost:6379/0

# CORS配置
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://172.28.166.164:3000

# WebSocket配置
WS_ALLOWED_ORIGINS=http://localhost:3000,http://172.28.166.164:3000

# 安全配置
JWT_SECRET_KEY=eventpilot-jwt-secret-change-in-production
WS_SECRET_KEY=eventpilot-websocket-secret-change-in-production

# 环境标识
ENVIRONMENT=development
EOF
    print_success ".env文件创建成功"
else
    print_success ".env文件已存在"
fi

# 步骤6: 安装前端依赖
echo ""
echo "📋 第六步: 安装前端依赖"
echo "------------------------------------"

cd frontend

# 清理旧的node_modules（可选）
if [ -d "node_modules" ]; then
    # 仅在用户确认时清理
    read -p "是否清理现有的node_modules并重新安装? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "清理node_modules..."
        rm -rf node_modules package-lock.json
    fi
fi

# 安装依赖
print_info "安装npm依赖..."
npm install

print_success "前端依赖安装完成"

# 创建前端环境变量文件
if [ ! -f ".env" ]; then
    print_info "创建前端.env文件..."
    cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=EventPilot DEBUG
VITE_APP_VERSION=1.0.0-dev
EOF
    print_success "前端.env文件创建成功"
else
    print_success "前端.env文件已存在"
fi

cd ..

# 步骤7: 创建执行脚本
echo ""
echo "📋 第七步: 创建执行脚本"
echo "------------------------------------"

# 创建start服务脚本
cat > start-services.sh << 'SCRIPT'
#!/bin/bash

# 启动所有服务：数据库、Redis、Django、前端

# 检查PostgreSQL
if ! systemctl is-active --quiet postgresql; then
    echo "启动PostgreSQL..."
    sudo systemctl start postgresql
fi

# 检查Redis
if ! systemctl is-active --quiet redis; then
    echo "启动Redis..."
    sudo systemctl start redis
fi

# 激活虚拟环境
source venv/bin/activate

# 启动Django后端
echo "启动Django后端..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# 启动前端
cd frontend
echo "启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

cd ..

# 等待几秒让服务启动
sleep 5

# 检查服务是否启动成功
if ! ps -p $DJANGO_PID > /dev/null; then
    echo "❌ Django后端启动失败"
    exit 1
fi

if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ 前端启动失败"
    exit 1
fi

echo "✅ 所有服务启动成功！"
echo "Django后端: http://localhost:8000"
echo "前端: http://localhost:3000"
echo ""
echo "按Ctrl+C停止所有服务"

# 关闭函数
cleanup() {
    echo ""
    echo "🛑 关闭服务..."
    kill $DJANGO_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 等待
wait
SCRIPT

chmod +x start-services.sh
print_success "启动脚本创建完成: ./start-services.sh"

# 步骤8: 运行测试
echo ""
echo "📋 第八步: 运行测试"
echo "------------------------------------"

# 激活虚拟环境
source venv/bin/activate

# 运行Python测试
print_info "运行后端测试..."
python manage.py test --verbosity=2 > logs/backend-test.log 2>&1

if [ $? -eq 0 ]; then
    print_success "后端测试通过"
else
    print_error "后端测试未通过，检查logs/backend-test.log"
fi

# 运行前端测试（如果存在测试用例）
if [ -f "frontend/package.json" ] && grep -q "\"test\":" frontend/package.json; then
    print_info "运行前端测试..."
    cd frontend
    npm test > ../logs/frontend-test.log 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "前端测试通过"
    else
        print_warning "前端测试未通过，检查logs/frontend-test.log"
    fi
    cd ..
else
    print_warning "前端测试未配置"
fi

# 步骤9: 创建开发文档
echo ""
echo "📋 第九步: 创建开发文档"
echo "------------------------------------"

cat > docs/DEV_ENVIRONMENT_SETUP.md << 'EOF'
# EventPilot 开发环境设置指南

创建时间: 2026-04-30

## 已完成设置

✅ Python 3.8+ 虚拟环境
✅ 后端依赖安装 (Django, DRF, Channels等)
✅ 前端依赖安装 (Vue 3, Vite, Element Plus等)
✅ 数据库迁移完成
✅ 环境变量配置完成 (.env)
✅ Redis缓存配置
✅ 日志目录创建: logs/

## 快速开始

### 启动所有服务

```bash
./start-services.sh
```

这将启动:
- PostgreSQL 数据库
- Redis 缓存服务
- Django 后端 (http://localhost:8000)
- Vue 3 前端 (http://localhost:8000)

### 手动启动服务

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动Django后端
python manage.py runserver 0.0.0.0:8000

# 新开终端，启动前端
cd frontend
npm run dev
```

## 访问应用

访问: http://localhost:3000 或 http://172.28.166.164:3000

默认登录凭据:
- 用户名: admin
- 密码: admin123

## 开发工具

### 代码格式化

```bash
# 后端 (Black)
black apps/ config/ .

# 前端 (Prettier)
cd frontend
npm run format
```

### 代码检查

```bash
# 后端 (flake8)
flake8 apps/ config/

# 前端 (ESLint)
cd frontend
npm run lint
```

### 运行测试

```bash
# 后端
python manage.py test

# 前端
cd frontend
npm test
```

## 故障排除

### 端口被占用

```bash
# 查找占用8000端口的进程
lsof -i :8000
# 或
netstat -tulpn | grep 8000

# 杀死进程
kill -9 <PID>
```

### 数据库连接问题

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### Redis问题

```bash
# 检查Redis状态
sudo systemctl status redis

# 清空Redis缓存
redis-cli FLUSHALL
```

### 查看日志

```bash
#后端日志
tail -f logs/django.log

# 前端日志
tail -f logs/frontend.log
```

## 生产环境部署

⚠️ 当前设置为开发环境，生产部署需要:

1. 修改`DEBUG=False` (config/settings.py)
2. 设置强密钥 (`SECRET_KEY`)
3. 配置生产数据库
4. 使用static文件服务
5. 配置HTTPS
6. 设置CORS白名单
7. 使用生产级WSGI服务器(Gunicorn + Nginx)

查看生产部署文档: docs/PRODUCTION_DEPLOYMENT.md

## 资源链接

- Django文档: https://docs.djangoproject.com/
- Vue 3文档: https://vuejs.org/
- DRF文档: https://www.django-rest-framework.org/
- Element Plus文档: https://element-plus.org/

## 支持

如有问题，请查看:
- 项目文档: docs/
- 问题日志: logs/
- GitHub Issues: https://github.com/your-repo/eventpilot/issues

---

EventPilot 开发团队 | 2026-04-30
EOF
print_success "开发文档创建完成"

# 完成步骤
echo ""
echo "===================================="
echo -e "${GREEN}🎉 EventPilot 开发环境设置完成！${NC}"
echo "===================================="
echo ""
print_info "📝 开发文档: docs/DEV_ENVIRONMENT_SETUP.md"
print_info "🚀 启动服务: ./start-services.sh"
print_info "🌐 前端访问: http://localhost:3000"
print_info "🔧 后端API: http://localhost:8000"
echo ""
print_warning "⚠️  请将.env文件添加到.gitignore，不要提交敏感信息"
print_warning "⚠️  生产环境部署前，请修改所有密钥和配置"
echo ""
print_success "你可以现在运行 ./start-services.sh 启动所有服务"