# Debug 调试工具目录

## 📁 目录结构

```
debug/
├── README.md                      # 本目录说明文档
├── phase1/                        # Phase 1 调试工具
├── phase2/                        # Phase 2 调试工具
├── phase3/                        # Phase 3 调试工具
├── jwt/                           # JWT认证相关测试
├── websocket/                     # WebSocket相关测试
├── integration/                   # 集成和端到端测试
├── infrastructure/                # 基础设施验证工具
└── verification/                  # Phase验收测试
```

## 🔧 各类调试工具说明

### 🧪 phase1/ - Phase 1 基础设施
**用途**: Phase 1的API基础设施、认证系统等测试验证

**主要测试内容**:
- 用户登录和认证流程
- JWT token生成和验证
- 基础API端点功能
- 前后端集成测试

### 🧪 phase2/ - Phase 2 核心功能
**用途**: Phase 2的核心CRUD功能、文件系统、WebSocket测试

**主要测试内容**:
- 用户管理CRUD验证 (`verify_phase2.py`)
- 事件管理CRUD验证 (`verify_event_management.py`)
- 文件上传系统测试
- WebSocket基础设施验证
- 清单高级功能测试

**示例运行**:
```bash
# 验证Phase 2核心功能
python debug/phase2/verify_phase2.py

# 验证事件管理功能
python debug/phase2/verify_event_management.py
```

### 🧪 phase3/ - Phase 3 智能档案系统
**用途**: Phase 3的关联方档案管理、智能推荐系统测试

**主要测试内容**:
- 档案管理系统API测试
- 智能推荐算法验证
- 评估系统功能测试
- 性能基准测试
- 数据分析功能验证

### 🔐 jwt/ - JWT认证系统
**用途**: 专门测试JWT认证机制

**主要测试内容**:
- JWT token生成和验证
- Token过期和刷新机制
- 认证和授权流程
- 安全机制验证

### 🔌 websocket/ - WebSocket实时通讯
**用途**: WebSocket基础设施和功能测试

**主要测试内容**:
- WebSocket连接建立
- 消息广播机制
- 心跳检测
- 并发连接处理
- 实时通知系统

**示例运行**:
```bash
# 验证WebSocket基础设施
bash debug/websocket/verify_websocket_setup.sh

# 测试WebSocket基本功能
python debug/websocket/test_websocket.py
```

### 🔄 integration/ - 集成测试
**用途**: 端到端集成测试，验证系统各模块协同工作

**主要测试内容**:
- 完整业务流程测试
- 跨模块功能验证
- 数据一致性测试
- 系统集成验证

### 🏗️ infrastructure/ - 基础设施
**用途**: 系统基础设施和配置验证

**主要测试内容**:
- Django配置检查
- 数据库连接验证
- 依赖包检查
- 环境配置验证
- 测试基础配置 (`conftest.py`)

**示例运行**:
```bash
# 基础设施检查
python debug/infrastructure/check_imports.py
```

### ✅ verification/ - 阶段验收
**用途**: 各阶段完成后的验收测试

**主要测试内容**:
- Phase 1完成验证 (`check_phase1_completion.py`)
- Phase 2完成验证
- Phase 3完成验证
- 功能完整性检查
- 性能基准验证

**示例运行**:
```bash
# 检查Phase 1完成情况
python debug/verification/check_phase1_completion.py
```

## 🚀 常用调试命令

### 快速系统状态检查
```bash
# 验证Phase 1基础设施
python debug/verification/check_phase1_completion.py

# 验证Phase 2核心功能
python debug/phase2/verify_phase2.py

# 验证Phase 3智能功能
python debug/phase3/system_verification.py
```

### 组件专项测试
```bash
# 测试WebSocket基础设施
bash debug/websocket/verify_websocket_setup.sh

# 测试文件上传系统
python debug/integration/test_file_upload_system.py

# 验证清单高级功能
python debug/integration/verify_checklist_advanced.py
```

### 环境和基础设施检查
```bash
# 检查Python导入依赖
python debug/infrastructure/check_imports.py

# 运行测试基础设施
pytest debug/infrastructure/conftest.py -v
```

## 📊 测试分类说明

### 按阶段分类
- `phase1/`: 基础认证和API基础设施
- `phase2/`: CRUD功能和实时通讯
- `phase3/`: 智能档案和推荐系统

### 按功能分类
- `jwt/`: 认证和授权
- `websocket/`: 实时通讯
- `integration/`: 功能集成
- `infrastructure/`: 基础环境

### 按用途分类
- `verification/`: 阶段验收测试
- `debug/`: 功能调试测试

## 🧭 使用指南

### 1. 问题排查流程
当遇到系统问题时，按以下顺序运行测试:

```bash
# 步骤1: 检查基础设施
python debug/infrastructure/check_imports.py

# 步骤2: 检查认证系统
python debug/jwt/test_jwt_system.py

# 步骤3: 检查WebSocket连接
bash debug/websocket/verify_websocket_setup.sh

# 步骤4: 检查核心功能
python debug/phase2/verify_phase2.py

# 步骤5: 检查最新功能
python debug/phase3/system_verification.py
```

### 2. 阶段验收前检查
在完成阶段开发后运行验收测试:

```bash
# Phase 1验收
python debug/verification/check_phase1_completion.py

# Phase 2验收
python debug/phase2/verify_phase2.py
python debug/phase2/verify_event_management.py

# Phase 3验收
python debug/phase3/all_tests.py
```

### 3. 性能和集成测试
运行更全面的测试套件:

```bash
# 集成测试
python debug/integration/test_integration.py

# 自动化验收测试
python debug/verification/automated_acceptance.py
```

## 💡 开发建议

1. **定期运行**: 在开发过程中定期运行相关测试
2. **问题定位**: 选择对应的功能模块测试定位问题
3. **集成验证**: 前确保单个模块正常后再进行集成测试
4. **性能监控**: 关注测试输出中的性能指标
5. **错误日志**: 查看详细错误日志进行深入调试

## ⚠️ 注意事项

### 测试环境要求
- Python 3.11+ 环境
- Django配置正确
- 数据库已迁移
- 所有依赖已安装

### 运行要求
- 大多数测试文件需要从项目根目录运行
- 部分测试需要正确的环境变量配置
- 某些集成测试需要服务正在运行

### 日志和输出
- 测试结果会直接显示在控制台
- 错误信息会详细描述问题
- 性能测试会输出关键指标

## 📚 相关文档

- [Phase 1完成验证](../development/PHASE1_COMPLETION.md)
- [Phase 2完成报告](../development/Phase2_COMPLETION_REPORT.md)
- [Phase 3完成报告](../development/Phase3_Completion_Report.md)
- [项目最终报告](../FINAL_REPORT.md)
- [项目总体说明](../README.md)

**维护说明**: debug目录中的工具主要用于开发和调试，不包含在生产环境中运行的代码。

---

**最后更新**: 2026-04-21  
**维护者**: EventPilot开发团队