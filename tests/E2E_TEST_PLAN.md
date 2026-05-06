# EventPilot E2E Testing Plan

**生成时间:** 2026-05-06
**参考:** tests/E2E_TEST_PROMPT.md

---

## 测试执行概览

| 模块 | 页面数 | 按钮/交互数 | 计划测试 | 已完成 | 待完成 | 优先级 |
|------|--------|------------|----------|--------|--------|--------|
| 认证 | 1 | 5 | 5 | 5 | 0 | P0 |
| 首页 | 1 | 4 | 4 | 1 | 3 | P0 |
| 活动管理 | 3 | 13 | 13 | 2 | 11 | P0 |
| 任务管理 | 1 | 8 | 8 | 0 | 8 | P0 |
| 用户管理 | 1 | 7 | 7 | 0 | 7 | P1 |
| 清单管理 | 1 | 8 | 8 | 0 | 8 | P1 |
| 文件管理 | 1 | 5 | 5 | 0 | 5 | P1 |
| 档案管理 | 1 | 5 | 5 | 0 | 5 | P1 |
| 通知中心 | 1 | 6 | 6 | 0 | 6 | P2 |
| 预算管理 | 1 | 4 | 4 | 0 | 4 | P1 |
| 知识库 | 1 | 3 | 3 | 0 | 3 | P2 |
| 复盘管理 | 1 | 4 | 4 | 0 | 4 | P2 |
| 分析报表 | 1 | 3 | 3 | 0 | 3 | P2 |
| 系统设置 | 1 | 3 | 3 | 0 | 3 | P2 |
| 404页面 | 1 | 1 | 1 | 0 | 1 | P2 |
| **总计** | **18** | **79** | **79** | **8** | **71** | - |

---

## 详细测试计划

### 📁 1. 认证模块 (/login) - P0

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| AUTH-001 | 登录按钮 | 正常登录 | ✅ 完成 | test_auth_v2.py::test_login_success | ~5s |
| AUTH-002 | 登录按钮（空表单）| 表单验证 | ✅ 完成 | test_auth_v2.py::test_login_failure_empty | ~3s |
| AUTH-003 | 登录按钮（错误密码）| 错误处理 | ✅ 完成 | test_auth_v2.py::test_login_failure_wrong_password | ~5s |
| AUTH-004 | 密码显示/隐藏 | 交互切换 | ✅ 完成 | test_auth_v2.py::test_password_visibility_toggle | ~4s |
| AUTH-005 | Enter键提交 | 键盘交互 | ✅ 完成 | test_auth_v2.py::test_enter_key_submission | ~4s |

---

### 📁 2. 首页/仪表盘 (/dashboard) - P0

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| DASH-001 | 统计卡片加载 | 数据展示 | ✅ 完成 | test_dashboard.py::test_stats_cards_load | ~6s |
| DASH-002 | 查看全部活动 | 导航跳转 | ⏳ 待测 | test_dashboard.py::test_view_all_events | ~4s |
| DASH-003 | 活动卡片点击 | 详情跳转 | ⏳ 待测 | test_dashboard.py::test_activity_card_click | ~5s |
| DASH-004 | 待处理任务列表 | 数据展示 | ⏳ 待测 | test_dashboard.py::test_pending_tasks_list | ~5s |

---

### 📁 3. 活动管理 - P0

#### 3.1 活动列表页 (/events)

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| EVT-001 | 新建活动按钮 | 打开弹窗 | ✅ 完成 | test_events.py::test_create_event_open_dialog | ~5s |
| EVT-002 | 新建活动-确定 | 成功创建（含DB验证）| ✅ 完成 | test_events.py::test_create_event_complete_workflow | ~9s |
| EVT-003 | 新建活动-取消 | 关闭弹窗 | ⏳ 待测 | test_events.py::test_create_event_cancel | ~4s |
| EVT-004 | 导出按钮 | 下载CSV/Excel | ⏳ 待测 | test_events.py::test_export_events | ~6s |
| EVT-005 | 批量编辑 | 批量操作 | ⏳ 待测 | test_events.py::test_bulk_edit_events | ~7s |
| EVT-006 | 批量删除 | 批量删除（含DB验证）| ⏳ 待测 | test_events.py::test_bulk_delete_events | ~6s |
| EVT-007 | 搜索框 | 实时搜索 | ✅ 完成 | test_events.py::test_events_search_functionality | ~9s |
| EVT-008 | 状态筛选 | 列表过滤 | ⏳ 待测 | test_events.py::test_status_filter | ~5s |
| EVT-009 | 分页-下一页 | 分页加载 | ⏳ 待测 | test_events.py::test_pagination_next | ~6s |
| EVT-010 | 活动行-查看 | 详情跳转 | ⏳ 待测 | test_events.py::test_view_event_detail | ~5s |
| EVT-011 | 活动行-编辑 | 编辑跳转 | ⏳ 待测 | test_events.py::test_edit_event | ~5s |
| EVT-012 | 活动行-删除 | 删除（含DB验证）| ⏳ 待测 | test_events.py::test_delete_event | ~6s |
| EVT-013 | 刷新按钮 | 数据刷新 | ⏳ 待测 | test_events.py::test_refresh_events | ~5s |

