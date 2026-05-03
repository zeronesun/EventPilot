## 角色
你是资深全栈测试工程师，同时也是系统架构师、UI/UX 设计师和真实用户。请对 EventPilot 项目进行全面深度测试。

## 项目真实信息（已确认，请严格遵循）

### 技术栈
- **前端**: Vue 3 + Vite 5 + TypeScript + Element Plus + Pinia + Vue Router（端口 5173）
- **后端**: Django 5.2 + Django REST Framework 3.15 + Django Channels 4.0（端口 8000）
- **数据库**: 开发环境 SQLite（`eventpilot_dev.db`），生产环境 PostgreSQL
- **缓存**: Redis（`127.0.0.1:6379/1`）
- **认证**: JWT（HS256），Access Token 15 分钟，Refresh Token 7 天
- **实时通信**: Django Channels + channels-redis（WebSocket）
- **文件存储**: 开发环境本地，生产环境 AWS S3（预签名 URL 架构）
- **API 文档**: drf-yasg（Swagger），可访问 `/api/docs/` 或 `/swagger/`

### 项目定位
**EventPilot 是企业内部的活动项目管理平台**（非售票/会议平台），用于管理活动项目的全生命周期：策划→执行→复盘。核心用户是项目经理、执行人员和观察者。

### 测试账号
| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| `admin` | `admin123` | 管理员 | 超级用户，可访问所有功能 |
| 密码重置脚本 | `scripts/utils/reset_password.py` | - | 可重置 admin 密码 |

### 前端页面路由（20 个页面）
| 路径 | 组件 | 功能 | 需认证 |
|------|------|------|--------|
| `/login` | Login.vue | 登录页 | 否 |
| `/dashboard` | Home.vue | 仪表盘首页 | 是 |
| `/events` | Events.vue | 活动列表 | 是 |
| `/events-kanban` | EventsKanban.vue | 活动看板 | 是 |
| `/events/:id` | EventDetail.vue | 活动详情 | 是 |
| `/events/:id/edit` | EventEdit.vue | 活动编辑 | 是 |
| `/tasks` | Tasks.vue | 任务管理 | 是 |
| `/users` | Users.vue | 用户管理 | 是 |
| `/checklists` | Checklists.vue | 核验清单 | 是 |
| `/files` | Files.vue | 文件管理 | 是 |
| `/profiles` | Profiles.vue | 关联方档案 | 是 |
| `/notifications` | Notifications.vue | 通知中心 | 是 |
| `/budget` | Budget.vue | 预算管理 | 是 |
| `/knowledge` | Knowledge.vue | 知识库 | 是 |
| `/reviews` | Reviews.vue | 复盘管理 | 是 |
| `/analytics` | Analytics.vue | 数据分析 | 是 |
| `/settings` | Settings.vue | 系统设置 | 是 |
| `/test` | TestPage.vue | 测试页 | 是 |
| `/404` | NotFound.vue | 404 页面 | 否 |

### 后端 API 端点（按模块）
| 模块 | 前缀 | 核心 ViewSet | 关键自定义 Action |
|------|------|-------------|------------------|
| 用户 | `/api/users/` | UserViewSet | `auth/login/`, `auth/refresh/`, `auth/verify/`, `me/`, `statistics/`, `roles/`, `bulk/update-status/`, `bulk/assign-roles/`, `bulk/delete/`, `import/` |
| 活动 | `/api/events/` | EventViewSet | `dashboard_analytics/`, `statistics/{id}/`, `complete/{id}/`, `apply_template/` |
| 任务 | `/api/tasks/` | TaskViewSet | `bulk_update_status/`, `kanban_data`, `complete/{id}/` |
| 清单 | `/api/checklists/` | 多个 ViewSet | `templates/`, `instances/`, `items/`, `advanced/versions/`, `advanced/exports/`, `advanced/imports/`, `advanced/verifications/`, `advanced/exceptions/` |
| 文件 | `/api/files/` | FileMetadataViewSet | `upload_part/`, `complete_upload/`, `download/`, `share/`, `batch_delete/`, `search/`, `stats/` |
| 档案 | `/api/profiles/` | ProfileViewSet | `recommendations/`, `search/`, `analytics/` |
| 知识库 | `/api/knowledge/` | KnowledgeEntryViewSet | - |
| 复盘 | `/api/reviews/` | ReviewViewSet | `complete/{id}/` |
| 通知 | `/api/notifications/` | NotificationViewSet | `unread_count/`, `mark_read/{id}/`, `bulk_mark_read/`, `statistics/` |
| 全局 | `/api/` | - | `health/`, `dashboard/stats/` |

