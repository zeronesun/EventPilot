#!/usr/bin/env python3
"""
EventPilot 数据库迁移和模型初始化脚本
为文件上传系统创建必要的数据库表
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.db import connection
from apps.files.models import (
    FileMetadata, FileShare, FileAuditLog, 
    PresignedURL, FileVersion, FilePreviewCache
)


def create_database_tables():
    """创建文件上传系统所需的数据库表"""
    
    print("EventPilot 文件上传系统数据库表初始化")
    print("=" * 50)
    
    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False
    
    # 检查并创建表
    tables_to_create = [
        ('files_metadata', FileMetadata),
        ('files_presigned_urls', PresignedURL),
        ('files_shares', FileShare),
        ('files_audit_logs', FileAuditLog),
        ('files_versions', FileVersion),
        ('files_preview_cache', FilePreviewCache)
    ]
    
    created_tables = []
    existing_tables = []
    
    for table_name, model in tables_to_create:
        try:
            # 检查表是否存在
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)
                result = cursor.fetchone()
                
                if result:
                    existing_tables.append(table_name)
                    print(f"○ 表 {table_name} 已存在")
                else:
                    # 使用Django的makemigrations命令来创建表
                    print(f"△ 表 {table_name} 不存在，需要创建")
                    created_tables.append(table_name)
        
        except Exception as e:
            print(f"✗ 检查表 {table_name} 时出错: {str(e)}")
    
    print(f"\n已存在表: {len(existing_tables)}")
    print(f"需要创建表: {len(created_tables)}")
    
    if created_tables:
        print("\n请运行以下命令来创建缺失的表:")
        print("  python manage.py makemigrations files")
        print("  python manage.py migrate files")
    else:
        print("\n✓ 所有必要的表都已存在！")
    
    return True


def verify_models():
    """验证模型配置"""
    
    print("\n模型配置验证")
    print("=" * 50)
    
    models_to_verify = [
        ('FileMetadata', FileMetadata),
        ('FileShare', FileShare),
        ('FileAuditLog', FileAuditLog),
        ('PresignedURL', PresignedURL),
        ('FileVersion', FileVersion),
        ('FilePreviewCache', FilePreviewCache)
    ]
    
    for model_name, model in models_to_verify:
        try:
            # 尝试访问模型的meta信息
            meta = model._meta
            db_table = meta.db_table
            fields = [field.name for field in meta.fields]
            
            print(f"✓ {model_name}:")
            print(f"  - 表名: {db_table}")
            print(f"  - 字段数: {len(fields)}")
            print(f"  - 字段: {', '.join(fields[:5])}...")
            
        except Exception as e:
            print(f"✗ {model_name} 验证失败: {str(e)}")
            return False
    
    return True


def check_dependencies():
    """检查依赖项"""
    
    print("\n依赖项检查")
    print("=" * 50)
    
    # 检查boto3
    try:
        import boto3
        print(f"✓ boto3 版本: {boto3.__version__}")
    except ImportError:
        print("✗ boto3 未安装，请运行: pip install boto3")
        return False
    
    # 检查其他必要模块
    dependencies = [
        ('django', None),
        ('djangorestframework', None),
        ('argon2', 'argon2-cffi'),
    ]
    
    missing = []
    
    for module, package in dependencies:
        try:
            if package:
                __import__(package)
                print(f"✓ {package}")
            else:
                __import__(module)
                print(f"✓ {module}")
        except ImportError:
            print(f"✗ {package or module} 未安装")
            missing.append(package or module)
    
    if missing:
        print(f"\n请安装缺失的依赖:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """主函数"""
    
    print("EventPilot 文件上传系统初始化检查")
    print("=" * 70)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 验证模型
    if not verify_models():
        return False
    
    # 创建数据库表
    if not create_database_tables():
        return False
    
    print("\n" + "=" * 70)
    print("初始化检查完成！")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)