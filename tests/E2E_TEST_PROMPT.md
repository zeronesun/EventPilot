# EventPilot 全栈全流程自动化测试提示词

> 本提示词用于指导 AI 完成对 EventPilot 项目的前后端全面测试，覆盖每一个页面、子页面、每一个按钮，并验证操作结果，发现问题后自动修复。

---

## 一、角色定义

你是资深全栈测试工程师，同时具备以下能力：
- **系统架构师**：验证系统设计、并发处理、数据一致性
- **UI/UX 设计师**：验证界面交互、响应式设计、用户体验
- **后端开发者**：验证 API 契约、数据库操作、业务逻辑
- **前端开发者**：验证组件行为、状态管理、错误处理
- **真实用户**：模拟真实使用场景，验证业务流程

### 核心能力要求

1. **主动调用工具**：不要等待用户指示，主动使用可用的工具完成测试
2. **主动定位问题**：发现缺陷时，主动搜索代码、查看日志、查询数据库定位根因
3. **主动修复问题**：在权限范围内，主动生成修复代码并验证
4. **主动补充工具**：如果当前工具无法满足需求，主动建议新的工具或方法

---

## 二、项目技术栈（已确认）

| 层级 | 技术 | 端口/路径 |
|------|------|-----------|
| 前端框架 | Vue 3 + Vite + Element Plus + Pinia | http://localhost:5173 |
| 后端框架 | Django 5.2 + Django REST Framework | http://localhost:8000 |
| 认证方式 | JWT (localStorage: eventpilot_token) | /api/users/auth/login/ |
| 数据库 | PostgreSQL | eventpilot / eventpilot_test |
| WebSocket | Django Channels + Redis | ws://localhost:8000/ws/ |
| API文档 | drf-yasg Swagger | /swagger/ |
| 测试框架 | pytest + pytest-django + Playwright | tests/e2e/ |

---

## 二-1、可用技能（Skills）

AI Agent 可以调用以下技能来增强测试能力：

### 核心测试技能

| 技能名称 | 功能描述 | 使用场景 |
|----------|----------|----------|
| `skill-creator` | 创建自定义技能 | 当需要扩展测试能力时，创建新的技能 |
| `playwright` | Playwright E2E 测试 | 浏览器自动化测试，页面交互验证 |
| `pytest` | Python 单元/集成测试 | 后端 API 测试，数据库验证 |

### 可调用的 Agent 类型

| Agent 类型 | 功能描述 | 使用场景 |
|------------|----------|----------|
| `search` | 代码搜索代理 | 查找前后端代码定位问题 |
| `code-reviewer` | 代码审查代理 | 审查发现的缺陷代码 |
| `debugger` | 调试代理 | 深入分析复杂问题 |

---

## 二-2、可用工具（Tools）

AI Agent 可以使用以下工具执行测试：

### 浏览器与 UI 测试工具

| 工具 | 功能描述 | 使用方法 |
|------|----------|----------|
| `browser` | 浏览器控制 | Playwright page 对象，执行点击、填写、截图 |
| `playwright` | Playwright API | `page.click()`, `page.fill()`, `page.wait_for_selector()` |
| `screenshot` | 页面截图 | 捕获测试失败时的页面状态 |
| `video` | 视频录制 | 录制测试过程便于回放分析 |

### 后端与 API 测试工具

| 工具 | 功能描述 | 使用方法 |
|------|----------|----------|
| `curl` / `httpx` | HTTP 请求 | 直接调用 API 验证后端逻辑 |
| `django ORM` | 数据库操作 | 直接查询/修改数据库验证数据 |
| `pytest-django` | Django 测试框架 | 运行后端单元测试 |
| `sql` | SQL 执行 | 直接执行 SQL 验证数据库状态 |

### 代码分析与修复工具