### 数据模型关键字段
**Event**: status(draft/planning/executing/completed/reviewed/cancelled), type(conference/exhibition/performance/party/training/other), estimated_budget, actual_budget, owner, participants
**Task**: status(pending/ready/in_progress/completed/cancelled/blocked), task_type(planning/guest/material/venue/promotion/onsite/review), progress(0-100), assignee, event(FK)
**User**: role(admin/project_owner/executor/observer), is_active, is_deleted(软删除), department, position
**BudgetItem**: category, estimated_amount, actual_amount, event(FK)
**Review**: status(draft/in_progress/completed), 5个复盘维度(goal_achievement/process_execution/cost_control/customer_feedback/team_collaboration)
**KnowledgeEntry**: entry_type(issue/experience/best_practice), is_public, is_verified, tags
**Notification**: type(info/warning/error/success), read, source

### 用户角色权限体系
| 角色 | 权限范围 |
|------|---------|
| admin | 全部权限，可管理所有资源和用户 |
| project_owner | 可创建/管理自己的活动及关联任务、预算、清单 |
| executor | 可查看分配给自己的任务，更新任务状态和进度 |
| observer | 只读权限，可查看活动和任务详情 |

### 已知问题（修复中）
- JWT Token 过期后需自动刷新（已实现自动刷新机制）
- Vite HMR WebSocket 在远程访问时可能连接失败（已优化配置）
- 部分页面 API 路径已从 `/events/events/` 修正为 `/events/`

## 必须覆盖的测试点

### 1. 认证与权限（最高优先级）

#### 登录流程
- 操作：使用 `admin/admin123` 登录
- **前端校验**：登录成功后跳转 `/dashboard`，localStorage 存储 `eventpilot_token` 和 `eventpilot_user`
- **后端校验**：POST `/api/users/auth/login/` 返回 `{token, user, expires_in}`，Token 格式为 JWT HS256
- **异常校验**：错误密码返回 401，空字段返回 400，被锁定账户返回 403

#### Token 刷新
- 操作：等待 Access Token 过期（15分钟）后操作
- **前端校验**：401/403 响应自动触发 Token 刷新，用户无感知
- **后端校验**：POST `/api/users/auth/refresh/` 返回新 Token
- **异常校验**：Refresh Token 也过期时，跳转 `/login`

#### 路由守卫
- 未认证访问 `/dashboard` → 重定向 `/login`
- 已认证访问 `/login` → 重定向 `/dashboard`
- Token 无效时清除 localStorage 并跳转登录

### 2. 活动管理（核心业务）

#### 活动列表页 `/events`
- 列表加载：GET `/api/events/` 返回 `{count, results, ...}`，分页 20 条/页
- 状态筛选：按 status(draft/planning/executing/completed/cancelled) 过滤
- 搜索功能：按名称/类型搜索
- 新建活动：点击"新建"→ 打开 EventFormDialog(mode='create')
- **深度校验**：新建活动必填 name/type/start_date，end_date 自动计算，estimated_budget 默认 0

#### 活动详情页 `/events/:id`
- 详情展示：GET `/api/events/{id}/` 返回完整活动信息
- 状态流转：draft→planning→executing→completed→reviewed
- 编辑功能：点击编辑→打开 EventFormDialog(mode='edit')
- 删除功能：软删除，DELETE `/api/events/{id}/` 返回 204
- **深度校验**：编辑保存时 end_date 不能早于 start_date，budget 变更需记录日志

#### 活动看板 `/events-kanban`
- 看板视图：按状态分列展示活动卡片
- 拖拽操作：使用 vuedraggable 实现状态变更
- **深度校验**：拖拽后 PUT `/api/events/{id}/` 更新 status，前端自动刷新

#### 活动统计
- GET `/api/events/dashboard_analytics/` 返回：overview, status_distribution, type_distribution, monthly_trend, high_risk_events, upcoming_deadlines, top_owners, task_type_distribution
- GET `/api/events/{id}/statistics/` 返回单个活动的统计

