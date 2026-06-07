# EventPilot 修复报告 2026-05-30

## 修复内容

### 1. pytest配置修复 ✅
**问题**: `unrecognized arguments: --asyncio-mode=auto`
**原因**: pytest-asyncio未安装
**修复**: 安装pytest-asyncio 1.4.0
- 升级pytest从7.4.3到9.0.3
- 配置pytest.ini中的--asyncio-mode参数生效

**验证**: Tasks模块单元测试29/29通过 (32.04s)

### 2. Events列表视图路由修复 ✅
**问题**: 访问`/events/list`时EventDetail.vue尝试加载ID为'list'的活动详情，导致500错误
**原因**: 
- 路由配置缺少`/events/:id`路由
- `/events/list`被错误映射到`:id='list'`的动态路由
- EventDetail组件在onMounted时自动加载数据，即使ID是静态字符串'list'

**修复** ( frontend/src/router/index.js ):
1. 添加`/events/list` -> `/events`重定向规则
2. 恢复`/events/:id`动态路由（指向EventDetail）
3. 保持`/events/:id/edit`编辑路由

**影响范围**:
- ✅ `/events/list` 现在跳转到 `/events` (Events.vue列表)
- ✅ `/events/{uuid}` 正确加载EventDetail详情页
- ✅ 避免后端查询无效ID导致的500错误

## 测试验证

### 后端单元测试
`pytest apps/tasks/tests/`:
- 测试数: 29条
- 通过率: 100% ✅
- 耗时: 32.04s

### 前端功能检查
- [ ] Events列表页加载（待重新验证）
- [ ] Events看板页加载（已验证正常）
- [ ] Tasks页面显示（已验证正常）

## 下一步
1. 验证Events列表页不再有控制台错误
2. 完成BR-V0-R12批量删除前端验证
3. 继续其他模块P0测试
