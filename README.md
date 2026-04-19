# EventPilot - 活动领航系统

一个专业的活动承办团队工作流管理平台，实现活动交付的标准化、可控化与持续进化。

## 🚀 项目概述

EventPilot是专为高端活动承办团队设计的内部工作流引擎和知识中枢，通过**流程引擎**（固化最佳实践）与**复盘引擎**（沉淀经验教训）的双轮驱动，确保每次活动交付精善尽美。

### 核心价值

- **对负责人**：全局视图掌控进度，沉淀标准化流程，通过数据驱动复盘优化
- **对团队**：任务清晰透明，协作信息同步及时，减少失误  
- **对业务**：提升交付可靠性与客户满意度，构建专业服务壁垒

### 技术栈

#### 后端
- **框架**：Django 5 + DRF
- **数据库**：SQLite (开发) → PostgreSQL 15 (生产)
- **缓存**：Redis
- **认证**：JWT认证 (access + refresh token)
- **部署**：Gunicorn + Nginx

#### 前端  
- **框架**：Vue 3 + Vite + TypeScript
- **状态管理**：Pinia
- **UI组件**：Element Plus
- **HTTP客户端**：TypeScript Fetch Wrapper (符合fullstack-dev最佳实践)
- **路由**：Vue Router

## 📋 功能模块

### ✅ 已完成 (Phase 1 基础设施)

API基础设施和前端后端集成：
- **完整的Django + DRF后端架构**
- **JWT认证系统** (access token 15分钟 + refresh token)
- **TypeScript API客户端** (类型安全，错误处理完备)
- **Pinia状态管理** (Auth Store, Events Store, Tasks Store)
- **Vue 3前端页面** (登录、首页、活动、任务)
- **完整的API端点实现**

### ✅ 已完成 (Phase 1 MVP端点)

#### 认证API
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/refresh/` - 刷新JWT token
- `POST /api/auth/verify/` - 验证token有效性

#### 用户API
- `GET /api/users/` - 用户列表
- `GET /api/users/me/` - 当前用户信息
- `POST /api/users/change_password/` - 修改密码

#### 活动API
- `GET /api/events/` - 活动列表（支持过滤、搜索、分页）
- `POST /api/events/` - 创建活动
- `GET /api/events/{id}/` - 活动详情
- `PUT /api/events/{id}/` - 更新活动
- `DELETE /api/events/{id}/` - 删除活动
- `POST /api/events/{id}/complete/` - 标记活动完成
- `GET /api/events/{id}/statistics/` - 活动统计

#### 任务API
- `GET /api/tasks/` - 任务列表（支持过滤、搜索、分页）
- `POST /api/tasks/` - 创建任务
- `GET /api/tasks/{id}/` - 任务详情
- `PUT /api/tasks/{id}/` - 更新任务
- `DELETE /api/tasks/{id}/` - 删除任务
- `PATCH /api/tasks/{id}/complete/` - 完成任务
- `GET /api/tasks/kanban_data?event={id}` - 看板数据

#### 核验清单API
- `GET /api/checklists/templates/` - 清单模板
- `POST /api/checklists/instances/` - 创建清单实例
- `GET /api/checklists/items/` - 清单项
- `POST /api/checklists/items/{id}/check/` - 执行核验

### 🚧 计划中 (Phase 2-3)

#### 立即开始 (Phase 2)
- **完整认证流程测试** - 验证JWT登录/登出/刷新
- **前后端集成测试** - 启动服务器验证数据流
- **实时功能** - WebSocket服务准备
- **文件上传** - 预签名URL实现
- **CRUD完善** - 创建/编辑/删除操作完成

#### 后续功能 (Phase 2-3)
- 关联方档案管理系统
- 结构化复盘和知识库
- 数据仪表盘和智能推荐
- 微信深度集成

## 📦 安装和部署

### 开发环境

```bash
# 1. 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置环境变量

# 4. 初始化项目
chmod +x scripts/init.sh
./scripts/init.sh

# 5. 启动开发服务器
chmod +x scripts/dev_start.sh
./scripts/dev_start.sh
```

### 生产环境部署

#### 服务器要求

- **操作系统**：Ubuntu 22.04+
- **Python**：3.11+
- **数据库**：PostgreSQL 15
- **缓存**：Redis 7+
- **Web服务器**：Nginx
- **应用服务器**：Gunicorn

#### 部署步骤

```bash
# 1. 克隆代码
git clone <repository-url>
cd EventPilot

