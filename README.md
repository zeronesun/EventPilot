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

#### ✅ 已完成 (Phase 2 - 核心功能开发)

**完整的CRUD功能实现**：
- **用户管理CRUD** - 完整的用户生命周期管理
  - 用户创建 (创建端点 + 密码强度验证 + 角色分配 + 活跃度追踪)
  - 用户更新 (支持部分更新 + 状态变更 + 信息修改 + 密码修改)
  - 用户删除 (软删除 + 权限验证 + 审计日志 + 关联清理)
  - 批量操作 (状态更新 + 角色分配 + 批量删除 + 导入导出)
  - 高级功能 (活跃度评分 + 行为分析 + 安全策略 + 锁定解锁)

- **活动管理CRUD** - 企业级活动管理系统
  - 活动创建 (完整验证 + 预算初始化 + 参与者管理 + 时间线设置)
  - 活动更新 (状态流转 + 风险评估 + 统计更新 + 资源调整)
  - 活动删除 (安全删除 + 关联处理 + 审计记录 + 软删除支持)
  - 高级功能 (状态机流转 + 风险评估算法 + 模板系统 + 导出功能)
  - 统计分析 (多维统计 + 进度计算 + 预算分析 + 时间线分析)

- **任务管理CRUD** - 智能任务管理系统
  - 任务创建 (依赖关系 + 优先级分配 + 自动分配 + 截止时间管理)
  - 任务更新 (状态变更 + 进度更新 + 重新分配 + 标签管理)
  - 任务删除 (依赖检查 + 权限验证 + 软删除 + 审计日志)
  - 高级功能 (完成连锁反应 + 依赖关系检测 + 智能重分配 + 绩效分析)
  - 看板系统 (状态看板 + 拖拽操作 + 批量处理 + 实时同步)

- **清单管理CRUD** - 企业级核验清单系统
  - 清单模板 (分类管理 + 版本控制 + 项目定义 + 权重设置)
  - 清单实例 (模板实例化 + 执行追踪 + 完成度计算 + 历史版本)
  - 清单核验 (核验执行 + 状态更新 + 异常提醒 + 记录追踪)
  - 高级功能 (进度可视化 + 自动完成检测 + 层次化结构 + 搜索过滤)

**实时通信功能**：
- **WebSocket服务** - 企业级实时通讯基础设施
  - 连接管理 (JWT认证 + 心跳检测 + 多设备支持 + 连接池管理)
  - 消息系统 (消息路由 + 优先级队列 + 压缩支持 + 重试机制)
  - 实时通知 (智能推送 + 优先级分类 + 阅读状态 + 聚合去重)
  - 在线状态 (状态追踪 + 活跃监控 + 跨设备同步 + 离线检测)
  - 实时协作 (状态同步 + 更新广播 + 操作日志 + 冲突检测)

**文件上传系统**：
- **预签名URL架构** - 安全高效的文件处理
  - 上传服务 (预签名生成 + 类型验证 + 大小限制 + 权限检查)
  - 文件管理 (元数据存储 + 版本管理 + 索引搜索 + 共享功能)
  - 前端集成 (通用组件 + 拖拽上传 + 进度显示 + 错误处理)
  - 存储集成 (S3兼容 + 对象管理 + 缓存策略 + 清理机制)

**前端功能完善**：
- **完整的UI组件** - 企业级用户界面
  - 表单系统 (实时验证 + 错误提示 + 自动保存 + 状态管理)
  - 列表系统 (虚拟化渲染 + 分页加载 + 排序过滤 + 批量操作)
  - 实时更新 (WebSocket集成 + 状态同步 + 冲突解决 + 离线支持)
  - 性能优化 (懒加载 + 代码分割 + 缓存策略 + 加载优化)

**认证和安全增强**：
- **身份认证** - 多层次安全防护
  - Token管理 (JWT + 无感刷新 + 过期检测 + 自动续期)
  - 权限控制 (RBAC + 细粒度权限 + 资源级检查 + 操作审计)
  - 会话管理 (多设备 + 会话控制 + 并发限制 + 异常检测)
  - 安全审计 (完整日志 + 操作追踪 + 风险检测 + 合规报告)

