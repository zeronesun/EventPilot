# EventPilot - 活动领航系统

一个专业的活动承办团队工作流管理平台，实现活动交付的标准化、可控化与持续进化。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://djangoproject.com)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0-green.svg)](https://vuejs.org)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

## 🚀 项目概述

EventPilot是专为高端活动承办团队设计的内部工作流引擎和知识中枢，通过**流程引擎**（固化最佳实践）与**复盘引擎**（沉淀经验教训）的双轮驱动，确保每次活动交付精善尽美。

### 核心价值

- **对负责人**：全局视图掌控进度，沉淀标准化流程，通过数据驱动复盘优化
- **对团队**：任务清晰透明，协作信息同步及时，减少失误  
- **对业务**：提升交付可靠性与客户满意度，构建专业服务壁垒

### 技术架构

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

### ✅ Phase 1 - 基础架构 (100% 完成)

**API基础设施和前后端集成**：
- **完整的Django + DRF后端架构**
- **JWT认证系统** (access token 15分钟 + refresh token)
- **TypeScript API客户端** (类型安全，错误处理完备)
- **Pinia状态管理** (Auth Store, Events Store, Tasks Store)
- **Vue 3前端页面** (登录、首页、活动、任务)
- **完整的API端点实现**

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

### ✅ Phase 2 - 核心功能 (100% 完成)

**完整的CRUD功能和实时协作**：

#### 用户管理CRUD
- **用户创建** - 创建端点 + 密码强度验证 + 角色分配 + 活跃度追踪
- **用户更新** - 支持部分更新 + 状态变更 + 信息修改 + 密码修改
- **用户删除** - 软删除 + 权限验证 + 审计日志 + 关联清理
- **高级功能** - 活跃度评分 + 行为分析 + 安全策略 + 锁定解锁

#### 活动管理CRUD
- **活动创建** - 完整验证 + 预算初始化 + 参与者管理 + 时间线设置
- **活动更新** - 状态流转 + 风险评估 + 统计更新 + 资源调整
- **活动删除** - 安全删除 + 关联处理 + 审计记录 + 软删除支持
- **高级功能** - 状态机流转 + 风险评估算法 + 模板系统 + 导出功能
- **统计分析** - 多维统计 + 进度计算 + 预算分析 + 时间线分析

#### 任务管理CRUD
- **任务创建** - 依赖关系 + 优先级分配 + 自动分配 + 截止时间管理
- **任务更新** - 状态变更 + 进度更新 + 重新分配 + 标签管理
- **任务删除** - 依赖检查 + 权限验证 + 软删除 + 审计日志
- **高级功能** - 完成连锁反应 + 依赖关系检测 + 智能重分配 + 绩效分析
- **看板系统** - 状态看板 + 拖拽操作 + 批量处理 + 实时同步

#### 清单管理CRUD
- **清单模板** - 分类管理 + 版本控制 + 项目定义 + 权重设置
- **清单实例** - 模板实例化 + 执行追踪 + 完成度计算 + 历史版本
- **清单核验** - 核验执行 + 状态更新 + 异常提醒 + 记录追踪
- **高级功能** - 进度可视化 + 自动完成检测 + 层次化结构 + 搜索过滤

#### 实时通信功能
- **WebSocket服务** - 企业级实时通讯基础设施
- **连接管理** - JWT认证 + 心跳检测 + 多设备支持 + 连接池管理
- **消息系统** - 消息路由 + 优先级队列 + 压缩支持 + 重试机制
- **实时通知** - 智能推送 + 优先级分类 + 阅读状态 + 聚合去重
- **在线状态** - 状态追踪 + 活跃监控 + 跨设备同步 + 离线检测
- **实时协作** - 状态同步 + 更新广播 + 操作日志 + 冲突检测

#### 文件上传系统
- **预签名URL架构** - 安全高效的文件处理
- **上传服务** - 预签名生成 + 类型验证 + 大小限制 + 权限检查
- **文件管理** - 元数据存储 + 版本管理 + 索引搜索 + 共享功能
- **前端集成** - 通用组件 + 拖拽上传 + 进度显示 + 错误处理
- **存储集成** - S3兼容 + 对象管理 + 缓存策略 + 清理机制

### ✅ Phase 3 - 关联方档案管理系统 (100% 完成)

**完整的档案管理和智能推荐系统**：

#### 关联方档案管理 API
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

