# EventPilot 开发指南

## 目录

- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [代码结构](#代码结构)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [常见问题](#常见问题)

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (可选，开发环境可用 SQLite)
- Redis 7+ (可选，仅用于缓存)

### 初始化项目

```bash
# 1. 克隆项目
git clone <repository-url> EventPilot
cd EventPilot

# 2. 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 3. 安装后端依赖
pip install -r requirements.txt

# 4. 安装前端依赖
cd frontend
npm install
cd ..

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 6. 初始化数据库
python manage.py migrate
python manage.py createsuperuser

# 7. 启动开发服务器
./start.sh start
```

### 访问应用

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/

## 环境配置

### 环境变量说明

创建 `.env` 文件并配置以下变量：

```bash
# Django 配置
DEBUG=True
SECRET_KEY=your-development-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置（开发环境用 SQLite）
DATABASE_URL=sqlite:///db.sqlite3

# 生产环境用 PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/eventpilot

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0

# WebSocket 配置
WS_ADDRESS=ws://localhost:8000/ws/

# CORS 配置
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 开发工具

推荐安装以下工具：

```bash
# 代码格式化
pip install black isort
pip install flake8 mypy

# 前端工具
npm install -g eslint prettier
```

## 代码结构

### 后端结构 (Django)

```
apps/
├── users/          # 用户管理
│   ├── api/        # API 层 (views, serializers, urls)
│   ├── models/    # 数据模型
│   ├── services/  # 业务逻辑
│   └── tests/     # 单元测试
├── events/         # 事件管理
├── tasks/          # 任务管理
├── checklists/     # 核验清单
├── profiles/       # 关联方档案
├── knowledge/      # 知识库
├── reviews/        # 复盘
├── files/          # 文件管理
├── notifications/  # 通知系统
├── websocket/      # WebSocket 连接
└── budgets/        # 预算管理
```

**开发规范：**
- 每个 app 采用 DDD (Domain-Driven Design) 结构
- API 层遵循 RESTful 设计原则
- Service 层封装复杂业务逻辑
- 所有模型使用 soft_delete 软删除

### 前端结构 (Vue 3)

```
frontend/src/
├── components/     # 可复用组件
│   ├── Layout/
│   ├── Forms/
│   └── Common/
├── views/          # 页面组件
├── router/         # 路由配置
├── stores/         # Pinia 状态管理
├── api/            # API 客户端
├── composables/    # 可组合函数
├── services/       # 服务层
├── utils/          # 工具函数
├── types/          # TypeScript 类型
└── styles/         # 样式文件
```

**开发规范：**
- 使用 Composition API
- 组件命名采用 PascalCase
- 文件命名采用 kebab-case
- 使用 TypeScript 进行类型检查

## 开发工作流

### 1. 创建新功能

#### 后端添加新 API

```bash
# 1. 创建新应用（如果需要）
python manage.py startapp new_feature

# 2. 定义模型
# apps/new_feature/models.py

# 3. 创建序列化器
# apps/new_feature/api/serializers.py

# 4. 创建视图
# apps/new_feature/api/views.py

# 5. 配置路由
# apps/new_feature/api/urls.py

# 6. 生成迁移
python manage.py makemigrations new_feature
python manage.py migrate

# 7. 注册到主路由
# config/urls.py
```

#### 前端添加新页面

```bash
# 1. 创建视图组件
# frontend/src/views/FeaturePage.vue

# 2. 创建 API 客户端
# frontend/src/api/feature.ts

# 3. 创建状态管理
# frontend/src/stores/featureStore.ts

# 4. 配置路由
# frontend/src/router/index.ts

# 5. 添加导航链接
```

### 2. 编写测试

#### 后端测试

```python
# apps/new_feature/tests/test_api.py
import pytest
from django.test import TestCase
from apps.new_feature.models import SomeModel

class SomeModelTest(TestCase):
    def setUp(self):
        SomeModel.objects.create(name='test')

    def test_model_creation(self):
        obj = SomeModel.objects.get(name='test')
        self.assertEqual(obj.name, 'test')
```

#### 前端测试

```typescript
// frontend/src/views/__tests__/FeaturePage.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FeaturePage from '../FeaturePage.vue'

describe('FeaturePage', () => {
  it('renders correctly', () => {
    expect(FeaturePage).toBeTruthy()
  })
})
```

### 3. 代码提交规范

```bash
# 格式化代码
black apps/
isort apps/
cd frontend && npm run format

# 运行测试
pytest
cd frontend && npm test

# 提交代码
git add .
git commit -m "feat: add new feature description"
```

**Commit Message 规范:**
- `feat:` 新功能
- `fix:` 修复错误
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建系统或工具

## 测试指南

### 运行所有测试

```bash
# 后端测试
pytest
pytest --cov=apps --cov-report=html

# 前端测试
cd frontend
npm test
npm test:run
```

### 运行特定测试

```bash
# 特定应用
pytest apps/events/tests/

# 特定文件
pytest tests/test_checklists_crud.py

# 特定测试函数
pytest tests/test_tasks.py::test_task_creation

# 前端特定测试
cd frontend
npm test -- FeaturePage
```

### 调试测试失败

```bash
# 显示详细输出
pytest -v

# 显示 print 输出
pytest -s

# 在失败时进入调试器
pytest --pdb

# 只运行上次失败的测试
pytest --lf
```

## 调试技巧

### 后端调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()

# 日志输出
import logging
logger = logging.getLogger(__name__)
logger.debug('Debug信息')
logger.info('信息信息')
logger.warning('警告信息')
logger.error('错误信息')
```

### 前端调试

```javascript
// 在代码中添加断点
console.log('调试信息')
console.table(data)
console.error('错误信息')

// Vue DevTools
// 使用 Vue DevTools 浏览器扩展
```

### 使用 IDE 断点

**VSCode 配置:**

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/manage.py",
      "args": ["runserver", "--noreload"],
      "django": true
    },
    {
      "type": "chrome",
      "request": "launch",
      "name": "Vue Debug",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

### 常用 Django 命令

```bash
# 启动开发服务器
python manage.py runserver

# 创建超级用户
python manage.py createsuperuser

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 收集静态文件
python manage.py collectstatic

# Django Shell
python manage.py shell

# 查看路由
python manage.py show_urls

# 数据库操作
python manage.py dbshell
```

### 常用 Vue 命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 类型检查
npm run type-check

# 代码格式化
npm run lint -- --fix
```

## 常见问题

### Q: 数据库迁移失败

**解决方案：**
```bash
# 重置迁移（谨慎使用）
python manage.py migrate app_name zero

# 或删除数据库重新开始
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Q: CORS 错误

**检查配置：**
```python
# config/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # 仅开发环境
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

### Q: WebSocket 连接失败

**排查步骤：**
1. 确认 Redis 正在运行
2. 检查 WS_ADDRESS 配置
3. 查看浏览器控制台错误
4. 检查防火墙设置

### Q: 前端无法连接后端

**解决方案：**
```bash
# 1. 确认后端正在运行
./start.sh status

# 2. 检查防火墙
sudo ufw allow 8000

# 3. 查看后端日志
./start.sh logs backend
```

### Q: 依赖冲突

**解决方案：**
```bash
# Python 虚拟环境问题
rm -rf venv/
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node.js 问题
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Q: 性能问题

**优化建议：**
1. 使用 Django Debug Toolbar 分析查询
2. 添加数据库索引
3. 使用 select_related 减少查询
4. 启用 Redis 缓存
5. 使用数据库分页

## 性能分析

### Django Debug Toolbar

```python
# config/settings.py (开发环境)
if DEBUG:
    try:
        import debug_toolbar
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INSTALLED_APPS.append('debug_toolbar')
        INTERNAL_IPS = ['127.0.0.1']
    except ImportError:
        pass
```

### 查询优化

```python
# 差: N+1 查询问题
events = Event.objects.all()
for event in events:
    print(event.project.name)  # 每次都查询

# 好: 使用 select_related
events = Event.objects.select_related('project')
for event in events:
    print(event.project.name)  # 只查询一次
```

## 扩展阅读

- [项目架构文档](../architecture/ARCHITECTURE.md)
- [API 文档](../api/)
- [部署指南](../guides/DEPLOYMENT.md)
- [测试方案](../TESTING_PLAN.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-05-03  
**维护者**: EventPilot 团队
