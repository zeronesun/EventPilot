#!/bin/bash
# EventPilot 启动/停止/重启脚本
# 支持前端和后端的管理

set -e

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
BACKEND_DIR="${PROJECT_DIR}"

# 配置
FRONTEND_PORT=5173
BACKEND_PORT=8000
FRONTEND_HOST="0.0.0.0"
BACKEND_HOST="0.0.0.0"

# Pid文件
FRONTEND_PID_FILE="${PROJECT_DIR}/.frontend.pid"
BACKEND_PID_FILE="${PROJECT_DIR}/.backend.pid"

# 日志文件
FRONTEND_LOG="${PROJECT_DIR}/logs/frontend.log"
BACKEND_LOG="${PROJECT_DIR}/logs/backend.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建日志目录
mkdir -p "${PROJECT_DIR}/logs"

# 检查进程是否运行
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 停止进程
stop_process() {
    local pid_file=$1
    local name=$2
    
    if [ ! -f "$pid_file" ]; then
        log_warning "${name} 未运行 (没有PID文件)"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        log_warning "${name} 未运行 (进程不存在)"
        rm -f "$pid_file"
        return 1
    fi
    
    log_info "正在停止 ${name} (PID: $pid)..."
    kill "$pid" 2>/dev/null || true
    
    # 等待进程停止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
        if [ $count -ge 10 ]; then
            log_warning "${name} 停止超时，强制终止..."
            kill -9 "$pid" 2>/dev/null || true
            break
        fi
    done
    
    rm -f "$pid_file"
    log_success "${name} 已停止"
}

# 启动前端
start_frontend() {
    cd "${PROJECT_DIR}"
    
    if is_running "$FRONTEND_PID_FILE"; then
        log_warning "前端已在运行中"
        return 0
    fi
    
    log_info "正在启动前端..."
    
    # 检查前端依赖
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        log_info "正在安装前端依赖..."
        cd "${FRONTEND_DIR}"
        npm install || {
            log_error "前端依赖安装失败"
            return 1
        }
    fi
    
    cd "${FRONTEND_DIR}"
    
    # 启动前端
    nohup node node_modules/vite/bin/vite.js --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"
    
    # 等待启动
    sleep 3
    
    if is_running "$FRONTEND_PID_FILE"; then
        log_success "前端启动成功 (PID: $pid, 地址: http://$FRONTEND_HOST:$FRONTEND_PORT)"
        log_info "前端日志: $FRONTEND_LOG"
    else
        log_error "前端启动失败，请检查日志: $FRONTEND_LOG"
        return 1
    fi
}

# 启动后端
start_backend() {
    cd "${PROJECT_DIR}"
    
    if is_running "$BACKEND_PID_FILE"; then
        log_warning "后端已在运行中"
        return 0
    fi
    
    log_info "正在启动后端..."
    
    # 检查端口是否被占用
    if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
        log_warning "端口 $BACKEND_PORT 已被占用，正在清理..."
        lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # 检查是否有虚拟环境
    USE_VENV=false
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        USE_VENV=true
        log_info "使用虚拟环境"
    else
        log_info "未找到虚拟环境，使用系统Python"
    fi
    
    # 激活虚拟环境并检查依赖
    if [ "$USE_VENV" = true ]; then
        source venv/bin/activate
    fi
    
    if ! python -c "import django" 2>/dev/null; then
        log_info "正在安装后端依赖..."
        pip install -r requirements.txt || {
            log_error "后端依赖安装失败"
            if [ "$USE_VENV" = true ]; then
                deactivate
            fi
            return 1
        }
    fi
    
    # 启动后端 - 使用 --noreload 避免进程 ID 变化
    if [ "$USE_VENV" = true ]; then
        nohup venv/bin/python manage.py runserver $BACKEND_HOST:$BACKEND_PORT --noreload > "$BACKEND_LOG" 2>&1 &
    else
        nohup python manage.py runserver $BACKEND_HOST:$BACKEND_PORT --noreload > "$BACKEND_LOG" 2>&1 &
    fi
    
    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"
    
    # 等待启动
    sleep 3
    
    if is_running "$BACKEND_PID_FILE"; then
        log_success "后端启动成功 (PID: $pid, 地址: http://$BACKEND_HOST:$BACKEND_PORT)"
        log_info "后端日志: $BACKEND_LOG"
    else
        log_error "后端启动失败，请检查日志: $BACKEND_LOG"
        if [ "$USE_VENV" = true ]; then
            deactivate
        fi
        return 1
    fi
    
    if [ "$USE_VENV" = true ]; then
        deactivate
    fi
}

