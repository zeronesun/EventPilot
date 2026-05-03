# EventPilot 项目架构全面分析

## 📋 项目概述

**项目名称**：EventPilot - 活动领航系统  
**版本**：v1.2 Phase 2  
**技术栈**：Django 5.2 + Vue 3 + Element Plus + PostgreSQL + Redis  
**定位**：企业级活动全生命周期管理系统

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                   前端 (Frontend)                     │
│  Vue 3 + TypeScript + Pinia + Element Plus           │
│  Vite构建 | 响应式设计 | 组件化开发                    │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────▼─────────────────────────────┐
│                  后端 (Backend)                       │
│              Django 5.2 + DRF                        │
│  ┌─────────────────────────────────────────────┐    │
│  │            API Layer (REST)                  │    │
│  │   Views | Serializers | Permissions          │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │         Service Layer (Business Logic)       │    │
│  │  EventService | TaskService | UserService... │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │            Data Layer (Models)               │    │
│  │     Django ORM | PostgreSQL | Redis Cache    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐   ┌───────────┐   ┌────────────┐
   │PostgreSQL│   │   Redis   │   │  WebSocket  │
   │ (主数据库)│   │(缓存/会话) │   │(实时通信)   │
   └─────────┘   └───────────┘   └────────────┘
```

---

## 📁 项目目录结构

```
EventPilot/
├── api/                          # API网关层
│   ├── middleware/                # 中间件（认证、日志、限流）
│   └── urls.py                   # 主路由配置
│
├── apps/                         # Django应用模块
│   ├── users/                    # 用户管理（认证、权限、角色）
│   ├── events/                   # 活动管理（核心模块）
│   ├── tasks/                    # 任务管理（依赖关系、状态机）
│   ├── checklists/               # 清单管理（模板、实例、验证）
│   ├── files/                    # 文件管理（上传、下载）
│   ├── profiles/                 # 关联方档案（联系人、供应商）
│   ├── knowledge/                # 知识库（经验总结、标签）
│   ├── notifications/            # 通知中心（站内信、邮件）
│   ├── reviews/                  # 复盘管理（活动回顾、改进）
│   ├── security/                 # 安全工具（JWT、密码加密）
│   ├── websocket/                # WebSocket服务（实时通信）
│   ├── authorization/            # 权限控制（RBAC）
│   └── core/                     # 核心工具（事件总线、仓库模式）
│
├── config/                       # 配置文件
│   ├── settings/
│   │   ├── base.py               # 基础配置
│   │   ├── development.py        # 开发环境配置
│   │   ├── production.py         # 生产环境配置
│   │   └── testing.py            # 测试环境配置
│   └── urls.py                   # URL路由
│
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── api/                  # API客户端（TypeScript类型定义）
│   │   ├── components/           # 公共组件
│   │   ├── views/                # 页面组件
│   │   ├── stores/               # Pinia状态管理
│   │   ├── router/               # 路由配置
│   │   ├── utils/                # 工具函数
│   │   └── App.vue               # 根组件
│   └── package.json
│
├── docs/                         # 文档
│   ├── architecture/             # 架构文档
│   └── development/              # 开发文档
│
├── tests/                        # 测试文件
├── scripts/                      # 工具脚本
├── logs/                         # 日志文件
├── start.sh                      # 启动脚本
├── manage.py                     # Django管理脚本
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明
```

---

## 🔧 核心技术栈详解

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要编程语言 |
| Django | 5.2 | Web框架 |
| Django REST Framework | 3.15+ | REST API框架 |
| PostgreSQL | 16+ | 主数据库 |
| Redis | 7+ | 缓存和会话存储 |
| Channels | 4+ | WebSocket支持 |
| JWT | PyJWT | 认证令牌 |
| Celery | 5.4+ | 异步任务队列 |
| Pillow | 图像处理 | 头像处理 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.x | 前端框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 6.x | 构建工具 |
| Pinia | 2.x | 状态管理 |
| Element Plus | 2.x | UI组件库 |
| Axios | HTTP客户端 | API调用 |
| ECharts | 5.x | 数据可视化 |
| Vue Router | 4.x | 路由管理 |

---

## 🎯 核心业务模块

### 1. 用户与权限系统 (`apps/users`)

**功能**：用户注册、登录、权限管理、角色分配

**模型**：
- `User` - 用户模型（继承AbstractBaseUser）
- `UserRole` - 角色枚举（admin, manager, operator, viewer, guest）

**特性**：
- JWT Token认证（12小时有效期）
- RBAC权限控制（基于角色的访问控制）
- 密码强度验证（8位以上，包含大小写、数字、特殊字符）
- 账户锁定机制（5次失败锁定30分钟）
- 用户导入导出功能

---

### 2. 活动管理 (`apps/events`)

**功能**：活动创建、编辑、状态流转、预算管理

**模型**：
- `Event` - 活动模型（名称、类型、时间、预算、状态等）
- `EventParticipant` - 参与者
- `EventTemplate` - 活动模板

**特性**：
- 活动生命周期管理（策划→执行→完成→复盘→取消）
- 预算管理（预估预算、实际支出、偏差计算）
- 风险评估（时间、预算、任务、进度风险因子）
- 数据统计仪表盘
- 活动模板复用

---

### 3. 任务管理 (`apps/tasks`)

**功能**：任务创建、分配、依赖管理、进度跟踪

**模型**：
- `Task` - 任务模型（标题、描述、优先级、状态等）
- `TaskDependency` - 任务依赖关系

**特性**：
- 任务状态机（待办→就绪→进行中→已完成→已取消→阻塞）
- 任务依赖关系（支持循环依赖检测）
- 自动状态更新（前置任务完成后自动触发后续任务）
- 批量操作支持
- 任务看板视图

---

### 4. 清单管理 (`apps/checklists`)

**功能**：检查清单模板、实例、验证、报告导出

**模型**：
- `ChecklistTemplate` - 清单模板
- `ChecklistInstance` - 清单实例
- `ChecklistItem` - 清单项

**特性**：
- 清单模板创建和管理
- 实例化清单并跟踪进度
- 自动完成度警告（80%/95%阈值）
- 报告导出（Markdown格式）
- 版本控制和历史记录

---

### 5. 文件管理 (`apps/files`)

**功能**：文件上传、下载、预览、分享

**特性**：
- 多种文件类型支持（图片、文档、视频等）
- 文件大小限制（10MB）
- 文件预览功能
- 文件关联到活动或任务

---

### 6. 关联方档案 (`apps/profiles`)

**功能**：联系人、供应商、合作伙伴信息管理

**模型**：
- `Profile` - 档案模型（姓名、联系方式、公司、角色等）

**特性**：
- 关联方分类（嘉宾、供应商、合作伙伴等）
- 联系方式管理
- 与活动和任务的关联

---

### 7. 知识库 (`apps/knowledge`)

**功能**：经验总结、知识沉淀、标签管理

**模型**：
- `KnowledgeEntry` - 知识条目（标题、内容、标签、分类等）

**特性**：
- Markdown内容编辑
- 标签和分类管理
- 知识搜索和推荐
- 从复盘自动提取经验

---

### 8. 通知中心 (`apps/notifications`)

**功能**：站内通知、邮件通知、WebSocket实时推送

**特性**：
- 多渠道通知（站内信、邮件）
- 通知类型分类（系统、任务、活动、安全）
- 已读未读状态管理
- WebSocket实时推送

---

### 9. 复盘管理 (`apps/reviews`)

**功能**：活动回顾、问题总结、改进建议

**模型**：
- `Review` - 复盘模型（评分、总结、改进建议等）

**特性**：
- 活动结束后自动创建复盘
- 多维度评分体系
- 问题追踪和改进建议
- 经验自动提取到知识库

---

### 10. WebSocket实时通信 (`apps/websocket`)

**功能**：实时消息推送、在线状态、协作功能

**特性**：
- 基于Django Channels的WebSocket实现
- 消息类型验证
- 连接管理和心跳检测
- 用户在线状态同步

---

## 🔐 安全机制

### 1. 认证系统

**JWT Token认证**
- Access Token: 12小时有效
- Refresh Token: 7天有效
- Token刷新机制
- Token黑名单（登出时失效）

### 2. 权限控制

**RBAC（基于角色的访问控制）**
- 5个角色级别：admin, manager, operator, viewer, guest
- 资源级权限控制
- 接口级权限装饰器
- 权限缓存优化

### 3. 数据安全

**密码安全**
- Argon2哈希算法
- 密码强度验证
- 常见弱密码检测

**数据传输**
- HTTPS强制跳转（生产环境）
- CORS跨域配置
- CSRF保护

### 4. 安全防护

**输入验证**
- 前后端双重验证
- SQL注入防护（Django ORM）
- XSS防护（前端过滤）

**访问控制**
- IP白名单
- 请求频率限制
- 账户暴力破解保护

---

## 🔄 数据流架构

### 典型用户操作流程

```
用户操作 → 前端组件 → API Client → REST API → Service Layer → Model/ORM → Database
                                    ↓
                              Permission Check
                                    ↓
                              Cache Layer (Redis)
                                    ↓
                              WebSocket Push (实时更新)