### 3. 任务管理

#### 任务列表 `/tasks`
- 列表加载：GET `/api/tasks/`，支持按 event/status/assignee 过滤
- 新建任务：必填 title/event/task_type，assignee 可选
- 批量操作：POST `/api/tasks/bulk_update_status/`，请求体 `[{id, status}]`
- **深度校验**：任务状态机 pending→ready→in_progress→completed，blocked 状态需先解除阻塞

#### 任务看板
- GET `/api/tasks/kanban_data?event={id}` 返回看板数据
- 拖拽更新状态和进度

#### 任务依赖
- GET/POST `/api/tasks/dependencies/`
- **深度校验**：循环依赖检测，依赖任务未完成时当前任务不能标记 completed

### 4. 用户管理 `/users`

#### 用户列表
- GET `/api/users/` 返回 `{count, results}`
- 角色筛选：admin/project_owner/executor/observer
- 批量操作：批量分配角色、批量删除、批量更新状态

#### 用户 CRUD
- 创建用户：必填 username/password/email，密码需确认
- 查看详情：handleView → UserFormDialog(mode='view')
- 编辑用户：handleEdit → UserFormDialog(mode='edit')
- 删除用户：软删除（is_deleted=True），DELETE `/api/users/{id}/`
- **深度校验**：用户名唯一性校验，密码强度校验，邮箱格式校验

### 5. 预算管理 `/budget`

- 预算项列表：GET `/api/events/budget-items/?event={id}`
- 创建预算项：POST `/api/events/budget-items/`，含 category/estimated_amount/actual_amount
- 预算差异计算：estimated_amount - actual_amount
- **深度校验**：金额不能为负，实际金额超过预算时预警

### 6. 核验清单 `/checklists`

- 模板管理：CRUD `/api/checklists/templates/`
- 实例管理：CRUD `/api/checklists/instances/`
- 清单项状态：pending/in_progress/passed/failed/skipped
- 高级功能：版本管理、导出(csv/excel/pdf/json)、导入、核验、异常处理
- **深度校验**：模板创建实例时项的复制完整性，导出格式正确性

### 7. 文件管理 `/files`

- 文件列表：GET `/api/files/`
- 上传流程：POST 发起上传 → 获取预签名 URL → PUT 上传分片 → POST 完成上传
- 下载流程：POST `/api/files/{id}/download/` 获取下载 URL
- 文件分享：POST `/api/files/{id}/share/`
- **深度校验**：大文件分片上传，文件类型限制，存储配额检查

### 8. 关联方档案 `/profiles`

- 档案列表：GET `/api/profiles/`
- 档案类型：speaker/venue/supplier/contact
- 搜索推荐：GET `/api/profiles/search/`, GET `/api/profiles/recommendations/`
- 数据分析：GET `/api/profiles/analytics/`

### 9. 知识库 `/knowledge`

- 知识条目：CRUD `/api/knowledge/`
- 条目类型：issue(问题)/experience(经验)/best_practice(最佳实践)
- 标签系统、公开/私有控制、验证标记

### 10. 复盘管理 `/reviews`

- 复盘列表：CRUD `/api/reviews/`
- 复盘状态：draft→in_progress→completed
- 五维度评分：goal_achievement/process_execution/cost_control/customer_feedback/team_collaboration
- 完成复盘：POST `/api/reviews/{id}/complete/`

### 11. 通知系统 `/notifications`

- 通知列表：GET `/api/notifications/`
- 未读计数：GET `/api/notifications/unread_count/`（30秒轮询）
- 标记已读：POST `/api/notifications/{id}/mark_read/`
- 批量已读：POST `/api/notifications/bulk_mark_read/`
- 通知统计：GET `/api/notifications/statistics/`

### 12. 数据分析 `/analytics`

- 仪表盘数据：GET `/api/events/dashboard_analytics/`
- 日期范围筛选：start_date_from/start_date_to 参数
- 数据展示：概览卡片、状态/类型分布、月度趋势、高风险预警、到期提醒、TOP负责人、任务类型分布

## 多角色专项测试

