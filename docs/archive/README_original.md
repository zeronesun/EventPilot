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
- **数据库**：PostgreSQL 15
- **缓存**：Redis
- **认证**：Token认证（可升级为JWT）
- **部署**：传统方式（Gunicorn + Nginx）

#### 前端  
- **框架**：Vue 3 + Vite
- **状态管理**：Pinia
- **UI组件**：Element Plus
- **HTTP客户端**：Axios

## 📋 功能模块

### ✅ 已完成 (Phase 1 MVP)

1. **用户和权限系统**
   - 扩展用户模型（支持手机、部门、职位）
   - 用户角色管理（管理员、项目负责人、执行成员、观察者）
   - 资源级权限控制（RBAC）

2. **活动管理**
   - 活动CRUD和状态跟踪
   - 预算明细管理
   - 自动预算计算和偏差分析
   - 活动统计数据API

3. **任务管理**
   - 任务CRUD和状态管理
   - 多线任务管理（策划、嘉宾、物料、场地、宣传、现场、复盘）
   - 任务依赖关系支持
   - 看板视图和拖拽支持
   - 任务完成触发依赖更新

4. **核验清单**
   - 清单模板系统
   - 清单实例化和核验操作
   - 离线支持（标记待同步）
   - 核验报告生成

### 🚧 计划中 (Phase 2-3)

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

- **认证**：Token认证（生产环境建议使用JWT）
- **权限**：基于角色的访问控制（RBAC）
- **密码**：Argon2加密存储
- **数据安全**：支持数据加密和完整审计日志

## 📊 性能目标

- **API响应时间**：核心接口 < 2秒
- **页面加载时间**：首屏渲染 < 1.5秒
- **并发支持**：100+ 用户同时操作

## 🚗 版本历史

- **v1.0 MVP** (当前)：基础活动、任务、核验清单管理
- **v1.1** (计划)：关联方档案、智能方案生成、结构化复盘
- **v1.2** (已完成)：功能完善与优化

## 📄 许可证

内部使用项目

## 👥 团队

开发团队和产品团队

## 📞 支持

联系系统管理员获取支持和文档

---

**EventPilot - 让活动交付精善尽美，让团队专业能力可持续积累**# EventPilot
