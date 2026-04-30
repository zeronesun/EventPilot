# EventPilot 测试数据摘要

## 当前系统数据状态

### 数据统计
- **事件总数**: 28 个
- **任务总数**: 1 个
- **检查清单模板**: 20 个
- **预算项目**: 若干个

### 已创建的测试事件示例

1. 2024年度科技创新峰会 (conference)
2. 新产品发布会 (corporate_event)
3. 秋季客户答谢会 (festival)
4. 测试事件/集成测试事件
5. 以及其他自动化测试生成的事件

### 已创建的检查清单模板

1. 活动现场标准检查清单
2. 活动策划阶段检查
3. 标准1-10检查清单
4. E2E测试检查清单
5. ...

## 访问信息

### 服务地址
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API代理**: http://localhost:3000/api/*

### 系统访问
- **WSL访问**: http://localhost:3000
- **从Windows访问**: http://172.28.166.164:3000

### 登录凭据
- **用户名**: admin
- **密码**: admin123

## 当前运行的进程

- **前端服务**: PID 22962 (Vite Dev Server on port 3000)
- **后端服务**: PID 20667 (Django Server on port 8000)

## API接口示例

### 基础操作
```bash
# 登录
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取事件列表
curl http://localhost:8000/api/events/events/ \
  -H "Authorization: Bearer <TOKEN>"

# 获取任务列表
curl http://localhost:8000/api/tasks/tasks/ \
  -H "Authorization: Bearer <TOKEN>"

# 获取检查清单模板
curl http://localhost:8000/api/checklists/templates/ \
  -H "Authorization: Bearer <TOKEN>"
```

## 测试数据生成器

已创建的生成脚本：

1. **create_sample_data.py** - 快速创建示例数据
2. **generate_test_data.py** - 完整测试数据生成
3. **generate_test_data_v2.py** - 改进版数据生成
4. **final_e2e_verification.py** - 端到端功能验证
5. **frontend_backend_integration.py** - 前后端联调测试

## 系统就绪状态

✅ **后端系统** - Django API 正常运行
✅ **前端系统** - Vite开发服务器正常运行
✅ **API代理** - 前端代理配置正确
✅ **数据库** - 数据正常存储
✅ **认证系统** - 用户认证工作正常
✅ **测试数据** - 已生成基础测试数据

EventPilot系统已准备好进行开发、测试或演示！