| 工具 | 功能描述 | 使用方法 |
|------|----------|----------|
| `Read` | 读取文件 | 查看前后端源代码定位问题 |
| `Write` / `Edit` | 写入/编辑文件 | 生成修复代码 |
| `Grep` | 代码搜索 | 查找函数调用、变量定义 |
| `Glob` | 文件查找 | 查找特定类型的文件 |
| `RunCommand` | 执行命令 | 运行测试、迁移、检查代码 |

### 日志与诊断工具

| 工具 | 功能描述 | 使用方法 |
|------|----------|----------|
| `logs` | 日志查看 | 查看 backend.log、frontend.log |
| `diagnostics` | 语言诊断 | 检查 TypeScript/JavaScript 错误 |
| `terminal` | 终端 | 执行 shell 命令 |

---

## 二-3、推荐的测试工作流工具组合

### 工作流 1：完整端到端测试
```
browser (Playwright) + RunCommand (pytest) + Read/Write (修复代码)
```
- 使用 Playwright 执行前端操作
- 使用 pytest-django 验证后端 API
- 直接修改代码修复问题

### 工作流 2：快速验证
```
browser (Playwright) + Grep/Read (定位) + RunCommand (测试)
```
- Playwright 快速执行操作
- Grep 定位相关代码
- RunCommand 运行特定测试

### 工作流 3：深度调试
```
browser + Read (查看代码) + sql (查询DB) + logs (查看日志)
```
- Playwright 复现问题
- 查看源代码
- 直接查询数据库
- 查看后端日志

### 工作流 4：并发与性能测试
```
RunCommand (pytest + pytest-xdist) + browser (录制) + diagnostics
```
- pytest-xdist 并发执行
- Playwright 性能录制
- 分析诊断信息

---

## 二-4、Agent 自行补充的工具建议

如果当前可用工具无法满足特定测试需求，Agent 可以建议并使用：

| 工具类型 | 推荐工具 | 使用场景 |
|----------|----------|----------|
| API 模拟 | `unittest.mock`, `responses` | Mock 外部 API 调用 |
| 负载测试 | `locust`, `k6` | 并发用户测试 |
| 视觉回归 | `playwright visual`, `backstop` | UI 视觉对比 |
| 数据库迁移 | `django migrations` | 测试数据准备 |
| 容器化测试 | `docker-compose` | 隔离测试环境 |
| CI/CD 集成 | `github actions`, `jenkins` | 自动化测试流程 |

---

## 三、测试覆盖范围

### 3.1 页面清单（必须全部测试）

| 序号 | 路由 | 页面名称 | 子功能/标签页 | 优先级 |
|------|------|----------|---------------|--------|
| 1 | /login | 登录页 | - | P0 |
| 2 | /dashboard | 首页/仪表盘 | 统计卡片、最近活动、待处理任务 | P0 |
| 3 | /events | 活动列表 | 搜索、筛选、批量操作、导出 | P0 |
| 4 | /events-kanban | 活动看板 | 拖拽、状态列 | P1 |
| 5 | /events/:id | 活动详情 | 基本信息、任务列表、预算明细、参与者 | P0 |
| 6 | /events/:id/edit | 活动编辑 | 表单、状态变更 | P0 |
| 7 | /tasks | 任务列表 | 搜索、筛选、批量操作 | P0 |
| 8 | /users | 用户管理 | 搜索、角色筛选、批量操作 | P1 |
| 9 | /checklists | 清单管理 | 清单实例、模板管理（标签切换） | P1 |
| 10 | /files | 文件管理 | 上传、下载、删除、预览 | P1 |
| 11 | /profiles | 关联方档案 | 搜索、分类筛选 | P1 |
| 12 | /notifications | 通知中心 | 已读/未读、WebSocket实时推送 | P2 |
| 13 | /budget | 预算管理 | 预算明细、统计图表 | P1 |
| 14 | /knowledge | 知识库 | 文档列表、搜索、分类 | P2 |
| 15 | /reviews | 复盘管理 | 复盘列表、创建复盘 | P2 |
| 16 | /analytics | 分析报表 | 图表、数据导出 | P2 |
| 17 | /settings | 系统设置 | 个人设置、系统配置 | P2 |
| 18 | /404 | 404页面 | - | P2 |

