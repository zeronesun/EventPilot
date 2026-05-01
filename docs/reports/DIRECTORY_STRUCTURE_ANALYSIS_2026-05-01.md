# EventPilot 项目目录结构和路径规划分析

## 执行摘要

EventPilot 是一个基于 Django + Vue 3 的全栈项目，采用前后端分离架构。项目总体结构清晰，但存在一些待改进的地方，如重复的虚拟环境、混合的代码组织、以及临时文件散落等问题。

---

## 项目整体架构

```
EventPilot/
├── backend/              (Django 后端)
├── frontend/             (Vue 3 前端)
├── docs/                 (文档)
├── scripts/              (工具脚本)
├── tests/                (测试)
├── archive/              (归档)
└── reports/              (报告)
```

---

## 详细目录结构分析

### 1. 核心架构层

#### 1.1 Django 后端 (`/`)

```
EventPilot/
├── manage.py                    # Django 管理入口
├──config/
│   ├── settings/                # Django 配置
│   │   ├── __init__.py          # 动态加载配置
│   │   ├── base.py              # 基础配置
│   │   ├── development.py       # 开发环境配置
│   │   └── production.py        # 生产环境配置
│   ├── urls.py                  # URL 路由配置
│   ├── wsgi.py
│   └── asgi.py
│
├── api/                         # API 层
│   ├── exceptions.py            # 自定义异常
│   ├── middleware.py            # 中间件
│   ├── permissions.py           # 权限控制
│   ├── urls.py                  # API 路由
│   └── views.py                 # API 视图
│
├── apps/                        # Django 应用 (业务逻辑层)
│   ├── authorization/           # 授权模块
│   │   └── permissions.py
│   ├── checklists/              # 核验清单模块
│   │   ├── api/
│   │   │   ├── advanced_views.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── views.py
│   │   ├── models/
│   │   │   ├── checklist_export.py
│   │   │   ├── checklist_template.py
│   │   │   ├── checklist_verification.py
│   │   │   └── checklist_version.py
│   │   ├── services/
│   │   │   ├── checklist_export_service.py
│   │   │   ├── checklist_service.py
│   │   │   ├── checklist_verification_service.py
│   │   │   └── checklist_version_service.py
│   │   ├── migrations/          # 数据库迁移
│   │   └── tests.py             # 模块测试
│   ├── core/                    # 核心业务模块
│   │   ├── event_bus.py
│   │   └── repositories.py
│   ├── events/                  # 事件管理模块
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── migrations/
│   ├── files/                   # 文件管理模块
│   │   ├── api/
│   │   ├── models/
│   │   └── migrations/
│   ├── tasks/                   # 任务管理模块
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── migrations/
│   │   └── tests/
│   │       └── test_tasks.py   # 任务测试
│   ├── websocket/              # WebSocket 实时通信模块
│   ├── profiles/                # 用户资料模块
│   ├── users/                   # 用户管理模块
│   ├── reviews/                 # 评价模块
│   ├── knowledge/               # 知识库模块
│   ├── home/                    # 首页模块
│   └── security/                # 安全模块
│
├── core/                        # Django 核心模块
├── conftest.py                  # Pytest 配置
├── pytest.ini                   # Pytest 配置文件
└── requirements.txt              # Python 依赖
```

**Django 应用模块结构分析**：

每个应用模块采用统一的 **DDD (Domain Driven Design)** 风格：
- `api/` - API 接口层 (views、serializers、urls)
- `models/` - 数据模型层
- `services/` - 业务逻辑层
- `migrations/` - 数据库迁移层
- `tests/` - 单元测试层

这种分离架构的优点：
1. **关注点分离**: API、业务逻辑、数据模型清晰分离
2. **易于测试**: service 层可以独立测试
3. **可维护性高**: 业务逻辑集中在 service 层

---

#### 1.2 Vue 3 前端 (`/frontend`)