# 停止前端
stop_frontend() {
    cd "${PROJECT_DIR}"
    stop_process "$FRONTEND_PID_FILE" "前端"
}

# 停止后端
stop_backend() {
    cd "${PROJECT_DIR}"
    stop_process "$BACKEND_PID_FILE" "后端"
}

# 显示状态
show_status() {
    cd "${PROJECT_DIR}"
    
    echo ""
    echo "=== EventPilot 服务状态 ==="
    echo ""
    
    # 前端状态
    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        log_success "前端: 运行中 (PID: $pid, 地址: http://$FRONTEND_HOST:$FRONTEND_PORT)"
    else
        log_error "前端: 未运行"
    fi
    
    # 后端状态
    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(cat "$BACKEND_PID_FILE")
        log_success "后端: 运行中 (PID: $pid, 地址: http://$BACKEND_HOST:$BACKEND_PORT)"
    else
        log_error "后端: 未运行"
    fi
    
    echo ""
}

# 查看日志
show_logs() {
    local service=$1
    
    cd "${PROJECT_DIR}"
    
    case "$service" in
        frontend)
            if [ -f "$FRONTEND_LOG" ]; then
                tail -f "$FRONTEND_LOG"
            else
                log_error "前端日志文件不存在"
            fi
            ;;
        backend)
            if [ -f "$BACKEND_LOG" ]; then
                tail -f "$BACKEND_LOG"
            else
                log_error "后端日志文件不存在"
            fi
            ;;
        *)
            log_error "未知的日志服务: $service"
            log_usage
            ;;
    esac
}

# 帮助信息
log_usage() {
    echo "用法: $0 {start|stop|restart|status|logs} [service]"
    echo ""
    echo "命令:"
    echo "  start          - 启动所有服务 (前端 + 后端)"
    echo "  stop           - 停止所有服务"
    echo "  restart        - 重启所有服务"
    echo "  status         - 显示服务状态"
    echo "  logs           - 查看日志"
    echo ""
    echo "服务:"
    echo "  frontend       - 仅前端服务"
    echo "  backend        - 仅后端服务"
    echo ""
    echo "示例:"
    echo "  $0 start              # 启动所有服务"
    echo "  $0 start frontend     # 仅启动前端"
    echo "  $0 stop backend       # 仅停止后端"
    echo "  $0 restart frontend   # 重启前端"
    echo "  $0 logs backend       # 查看后端日志"
    echo ""
}

# 主函数
main() {
    cd "${PROJECT_DIR}"
    
    if [ -z "$1" ]; then
        log_usage
        exit 1
    fi
    
    local command=$1
    local service=$2
    
    case "$command" in
        start)
            case "$service" in
                frontend)
                    start_frontend
                    ;;
                backend)
                    start_backend
                    ;;
                "")
                    start_frontend
                    start_backend
                    ;;
                *)
                    log_error "未知的服务: $service"
                    log_usage
                    exit 1
                    ;;
            esac
            ;;
        stop)
            case "$service" in
                frontend)
                    stop_frontend
                    ;;
                backend)
                    stop_backend
                    ;;
                "")
                    stop_frontend
                    stop_backend
                    ;;
                *)
                    log_error "未知的服务: $service"
                    log_usage
                    exit 1
                    ;;
            esac
            ;;
        restart)
            case "$service" in
                frontend)
                    stop_frontend
                    sleep 1
                    start_frontend
                    ;;
                backend)
                    stop_backend
                    sleep 1
                    start_backend
                    ;;
                "")
                    stop_frontend
                    stop_backend
                    sleep 2
                    start_frontend
                    start_backend
                    ;;
                *)
                    log_error "未知的服务: $service"
                    log_usage
                    exit 1
                    ;;
            esac
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$service"
            ;;
        *)
            log_error "未知命令: $command"
            log_usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"