```

### 示例：创建活动流程

1. 用户填写活动表单
2. 前端验证数据完整性
3. 发送POST `/api/events/events/`
4. API层检查用户权限
5. Service层验证业务规则
6. 创建Event记录到PostgreSQL
7. 更新Redis缓存
8. 通过WebSocket推送通知
9. 返回响应给前端
10. 前端更新UI显示

---

## 📊 数据库设计核心表

### 核心实体关系

```
User (用户)
├── owns many Event (活动)
├── assigned to many Task (任务)
├── creates many ChecklistTemplate (清单模板)
├── creates many KnowledgeEntry (知识条目)
└── receives many Notification (通知)

Event (活动)
├── has many Task (任务)
├── has many File (文件)
├── has many Profile (关联方档案)
├── has one Review (复盘)
└── has many ChecklistInstance (清单实例)

Task (任务)
├── has many TaskDependency (依赖关系)
├── has many File (文件)
└── belongs to one Event (活动)

ChecklistTemplate (清单模板)
├── has many ChecklistItem (清单项)
└── instances many ChecklistInstance (清单实例)

ChecklistInstance (清单实例)
├── has many ChecklistItemInstance (清单项实例)
└── belongs to one Event (活动)
```

---

## 🚀 部署架构

### 生产环境部署

```
┌─────────────────────────────────────────┐
│              Nginx (反向代理)             │
│         SSL终止 | 静态资源 | 反向代理     │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│ Gunicorn│  │  Daphne  │  │  Nginx   │
│(Django) │  │(Channels)│  │(静态文件) │
└────┬───┘  └────┬─────┘  └──────────┘
     │           │
     ▼           ▼
