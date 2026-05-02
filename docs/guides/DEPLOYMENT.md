# EventPilot 部署指南

## 概述

本指南介绍如何在不同环境中部署 EventPilot 系统。

## 目录

- [系统要求](#系统要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [配置管理](#配置管理)
- [监控与维护](#监控与维护)
- [常见问题](#常见问题)

## 系统要求

### 最低硬件要求

- **CPU**: 2核或更高
- **内存**: 4GB RAM (8GB推荐)
- **存储**: 20GB 可用空间

### 软件要求

- **Python**: 3.11+
- **Node.js**: 18.0+
- **数据库**: PostgreSQL 15+ (生产环境)
- **缓存**: Redis 7+
- **Web服务器**: Nginx
- **应用服务器**: Gunicorn

## 开发环境部署

### 快速开始

1. **克隆项目**
   ```bash
   git clone <repository-url> EventPilot
   cd EventPilot
   ```

2. **环境配置**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件配置环境变量
   ```

3. **运行一键设置脚本**
   ```bash
   chmod +x setup-dev.sh
   ./setup-dev.sh
   ```

4. **启动服务**
   ```bash
   ./start.sh start
   ```

### 手动设置

详见 [脚本使用指南](SCRIPT_USAGE.md)

## 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3.11 python3-pip python3-venv nginx postgresql redis-server
```

### 2. 数据库配置

```bash
# 创建数据库用户
sudo -u postgres createuser -P eventpilot

# 创建数据库
sudo -u postgres createdb -O eventpilot eventpilot

# 配置 PostgreSQL 认证
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 添加：local all eventpilot md5
```

### 3. 应用部署

```bash
# 创建应用目录
sudo mkdir -p /opt/eventpilot
sudo chown $USER:$USER /opt/eventpilot

# 复制代码到生产目录
cp -r EventPilot/* /opt/eventpilot/

# 创建虚拟环境
cd /opt/eventpilot
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 4. 前端构建

```bash
cd /opt/eventpilot/frontend
npm install
npm run build
```

### 5. 配置文件

创建生产环境配置 `/opt/eventpilot/.env.production`：

```bash
# 数据库配置
DATABASE_URL=postgresql://eventpilot:password@localhost/eventpilot

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# WebSocket 配置
WS_ADDRESS=ws://your-domain.com/ws/
```

### 6. 数据库迁移

```bash
cd /opt/eventpilot
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 7. Gunicorn 配置

创建 Systemd 服务 `/etc/systemd/system/eventpilot.service`：

```ini
[Unit]
Description=EventPilot backend service
After=network.target postgresql.service

[Service]
Type=notify
User=eventpilot
Group=eventpilot
WorkingDirectory=/opt/eventpilot
Environment="PATH=/opt/eventpilot/venv/bin"
ExecStart=/opt/eventpilot/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/eventpilot/access.log \
    --error-logfile /var/log/eventpilot/error.log \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 8. Nginx 配置

创建配置文件 `/etc/nginx/sites-available/eventpilot`：

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 静态文件
    location /static/ {
        alias /opt/eventpilot/staticfiles/;
        expires 30d;
    }

    # 前端文件
    location / {
        root /opt/eventpilot/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/eventpilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. 启动服务

```bash
# 创建日志目录
sudo mkdir -p /var/log/eventpilot
sudo chown eventpilot:eventpilot /var/log/eventpilot

# 启动后端服务
sudo systemctl enable eventpilot
sudo systemctl start eventpilot

# 检查状态
sudo systemctl status eventpilot
```

### 10. SSL 配置

使用 Let's Encrypt：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

## 配置管理

### 环境变量

所有环境变量都通过 `.env` 文件管理：

- `.env.development` - 开发环境
- `.env.production` - 生产环境
- `.env.example` - 模板文件

### 敏感信息保护

- 不要将 `.env.production` 提交到版本控制
- 使用适当的权限设置：`chmod 600 .env.production`
- 考虑使用密钥管理服务（如 AWS Secrets Manager）

## 监控与维护

### 日志管理

```bash
# 查看应用日志
sudo journalctl -u eventpilot -f

# 查看错误日志
sudo tail -f /var/log/eventpilot/error.log

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/access.log
```

### 性能监控

推荐工具：
- **Prometheus + Grafana**: 系统监控和可视化
- **Sentry**: 错误追踪和报警
- **APM 工具**: 如 Datadog, New Relic

### 备份策略

```bash
# 数据库备份脚本
#!/bin/bash
BACKUP_DIR="/backups/eventpilot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -U eventpilot eventpilot | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 保留最近7天的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

### 更新部署

```bash
# 1. 备份数据库
pg_dump -U eventpilot eventpilot > backup.sql

# 2. 拉取最新代码
cd /opt/eventpilot
git pull

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 更新依赖
pip install -r requirements.txt

# 5. 运行迁移
python manage.py migrate

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 构建前端
cd frontend
npm install
npm run build
cd ..

# 8. 重启服务
sudo systemctl restart eventpilot
```

## 常见问题

### Q: 服务无法启动

**检查清单：**
1. 确认 PostgreSQL 和 Redis 正在运行
2. 检查 `.env` 配置是否正确
3. 查看日志：`sudo journalctl -u eventpilot -n 50`

### Q: WebSocket 连接失败

**解决方案：**
1. 确认 Nginx WebSocket 配置正确
2. 检查防火墙是否阻止 WebSocket
3. 验证 WS_ADDRESS 配置

### Q: 性能问题

**优化建议：**
1. 增加数据库索引
2. 配置 Redis 缓存
3. 调整 Gunicorn workers 数量
4. 使用 CDN 分发静态文件

### Q: 内存使用过高

**排查步骤：**
1. 检查进程：`ps aux | grep eventpilot`
2. 分析慢查询日志
3. 优化数据库查询
4. 考虑使用连接池

## 安全最佳实践

1. **定期更新**: 保持系统和依赖包最新
2. **访问控制**: 限制数据库和 Redis 的网络访问
3. **防火墙规则**: 只开放必要的端口
4. **HTTPS 强制**: 所有通信使用 SSL/TLS
5. **定期备份**: 自动化备份策略
6. **监控报警**: 设置异常行为检测

## 扩展阅读

- [系统架构文档](../architecture/ARCHITECTURE.md)
- [开发文档](../development/)
- [使用指南](../guides/SCRIPT_USAGE.md)
- [测试方案](../TESTING_PLAN.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-05-03  
**维护者**: EventPilot 团队
