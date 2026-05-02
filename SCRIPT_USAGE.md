# EventPilot 管理脚本使用说明

## 概述

`start.sh` 脚本用于统一管理 EventPilot 项目的启动、停止、重启和监控。

## 脚本位置

项目根目录：`/mnt/d/projects/sourcecode/EventPilot/start.sh`

## 使用方法

### 基本命令

```bash
# 启动所有服务（前端+后端）
./start.sh start

# 停止所有服务
./start.sh stop

# 查看服务状态
./start.sh status

# 重启所有服务
./start.sh restart
```

### 针对特定服务的命令

```bash
# 仅启动前端
./start.sh start frontend

# 仅启动后端
./start.sh start backend

# 仅停止前端
./start.sh stop frontend

# 仅停止后端
./start.sh stop backend

# 重启前端
./start.sh restart frontend

# 重启后端
./start.sh restart backend
```

### 查看日志

```bash
# 查看前端日志（实时）
./start.sh logs frontend

# 查看后端日志（实时）
./start.sh logs backend
```

## 服务地址

- **前端**: http://0.0.0.0:5173 或 http://172.28.166.164:5173
- **后端**: http://0.0.0.0:8000 或 http://172.28.166.164:8000

## 日志文件位置

- **前端日志**: `logs/frontend.log`
- **后端日志**: `logs/backend.log`

## 虚拟环境支持

脚本会自动检测并使用虚拟环境（如果存在）：
- 如果存在 `venv/` 目录，自动使用虚拟环境
- 如果不存在虚拟环境，使用系统 Python

## 特性

1. **统一管理**: 一个脚本控制前后端启动
2. **状态监控**: 实时显示服务运行状态
3. **日志管理**: 自动创建日志目录和文件
4. **进程管理**: 使用 PID 文件跟踪进程
5. **容错处理**: 智能处理重复启动、停止超时等情况
6. **彩色输出**: 清晰区分信息、成功、警告和错误消息

## 验证结果

✅ **所有功能验证通过**

1. **启动功能**
   - 前端启动成功，端口 5173
   - 后端启动成功，端口 8000
   - 虚拟环境检测正常

2. **状态检查**
   - 正确显示前端/后端运行状态
   - 显示进程PID和访问地址

3. **停止功能**
   - 正确停止前端服务
   - 正确停止后端服务
   - 进程确认结束

4. **重启功能**
   - 正确重启单个服务
   - 正确重启所有服务

5. **日志功能**
   - 前端日志正常记录
   - 后端日志正常记录
   - 日志文件自动创建

## 常见问题

### Q: 如何修改服务端口？
A: 编辑 `start.sh` 脚本中的以下变量：
```bash
FRONTEND_PORT=5173
BACKEND_PORT=8000
FRONTEND_HOST="0.0.0.0"
BACKEND_HOST="0.0.0.0"
```

### Q: 如何查看所有可用命令？
A: 运行 `./start.sh` 不带参数，会显示帮助信息。

### Q: 服务启动失败如何排查？
A: 
1. 查看 `logs/frontend.log` 或 `logs/backend.log`
2. 运行 `./start.sh status` 检查状态
3. 使用 `./start.sh logs [service]` 查看实时日志

## 技术细节

- 前端使用 `node node_modules/vite/bin/vite.js` 启动
- 后端使用 `python manage.py runserver` 启动
- 都使用 nohup 后台运行，支持长时间运行
- PID 文件位于项目根目录：`.frontend.pid` 和 `.backend.pid`