### 3.2 每个页面的按钮清单与测试要求

#### 3.2.1 登录页 (/login)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 登录按钮 | 点击提交表单 | 1. loading状态显示<br>2. 按钮禁用<br>3. 跳转到/dashboard | 1. POST /api/users/auth/login/<br>2. 返回200 + access/refresh token<br>3. 返回用户信息 | - |
| 登录按钮（空表单） | 不填内容点击 | 1. 表单验证错误显示<br>2. "请输入用户名"提示 | 无请求 | - |
| 登录按钮（错误密码） | 填写错误密码 | 1. 错误提示显示<br>2. ElMessage.error显示<br>3. 停留在登录页 | 1. 返回401<br>2. 错误消息："用户名或密码错误" | - |
| 密码显示/隐藏 | 点击眼睛图标 | 密码明文/密文切换 | - | - |
| Enter键提交 | 在密码框按Enter | 触发登录按钮点击 | 同登录按钮 | - |

#### 3.2.2 首页/仪表盘 (/dashboard)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 查看全部活动 | 点击 | 跳转到/events | - | - |
| 活动卡片点击 | 点击活动项 | 跳转到/events/:id | - | - |
| 统计卡片 | 加载时 | 1. 显示数字<br>2. 图标正确 | GET /api/dashboard/stats/<br>返回eventCount, executingEventCount等 | 查询events表count |
| 待处理任务列表 | 加载时 | 显示任务列表 | GET /api/tasks/?status=todo | 查询tasks表 |

#### 3.2.3 活动列表页 (/events)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 新建活动 | 点击 | 1. 弹出CreateEventDialog<br>2. 表单字段显示 | - | - |
| 新建活动-确定 | 填写表单后点击 | 1. 表单验证通过<br>2. loading状态<br>3. 弹窗关闭<br>4. 列表刷新<br>5. ElMessage.success | POST /api/events/<br>返回201 + 完整活动对象 | events表新增记录 |
| 新建活动-取消 | 点击取消 | 1. 弹窗关闭<br>2. 表单重置 | - | - |
| 导出 | 选中活动后点击 | 1. 下载CSV/Excel文件<br>2. 文件名正确 | GET /api/events/export/ | - |
| 批量编辑 | 选中多个活动后点击 | 1. 弹出批量编辑弹窗<br>2. 显示选中数量 | - | - |
| 批量删除 | 选中后点击 | 1. 确认对话框<br>2. 删除后列表刷新 | DELETE /api/events/bulk/ | events表记录删除 |
| 搜索框 | 输入关键词 | 1. 防抖处理<br>2. 结果实时更新 | GET /api/events/?search=xxx | - |
| 状态筛选 | 选择状态 | 列表按状态过滤 | GET /api/events/?status=xxx | - |
| 分页-下一页 | 点击 | 1. 加载下一页数据<br>2. 页码更新 | GET /api/events/?page=2 | - |
| 活动行-查看 | 点击查看按钮 | 跳转到/events/:id | - | - |
| 活动行-编辑 | 点击编辑按钮 | 跳转到/events/:id/edit | - | - |
| 活动行-删除 | 点击删除按钮 | 1. 确认对话框<br>2. 删除后行消失 | DELETE /api/events/:id/ | events表记录删除 |
| 刷新按钮 | 点击 | 1. loading状态<br>2. 数据重新加载 | GET /api/events/ | - |

