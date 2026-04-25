## 发现的问题和缺失功能 (2025-04-25)

### Bug #1: API认证配置不一致

**症状:**
- Tasks API返回正常（使用IsAuthenticatedOrReadOnly）
- Events/Users/Checklists/Files API返回"身份认证信息未提供"
- 前端登录返回JWT token格式：`{"data": {"user": {...}, "token": "...", "expires_in": 900}}`
- REST Framework配置使用`rest_framework.authentication.TokenAuthentication`
- 前端尝试使用`Bearer {token}`格式

**根本原因:**
后端REST_FRAMEWORK配置使用TokenAuthentication，但登录接口返回token的格式和认证方式不匹配。

**影响范围:**
- Events API - 完全不可访问
- Users API - 完全不可访问
- Checklists API - 部分不可访问
- Files API - 完全不可访问

**修复方案:**
1. 检查当前是否支持JWT认证
2. 如不支持，添加JWT认证或修复token格式

### Bug #2: Checklists API返回格式错误

**症状:**
- Checklists API调用返回"Expecting value: line 1 column 1 (char 0)"
- 说明返回的不是有效JSON

**可能原因:**
- API端点不存在
- 返回空内容或HTML错误页面
- 路由配置问题

### 缺失功能（待确认）

#### P0级别（核心功能）
1. **任务拖拽功能** - Tasks页面中有看板视图，需要测试拖拽是否实际工作
2. **任务批量操作** - Tasks页面中有批量更新状态功能
3. **活动统计功能** - Events页面有统计端点，需要测试
4. **活动完成功能** - Events页面有完成端点，需要测试

#### P1级别（重要功能）
1. **文件上传功能** - Files页面需要完整的文件上传流程
2. **文件下载功能** - Files页面需要下载验证
3. **检查清单模板管理** - Checklists页面有模板功能
4. **检查清单实例化** - Checklists页面有实例化功能

#### P2级别（增强功能）
1. **个人资料高级搜索** - Profiles页面有高级搜索组件
2. **个人资料智能推荐** - Profiles页面有智能推荐组件
3. **个人资料分析仪表板** - Profiles页面有分析组件
4. **联系人管理** - Profiles页面有联系人管理组件
5. **课程/证书/技能管理** - Profiles相关高级功能
6. **活动管理** - Profiles页面有活动管理组件
7. **文件管理器高级功能** - Files页面有完整文件管理器
8. **高级搜索组件** - 独立组件
9. **错误边界** - 独立组件

### 待调查功能
1. WebSocket实时协作 - 需要测试多用户场景
2. 通知系统 - 需要测试通知触发和展示
3. 权限系统 - 需要测试不同角色权限
4. 数据导出 - 需要测试各种导出功能

### 测试覆盖缺口

| 模块 | 已测试功能 | 待测试功能 | 缺失功能 |
|------|----------|----------|---------|
| Login | ✅ 正常登录 | ❌ 错误凭据 | - |
| Home | ❌ 导航菜单 | ❌ 所有交互 | - |
| Tasks | ⚠️ API返回空 | ❌ CRUD | ❌ 拖拽 |
| Events | ❌ 认证失败 | ❌ CRUD | ❌ 统计 |
| Users | ❌ 认证失败 | ❌ CRUD | - |
| Files | ❌ 认证失败 | ❌ CRUD | ❌ 上传/下载 |
| Checklists | ❌ API错误 | ❌ CRUD | ❌ 模板/实例化 |
| Profiles | ❌ 未测试 | ❌ 所有功能 | ❌ 所有高级功能 |

## 修复优先级

1. **P0 - 立即修复:**
   - Bug #1: API认证配置
   - Bug #2: Checklists API

2. **P0 - 实现缺失功能:**
   - 任务拖拽功能
   - 任务CRUD实际操作
   - 活动CRUD实际操作
   - 用户CRUD实际操作

3. **P1 - 实现重要功能:**
   - 文件上传/下载
   - 检查清单功能
   - 个人资料基础功能

4. **P2 - 增强功能:**
   - 所有高级搜索/推荐/分析功能
   - 联系人管理
   - 文件管理器高级功能