```
frontend/
├── public/                      # 静态资源
│   └── ...
│
├── src/
│   ├── components/              # 组件库
│   │   ├── AdvancedSearch.vue
│   │   ├── AnalyticsDashboard.vue
│   │   ├── ContactsManager.vue
│   │   ├── ErrorBoundary.vue
│   │   ├── EvaluationsManager.vue
│   │   ├── FileManager.vue
│   │   ├── FileUploader.vue
│   │   ├── IntelligentRecommendations.vue
│   │   ├── InteractionsManager.vue
│   │   ├── KanbanColumn.vue     # 看板列组件
│   │   └── Skeleton.vue         # 骨架屏
│   │
│   ├── views/                   # 页面视图
│   │   ├── Home.vue
│   │   ├── Login.vue
│   │   ├── Events.vue
│   │   ├── Tasks.vue            # 任务管理页面
│   │   ├── Users.vue
│   │   ├── Checklists.vue
│   │   ├── Files.vue
│   │   ├── Profiles.vue
│   │   ├── Budget.vue
│   │   ├── Knowledge.vue
│   │   ├── Reviews.vue
│   │   ├── Analytics.vue
│   │   └── NotFound.vue
│   │
│   ├── router/                  # 路由配置
│   │   └── index.js
│   │
│   ├── store/                   # 状态管理 (Pinia)
│   │   └── index.ts             # 主状态商店
│   │
│   ├── stores/                  # 其他状态商店
│   │   ├── profiles.ts         # 用户资料状态
│   │   └── websocket.ts        # WebSocket 状态
│   │
│   ├── api/                     # API 客户端
│   │   ├── client.ts           # Axios 客户端配置
│   │   ├── budget.ts
│   │   └── ...
│   │
│   ├── services/                # 服务层
│   │   └── ...
│   │
│   ├── composables/             # 可组合函数
│   │   ├── useAuthorization.ts
│   │   ├── useDebounce.ts
│   │   ├── useDragDebounce.ts
│   │   ├── useErrorHandler.ts
│   │   ├── useTaskDrag.ts       # 任务拖拽逻辑
│   │   └── useWebSocketHeartbeat.ts
│   │
│   ├── plugins/                 # 插件
│   │   └── ...
│   │
│   ├── utils/                   # 工具函数
│   │   └── ...
│   │
│   ├── types/                   # TypeScript 类型定义
│   │   └── ...
│   │
│   ├── lib/                     # 第三方库封装
│   │   └── ...
│   │
│   ├── test/                    # 测试工具
│   │   └── ...
│   │
│   ├── App.vue                  # 根组件
│   └── main.js                  # 入口文件
│
├── package.json                 # NPM 依赖
├── vite.config.js              # Vite 配置
└── index.html                   # HTML 入口
```

**前端架构分析**：

1. **路由模块**: 采用 Vue Router 懒加载模式，所有页面组件按需加载
2. **状态管理**: 使用 Pinia，分为 `store/` (主状态) 和 `stores/` (模块状态)，存在冗余
3. **Composables**: 采用 Vue 3 Composition API，逻辑复用性高
4. **组件库**: 分为通用组件 (`components/`) 和页面组件 (`views/`)

---

### 2. 配置和基础设施层

```
EventPilot/
├── .env                         # 环境变量 (开发环境)
├── .env.example                 # 环境变量模板
├── .env_test                    # 测试环境变量
├── .gitignore                   # Git 忽略配置
├── conftest.py                  # Pytest 配置 (全局)
├── pytest.ini                   # Pytest 配置文件
├── requirements.txt             # Python 生产依赖
├── requirements-dev.txt         # Python 开发依赖
└── setup-dev.sh                 # 开发环境初始化脚本
```

---

### 3. 文档层 (`/docs`)

```
docs/
├── architecture/                # 架构文档
│   ├── ARCHITECTURE.md
│   └── 技术架构深度分析.md
│
├── audit/                       # 审计文档
│   └── VUE_AUDIT_REPORT.json
│
├── debug/                       # 调试文档
│   └── README.md
│
├── development/                 # 开发文档
│   ├── 2024-04--code-review-and-modularity-analysis.md
│   ├── 2024-04-19-DEVELOPMENT-frontend.md
│   ├── 2024-04-21-kanban-drag-implementation.md
│   ├── CHECKLIST ADVANCED FEATURES REPORT.md
│   ├── EventPilot_开发方案.md
│   ├── FUNCTIONALITY_AUDIT_DETAILED.md
│   ├── ISSUES_AND_GAPS.md
│   └── ...
│
├── guides/                      # 使用指南
├── logs/                        # 日志文档
│   └── BUGLOG_2025-04-23.md
│
├── optimization/                # 优化文档
│
├── quality/                     # 质量文档
│
├── reports/                     # 测试报告
│   ├── TASKS_TEST_FIX_REPORT_2026-05-01.md
│   └── ...
│
├── 2026-04-30-COMPLETION_CHECKLIST.md
├── 2026-04-30-COMPREHENSIVE-TEST-REPORT.md
├── 2026-04-30-EXECUTIVE_SUMMARY.md
├── 2026-04-30-FINAL-SUMMARY.md
├── Analysis_Completion_Summary.md
└── ...
```

**文档组织分析**：