#### 3.2.4 活动详情页 (/events/:id)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 页面加载 | 进入页面 | 1. 显示活动信息<br>2. 显示任务列表<br>3. 显示预算明细 | GET /api/events/:id/<br>返回嵌套数据 | 查询events表 |
| 编辑活动 | 点击 | 跳转到/events/:id/edit | - | - |
| 更改状态 | 选择新状态 | 1. 确认对话框<br>2. 状态标签更新<br>3. ElMessage.success | PATCH /api/events/:id/<br>返回200 | events.status更新 |
| 删除活动 | 点击 | 1. 确认对话框<br>2. 跳转到列表页 | DELETE /api/events/:id/ | events表记录删除 |
| 添加任务 | 点击 | 1. 弹出任务表单<br>2. 关联当前活动 | - | - |
| 添加预算项 | 点击 | 1. 弹出预算表单<br>2. 关联当前活动 | - | - |
| 添加参与者 | 点击 | 1. 弹出参与者选择<br>2. 显示角色选择 | POST /api/events/:id/participants/ | event_participants表新增 |
| 任务完成 | 点击任务完成按钮 | 1. 任务状态变更<br>2. 进度条更新 | PATCH /api/tasks/:id/ | tasks.status = completed |

#### 3.2.5 活动编辑页 (/events/:id/edit)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 保存更改 | 点击 | 1. 表单验证<br>2. loading状态<br>3. ElMessage.success<br>4. 跳转到详情页 | PATCH /api/events/:id/ | events表记录更新 |
| 取消编辑 | 点击 | 1. 确认对话框（如有修改）<br>2. 跳转回详情页 | - | - |
| 删除活动 | 点击 | 1. 确认对话框<br>2. 跳转到列表 | DELETE /api/events/:id/ | events表记录删除 |

#### 3.2.6 任务列表页 (/tasks)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 新建任务 | 点击 | 弹出TaskFormDialog | - | - |
| 新建任务-确定 | 填写后点击 | 1. 表单验证<br>2. 弹窗关闭<br>3. 列表刷新 | POST /api/tasks/ | tasks表新增记录 |
| 批量分配 | 选中任务后点击 | 弹出用户选择框 | POST /api/tasks/bulk/assign/ | tasks.assignee更新 |
| 批量状态更新 | 选中后点击 | 状态选择框 | POST /api/tasks/bulk/status/ | tasks.status更新 |
| 任务行-编辑 | 点击 | 弹出编辑表单 | GET /api/tasks/:id/ | - |
| 任务行-删除 | 点击 | 确认后删除 | DELETE /api/tasks/:id/ | tasks表记录删除 |
| 优先级筛选 | 选择优先级 | 列表过滤 | GET /api/tasks/?priority=xxx | - |
| 负责人筛选 | 选择负责人 | 列表过滤 | GET /api/tasks/?assignee=xxx | - |

#### 3.2.7 用户管理页 (/users)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 新增用户 | 点击 | 弹出UserFormDialog | - | - |
| 新增用户-确定 | 填写后点击 | 1. 表单验证<br>2. 弹窗关闭<br>3. 列表刷新 | POST /api/users/ | users表新增记录 |
| 搜索用户 | 输入用户名 | 列表实时过滤 | GET /api/users/?username=xxx | - |
| 角色筛选 | 选择角色 | 列表过滤 | GET /api/users/?role=xxx | - |
| 用户行-编辑 | 点击 | 弹出编辑表单 | GET /api/users/:id/ | - |
| 用户行-删除 | 点击 | 确认后删除 | DELETE /api/users/:id/ | users表记录删除（软删除） |
| 批量分配角色 | 选中后点击 | 角色选择框 | POST /api/users/bulk/assign-roles/ | users.role更新 |
| 批量禁用 | 选中后点击 | 确认后禁用 | POST /api/users/bulk/update-status/ | users.is_active=False |
| 重置密码 | 点击 | 弹出密码输入框 | POST /api/users/:id/reset-password/ | users.password更新 |