┌─────────────────────────┐
│      PostgreSQL 16      │
└─────────────────────────┘
     │
┌─────────────────────────┐
│       Redis 7           │
│  缓存 | 会话 | Celery    │
└─────────────────────────┘
     │
┌─────────────────────────┐
│      Celery Worker      │
│  异步任务 | 定时任务      │
└─────────────────────────┘
```

---

## 🧪 测试策略

### 测试层次

1. **单元测试** - 服务层逻辑测试
2. **集成测试** - API接口测试
3. **E2E测试** - 端到端流程测试

### 测试工具

- **后端**: pytest, pytest-django, factory-boy
- **前端**: Vitest, Cypress

---

## 📈 性能优化策略

### 后端优化

1. **数据库优化**
   - 索引优化
   - 查询优化（select_related, prefetch_related）
   - 数据库连接池

2. **缓存策略**
   - Redis缓存热点数据
   - 页面级缓存
   - API响应缓存

3. **异步处理**
   - Celery异步任务
   - 邮件发送异步化
   - 大数据处理异步化

### 前端优化

1. **代码分割** - 路由懒加载
2. **组件缓存** - keep-alive
3. **虚拟滚动** - 大列表优化
4. **图片懒加载** - 减少首屏加载时间

---

## 🔧 开发工具链

### 代码质量工具

- **后端**: black (格式化), flake8 (linting), mypy (类型检查)
- **前端**: ESLint, Prettier

### CI/CD流程

1. 代码提交触发CI
2. 单元测试执行
3. 代码质量检查
4. 构建Docker镜像
5. 部署到测试环境
6. 自动化测试通过后部署生产

---

## 🎨 设计原则

### 1. 分层架构

- **表现层**: API接口和前端页面
- **业务层**: Service封装业务逻辑
- **数据层**: Model和数据访问

### 2. 设计模式应用

- **仓库模式**: 数据访问抽象
- **工厂模式**: 对象创建
- **观察者模式**: 事件驱动
- **策略模式**: 业务规则可插拔

### 3. SOLID原则

- **单一职责**: 每个类只负责一件事
- **开闭原则**: 对扩展开放，对修改关闭
- **依赖倒转**: 依赖抽象而非具体实现

---

## 📝 总结

EventPilot是一个**功能完善、架构清晰、技术先进**的企业级活动管理系统。它采用了现代化的技术栈，遵循最佳实践，具备良好的可维护性和可扩展性。

### 项目亮点

✅ **完整的RBAC权限系统**  
✅ **灵活的活动生命周期管理**  
✅ **强大的任务依赖和状态机**  
✅ **实时的WebSocket通信**  
✅ **完善的文档和测试覆盖**  
✅ **生产级的部署方案**

### 适用场景

- 企业活动策划和管理
- 会议和展会组织
- 团队协作项目管理
- 流程标准化和知识沉淀

---

**文档生成时间**: 2026年5月2日  
**文档版本**: v1.0  
**适用项目版本**: EventPilot v1.2 Phase 2