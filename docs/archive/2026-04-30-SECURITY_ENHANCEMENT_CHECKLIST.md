# EventPilot 安全增强实现清单

实现日期: 2026-04-30

## ✅ 已完成的安全增强

### 1. 密码安全
- ✅ 使用PBKDF2-SHA256进行密码哈希（100,000次迭代）
- ✅ 每个密码使用随机盐值
- ✅ 密码比较使用安全字符串对比（防止时序攻击）
- 文件: `apps/security/utils.py` (PasswordHasher类)

### 2. JWT令牌管理
- ✅ 生成JWT令牌（HMAC-SHA256签名）
- ✅ 令牌过期时间验证（12小时）
- ✅ 令牌签名验证（防止伪造）
- 文件: `apps/security/utils.py` (TokenValidator类)

### 3. 输入验证和XSS防护
- ✅ 字符串输入清理（移除危险字符）
- ✅ HTML输入清理（仅保留安全标签）
- ✅ 表单输入长度限制
- ✅ XSS转义和防护
- 文件: 
  - `apps/security/utils.py` (InputSanitizer类)
  - `frontend/src/utils/security.ts` (XSSProtection类)

### 4. WebSocket消息安全
- ✅ 消息签名验证（HMAC-SHA256）
- ✅ 时间检查（防止重放攻击，60秒过期）
- ✅ 消息大小限制（最大1MB）
- ✅ 消息内容清理和验证
- 文件: 
  - `apps/security/utils.py` (WebSocketSecurity类)
  - `frontend/src/utils/security.ts` (WebSocketSigner类)

### 5. 速率限制
- ✅ 基于IP的请求速率限制（100请求/60秒）
- ✅ 自定义速率限制器
- ✅ Redis缓存的速率限制（可扩展）
- 文件: `apps/security/utils.py` (RateLimiter类)

### 6. 权限控制系统
- ✅ 5种用户角色：admin, manager, operator, viewer, guest
- ✅ 15+ 系统权限定义
- ✅ 角色层级管理
- ✅ 角色到权限的映射
- ✅ Django装饰器：require_permission, require_role, require_or_higher_role
- ✅ DRF自定义权限类
- 文件: 
  - `apps/authorization/permissions.py`（后端）
  - `frontend/src/composables/useAuthorization.ts`（前端）

### 7. 前端安全工具
- ✅ 密码哈希函数（SHA-256）
- ✅ WebSocket消息签名验证
- ✅ 输入清理和验证
- ✅ XSS防护（escapeHTML）
- ✅ 请求防抖和节流
- ✅ 安全的本地存储
- ✅ 内容安全策略（CSP）支持
- ✅ 环境检测（开发/生产）
- 文件: `frontend/src/utils/security.ts`

### 8. 前端权限管理
- ✅ Composable：useAuthorization
- ✅ 权限检查函数：hasPermission, hasAnyPermission, hasAllPermissions
- ✅ 角色检查函数：hasRole, hasRoleOrHigher
- ✅ 权限指令：v-permission
- ✅ 菜单和操作按钮过滤
- ✅ 角色层级自动检查
- 文件: `frontend/src/composables/useAuthorization.ts`

### 9. 开发环境标准化
- ✅ 一键环境设置脚本
- ✅ Python虚拟环境自动创建
- ✅ 依赖自动安装
- ✅ 数据库自动迁移
- ✅ 环境变量自动配置
- ✅ 日志目录创建
- ✅ 启动脚本（一键前后端）
- ✅ 开发环境设置文档
- 文件: `setup-dev.sh`, `start-services.sh`, `docs/DEV_ENVIRONMENT_SETUP.md`

## 🔐 安全配置项

### 后端安全配置 (.env)
```bash
# Django配置
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,172.28.166.164

# 数据库配置
DATABASE_URL=postgresql://eventpilot:eventpilot@localhost:5432/eventpilot

# Redis配置
REDIS_URL=redis://localhost:6379/0

# CORS配置
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://172.28.166.164:3000

# WebSocket配置
WS_ALLOWED_ORIGINS=http://localhost:3000,http://172.28.166.164:3000

# 安全配置
JWT_SECRET_KEY=eventpilot-jwt-secret-change-in-production
WS_SECRET_KEY=eventpilot-websocket-secret-change-in-production

# 环境标识
ENVIRONMENT=development
```

### 前端安全配置 (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=EventPilot DEBUG
VITE_APP_VERSION=1.0.0-dev
```

## 🔍 如何使用安全功能

### 1. 后端权限控制

在View中使用权限装饰器：

```python
from apps.authorization.permissions import require_permission, require_role

@require_permission('CREATE_EVENT')
def create_event(request):
    # 只有拥有创建事件权限的用户可以访问
    pass

@require_role('admin')
def admin_only_view(request):
    # 只有管理员可以访问
    pass
```

在DRF ViewSet中使用权限类：

```python
from apps.authorization.permissions import EventPilotPermission

class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [EventPilotPermission]
    # ...
```

### 2. 前端权限控制

在组件中使用Composition API：

```typescript
import { useAuthorization } from '@/composables/useAuthorization';