#### 3.2.8 清单管理页 (/checklists)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 清单实例/模板切换 | 点击标签 | 内容区域切换 | - | - |
| 新建清单实例 | 点击 | 弹出创建表单 | - | - |
| 新建模板 | 点击 | 弹出模板表单 | POST /api/checklists/templates/ | checklist_templates表新增 |
| 模板-编辑 | 点击 | 弹出编辑表单 | PATCH /api/checklists/templates/:id/ | 模板记录更新 |
| 模板-删除 | 点击 | 确认后删除 | DELETE /api/checklists/templates/:id/ | 模板记录删除 |
| 实例-开始执行 | 点击 | 状态变为执行中 | POST /api/checklists/instances/:id/start/ | instance.status=executing |
| 实例-完成检查项 | 勾选 | 1. 进度更新<br>2. 完成时间记录 | PATCH /api/checklists/instances/:id/items/:itemId/ | item.completed=True |
| 实例-导出 | 点击 | 下载PDF/Excel | GET /api/checklists/instances/:id/export/ | - |

#### 3.2.9 文件管理页 (/files)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 上传文件 | 点击或拖拽 | 1. 进度条显示<br>2. 上传成功提示 | POST /api/files/ (multipart) | files表新增记录 |
| 下载文件 | 点击下载 | 文件开始下载 | GET /api/files/:id/download/ | - |
| 预览文件 | 点击预览 | 弹出预览窗口 | GET /api/files/:id/preview/ | - |
| 删除文件 | 点击删除 | 确认后删除 | DELETE /api/files/:id/ | files表记录删除 |
| 文件搜索 | 输入文件名 | 列表过滤 | GET /api/files/?search=xxx | - |

#### 3.2.10 通知中心 (/notifications)

| 按钮/交互 | 操作 | 前端验证 | 后端验证 | 数据库验证 |
|-----------|------|----------|----------|------------|
| 页面加载 | 进入页面 | 显示通知列表 | GET /api/notifications/ | - |
| 标记已读 | 点击 | 状态变更、未读数减少 | POST /api/notifications/:id/read/ | notification.is_read=True |
| 全部已读 | 点击 | 所有通知变为已读 | POST /api/notifications/read-all/ | 批量更新 |
| 删除通知 | 点击 | 通知从列表移除 | DELETE /api/notifications/:id/ | 记录删除 |
| WebSocket连接 | 页面加载 | 建立WS连接 | ws://localhost:8000/ws/notifications/ | - |
| 实时通知接收 | 收到消息 | 1. 新通知出现<br>2. 提示音/闪烁 | - | notifications表新增 |

---

## 四、测试执行规范

### 4.1 每个按钮测试的完整流程

```
1. 【前置条件】
   - 确认用户登录状态
   - 确认所需测试数据已准备
   - 确认页面已加载完成

2. 【操作执行】
   - 定位按钮元素
   - 执行点击/输入操作
   - 等待响应完成

3. 【前端验证】
   - 检查UI状态变化（loading、禁用、显示/隐藏）
   - 检查消息提示（ElMessage、ElNotification）
   - 检查路由跳转
   - 检查控制台无错误

4. 【后端验证】
   - 检查HTTP请求发出（URL、Method、Body）
   - 检查响应状态码（200/201/400/401/404等）
   - 检查响应数据结构

5. 【数据库验证】
   - 直接查询数据库验证数据变化
   - 验证关联数据一致性
   - 验证软删除/硬删除

6. 【异常测试】
   - 网络错误模拟
   - 权限不足测试
   - 并发操作测试
   - 边界值测试

7. 【清理工作】
   - 删除测试数据
   - 恢复初始状态
```

### 4.2 测试数据准备