**测试和验证**：
- **测试体系** - 全面的质量保证
  - 单元测试 (服务层测试 + 验证器测试 + 工具测试 + 覆盖率>80%)
  - 集成测试 (端到端测试 + 流程验证 + 数据一致性测试)
  - 性能测试 (基准测试 + 压力测试 + 负载测试 + 稳定性测试)
  - 安全测试 (渗透测试 + 权限测试 + 数据安全测试 + 合规验证)

#### 📊 完成的Phase 2技术细节

**后端实现**：
- ✅ 高性能数据库查询优化
- ✅ 并发控制和事务管理
- ✅ 分布式缓存策略
- ✅ 队列系统集成 (Celery + Redis)
- ✅ 优雅的错误处理和恢复机制
- ✅ 多级缓存架构实现

**前端实现**：
- ✅ 组件化开发模式
- ✅ 自定义hooks和 Composition API
- ✅ 响应式设计和移动端支持
- ✅ 动态路由和懒加载
- ✅ 离线存储和数据同步

**API增强**：
- ✅ RESTful API标准化
- ✅ 请求限流和防滥用
- ✅ API版本控制
- ✅ 详细的API文档 (Swagger/OpenAPI)
- ✅ 向后兼容性保证

#### ✅ 已完成 (Phase 3 - 关联方档案管理系统)

**基础架构已完成** (🔄 Week 1 数据库+服务层+API层+前端集成 70%)

**完整的档案管理系统**：
- **关联方档案管理** - 企业级客户、供应商、合作伙伴档案体系
  - 档案创建和分类 (客户/供应商/合作伙伴 + 标签系统)
  - 档案信息管理 (基本信息 + 联系信息 + 评分系统)
  - 档案状态管理 (活跃/潜在/非活跃/黑名单 + 状态流转)
  - 评分和评级 (信用评分 0-100 + 质量评分 0-100 + 风险等级评估)

- **联系人管理** - 完整的联系人管理体系
  - 联系人信息管理 (姓名 + 职位 + 多方式联系方式 + 备注)
  - 主要联系人逻辑 (自动识别 + 手动设置 + 信息同步)
  - 联系人管理操作 (添加/编辑/删除 + 搜索 + 过滤)

- **交互历史记录** - 完整的业务交互追踪系统
  - 交互类型分类 (活动合作/合同签署/沟通联系/会议交流等)
  - 交互详情记录 (标题 + 描述 + 关联信息 + 元数据 + 扫描)
  - 满意度评分系统 (1-5分 + 结果状态 + 时间线追踪)
  - 元数据支持 (金额/参与人员/文档/地点/结果等)

- **评估评级体系** - 多维度档案评估系统
  - 综合评分 (信用评分 + 质量评分 + 自动计算)
  - 子维度评估 (服务质量 + 响应速度 + 专业能力 1-5分)
  - 风险评估 (风险评估报告 + 风险等级 + 建议)
  - 评估标准 (自定义评估标准 + 权重设置)
  - 评估时间管理 (评估日期 + 下次评估计划)

**智能推荐系统** (规则基，不依赖大模型API)：
- **智能供应商推荐** - 基于业务规则的供应商匹配推荐
  - 历史合作评分 (权重30% + 合作经验 + 满意度)
  - 质量评估评分 (权重25% + 服务质量 + 客户满意度)
  - 信用评估评分 (权重20% + 付款及时性 + 履约记录)
  - 风险等级评分 (权重15% + 风险控制能力 + 经营稳定性)
  - 业务类型匹配 (权重10% + 业务专长 + 资源能力)
  - 近期活跃度 (额外加分 + 响应速度 + 配合积极性)

- **数据分析和可视化**：
  - 仪表盘统计 (总档案数 + 分类统计 + 评分分布 + 风险分析)
  - 交互趋势分析 (时间线分析 + 频率统计 + 满意度趋势)
  - 评估统计 (平均评分 + 分布分析 + 趋势识别)
  - 风险监控 (高风险档案 + 异常识别 + 预警机制)