export default {
  setup() {
    const { hasPermission, isAdmin, filterMenu } = useAuthorization();
    
    // 检查权限
    if (hasPermission('CREATE_EVENT')) {
      // 显示创建按钮
    }
    
    // 过滤菜单
    const visibleMenu = filterMenu(menuItems);
    
    return { isAdmin, visibleMenu };
  }
};
```

使用v-permission指令：

```vue
<template>
  <button v-permission="'CREATE_EVENT'">创建事件</button>
</template>
```

### 3. WebSocket消息签名

前端发送签名消息：

```typescript
import { WebSocketSigner } from '@/utils/security';

const signer = new WebSocketSigner('your-secret-key');
const result = await signer.signMessage({ action: 'update', data: {...} });

ws.send(JSON.stringify({
  message: result.message,
  signature: result.signature
}));
```

后端验证消息签名：

```python
from apps.security.utils import WebSocketSecurity

def handle_ws_message(message, signature):
    if WebSocketSecurity.verify_message(message, signature, 'your-secret-key'):
        # 验证通过，处理消息
        process_message(message)
    else:
        # 签名验证失败，拒绝
        reject_message()
```

### 4. 输入清理

后端清理输入：

```python
from apps.security.utils import InputSanitizer

clean_input = InputSanitizer.sanitize_string(user_input, max_length=100)
```

前端清理输入：

```typescript
import { InputSanitizer } from '@/utils/security';

const cleanInput = InputSanitizer.sanitizeString(userInput, 1000);
```

## ⚠️ 生产环境部署要点

### 必须修改的安全配置
1. **修改所有密钥**
   - `SECRET_KEY` - Django密钥
   - `JWT_SECRET_KEY` - JWT签名密钥
   - `WS_SECRET_KEY` - WebSocket签名密钥

2. **禁用调试模式**
   - `DEBUG=False`
   - `ALLOWED_HOSTS` 仅允许生产域名

3. **配置HTTPS**
   - 使用Let's Encrypt获取SSL证书
   - Nginx配置HTTPS
   - 强制HTTPS重定向

4. **数据库安全**
   - 修改数据库用户名和密码
   - 配置数据库防火墙
   - 定期备份

5. **CORS白名单**
   - 仅允许生产域名
   - 移除localhost

6. **禁用开发工具**
   - 移除调试代码
   - 禁用Vue DevTools
   - 禁用详细错误信息

### 推荐的安全配置

```python
# 生产设置建议
DEBUG = False
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # 从环境变量读取
ALLOWED_HOSTS = ['eventpilot.yourdomain.com']

# HTTPS设置
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOWED_ORIGINS = ['https://eventpilot.yourdomain.com']
CORS_ALLOW_CREDENTIALS = True

# 密钥轮换（每月）
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
WS_SECRET_KEY = os.getenv('WS_SECRET_KEY')
```

## 📊 安全增强前后对比

### 密码安全
- ❌ 之前: 明文存储或简单MD5
- ✅ 现在: PBKDF2-SHA256 + 随机盐 + 100,000次迭代

### WebSocket通信
- ❌ 之前: 无验签，易被伪造和重放
- ✅ 现在: HMAC-SHA256签名 + 时间戳验证 + 过期机制

### 权限管理
- ❌ 之前: 基础is_authenticated检查
- ✅ 现在: 5级角色 + 15+权限 + 细粒度控制

### 输入验证
- ❌ 之前: 最小验证，XSS漏洞
- ✅ 现在: 全面的输入清理 + XSS防护

### 速率限制
- ❌ 之前: 无限制，易被Dos攻击
- ✅ 现在: 基于IP的速率限制（100请求/分钟）

### 令牌管理
- ❌ 之前: 简单的会话ID
- ✅ 现在: JWT令牌 + 过期验证 + 签名验证

## 🧪 安全测试建议

### 测试清单
- [ ] 密码登录验证测试
- [ ] JWT令牌过期测试
- [ ] 权限边界测试（角色越权）
- [ ] 输入清理测试（XSS攻击尝试）
- [ ] WebSocket消息伪造测试
- [ ] 重放攻击防护测试
- [ ] 速率限制测试（DoS攻击尝试）
- [ ] CSRF攻击防护测试

### 安全扫描工具
- OWASP ZAP - Web应用安全扫描
- Burp Suite - Web应用安全测试
- SQLMap - SQL注入测试
- Nmap - 端口扫描
- Nessus - 专业漏洞扫描

## 📚 相关文档

- 安全部件实现:
  - 后端安全工具: `apps/security/utils.py`
  - 前端安全工具: `frontend/src/utils/security.ts`
  - 权限控制系统: `apps/authorization/permissions.py`
  - 前端权限管理: `frontend/src/composables/useAuthorization.ts`
  
- 使用指南:
  - 开发环境设置: `docs/DEV_ENVIRONMENT_SETUP.md`
  - 优化方案: `docs/2026-04-30-COMPREHENSIVE_OPTIMIZATION_PLAN.md`
  
- 脚本:
  - 环境设置: `setup-dev.sh`
  - 服务启动: `start-services.sh`

---

EventPilot 安全增强实现完成 | 2026-04-30
所有安全模块已集成到现有架构中，可立即使用！