### 开发者视角
- 前端控制台无未捕获异常，无未处理的 Promise rejection
- 后端 API 返回字段与 DRF Serializer 定义一致（类型、必填、默认值）
- JWT Token 过期后自动刷新，不会导致用户操作中断
- API 错误响应格式统一：`{error: {code, message}}` 或 `{detail: "..."}`
- 前端 API Client 的 `response.data` 处理逻辑：DRF 直接返回数据（不包裹在 data 字段）

### 架构师视角
- 并发操作：两个用户同时编辑同一活动，检查乐观锁/悲观锁处理
- 后端日志：错误时记录堆栈，INFO 级别包含请求 ID（中间件 `api/middleware.py`）
- API 契约：检查 Swagger 文档 `/api/docs/` 是否与实际 API 一致
- 数据库事务：活动状态变更时关联任务/预算的级联更新是否在事务中
- 软删除：用户/活动删除后 is_deleted=True，查询默认过滤已删除记录

### UI/UX 设计师视角
- Element Plus 组件一致性：所有表单对话框使用统一的 FormDialog 模式
- 加载反馈：列表页有 v-loading，长列表有骨架屏
- 错误提示：后端返回 400/422 时，前端用 ElMessage.error 显示具体错误
- 空状态：无数据时显示 el-empty 组件
- 表单验证：必填字段标红星，提交前前端校验+后端校验双重保障
- 移动端适配：导航菜单折叠、表格横向滚动

### 用户视角
- 新人首次访问：能否在 3 分钟内创建一个活动并添加任务？
- 数据不丢失：表单填写过程中切换标签页，数据是否保留（对话框未关闭）
- 状态可追溯：活动状态变更历史是否可查（EventActivityLog）
- 批量操作效率：能否快速批量更新任务状态？

## 输出要求

### 1. 测试计划表格
按模块罗列测试项、预期结果、所属视角、优先级（P0-P3）。

### 2. 可执行测试代码
- **框架**：Playwright + Python（项目已有 `pytest-playwright` 依赖）
- **测试目录**：保存到 `tests/e2e/`
- **配置文件**：提供 `conftest.py`，包含：
  - 测试数据库连接（SQLite `eventpilot_dev.db`）
  - 测试账号 fixture（admin/admin123）
  - 页面基础 URL（`http://localhost:5173`）
  - API 基础 URL（`http://localhost:8000/api`）
  - 登录 fixture（自动完成 JWT 登录）
  - 截图 fixture（失败时自动截图）
- **前后端联动**：使用 `page.wait_for_response` 拦截 API 响应并断言
- **数据库校验**：通过 Django ORM 直接查询验证数据一致性
- **测试数据管理**：每个测试用例独立，测试后清理

### 3. 缺陷报告
如果发现任何失败，按视角分类：
- **[开发者]** / **[架构师]** / **[UI/UX]** / **[用户]**
- 包含：复现步骤、实际结果、预期结果、根因分析、修复建议（diff 格式）

### 4. 修复代码示例
提供前端组件修改和后端视图/序列化器修改的具体代码。

## 启动测试的方法

```bash
# 1. 确保前后端运行中
./start.sh status

# 2. 安装测试依赖（如未安装）
pip install pytest-playwright pytest-django factory-boy Faker
playwright install chromium

# 3. 运行 E2E 测试
pytest tests/e2e/ --headed -v

# 4. 运行特定模块测试
pytest tests/e2e/test_events.py -v
pytest tests/e2e/test_tasks.py -v

# 5. 将错误截图或日志贴回对话，继续修复
```

## 注意事项
- 本项目使用 **JWT 认证**（非 Session/CSRF），API 请求通过 `Authorization: Bearer <token>` 认证
- 前端 API Client 使用原生 **fetch**（非 axios），响应数据不包裹在 `data` 字段
- 后端使用 **DRF ViewSet + Router**，URL 格式为 `/api/{resource}/` 和 `/api/{resource}/{id}/`
- 用户删除为**软删除**（is_deleted=True），不是物理删除
- 活动状态有**严格的状态机**，不能随意跳转（如 draft 不能直接变 completed）
- 文件上传使用 **S3 预签名 URL** 架构，开发环境可能需要 mock S3
- WebSocket 端点在 `/ws/` 前缀下，需要 JWT 认证