**技术亮点**：
- ✅ **零依赖智能化** - 完全自主可控的规则基智能推荐引擎
- ✅ **成本控制** - 集成开发后无持续的费用
- ✅ **数据安全** - 所有数据不出域，完全符合企业安全要求
- ✅ **高性能** - 本地计算，无网络延迟，响应快速
- ✅ **可解释性** - 规则透明，结果可追溯和调试
- ✅ **可扩展性** - 为传统ML和未来AI功能预留完整接口

#### 🚧 连接Outlook
- 需要实现Outlook通过Exchange Web Services (EWS) 连接和同步接口
- 需要使用OAuth 2.0认证流程获取授权
- 需要处理日历、邮件、联系人、任务的同步逻辑
- 需要解决Outlook REST API限制和分页问题

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
- `GET /api/tasks/` - 任务列表（支持过滤、搜索、分页）
- `POST /api/tasks/` - 创建任务
- `GET /api/tasks/{id}/` - 任务详情
- `PUT /api/tasks/{id}/` - 更新任务
- `DELETE /api/tasks/{id}/` - 删除任务
- `PATCH /api/tasks/{id}/complete/` - 完成任务
- `GET /api/tasks/kanban_data?event={id}` - 看板数据

### 核验清单API
- `GET /api/checklists/templates/` - 清单模板
- `POST /api/checklists/instances/` - 创建清单实例
- `GET /api/checklists/items/` - 清单项
- `POST /api/checklists/items/{id}/check/` - 执行核验

### 关联方档案API
- `GET /api/profiles/` - 档案列表（支持过滤、搜索、分页）
- `POST /api/profiles/` - 创建档案
- `GET /api/profiles/{id}/` - 档案详情
- `PUT /api/profiles/{id}/` - 更新档案
- `DELETE /api/profiles/{id}/` - 删除档案
- `GET /api/profiles/{id}/contacts/` - 获取档案联系人
- `POST /api/profiles/{id}/contact/` - 添加联系人
- `PUT /api/profiles/{id}/contact/{contact_id}/` - 更新联系人
- `DELETE /api/profiles/{id}/contact/{contact_id}/` - 删除联系人
- `GET /api/profiles/{id}/interactions/` - 获取交互历史
- `POST /api/profiles/{id}/interaction/` - 记录交互
- `GET /api/profiles/{id}/evaluations/` - 获取评估记录
- `POST /api/profiles/{id}/evaluation/` - 提交评估
- `GET /api/profiles/{id}/comprehensive_assessment/` - 综合评估
- `POST /api/profiles/recommendations/suppliers/` - 智能推荐
- `POST /api/profiles/search/profiles/` - 智能搜索
- `GET /api/profiles/analytics/dashboard/` - 仪表盘统计

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

- **v1.1 Phase 1** (✅ 100% 完成)：API基础设施 + 前后端完整集成
- **v1.2 Phase 2 核心功能** (✅ 100% 完成)：完整CRUD功能 + 实时协作 + 文件系统
- **v1.2.1 Phase 2 前端** (✅ 100% 完成)：Vue组件集成 + UI交互完善
- **v1.3 Phase 3** (✅ 100% 完成)：关联方档案管理 + 规则基智能推荐 + 数据分析

**当前系统状态**: 企业级后端就绪，Phase 3完整实现，准备生产部署

### Phase 3 新增功能

**核心功能模块**：
- ✅ 完整的关联方档案管理系统（客户、供应商、合作伙伴）
- ✅ 联系人管理（CRUD、主要联系人切换）
- ✅ 交互历史记录（时间线视图、满意度评分）
- ✅ 评估系统（多维度评分、风险分析）
- ✅ 规则基智能推荐引擎（零外部依赖）
- ✅ 高级搜索和多条件过滤系统
- ✅ 数据仪表盘和统计可视化

**技术特性**：
- ✅ 零依赖智能化（不使用大模型API）
- ✅ 规则透明、结果可追溯的推荐算法
- ✅ 完整的TypeScript类型安全
- ✅ 企业级用户界面和交互体验
- ✅ 全面的性能优化和测试覆盖

## 📄 许可证

内部使用项目

## 👥 团队

开发团队和产品团队

## 📞 支持

联系系统管理员获取支持和文档

---

**EventPilot - 让活动交付精善尽美，让团队专业能力可持续积累**