#### 智能功能特性
- **规则基智能推荐** - 零外部依赖的推荐引擎
- **多维度评分** - 信用评分 + 质量评分 + 风险评估
- **交互历史追踪** - 完整的业务交互记录和时间线
- **评估评级体系** - 多维度档案评估和风险控制
- **数据分析和可视化** - 仪表盘统计、趋势分析、风险监控

#### 技术亮点
- ✅ **零依赖智能化** - 完全自主可控的规则基智能推荐引擎
- ✅ **成本控制** - 集成开发后无持续费用
- ✅ **数据安全** - 所有数据不出域，完全符合企业安全要求
- ✅ **高性能** - 本地计算，无网络延迟，响应快速
- ✅ **可解释性** - 规则透明，结果可追溯和调试
- ✅ **可扩展性** - 为传统ML和未来AI功能预留完整接口

## 🔌 API 端点完整列表

### 基础端点
- `GET /api/health` - 健康检查
- `GET /api/` - API信息

## 🧪 开发和测试

### 调试工具
项目包含完整的调试和测试工具，位于 `debug/` 目录：

```bash
# 查看可用的调试工具
cat debug/README.md

# Phase 2 功能验证
python debug/phase2/verify_phase2.py

# WebSocket 基础设施验证  
bash debug/websocket/verify_websocket_setup.sh
```

### 测试覆盖
- `debug/phase1/` - Phase 1 基础架构测试
- `debug/phase2/` - Phase 2 核心功能测试
- `debug/phase3/` - Phase 3 智能系统测试
- `debug/integration/` - 集成测试
- `debug/infrastructure/` - 基础设施验证
- `debug/verification/` - 阶段验收测试

## 📦 安装和部署

### 开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd EventPilot

# 2. 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置环境变量

# 5. 初始化项目
chmod +x scripts/init.sh
./scripts/init.sh

# 6. 启动开发服务器
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

## 📁 项目结构

```
EventPilot/
├── api/                    # API框架
├── apps/                   # 应用模块
│   ├── users/             # 用户管理
│   ├── events/            # 活动管理
│   ├── tasks/             # 任务管理
│   ├── checklists/        # 核验清单
│   ├── profiles/          # 关联方档案 (Phase 3)
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
├── debug/                 # 调试和测试工具 🆕
├── frontend/              # Vue.js前端
├── devdoc/                # 开发文档 🆕
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

## 🚀 版本历史

- **v1.1 Phase 1** (✅ 100%)：API基础设施 + 前后端完整集成
- **v1.2 Phase 2** (✅ 100%)：完整CRUD功能 + 实时协作 + 文件系统
- **v1.3 Phase 3** (✅ 100%)：关联方档案管理 + 规则基智能推荐 + 数据分析

**系统状态**: 🟢 生产就绪，准备部署

## 📚 文档

### 开发文档
- [Phase 3 开发方案](devdoc/Phase3_开发方案.md)
- [Phase 3 完成报告](devdoc/Phase3_Completion_Report.md)
- [Phase 2 功能实现文档](devdoc/PHASE2_EVENT_MANAGEMENT_IMPLEMENTATION.md)
- [Phase 2 WebSocket 实现](devdoc/PHASE2_WEBSOCKET_IMPLEMENTATION.md)
- [WebSocket 快速开始](devdoc/WEBSOCKET_QUICK_START.md)

### 测试和调试
- [调试工具说明](debug/README.md)

## 🧪 测试工具使用

### 快速验证系统状态
```bash
# 验证 Phase 2 核心功能
python debug/phase2/verify_phase2.py

# 验证 WebSocket 基础设施
bash debug/websocket/verify_websocket_setup.sh
```

### 查看可用测试
```bash
# 查看所有可用的测试工具
cat debug/README.md
```

## 🎯 项目特点

### 技术创新
- 🔄 **规则基AI智能** - 不依赖大模型API，完全自主可控
- 🔒 **企业级安全** - 数据完全在本地，符合企业安全要求
- ⚡ **高性能架构** - 零网络延迟，响应速度极快
- 🎨 **现代化UI** - Material Design 3，优秀的用户体验

### 业务价值
- 📊 **数据驱动决策** - 智能推荐和数据分析
- 🤝 **完整的关系管理** - 客户、供应商、合作伙伴全面管理
- ⚠️ **风险控制** - 多维度风险监控和预警
- 🎯 **业务洞察** - 数据可视化和趋势分析

## 📄 许可证

内部使用项目

## 👥 团队

开发团队和产品团队

## 📞 支持

联系系统管理员获取支持和文档

---

**EventPilot - 让活动交付精善尽美，让团队专业能力可持续积累**