#### 3.2 活动详情页 (/events/:id)

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| EVT-DTL-001 | 页面加载 | 数据加载验证（API+DB）| ⏳ 待测 | test_event_detail.py::test_event_detail_page_load | ~7s |
| EVT-DTL-002 | 编辑活动 | 跳转编辑页 | ⏳ 待测 | test_event_detail.py::test_edit_event_button | ~4s |
| EVT-DTL-003 | 更改状态 | 状态变更（含DB验证）| ⏳ 待测 | test_event_detail.py::test_change_status | ~6s |
| EVT-DTL-004 | 删除活动 | 删除（含DB验证）| ⏳ 待测 | test_event_detail.py::test_delete_event_button | ~6s |
| EVT-DTL-005 | 添加任务 | 打开任务表单 | ⏳ 待测 | test_event_detail.py::test_add_task | ~5s |
| EVT-DTL-006 | 添加预算项 | 打开预算表单 | ⏳ 待测 | test_event_detail.py::test_add_budget | ~5s |
| EVT-DTL-007 | 添加参与者 | 参与者添加（API验证）| ⏳ 待测 | test_event_detail.py::test_add_participant | ~6s |

#### 3.3 活动编辑页 (/events/:id/edit)

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| EVT-EDT-001 | 保存更改 | 数据更新（API+DB验证）| ⏳ 待测 | test_event_edit.py::test_save_changes | ~7s |
| EVT-EDT-002 | 取消编辑 | 返回详情页 | ⏳ 待测 | test_event_edit.py::test_cancel_edit | ~5s |
| EVT-EDT-003 | 删除活动 | 删除（含DB验证）| ⏳ 待测 | test_event_edit.py::test_delete_event_from_edit | ~6s |

---

### 📁 4. 任务管理 (/tasks) - P0

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| TASK-001 | 新建任务按钮 | 打开任务表单 | ⏳ 待测 | test_tasks_e2e.py::test_create_task_open | ~5s |
| TASK-002 | 新建任务-确定 | 创建任务（API+DB验证）| ⏳ 待测 | test_tasks_e2e.py::test_create_task_submit | ~7s |
| TASK-003 | 批量分配 | 批量分配负责人 | ⏳ 待测 | test_tasks_e2e.py::test_bulk_assign | ~6s |
| TASK-004 | 批量状态更新 | 批量状态变更 | ⏳ 待测 | test_tasks_e2e.py::test_bulk_status_update | ~6s |
| TASK-005 | 任务行-编辑 | 打开编辑表单 | ⏳ 待测 | test_tasks_e2e.py::test_edit_task | ~5s |
| TASK-006 | 任务行-删除 | 删除（含DB验证）| ⏳ 待测 | test_tasks_e2e.py::test_delete_task | ~6s |
| TASK-007 | 优先级筛选 | 列表过滤 | ⏳ 待测 | test_tasks_e2e.py::test_priority_filter | ~5s |
| TASK-008 | 负责人筛选 | 列表过滤 | ⏳ 待测 | test_tasks_e2e.py::test_assignee_filter | ~5s |

---

### 📁 5. 用户管理 (/users) - P1

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| USER-001 | 新增用户按钮 | 打开用户表单 | ⏳ 待测 | test_users_e2e.py::test_create_user_open | ~5s |
| USER-002 | 新增用户-确定 | 创建用户（DB验证）| ⏳ 待测 | test_users_e2e.py::test_create_user_submit | ~6s |
| USER-003 | 搜索用户 | 实时搜索 | ⏳ 待测 | test_users_e2e.py::test_search_users | ~5s |
| USER-004 | 角色筛选 | 列表过滤 | ⏳ 待测 | test_users_e2e.py::test_role_filter | ~5s |
| USER-005 | 用户行-编辑 | 打开编辑表单 | ⏳ 待测 | test_users_e2e.py::test_edit_user | ~5s |
| USER-006 | 用户行-删除 | 删除（软删除验证）| ⏳ 待测 | test_users_e2e.py::test_delete_user | ~6s |
| USER-007 | 重置密码 | 密码重置（DB验证）| ⏳ 待测 | test_users_e2e.py::test_reset_password | ~5s |

