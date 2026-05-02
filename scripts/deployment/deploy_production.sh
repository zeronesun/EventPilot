#!/usr/bin/env python
"""生产环境启动脚本"""
import os
import sys
import subprocess
import subprocess

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查PostgreSQL
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True)
        if result.returncode == 0:
            print("✅ PostgreSQL已安装")
        else:
            print("❌ PostgreSQL未安装")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL未安装")
        return False
    
    # 检查Redis
    try:
        result = subprocess.run(['redis-cli', '--version'], capture_output=True)
        if result.returncode == 0:
            print("✅ Redis已安装")
        else:
            print("❌ Redis未安装")
            return False
    except FileNotFoundError:
        print("❌ Redis未安装")
        return False
    
    return True


def run_migrations():
    """运行数据库迁移"""
    print("📦 运行数据库迁移...")
    try:
        subprocess.run(['python', 'manage.py', 'migrate', '--noinput'], check=True)
        print("✅ 数据库迁移完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False
    return True


def collect_static():
    """收集静态文件"""
    print("📂 收集静态文件...")
    try:
        subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("✅ 静态文件收集完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 静态文件收集失败: {e}")
        return False
    return True


def restart_services():
    """重启服务"""
    print("🔄 重启服务...")
    try:
        # 重启Gunicorn
        subprocess.run(['sudo', 'systemctl', 'restart', 'gunicorn-eventpilot'])
        print("✅ Gunicorn已重启")
        
        # 重启Nginx
        subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'])
        print("✅ Nginx已重启")
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务重启失败: {e}")
        return False
    return True


def main():
    """主函数"""
    if not check_dependencies():
        sys.exit(1)
    
    print()
    if os.getenv('DJANGO_DEBUG') == 'True':
        print("⚠️  警告：正在开发模式下运行！")
    
    if input("是否继续部署？ (yes/no): ").lower() != 'yes':
        print("❌ 部署已取消")
        sys.exit(0)
    
    if not run_migrations():
        sys.exit(1)
    
    if not collect_static():
        sys.exit(1)
    
    if not restart_services():
        sys.exit(1)
    
    print()
    print("✅ 部署成功！")
    print("🌐 服务运行中: https://yourdomain.com")


if __name__ == '__main__':
    main()