1. **优点**:
   - 分类清晰：`architecture/`, `audit/`, `development/`, `reports/`
   - 测试报告集中在 `reports/` 目录
   - 历史开发信息在 `development/` 保留

2. **待改进**:
   - 大量日期前缀的文档 (如 `2026-04-30-*`) 应归档到 `archive/` 或 `history/`
   - 顶层散落了许多总结性文档，应归档

---

### 4. 测试层 (`/tests`)

```
tests/
├── e2e/                         # E2E 测试
├── fixtures/                    # 测试数据
├── integration/                 # 集成测试
├── unit/                        # 单元测试
├── invalid/                     # 无效测试 (待清理)
│   ├── test_dashboard_stats.py
│   ├── test_serializer_create.py
│   └── test_validate_method.py
├── test_checklists_crud.py
├── test_checklists_instance.py
├── test_events_stats.py
├── test_files_basic.py
├── test_files_upload_download.py
├── test_jwt_auth.py
├── test_jwt_auth2.py
├── test_profiles_api.py
├── test_profiles_api_debug.py
├── test_profiles_api_final.py
├── test_profiles_api_v2.py
├── test_reviews_complete_endpoint.py
└── test_sidebar_simple.py
```

**测试组织分析**：

1. **优点**:
   - 分类清晰：`e2e/`, `integration/`, `unit/`, `fixtures/`
   - 模块内嵌测试：`apps/*/tests/`

2. **待改进**:
   - `invalid/` 目录下有无用测试，应删除
   - 大量重复的测试文件 (`test_jwt_auth.py`, `test_jwt_auth2.py`) 应合并或删除

---

### 5. 脚本工具层 (`/scripts`)

```
scripts/
├── verification/                # 验证脚本 (新增)
│   ├── verify_bugfix.py
│   └── test_complete_fix.py
│
├── audit_vue_components.py
├── debug_appcheck.py
├── debug_checklist_urls.py
├── debug_nsp.py
├── debug_patterns.py
├── debug_routes.py
├── deploy_production.sh
├── dev_start.sh
├── init.sh
├── jiandaoyun-auto-review.ts
├── reset_password.py
├── test_api.py
├── test_api.sh
├── test_checklist_create.py
├── test_db_config.py
└── test_urls.py
```

**脚本组织分析**：

1. **优点**:
   - 脚本集中在 `/scripts` 目录

2. **待改进**:
   - 调试脚本 (`debug_*.py`) 应移到 `scripts/debug/`
   - 测试脚本 (`test_*.py`) 应移到 `tests/` 或 `scripts/tests/`
   - 应用程序脚本 (`.ts`, `.sh`) 可分类

---

### 6. 归档和报告层

```
archive/                        # 存档目录 (新增)
└── debug/                       # 调试脚本存档
    ├── debug_complete_api.py
    ├── test_communication_debug.py
    └── test_instance_debug.py

reports/                        # 报告目录 (新增)
├── COMPLETE_TEST_REGRESSION_2026-05-01.md
└── pytest-report.log
```

---

### 7. 其他目录

```
cache/                          # 缓存目录
logs/                           # 应用日志
├── debug/

storage/                        # 存储目录
├── exports/                    # 导出文件
└── temp/                       # 临时文件

tasks/                          # 任务目录 (非 Django 任务)
└── api/

public/                         # 公共静态资源
```

---

## 路径规划评估

### ✅ 优点

1. **Django 应用模块化**：每个 app 采用统一的 DDD 结构 (api/models/services/migrations/tests)
2. **前后端分离清晰**：`/frontend` 与后端代码分离
3. **配置分层**：`config/settings/` 支持 base/development/production
4. **文档分类**：`docs/` 下按类型分类文档
5. **测试集中**：`tests/` 和模块内 `tests/` 分离
6. **可组合函数**：`composables/` 封装前端逻辑复用

### ⚠️  待改进

1. **重复的虚拟环境**：
   ```
   venv/           # 旧虚拟环境
   new_venv/       # 新虚拟环境
   ```
   **建议**：保留一个，删除另一个

2. **前端状态管理冗余**：
   ```
   frontend/src/store/index.ts      # 主状态
   frontend/src/stores/profiles.ts  # 用户资料状态
   frontend/src/stores/websocket.ts  # WebSocket 状态
   ```
   **建议**：统一使用 `stores/`，删除 `store/index.ts`

3. **测试文件散落**：
   - `/tests/` 下有大量独立测试文件
   - `/apps/*/tests/` 下也有测试
   **建议**：统一将测试移到 `/tests/` 模块目录下

4. **临时脚本散在**：
   - `debug_*`, `test_*` 脚本在 `/scripts/` 根目录
   **建议**：分类到 `scripts/debug/`, `scripts/tests/`