---

### 📁 6. 清单管理 (/checklists) - P1

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| CHK-001 | 清单实例/模板切换 | 标签切换 | ⏳ 待测 | test_checklists_e2e.py::test_tab_switch | ~4s |
| CHK-002 | 新建清单实例 | 打开创建表单 | ⏳ 待测 | test_checklists_e2e.py::test_create_instance_open | ~5s |
| CHK-003 | 新建模板 | 创建模板（API+DB验证）| ⏳ 待测 | test_checklists_e2e.py::test_create_template | ~7s |
| CHK-004 | 模板-编辑 | 编辑模板 | ⏳ 待测 | test_checklists_e2e.py::test_edit_template | ~6s |
| CHK-005 | 模板-删除 | 删除模板 | ⏳ 待测 | test_checklists_e2e.py::test_delete_template | ~6s |
| CHK-006 | 实例-开始执行 | 状态变更（DB验证）| ⏳ 待测 | test_checklists_e2e.py::test_start_instance | ~6s |
| CHK-007 | 实例-完成检查项 | 进度更新 | ⏳ 待测 | test_checklists_e2e.py::test_complete_checkitem | ~5s |
| CHK-008 | 实例-导出 | 下载PDF/Excel | ⏳ 待测 | test_checklists_e2e.py::test_export_instance | ~6s |

---

### 📁 7. 文件管理 (/files) - P1

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| FILE-001 | 上传文件 | 文件上传（DB验证）| ⏳ 待测 | test_files_e2e.py::test_upload_file | ~8s |
| FILE-002 | 下载文件 | 文件下载 | ⏳ 待测 | test_files_e2e.py::test_download_file | ~6s |
| FILE-003 | 预览文件 | 打开预览 | ⏳ 待测 | test_files_e2e.py::test_preview_file | ~5s |
| FILE-004 | 删除文件 | 删除（含DB验证）| ⏳ 待测 | test_files_e2e.py::test_delete_file | ~6s |
| FILE-005 | 文件搜索 | 列表过滤 | ⏳ 待测 | test_files_e2e.py::test_search_files | ~5s |

---

### 📁 8. 档案管理 (/profiles) - P1

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| PRF-001 | 档案列表加载 | 数据展示 | ⏳ 待测 | test_profiles_e2e.py::test_profiles_list_load | ~6s |
| PRF-002 | 搜索档案 | 实时搜索 | ⏳ 待测 | test_profiles_e2e.py::test_search_profiles | ~5s |
| PRF-003 | 分类筛选 | 列表过滤 | ⏳ 待测 | test_profiles_e2e.py::test_category_filter | ~5s |
| PRF-004 | 档案行-查看 | 打开详情 | ⏳ 待测 | test_profiles_e2e.py::test_view_profile | ~5s |
| PRF-005 | 档案行-编辑 | 打开编辑 | ⏳ 待测 | test_profiles_e2e.py::test_edit_profile | ~6s |

---

### 📁 9. 通知中心 (/notifications) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| NOTIF-001 | 页面加载 | 通知列表加载 | ⏳ 待测 | test_notifications_e2e.py::test_notifications_load | ~6s |
| NOTIF-002 | 标记已读 | 状态变更（DB验证）| ⏳ 待测 | test_notifications_e2e.py::test_mark_read | ~5s |
| NOTIF-003 | 全部已读 | 批量标记 | ⏳ 待测 | test_notifications_e2e.py::test_mark_all_read | ~6s |
| NOTIF-004 | 删除通知 | 删除（DB验证）| ⏳ 待测 | test_notifications_e2e.py::test_delete_notification | ~5s |
| NOTIF-005 | WebSocket连接 | 实时连接验证 | ⏳ 待测 | test_notifications_ws.py::test_ws_connection | ~5s |
| NOTIF-006 | 实时通知接收 | 实时推送验证（DB验证）| ⏳ 待测 | test_notifications_ws.py::test_realtime_notification | ~7s |