```python
# 必须创建的测试数据
TEST_USERS = {
    'admin': {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
    'owner': {'username': 'owner', 'password': 'owner123', 'role': 'project_owner'},
    'executor': {'username': 'executor', 'password': 'executor123', 'role': 'executor'},
}

TEST_EVENTS = [
    {'name': '测试活动-策划中', 'status': 'planning'},
    {'name': '测试活动-执行中', 'status': 'executing'},
    {'name': '测试活动-已完成', 'status': 'completed'},
]

TEST_TASKS = [
    {'title': '测试任务-待办', 'status': 'todo', 'priority': 'high'},
    {'title': '测试任务-进行中', 'status': 'in_progress', 'priority': 'medium'},
    {'title': '测试任务-已完成', 'status': 'done', 'priority': 'low'},
]
```

### 4.3 断言标准

```python
# 前端断言
assert button.is_visible()
assert button.is_enabled()
assert loading_spinner.is_visible()
assert success_message.text == '操作成功'
assert page.url == '/events'

# 后端断言
assert response.status_code == 201
assert 'id' in response.json()
assert response.json()['status'] == 'planning'

# 数据库断言
event = Event.objects.get(id=event_id)
assert event.name == '测试活动'
assert event.status == 'planning'
assert event.owner == current_user
```

---

## 五、缺陷修复流程

### 5.1 发现缺陷后的处理

```
1. 【记录缺陷】
   - 截图/录屏
   - 控制台错误日志
   - 网络请求/响应
   - 复现步骤

2. 【定位根因】
   - 前端代码问题 → 定位到具体组件/方法
   - 后端代码问题 → 定位到具体视图/序列化器
   - 数据库问题 → 定位到具体模型/迁移

3. 【生成修复代码】
   - 使用 diff 格式展示修改
   - 包含修改原因说明
   - 包含测试验证代码

4. 【验证修复】
   - 重新运行失败的测试
   - 运行回归测试
   - 检查是否引入新问题
```

### 5.2 缺陷报告模板

```markdown
## 缺陷报告

### 基本信息
- **视角**: [开发者/架构师/UI设计师/用户]
- **严重程度**: [P0-阻塞/P1-严重/P2-一般/P3-轻微]
- **模块**: [认证/活动/任务/用户/...]

### 复现步骤
1. 打开页面 /events
2. 点击"新建活动"按钮
3. 填写表单...
4. 点击"确定"按钮

### 预期结果
活动创建成功，列表刷新显示新活动

### 实际结果
报错 500，控制台显示 "TypeError: Cannot read property 'id' of undefined"

### 根因分析
后端返回数据结构中缺少 id 字段，前端未做空值判断

### 修复代码

**后端修复 (apps/events/api/views.py):**
```diff
 def create(self, request, *args, **kwargs):
     serializer = self.get_serializer(data=request.data)
     serializer.is_valid(raise_exception=True)
-    self.perform_create(serializer)
+    instance = self.perform_create(serializer)
+    return Response({
+        'id': str(instance.id),
+        **serializer.data
+    }, status=status.HTTP_201_CREATED)
```

**前端修复 (frontend/src/views/Events.vue):**
```diff
 const handleCreateSuccess = (response) => {
-    const eventId = response.data.id
+    const eventId = response.data?.id || response.id
     if (eventId) {
         router.push(`/events/${eventId}`)
     }
 }
```

### 验证测试
```python
def test_create_event_returns_id(api_client):
    response = api_client.post('/api/events/', {...})
    assert response.status_code == 201
    assert 'id' in response.json()
```
```

---

## 六、输出要求

### 6.1 必须输出的内容

1. **测试计划表格**
   - 按页面分组
   - 包含每个按钮的测试项
   - 标注优先级和状态

2. **可执行测试代码**
   - pytest + Playwright 格式
   - 包含完整的 fixtures
   - 包含前后端联动断言
   - 包含数据库验证

3. **测试执行报告**
   - 通过/失败数量
   - 失败用例详情
   - 覆盖率统计

4. **缺陷修复代码**
   - diff 格式
   - 包含注释说明
   - 包含验证测试

### 6.2 代码规范

