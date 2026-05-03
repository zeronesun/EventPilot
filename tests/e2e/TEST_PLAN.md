# EventPilot 测试计划

## 项目信息
- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **后端**: Django 5.2 + DRF + JWT
- **数据库**: PostgreSQL
- **测试框架**: pytest + Playwright

---

## 测试覆盖矩阵

| 模块 | 测试项 | 预期结果 | 视角 | 优先级 | 状态 |
|------|--------|----------|------|--------|------|
| **认证** | 登录页加载 | 显示品牌、表单元素 | UI/UX | P0 | ✅ |
| **认证** | 成功登录 | Token存储、跳转首页 | 用户 | P0 | ✅ |
| **认证** | 密码错误 | 显示错误提示、留在登录页 | 用户 | P0 | ✅ |
| **认证** | 未认证访问 | 重定向到登录页 | 开发者 | P0 | ✅ |
| **认证** | 已登录访问登录页 | 重定向到首页 | 开发者 | P1 | ✅ |
| **认证** | Token刷新 | 自动刷新或跳转登录 | 开发者 | P1 | ⬜ |
| **活动** | 列表页加载 | 显示表格、工具栏、搜索 | UI/UX | P0 | ✅ |
| **活动** | 创建活动弹窗 | 显示表单字段 | UI/UX | P0 | ✅ |
| **活动** | 创建活动完整流程 | 201响应、数据库有记录 | 前后端联动 | P0 | ✅ |
| **活动** | 活动详情页 | 显示嵌套数据(budget_items) | 前后端联动 | P0 | ✅ |
| **活动** | 状态流转 | 合法转换成功、非法返回400 | 架构师 | P0 | ✅ |
| **活动** | 搜索筛选 | 结果匹配关键词 | 用户 | P1 | ✅ |
| **活动** | 删除活动 | 数据库记录删除 | 前后端联动 | P1 | ✅ |
| **活动** | API响应结构 | 符合序列化器定义 | 开发者 | P1 | ✅ |
| **任务** | 列表页加载 | 显示任务列表 | UI/UX | P1 | ✅ |
| **任务** | 创建任务 | 201响应 | 前后端联动 | P1 | ✅ |
| **任务** | 看板加载 | 显示三列(待办/进行中/已完成) | UI/UX | P1 | ✅ |
| **任务** | 状态更新 | 数据库状态变更 | 用户 | P1 | ✅ |
| **用户** | 用户列表 | 分页返回 | 开发者 | P1 | ⬜ |
| **用户** | 批量操作 | 批量更新状态成功 | 架构师 | P1 | ⬜ |
| **文件** | 文件上传 | 文件保存到存储 | 用户 | P2 | ⬜ |
| **文件** | 文件下载 | 返回文件内容 | 用户 | P2 | ⬜ |
| **通知** | WebSocket连接 | 连接成功、接收消息 | 架构师 | P2 | ⬜ |
| **UI/UX** | 表单验证 | 显示字段级错误 | UI/UX | P0 | ✅ |
| **UI/UX** | 加载状态 | 显示骨架屏/loading | UI/UX | P1 | ✅ |
| **UI/UX** | 空状态 | 显示Empty组件 | UI/UX | P1 | ✅ |
| **UI/UX** | 移动端适配 | 布局正确、按钮可点击 | UI/UX | P1 | ✅ |
| **UI/UX** | 错误提示 | 红色字体显示具体错误 | UI/UX | P1 | ✅ |
| **性能** | 页面加载 | < 2秒 | 架构师 | P1 | ✅ |
| **性能** | API响应 | < 500ms | 架构师 | P1 | ✅ |
| **性能** | JS资源大小 | 单个文件 < 1MB | 架构师 | P2 | ✅ |
| **集成** | 数据库一致性 | 前端操作与数据库一致 | 架构师 | P0 | ✅ |
| **集成** | 并发更新 | 无数据丢失 | 架构师 | P1 | ✅ |
| **集成** | 权限控制 | 角色访问控制正确 | 架构师 | P1 | ⬜ |
| **API契约** | Swagger文档 | 可访问、Schema完整 | 架构师 | P1 | ✅ |
| **API契约** | CORS头 | 允许前端域名 | 架构师 | P1 | ✅ |
| **API契约** | 健康检查 | 返回healthy | 开发者 | P0 | ✅ |

---

## 测试执行命令

```bash
# 1. 确保前后端运行
./start.sh status

# 2. 安装 Playwright 依赖
cd frontend
npx playwright install

# 3. 运行所有 E2E 测试
pytest tests/e2e/ -v --headed

# 4. 运行特定测试文件
pytest tests/e2e/test_auth.py -v
pytest tests/e2e/test_events.py -v
pytest tests/e2e/test_api_contract.py -v

# 5. 生成 HTML 报告
pytest tests/e2e/ --html=tests/e2e/report.html

# 6. 运行性能测试
pytest tests/e2e/test_performance.py -v
```

---

## 测试数据准备

```bash
# 创建测试用户
python manage.py shell -c "
from apps.users.models import User
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
User.objects.create_user('testuser', 'test@example.com', 'testpass123')
"

# 创建测试数据
python tests/fixtures/create_test_data.py
```

---

## 缺陷报告模板

```markdown
### [视角] 缺陷标题

**严重程度**: P0/P1/P2
**模块**: 认证/活动/任务/...

**复现步骤**:
1. ...
2. ...

**预期结果**:
...

**实际结果**:
...

**根因分析**:
...

**修复代码**:
```diff
- 旧代码
+ 新代码
```
```
