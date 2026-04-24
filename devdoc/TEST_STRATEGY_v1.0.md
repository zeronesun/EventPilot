# EventPilot 测试策略与执行指南

## 项目架构

EventPilot 采用 Django + Vue 3 前后端分离架构：

```
EventPilot/
├── apps/           # Django 后端应用
│   ├── tasks/      # 任务管理
│   ├── events/     # 活动管理
│   ├── checklists/ # 清单管理
│   ├── websocket/  # WebSocket 实时通信
│   └── notifications/ # 通知系统
├── frontend/       # Vue 3 前端
│   ├── src/
│   │   ├── test/   # 前端测试
│   │   ├── lib/    # WebSocket 客户端
│   │   └── store/  # 状态管理
└── config/         # Django 配置
```

## 测试分层策略

### 1. 单元测试 (Unit Tests)

**后端 (pytest)**
- `apps/tasks/tests/test_tasks.py` - 任务 API 测试
  - CRUD 操作
  - 任务依赖关系
  - 权限验证
- `apps/checklists/tests.py` - 清单模板测试
- `apps/websocket/tests/` - **缺失**
- `apps/notifications/tests/` - **缺失**

**前端 (vitest)**
- `src/test/crypto.test.ts` - 加密工具测试 (22 tests)
- `src/test/websocket.test.ts` - WebSocket 客户端测试 (11 tests)
- `src/test/components/` - **缺失**
- `src/test/store/` - **缺失**

### 2. 集成测试 (Integration Tests)

- Django REST API 测试
- WebSocket 消息验证测试
- 前后端 API 对接测试

### 3. E2E 测试 (End-to-End)

- **缺失** - 建议使用 Playwright 测试：
  - 用户登录流程
  - 任务创建和拖拽
  - 实时协作场景

## 运行测试

### 后端测试

```bash
cd /path/to/EventPilot

# 1. 安装依赖
pip install pytest pytest-django pytest-cov coverage factory-boy faker

# 2. 运行所有测试
pytest --settings=config.settings --verbose

# 3. 运行特定应用测试
pytest apps/tasks/tests/

# 4. 覆盖率报告
pytest --cov=apps --cov-report=html --cov-report=term
```

### 前端测试

```bash
cd frontend

# 运行所有测试
npm run test:run

# 交互式测试 UI
npm run test:ui

# 覆盖率报告
npm run coverage
```

## 测试覆盖率目标

| 层级 | 目标 | 当前 |
|------|-----------|--------|
| 后端单元测试 | 80%+ | 待测 |
| 前端单元测试 | 70%+ | ~30% |
| E2E 测试 | 核心路径 100% | 0% |

## 缺失的测试

### 后端
- [ ] WebSocket 消息签名验证测试
- [ ] 通知系统测试
- [ ] API 权限和认证测试
- [ ] WebSocket 心跳机制测试
- [ ] 消息重放攻击防护测试

### 前端
- [ ] Vue 组件测试 (Tasks.vue, Files.vue 等)
- [ ] Store 状态管理测试
- [ ] 拖拽交互测试
- [ ] 乐观 UI 回滚机制测试
- [ ] WebSocket 心跳和重连测试
- [ ] Error Boundary 组件测试

### 端到端
- [ ] 用户注册和登录
- [ ] 创建和分配任务
- [ ] 看板拖拽流程
- [ ] 实时协作场景（多用户）
- [ ] 错误恢复流程

## 测试执行日志

### 后端测试执行记录
- add_date: 2025-04-23
- status: 待执行

### 前端测试执行记录
- date: 2025-04-23
- framework: Vitest
- total_tests: 33
- passed: 33
- failed: 0
- duration: ~18s

## 下一步计划

1. 创建 pytest.ini 配置文件
2. 运行完整后端测试套件
3. 生成测试覆盖率报告
4. 识别缺失的测试覆盖
5. 为核心模块补充单元测试

## CI/CD 集成

建议在 GitHub Actions 中配置自动测试：

```yaml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest --cov=apps --cov-report=xml
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: cd frontend && npm install
      - run: npm run test:run
```