5. **文档散落**：
   - `/docs/` 下有大量总结文档，日期前缀文件
   **建议**：归档到 `/docs/archive/` 或 `/archive/docs/`

6. **无用文件**：
   - `/tests/invalid/` 下有无用测试
   - 重复的 `test_jwt_auth.py`, `test_jwt_auth2.py`
   **建议**：删除

---

## 推荐的目录重构方案

### 方案 A: 最小调整 (推荐)

只做必要的清理，不破坏现有结构：

```
EventPilot/
├── archive/
│   ├── debug/                   # 已归档调试脚本 ✓
│   └── docs/                    # 归档旧文档 (新增)
│
├── docs/
│   ├── archive/                 # 归档历史文档 (新增)
│   │   ├── 2024-*/
│   │   └── 2026-04-30-*.md
│   ├── reports/                 # 测试报告保持
│   └── ...
│
├── scripts/
│   ├── debug/                   # 调试脚本 (新增)
│   │   ├── debug_*.py
│   │   └── ...
│   ├── tests/                   # 测试脚本 (新增)
│   │   └── test_*.py
│   └── verification/           # 验证脚本 (已有) ✓
│
├── tests/
│   ├── e2e/                     # ✓
│   ├── integration/             # ✓
│   ├── unit/                    # ✓
│   └── fixtures/                # ✓
│   (删除 invalid/ 及重复测试)   # ✗
│
├── frontend/src/
│   ├── stores/                  # 统一状态管理 (合并 store/)
│   │   ├── index.ts             # 从原 store/ 移过来
│   │   ├── profiles.ts
│   │   └── websocket.ts
│   └── (删除 store/index.ts)    # ✗
```

### 方案 B: 大规模重构 (不推荐)

将 Django 应用和环境配置移出项目根目录：

```
EventPilot/
├── backend/
│   ├── config/
│   ├── apps/
│   └── manage.py
├── frontend/
│   └── ...
```

**评价**：重构成本高，破坏现有 Git 历史，不建议

---

## 具体改进建议

### 1. 清理重复的虚拟环境

```bash
# 确定使用的虚拟环境 (检查哪个是活跃的)
ls -la venv/ new_venv/

# 删除不使用的
rm -rf new_venv/
# 或
rm -rf venv/
```

### 2. 统一前端状态管理

```bash
# 将 store/index.ts 移到 stores/ 目录
rm frontend/src/store/index.ts
# 或将 stores/ 的内容合并到 store/index.ts
```

### 3. 整理脚本

```bash
# 创建脚本子目录
mkdir -p scripts/debug scripts/tests

# 移动调试脚本
mv scripts/debug_*.py scripts/debug/

# 移动测试脚本
mv scripts/test_*.py scripts/tests/
```

### 4. 归档文档

```bash
# 创建文档归档目录
mkdir -p docs/archive

# 移动历史文档到归档
mv docs/2024-* docs/archive/
mv docs/2026-04-30-* docs/archive/
```

### 5. 删除无用测试

```bash
# 删除无效测试目录
rm -rf tests/invalid/

# 删除重复测试
rm tests/test_jwt_auth2.py
```

---

## 路径命名规范建议

### Django 应用模块

- `/apps/{module}/api/` - API 接口层
- `/apps/{module}/models/` - 数据模型
- `/apps/{module}/services/` - 业务逻辑
- `/apps/{module}/tests/` - 单元测试

### 前端源码

- `/frontend/src/components/{ComponentName}.vue` - 组件
- `/frontend/src/views/{ViewName}.vue` - 页面
- `/frontend/src/composables/use{Function}.ts` - 可组合函数
- `/frontend/src/stores/{storeName}.ts` - 状态存储

### 测试

- `/tests/unit/{module}_test.py` - 单元测试
- `/tests/integration/{module}_test.py` - 集成测试
- `/tests/e2e/{feature}_test.py` - E2E 测试

### 文档

- `/docs/{category}/{document}.md` - 分类文档
- `/docs/reports/{report}.md` - 报告
- `/docs/archive/{old-document}.md` - 归档文档

---

## 总结

EventPilot 项目的目录结构总体清晰，采用了统一的后端 DDD 架构和前端组件化设计。主要问题集中在临时文件管理、重复配置和测试散落上。

**推荐行动**：
1. 优先清理重复的虚拟环境
2. 整理脚本和测试文件
3. 统一前端状态管理
4. 归档历史文档

这些改进将提升项目的可维护性和开发效率。

---

**分析日期**: 2026-05-01  
**分析者**: Hermes Agent  
**报告版本**: 1.0
