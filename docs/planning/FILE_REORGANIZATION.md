# 文件重组建议方案

## 📁 当前问题

项目根目录存在大量测试脚本、调试工具和文档文件，需要整理到合适的目录中：

### 根目录混乱的文件
- **测试脚本**: comprehensive-test.js, deep-interaction-test.js, systematic-user-test.js, test-final-login.js, test-login-direct.js, test_kanban.sh
- **调试脚本**: debug-router.js, inspect-login.js
- **测试数据**: create_test_data.py, create_sample_data.py
- **打包工具**: check-functionality.js
- **文档文件**: README.md, BUGFIX_SUMMARY.md, P0_BUG_FIX_SUMMARY.md, PROJECT_ANALYSIS_SUMMARY.md, PROJECT_STRUCTURE.md, SYSTEM_STATUS.md, SCRIPT_USAGE.md

## 🗂️ 建议的重组方案

### 1. 测试脚本移至 tests/ 目录
```
tests/
  ├── e2e/
  │   ├── comprehensive-test.js          (集成测试)
  │   ├── deep-interaction-test.js        (深度交互测试)
  │   ├── systematic-user-test.js         (系统性用户测试)
  │   ├── test-final-login.js             (登录最终测试)
  │   └── test-login-direct.js            (直接登录测试)
  ├── e2e-tests/                          (新增)
  │   └── kanban/
  │       └── test_kanban.sh              (看板测试脚本)
```

### 2. 调试脚本移至 scripts/debug/ 目录
```
scripts/debug/
  ├── debug-router.js                     (路由调试)
  ├── inspect-login.js                    (登录检查)
  └── (现有的debug_*.py文件都保留在此)
```

### 3. 测试数据工具移至 tests/fixtures/ 目录
```
tests/fixtures/
  └── create_test_data.py                 (测试数据创建)
```

### 4. 文档整理
```
docs/
  ├── about/
  │   ├── README.md                        (项目主README移至此)
  │   ├── PROJECT_ANALYSIS_SUMMARY.md      (项目分析总结)
  │   └── PROJECT_STRUCTURE.md             (项目结构说明)
  ├── status/
  │   ├── SYSTEM_STATUS.md                 (系统状态)
  │   └── BUGFIX_SUMMARY.md                (Bug修复总结)
  │   └── P0_BUG_FIX_SUMMARY.md            (P0 Bug总结)
  ├── guides/
  │   └── SCRIPT_USAGE.md                  (脚本使用指南)
  └── reports/ (已存在)
      └── (所有测试报告都保留在此)
```

### 5. 工具脚本保留在根目录
```
根目录保留:
  ├── setup-env.sh                        (环境设置)
  ├── setup-dev.sh                        (开发环境设置)
  ├── start.sh                            (服务启动脚本 - 用户经常使用)
  └── manage.py                           (Django管理工具)
```

## 🚀 执行步骤

需要执行以下文件移动操作：

```bash
# 测试脚本移至 tests/e2e
mv comprehensive-test.js tests/e2e/
mv deep-interaction-test.js tests/e2e/
mv systematic-user-test.js tests/e2e/
mv test-final-login.js tests/e2e/
mv test-login-direct.js tests/e2e/

# 创建看板测试目录并移动
mkdir -p tests/e2e/kanban
mv test_kanban.sh tests/e2e/kanban/

# 调试脚本移至 scripts/debug
mv debug-router.js scripts/debug/
mv inspect-login.js scripts/debug/

# 测试数据移至 tests/fixtures
mv create_test_data.py tests/fixtures/

# 文档整理
mkdir -p docs/about
mkdir -p docs/status
mkdir -p docs/guides

mv README.md docs/about/
mv PROJECT_ANALYSIS_SUMMARY.md docs/about/
mv PROJECT_STRUCTURE.md docs/about/

mv SYSTEM_STATUS.md docs/status/
mv BUGFIX_SUMMARY.md docs/status/
mv P0_BUG_FIX_SUMMARY.md docs/status/

mv SCRIPT_USAGE.md docs/guides/
```

## ⚠️ 注意事项

1. **Git提交**：文件移动后需要一次Git提交
2. **路径更新**：需要检查是否有脚本中引用了这些文件路径
3. **文档链接**：检查文档中的相对链接是否需要更新
4. **README引导**：根目录需要创建一个简单的README，指向docs/about/README.md

## 📝 重组后的根目录
重组后根目录将更加简洁，只保留：
- 配置文件
- 主要启动脚本
- 构建相关文件
- 核心目录
