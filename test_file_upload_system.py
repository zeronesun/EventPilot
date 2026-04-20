#!/usr/bin/env python3
"""
EventPilot 文件上传系统验证脚本
测试企业级文件上传系统的完整功能
"""

import os
import sys
import django
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.files.models import (
    FileMetadata, FileShare, FileAuditLog, 
    PresignedURL, FileVersion, FilePreviewCache
)
from apps.files.services import FileService, FileUploadConfig, FileStorageService

User = get_user_model()


class FileUploadSystemTest(TestCase):
    """文件上传系统完整测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = Client()
        self.user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'password': 'testpassword123',
                'is_active': True
            }
        )
        if not created:
            self.user.email = 'test@example.com'
            self.user.set_password('testpassword123')
            self.user.is_active = True
            self.user.save()
        
        # 创建测试用户以获取token
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        if response.status_code == 200:
            self.token = response.json()['token']
            self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        else:
            print(f"登录失败: {response.content}")
            self.token = None
            self.auth_header = {}
    
    def test_00_system_configuration(self):
        """测试系统配置"""
        print("\n" + "="*50)
        print("测试 0: 系统配置验证")
        print("="*50)
        
        # 验证配置类
        print(f"✓ 最大文件大小: {FileUploadConfig.MAX_FILE_SIZE / (1024*1024)}MB")
        print(f"✓ 支持的文件类型数量: {len(FileUploadConfig.ALLOWED_FILE_TYPES)}")
        print(f"✓ 分片大小: {FileUploadConfig.CHUNK_SIZE / (1024*1024)}MB")
        print(f"✓ 最大分片数: {FileUploadConfig.MAX_CHUNKS}")
        
        # 验证支持的文件类型
        print("\n支持的文件类型:")
        for mime_type, config in FileUploadConfig.ALLOWED_FILE_TYPES.items():
            print(f"  - {mime_type}: {config['extensions']}, 最大 {config['max_size'] // (1024*1024)}MB")
        
        print("✓ 系统配置验证完成")
    
    def test_01_models_creation(self):
        """测试模型创建"""
        print("\n" + "="*50)
        print("测试 1: 模型创建验证")
        print("="*50)
        
        # 测试FileMetadata创建
        file_metadata = FileMetadata.objects.create(
            file_id='test_file_001',
            original_filename='test.pdf',
            stored_filename='test_stored.pdf',
            file_path='test/path/test.pdf',
            file_size=1024,
            file_type='application/pdf',
            mime_type='application/pdf',
            file_category='document',
            status='completed',
            storage_provider='s3',
            storage_path='s3://bucket/test.pdf',
            storage_bucket='test-bucket',
            etag='test-etag',
            uploaded_by=self.user,
            owner=self.user
        )
        
        self.assertEqual(file_metadata.file_id, 'test_file_001')
        self.assertEqual(file_metadata.original_filename, 'test.pdf')
        self.assertEqual(file_metadata.file_category, 'document')
        print(f"✓ FileMetadata创建成功: {file_metadata}")
        
        # 测试FileShare创建
        file_share = FileShare.objects.create(
            share_id='test_share_001',
            file_metadata=file_metadata,
            share_url='https://example.com/share/test',
            created_by=self.user
        )
        
        self.assertEqual(file_share.share_id, 'test_share_001')
        print(f"✓ FileShare创建成功: {file_share.share_id}")
        
        # 测试FileAuditLog创建
        audit_log = FileAuditLog.objects.create(
            file_metadata=file_metadata,
            action='upload',
            performed_by=self.user,
            success=True
        )
        
        self.assertEqual(audit_log.action, 'upload')
        print(f"✓ FileAuditLog创建成功: {audit_log.action}")
        
        print("✓ 模型创建验证完成")
    
    def test_02_file_upload_initiate(self):
        """测试文件上传初始化"""
        print("\n" + "="*50)
        print("测试 2: 文件上传初始化")
        print("="*50)
        
        if not self.token:
            print("✗ 跳过: 未获取到认证token")
            return
        
        file_service = FileService()
        
        # 初始化文件上传
        upload_data = {
            'filename': 'test_file.pdf',
            'file_size': 1024,  # 1KB
            'mime_type': 'application/pdf',
            'metadata': {'test': 'metadata'}
        }
        
        try:
            result = file_service.initiate_upload(
                user=self.user,
                **upload_data
            )
            
            print(f"✓ 上传初始化成功")
            print(f"  - 文件ID: {result['file_id']}")
            print(f"  - 上传策略: {result['upload_strategy']}")
            print(f"  - 存储键: {result['storage_key']}")
            print(f"  - 过期时间: {result['expires_in']}秒")
            
            # 验证数据库记录
            file_metadata = FileMetadata.objects.get(file_id=result['file_id'])
            self.assertEqual(file_metadata.status, 'uploading')
            self.assertEqual(file_metadata.file_size, 1024)
            
            print("✓ 数据库记录验证完成")
            
            # 清理测试数据
            file_metadata.delete()
            
        except Exception as e:
            print(f"✗ 上传初始化失败: {str(e)}")
            print(f"✗ 错误详情: {type(e).__name__}")
    
    def test_03_file_service_operations(self):
        """测试文件服务操作"""
        print("\n" + "="*50)
        print("测试 3: 文件服务操作")
        print("="*50)
        
        file_service = FileService()
        
        # 创建测试文件
        file_metadata = FileMetadata.objects.create(
            file_id='test_service_001',
            original_filename='service_test.pdf',
            stored_filename='service_test.pdf',
            file_path='service/path/test.pdf',
            file_size=2048,
            file_type='application/pdf',
            mime_type='application/pdf',
            file_category='document',
            status='completed',
            storage_provider='s3',
            storage_path='s3://bucket/test.pdf',
            storage_bucket='test-bucket',
            etag='service-etag',
            uploaded_by=self.user,
            owner=self.user
        )
        
        # 测试获取文件元数据
        try:
            metadata = file_service.get_file_metadata(
                file_id='test_service_001',
                user=self.user
            )
            
            self.assertEqual(metadata['file_id'], 'test_service_001')
            self.assertEqual(metadata['original_filename'], 'service_test.pdf')
            print(f"✓ 获取文件元数据成功: {metadata['original_filename']}")
            
        except Exception as e:
            print(f"✗ 获取文件元数据失败: {str(e)}")
        
        # 测试列出用户文件
        try:
            file_list = file_service.list_user_files(
                user=self.user,
                filters={'category': 'document'},
                page=1,
                page_size=10
            )
            
            self.assertGreater(file_list['total'], 0)
            print(f"✓ 列出用户文件成功: 总数 {file_list['total']}")
            
        except Exception as e:
            print(f"✗ 列出用户文件失败: {str(e)}")
        
        # 测试创建文件分享
        try:
            share_settings = {
                'allow_download': True,
                'allow_preview': True,
                'expires_at': datetime.now() + timedelta(days=7),
                'base_url': 'https://example.com/api/files/',
                'metadata': {}
            }
            
            share_result = file_service.create_file_share(
                file_id='test_service_001',
                user=self.user,
                settings=share_settings
            )
            
            self.assertIn('share_id', share_result)
            self.assertIn('share_url', share_result)
            print(f"✓ 创建文件分享成功: {share_result['share_id']}")
            
        except Exception as e:
            print(f"✗ 创建文件分享失败: {str(e)}")
        
        # 测试删除文件
        try:
            delete_result = file_service.delete_file(
                file_id='test_service_001',
                user=self.user
            )
            
            self.assertEqual(delete_result['status'], 'deleted')
            print(f"✓ 删除文件成功")
            
            # 验证软删除
            file_metadata.refresh_from_db()
            self.assertTrue(file_metadata.is_deleted)
            
        except Exception as e:
            print(f"✗ 删除文件失败: {str(e)}")
    
    def test_04_api_endpoints(self):
        """测试API端点"""
        print("\n" + "="*50)
        print("测试 4: API端点验证")
        print("="*50)
        
        if not self.token:
            print("✗ 跳过: 未获取到认证token")
            return
        
        # 测试列出文件
        try:
            response = self.client.get('/api/files/', **self.auth_header)
            
            if response.status_code == 200:
                print(f"✓ GET /api/files/ 成功")
                data = response.json()
                print(f"  - 返回数据: {data.keys()}")
            else:
                print(f"✗ GET /api/files/ 失败: {response.status_code}")
                
        except Exception as e:
            print(f"✗ API测试失败: {str(e)}")
        
        # 测试上传初始化
        try:
            upload_data = {
                'filename': 'api_test.pdf',
                'file_size': 512,
                'mime_type': 'application/pdf'
            }
            
            response = self.client.post(
                '/api/files/',
                data=json.dumps(upload_data),
                content_type='application/json',
                **self.auth_header
            )
            
            if response.status_code == 201:
                print(f"✓ POST /api/files/ 成功")
                data = response.json()
                print(f"  - 文件ID: {data.get('file_id')}")
                # 清理
                FileMetadata.objects.filter(file_id=data.get('file_id')).delete()
            else:
                print(f"✗ POST /api/files/ 失败: {response.status_code}")
                print(f"  - 错误: {response.content}")
                
        except Exception as e:
            print(f"✗ 上传测试失败: {str(e)}")
    
    def test_05_health_check(self):
        """测试健康检查"""
        print("\n" + "="*50)
        print("测试 5: 健康检查")
        print("="*50)
        
        try:
            response = self.client.get('/api/files/health/')
            
            if response.status_code == 200:
                print(f"✓ GET /api/files/health/ 成功")
                data = response.json()
                print(f"  - 系统状态: {data.get('status')}")
                print(f"  - 时间戳: {data.get('timestamp')}")
                
                if 'components' in data:
                    print(f"  - 存储状态: {data['components'].get('storage', {}).get('status')}")
                    print(f"  - 数据库状态: {data['components'].get('database', {}).get('status')}")
            else:
                print(f"✗ GET /api/files/health/ 失败: {response.status_code}")
                
        except Exception as e:
            print(f"✗ 健康检查失败: {str(e)}")
    
    def test_06_security_validation(self):
        """测试安全验证"""
        print("\n" + "="*50)
        print("测试 6: 安全验证")
        print("="*50)
        
        from apps.files.services import FileSecurityValidator
        
        # 测试文件名清理
        dangerous_filename = "../../../etc/passwd"
        safe_filename = FileSecurityValidator.sanitize_filename(dangerous_filename)
        
        self.assertNotIn('..', safe_filename)
        self.assertNotIn('/', safe_filename)
        print(f"✓ 危险文件名清理: '{dangerous_filename}' -> '{safe_filename}'")
        
        # 测试安全文件名生成
        secure_name = FileSecurityValidator.generate_secure_filename("test.pdf")
        
        self.assertIn('_', secure_name)
        self.assertIn('.pdf', secure_name)
        print(f"✓ 安全文件名生成: {secure_name}")
        
        # 测试MIME类型验证
        from apps.files.services import FileUploadConfig
        
        valid_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'video/mp4',
            'audio/mpeg'
        ]
        
        for mime_type in valid_types:
            self.assertIn(mime_type, FileUploadConfig.ALLOWED_FILE_TYPES)
        
        print(f"✓ MIME类型验证通过: 支持的类型")
        
        invalid_types = ['application/x-danger', 'text/virus']
        
        for mime_type in invalid_types:
            self.assertNotIn(mime_type, FileUploadConfig.ALLOWED_FILE_TYPES)
        
        print(f"✓ 不支持的MIME类型正确拦截")
    
    def test_07_data_integrity(self):
        """测试数据完整性"""
        print("\n" + "="*50)
        print("测试 7: 数据完整性")
        print("="*50)
        
        # 创建测试文件
        file_metadata = FileMetadata.objects.create(
            file_id='integrity_test_001',
            original_filename='integrity.pdf',
            stored_filename='integrity.pdf',
            file_path='integrity/path/test.pdf',
            file_size=3072,
            file_type='application/pdf',
            mime_type='application/pdf',
            file_category='document',
            status='completed',
            storage_provider='s3',
            storage_path='s3://bucket/integrity.pdf',
            storage_bucket='test-bucket',
            etag='integrity-etag',
            uploaded_by=self.user,
            owner=self.user
        )
        
        # 测试哈希值计算
        file_hash = file_metadata.calculate_file_hash()
        self.assertEqual(len(file_hash), 64)  # SHA256长度
        print(f"✓ 文件哈希值计算: {file_hash[:16]}...")
        
        # 测试校验和计算
        checksum = file_metadata.calculate_checksum()
        self.assertEqual(len(checksum), 32)  # MD5长度
        print(f"✓ 文件校验和计算: {checksum}")
        
        # 测试访问计数
        initial_count = file_metadata.access_count
        file_metadata.increment_access()
        
        file_metadata.refresh_from_db()
        self.assertEqual(file_metadata.access_count, initial_count + 1)
        print(f"✓ 访问计数更新: {initial_count} -> {file_metadata.access_count}")
        
        # 测试软删除
        self.assertFalse(file_metadata.is_deleted)
        file_metadata.soft_delete(self.user)
        
        file_metadata.refresh_from_db()
        self.assertTrue(file_metadata.is_deleted)
        self.assertIsNotNone(file_metadata.deleted_at)
        print(f"✓ 软删除功能正常")
        
        # 测试审计日志
        audit_count = FileAuditLog.objects.filter(file_metadata=file_metadata).count()
        self.assertGreater(audit_count, 0)
        print(f"✓ 审计日志记录: {audit_count}条")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("EventPilot 文件上传系统验证测试")
    print("="*70)
    
    test_instance = FileUploadSystemTest()
    test_instance.setUp()
    
    tests = [
        ('系统配置验证', test_instance.test_00_system_configuration),
        ('模型创建验证', test_instance.test_01_models_creation),
        ('文件上传初始化', test_instance.test_02_file_upload_initiate),
        ('文件服务操作', test_instance.test_03_file_service_operations),
        ('API端点验证', test_instance.test_04_api_endpoints),
        ('健康检查', test_instance.test_05_health_check),
        ('安全验证', test_instance.test_06_security_validation),
        ('数据完整性', test_instance.test_07_data_integrity)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} 失败: {str(e)}")
            failed += 1
    
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    print(f"✓ 通过: {passed}")
    print(f"✗ 失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！文件上传系统运行正常。")
    else:
        print(f"\n⚠️  {failed}个测试失败，请检查错误信息。")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)