---

### 📁 10. 预算管理 (/budget) - P1

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| BUD-001 | 预算明细加载 | 数据展示 | ⏳ 待测 | test_budget_e2e.py::test_budget_detail_load | ~6s |
| BUD-002 | 添加预算项 | 创建项（API+DB验证）| ⏳ 待测 | test_budget_e2e.py::test_add_budget_item | ~7s |
| BUD-003 | 编辑预算项 | 更新项 | ⏳ 待测 | test_budget_e2e.py::test_edit_budget_item | ~6s |
| BUD-004 | 删除预算项 | 删除（DB验证）| ⏳ 待测 | test_budget_e2e.py::test_delete_budget_item | ~6s |

---

### 📁 11. 知识库 (/knowledge) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| KNW-001 | 文档列表加载 | 数据展示 | ⏳ 待测 | test_knowledge_e2e.py::test_documents_list_load | ~6s |
| KNW-002 | 搜索文档 | 实时搜索 | ⏳ 待测 | test_knowledge_e2e.py::test_search_docs | ~5s |
| KNW-003 | 分类筛选 | 列表过滤 | ⏳ 待测 | test_knowledge_e2e.py::test_category_filter | ~5s |

---

### 📁 12. 复盘管理 (/reviews) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| REV-001 | 复盘列表加载 | 数据展示 | ⏳ 待测 | test_reviews_e2e.py::test_reviews_list_load | ~6s |
| REV-002 | 创建复盘 | 创建复盘（API+DB验证）| ⏳ 待测 | test_reviews_e2e.py::test_create_review | ~8s |
| REV-003 | 查看复盘 | 打开详情 | ⏳ 待测 | test_reviews_e2e.py::test_view_review | ~5s |
| REV-004 | 完成复盘 | 状态变更（含API验证）| ⏳ 待测 | test_reviews_e2e.py::test_complete_review | ~6s |

---

### 📁 13. 分析报表 (/analytics) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| ANL-001 | 图表加载 | 数据展示 | ⏳ 待测 | test_analytics_e2e.py::test_charts_load | ~7s |
| ANL-002 | 数据导出 | 下载报表 | ⏳ 待测 | test_analytics_e2e.py::test_export_data | ~6s |
| ANL-003 | 时间范围选择 | 数据过滤 | ⏳ 待测 | test_analytics_e2e.py::test_time_range_filter | ~5s |

---

### 📁 14. 系统设置 (/settings) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| SET-001 | 个人设置打开 | 设置展示 | ⏳ 待测 | test_settings_e2e.py::test_personal_settings_load | ~5s |
| SET-002 | 保存个人设置 | 更新设置（DB验证）| ⏳ 待测 | test_settings_e2e.py::test_save_personal_settings | ~6s |
| SET-003 | 系统配置打开 | 配置展示 | ⏳ 待测 | test_settings_e2e.py::test_system_config_load | ~6s |

---

### 📁 15. 404页面 (/404) - P2

| 测试ID | 按钮/交互 | 测试场景 | 状态 | 测试文件 | 执行时间 |
|--------|----------|---------|------|---------|---------|
| ERROR-001 | 访问不存在的URL | 404页面展示 | ⏳ 待测 | test_error_pages_e2e.py::test_404_page | ~4s |

---

## 进度跟踪

| 分类 | 计划数 | 已完成 | 完成率 |
|------|-------|--------|--------|
| P0 | 38 | 5 | 13.16% |
| P1 | 27 | 0 | 0% |
| P2 | 14 | 0 | 0% |
| **总计** | **79** | **5** | **6.33%** |

---

## 下一步行动计划

### 立即执行（当前阶段）
1. ✅ 完成测试数据准备脚本（已完成）
2. ⏳ 运行测试数据准备脚本
3. ⏳ 首先完成所有P0测试（33个待测）
4. ⏳ 补充完成P0数据库验证逻辑

### 后续阶段
5. ⏳ 完成P1测试（27个）
6. ⏳ 完成P2测试（14个）
7. ⏳ 异常测试（网络错误、权限、并发、边界值）
8. ⏳ 性能测试
9. ⏳ 生成完整测试报告

---

**测试原则**
- ✅ 真实浏览器操作（Playwright）
- ✅ 真实API调用（无mock）
- ✅ 直接数据库验证
- ✅ 前端+后端+数据库三重断言
- ✅ 修复任何发现的问题
