# EventPilot 项目目录结构

```
EventPilot/
├── archive/                    # 存档目录
│   └── debug/                  # 调试脚本存档
│       ├── debug_complete_api.py
│       ├── test_communication_debug.py
│       └── test_instance_debug.py
├── apps/                       # Django 应用
│   ├── checklists/             # 核验清单模块
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── tests.py            # Checklist 测试 (15 tests)
│   ├── files/                  # 文件管理模块
│   ├── tasks/                  # 任务管理模块
│   │   ├── api/
│   │   │   └── views.py        # 修复: dependencies action 使用 getlist()
│   │   ├── models/
│   │   ├── services/
│   │   └── tests/
│   │       └── test_tasks.py   # Tasks 测试 (29 tests)
│   └── websocket/              # WebSocket 模块
├── config/                     # Django 配置
├── core/                       # 核心模块
├── docs/                       # 文档
│   └── reports/                # 报告文档
│       └── TASKS_TEST_FIX_REPORT_2026-05-01.md
├── frontend/                   # Vue 3 前端
├── reports/                    # 测试报告 (新增)
│   ├── COMPLETE_TEST_REGRESSION_2026-05-01.md
│   └── pytest-report.log
├── scripts/                    # 脚本目录
│   ├── verification/           # 验证脚本 (新增)
│   │   ├── verify_bugfix.py
│   │   └── test_complete_fix.py
│   ├── audit_vue_components.py
│   ├── test_api.py
│   ├── test_checklist_create.py
│   └── ...
├── tests/                      # 旧测试目录 (保留)
│   ├── invalid/
│   └── ...
├── api/                        # API 层
├── cache/                      # 缓存目录
├── logs/                       # 日志目录
├── storage/                    # 存储目录
├── public/                     # 公共资源
├── tasks/                      # 任务目录
├── venv/                       # Python 虚拟环境
├── .env                        # 环境变量
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略配置
├── conftest.py                 # Pytest 配置
├── create_sample_data.py       # 示例数据生成
├── EventPilot-icon.png         # 项目图标
├── frontend_backend_integration.py  # 前后端集成测试
├── manage.py                   # Django 管理脚本
├── P0_BUG_FIX_SUMMARY.md       # P0 Bug 修复摘要
├── pytest.ini                  # Pytest 配置
├── README.md                   # 项目说明
├── requirements.txt            # Python 依赖
├── requirements-dev.txt        # 开发依赖
├── setup-dev.sh                # 开发环境设置
└── SYSTEM_STATUS.md            # 系统状态
```

## 新增目录说明

- **archive/debug/**: 存放过时的调试脚本，便于历史追踪
- **scripts/verification/**: 存放验证脚本和 bug 修复验证代码
- **reports/**: 存放测试报告和日志，统一管理测试输出

## 测试文件分布

| 位置 | 类型 | 数量 |
|------|------|------|
| apps/tasks/tests/ | 单元测试 | 29 |
| apps/checklists/tests.py | 单元测试 | 15 |
| tests/ | 旧测试目录 | 保留 |
| scripts/verification/ | 验证脚本 | 2 |

## 测试运行命令

```bash
# 运行全量测试
python -m pytest -v --tb=short

# 运行 Tasks 模块测试
python -m pytest apps/tasks/tests/test_tasks.py -v

# 运行 Checklist 模块测试
python -m pytest apps/checklists/tests.py -v
```

## 清理说明

已从项目根目录移动或删除以下临时文件：
- 调试脚本: `debug_complete_api.py`, `test_communication_debug.py`, `test_instance_debug.py`
- 验证脚本: `verify_bugfix.py`, `test_complete_fix.py`
- 测试日志: `pytest-report.log`
- 数据生成: `generate_test_data.py`, `generate_test_data_v2.py`, `test_dependencies.py`
- E2E 验证: `final_e2e_verification.py`

这些文件已按功能分类到相应的目录中，保持项目根目录整洁。