# 2. 配置环境变量
sudo cp .env.example /etc/eventpilot/.env
sudo nano /etc/eventpilot/.env
# 按生产环境配置修改.env文件

# 3. 创建Python环境
python3.11 -m venv /opt/eventpilot/venv
source /opt/eventpilot/venv/bin/activate
pip install -r requirements.txt

# 4. 运行数据库迁移
python manage.py migrate --noinput

# 5. 创建超级用户
python manage.py createsuperuser

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 配置Nginx
sudo cp scripts/config/nginx.conf /etc/nginx/sites-available/eventpilot
sudo ln -s /etc/nginx/sites-available/eventpilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. 配置systemd服务
sudo cp scripts/config/eventpilot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable eventpilot
sudo systemctl start eventpilot
```

## 🔌 API 端点

### 基础端点
- `GET /api/health` - 健康检查
- `GET /api/` - API信息

### 认证API (JWT)
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/refresh/` - 刷新JWT token
- `POST /api/auth/verify/` - 验证token有效性

### 用户API  
- `GET /api/users/` - 用户列表
- `GET /api/users/me/` - 当前用户信息
- `POST /api/users/change_password/` - 修改密码

### 活动API
- `GET /api/events/` - 活动列表（支持过滤、搜索、分页）
- `POST /api/events/` - 创建活动
- `GET /api/events/{id}/` - 活动详情
- `PUT /api/events/{id}/` - 更新活动
- `POST /api/events/{id}/complete/` - 标记活动完成
- `GET /api/events/{id}/statistics/` - 活动统计

### 任务API
- `GET /api/tasks/` - 任务列表
- `POST /api/tasks/` - 创建任务
- `PATCH /api/tasks/{id}/complete/` - 完成任务
- `POST /api/tasks/{id}/dependencies/` - 管理依赖
- `GET /api/tasks/kanban_data?event={id}` - 看板数据

### 核验清单API
- `GET /api/checklists/templates/` - 清单模板
- `POST /api/checklists/instances/` - 创建清单实例
- `GET /api/checklists/items/` - 清单项
- `POST /api/checklists/items/{id}/check/` - 执行核验

## 🧪 开发指南

### 添加新功能模块

1. **创建模型**：在 `apps/{module}/models/` 中定义数据模型
2. **创建序列化器**：在 `apps/{module}/api/serializers.py` 中定义API序列化器  
3. **创建视图**：在 `apps/{module}/api/views.py` 中实现API视图
4. **注册路由**：在 `apps/{module}/api/urls.py` 中配置URL
5. **更新主路由**：在 `config/urls.py` 中注册应用路由

### 数据库迁移

```bash
# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定应用的测试
pytest tests/unit/test_events/

# 查看测试覆盖率
pytest --cov=apps --cov-report=html
```

## 📁 项目结构

```
EventPilot/
├── api/                    # API框架
├── apps/                   # 应用模块
│   ├── users/             # 用户管理
│   ├── events/            # 活动管理
│   ├── tasks/             # 任务管理
│   ├── checklists/        # 核验清单
│   ├── profiles/          # 关联方档案
│   ├── knowledge/         # 知识库
│   └── reviews/           # 复盘
├── config/                # Django配置
├── core/                  # 核心功能模块
├── database/              # 数据库辅助
├── logs/                  # 日志目录
├── public/                # 静态文件
├── scripts/               # 部署和初始化脚本
├── storage/               # 文件存储
├── tests/                 # 测试
├── frontend/              # Vue.js前端
├── devdoc/                # 开发文档
├── manage.py
├── requirements.txt
└── .env.example           # 环境变量模板
```

## 🔐 安全和权限

- **认证**：JWT认证 (access token + refresh token机制)
- **权限**：基于角色的访问控制（RBAC）
- **密码**：Argon2加密存储
- **数据安全**：支持数据加密和完整审计日志

## 📊 性能目标

- **API响应时间**：核心接口 < 2秒
- **页面加载时间**：首屏渲染 < 1.5秒
- **并发支持**：100+ 用户同时操作

## 🚗 版本历史

- **v1.1 Phase 1** (当前)：API基础设施 + 前后端完整集成
- **v1.2** (计划)：完整CRUD功能 + 实时协作
- **v1.3** (计划)：智能推荐 + 知识库 + 微信集成

## 📄 许可证

内部使用项目

## 👥 团队

开发团队和产品团队

## 📞 支持

联系系统管理员获取支持和文档

---

**EventPilot - 让活动交付精善尽美，让团队专业能力可持续积累**