```python
# 测试函数命名
def test_<页面>_<按钮>_<场景>():
    """
    [视角] 测试描述
    
    前置条件: ...
    操作步骤: ...
    预期结果: ...
    """
    pass

# 示例
def test_events_create_button_success(authenticated_page, db):
    """
    [前后端联动] 测试活动列表页新建活动按钮-成功创建
    
    前置条件: 用户已登录，活动列表页已加载
    操作步骤: 
        1. 点击"新建活动"按钮
        2. 填写表单
        3. 点击"确定"按钮
    预期结果:
        - 前端: 弹窗关闭，列表刷新，成功提示
        - 后端: POST /api/events/ 返回 201
        - 数据库: events 表新增记录
    """
    pass
```

---

## 七、启动测试

### 7.1 环境准备

```bash
# 1. 确保服务运行
./start.sh status

重启的时候，建议使用
先
./start.sh stop

再
./start.sh start

# 2. 检查服务健康状态
curl http://localhost:8000/api/health/
curl http://localhost:5173/

# 3. 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 4. 创建测试数据
python tests/fixtures/create_test_data.py

# 5. 安装/更新依赖
cd frontend && npm install
pip install -r requirements.txt
```

### 7.2 测试执行命令

```bash
# ===== Playwright E2E 测试 =====
# 安装浏览器
cd frontend && npx playwright install chromium

# 运行所有 E2E 测试（headed 模式可见浏览器）
pytest tests/e2e/ -v --headed

# 运行所有 E2E 测试（headless 模式）
pytest tests/e2e/ -v

# 运行特定页面测试
pytest tests/e2e/test_events.py -v --headed
pytest tests/e2e/test_auth.py -v --headed

# 运行特定按钮测试
pytest tests/e2e/test_events.py -v -k "create"
pytest tests/e2e/test_events.py -v -k "delete"

# 生成 HTML 报告
pytest tests/e2e/ --html=tests/e2e/report.html --self-contained-html

# 截图失败用例
pytest tests/e2e/ --screenshot=on

# ===== pytest-django API 测试 =====
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定模块测试
pytest tests/integration/test_events_crud.py -v

# 运行单元测试
pytest tests/unit/ -v

# 数据库直接验证
pytest tests/check/ -v

# ===== 代码质量检查 =====
# 前端 lint
cd frontend && npm run lint

# 后端 lint
ruff check apps/

# 类型检查
cd frontend && npx tsc --noEmit

# ===== 性能测试 =====
# API 响应时间
pytest tests/e2e/test_performance.py -v

# 页面加载时间
pytest tests/e2e/test_performance.py -v -k "load_time"
```

### 7.3 调试与问题定位

```bash
# 查看后端错误日志
tail -100 logs/backend.log | grep ERROR

# 查看前端控制台（开发者工具）
# 访问 http://localhost:5173 并打开 F12

# Django shell 查询数据库
python manage.py shell -c "
from apps.events.models import Event
print(Event.objects.count())
"

# 直接执行 SQL
python manage.py dbshell
# SELECT * FROM events LIMIT 5;

# 重启服务
./start.sh restart

# 清除缓存
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
"
```

### 7.4 使用 Skill 调用

```bash
# 当需要创建新的测试技能时
/skill skill-creator

# 当需要代码审查时
/skill code-reviewer

# 当需要搜索代码时
/skill search
```

---

## 八、注意事项

1. **每个测试必须独立**：不依赖其他测试的执行顺序
2. **测试数据必须清理**：使用 pytest fixtures 自动清理
3. **异步操作必须等待**：使用 page.wait_for_* 方法
4. **断言必须完整**：前端 + 后端 + 数据库 三重验证
5. **发现问题必须修复**：生成修复代码并验证

---

**请按照以上要求，对 EventPilot 项目进行全面测试，发现问题后立即修复，确保每个页面、每个按钮都能正常工作。**
