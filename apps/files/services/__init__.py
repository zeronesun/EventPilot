"""
企业级文件服务
提供完整的文件上传、下载、管理和安全功能
"""

import os
import uuid
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import mimetypes
import time
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.core.exceptions import ValidationError, PermissionDenied

User = get_user_model()

# 延迟导入模型以避免循环导入
from ..models import (
    FileMetadata, PresignedURL, FileShare, FileAuditLog, 
    FileVersion, FilePreviewCache
)

logger = logging.getLogger(__name__)


class FileUploadConfig:
    """
    文件上传配置
    集中管理上传相关的配置参数
    """
    
    # 文件类型白名单（支持魔数检查）
    ALLOWED_FILE_TYPES = {
        # 文档类型
        'application/pdf': {'extensions': ['.pdf'], 'max_size': 50 * 1024 * 1024},
        'application/msword': {'extensions': ['.doc'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'extensions': ['.docx'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.ms-excel': {'extensions': ['.xls'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {'extensions': ['.xlsx'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.ms-powerpoint': {'extensions': ['.ppt'], 'max_size': 20 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': {'extensions': ['.pptx'], 'max_size': 20 * 1024 * 1024},
        'text/plain': {'extensions': ['.txt'], 'max_size': 5 * 1024 * 1024},
        'text/csv': {'extensions': ['.csv'], 'max_size': 5 * 1024 * 1024},
        
        # 图片类型
        'image/jpeg': {'extensions': ['.jpg', '.jpeg'], 'max_size': 20 * 1024 * 1024},
        'image/png': {'extensions': ['.png'], 'max_size': 20 * 1024 * 1024},
        'image/gif': {'extensions': ['.gif'], 'max_size': 10 * 1024 * 1024},
        'image/webp': {'extensions': ['.webp'], 'max_size': 20 * 1024 * 1024},
        'image/svg+xml': {'extensions': ['.svg'], 'max_size': 5 * 1024 * 1024},
        'image/bmp': {'extensions': ['.bmp'], 'max_size': 10 * 1024 * 1024},
        
        # 视频类型
        'video/mp4': {'extensions': ['.mp4'], 'max_size': 500 * 1024 * 1024},
        'video/quicktime': {'extensions': ['.mov'], 'max_size': 500 * 1024 * 1024},
        'video/avi': {'extensions': ['.avi'], 'max_size': 200 * 1024 * 1024},
        'video/webm': {'extensions': ['.webm'], 'max_size': 200 * 1024 * 1024},
        
        # 音频类型
        'audio/mpeg': {'extensions': ['.mp3'], 'max_size': 50 * 1024 * 1024},
        'audio/wav': {'extensions': ['.wav'], 'max_size': 50 * 1024 * 1024},
        'audio/ogg': {'extensions': ['.ogg'], 'max_size': 50 * 1024 * 1024},
        'audio/flac': {'extensions': ['.flac'], 'max_size': 50 * 1024 * 1024},
        
        # 压缩包类型
        'application/zip': {'extensions': ['.zip'], 'max_size': 200 * 1024 * 1024},
        'application/x-rar-compressed': {'extensions': ['.rar'], 'max_size': 200 * 1024 * 1024},
        'application/x-7z-compressed': {'extensions': ['.7z'], 'max_size': 200 * 1024 * 1024},
        'application/x-tar': {'extensions': ['.tar'], 'max_size': 200 * 1024 * 1024},
        'application/gzip': {'extensions': ['.gz'], 'max_size': 200 * 1024 * 1024},
    }
    
    # 文件魔数签名（用于扩展类型验证）
    FILE_MAGIC_NUMBERS = {
        b'\x25\x50\x44\x46': 'application/pdf',
        b'\x50\x4b\x03\x04': 'application/zip',
        b'\x52\x61\x72\x21': 'application/x-rar-compressed',
        b'\x37\x7a\xbc\xaf': 'application/x-7z-compressed',
        b'\x1f\x8b': 'application/gzip',
        b'\xff\xd8\xff': 'image/jpeg',
        b'\x89\x50\x4e\x47': 'image/png',
        b'\x47\x49\x46\x38': 'image/gif',
        b'\x42\x4d': 'image/bmp',
        b'\x3c\x73\x76\x67': 'image/svg+xml',
    }
    
    # 预签名URL配置
    PRESIGNED_URL_TTL = {
        'upload': 900,      # 15分钟 - 上传URL
        'download': 3600,   # 1小时 - 下载URL
        'preview': 7200,    # 2小时 - 预览URL
    }
    
    # 存储配置
    DEFAULT_STORAGE_BUCKET = os.getenv('S3_BUCKET_NAME', 'eventpilot-files')
    STORAGE_REGION = os.getenv('AWS_REGION', 'us-east-1')
    STORAGE_PATH_PREFIX = os.getenv('STORAGE_PATH_PREFIX', 'files')
    
    # 上传限制
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB 总大小限制
    MAX_CONCURRENT_UPLOADS = 5           # 最大并发上传数
    
    # 分片上传配置
    CHUNK_SIZE = 8 * 1024 * 1024         # 8MB 分片大小
    MAX_CHUNKS = 100                     # 最大分片数量 - 支持最大800MB文件
    
    # 缓存配置
    CACHE_TIMEOUTS = {
        'presigned_url': 900,      # 15分钟
        'file_metadata': 3600,     # 1小时
        'preview_cache': 86400,    # 24小时
        'share_link': 7200,        # 2小时
    }


class FileSecurityValidator:
    """
    文件安全验证器
    执行各种安全检查和验证
    """
    
    @staticmethod
    def validate_file_type(file_obj: UploadedFile, expected_mime_type: str = None) -> Tuple[bool, str]:
        """
        验证文件类型（包括魔数检查）
        
        Args:
            file_obj: 上传的文件对象
            expected_mime_type: 期望的MIME类型
            
        Returns:
            Tuple[是否通过验证, 错误消息]
        """
        try:
            # 检查MIME类型
            mime_type = file_obj.content_type
            if mime_type not in FileUploadConfig.ALLOWED_FILE_TYPES:
                return False, f"不支持的文件类型: {mime_type}"
            
            # 检查文件扩展名
            filename = file_obj.name.lower()
            allowed_extensions = FileUploadConfig.ALLOWED_FILE_TYPES[mime_type]['extensions']
            
            if not any(filename.endswith(ext) for ext in allowed_extensions):
                return False, f"文件扩展名不匹配，期望: {', '.join(allowed_extensions)}"
            
            # 检查文件大小
            max_size = FileUploadConfig.ALLOWED_FILE_TYPES[mime_type]['max_size']
            if file_obj.size > max_size:
                return False, f"文件大小超过限制 ({max_size / (1024*1024)}MB)"
            
            # 验证魔数（如果文件足够大）
            if file_obj.size > 4:
                file_obj.seek(0)
                file_header = file_obj.read(4)
                file_obj.seek(0)
                
                for magic_number, expected_mime in FileUploadConfig.FILE_MAGIC_NUMBERS.items():
                    if file_header.startswith(magic_number):
                        if expected_mime_type and expected_mime != expected_mime:
                            return False, f"文件内容与扩展名不匹配"
                        return True, ""
            
            return True, ""
            
        except Exception as e:
            logger.error(f"文件类型验证错误: {str(e)}")
            return False, f"文件类型验证失败: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除危险的字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的安全文件名
        """
        # 移除路径分隔符和特殊字符
        safe_filename = filename.replace('/', '').replace('\\', '').replace('..', '')
        
        # 移除控制字符
        safe_filename = ''.join(c for c in safe_filename if c.isprintable() and c not in '<>:"|?*\x00-\x1f')
        
        # 限制长度
        if len(safe_filename) > 255:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:255-len(ext)] + ext
        
        return safe_filename.strip()
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """
        生成安全的存储文件名
        
        Args:
            original_filename: 原始文件名
            
        Returns:
            安全的存储文件名
        """
        safe_name = FileSecurityValidator.sanitize_filename(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_id = uuid.uuid4().hex[:8]
        
        name, ext = os.path.splitext(safe_name)
        return f"{timestamp}_{random_id}_{name}{ext}"


class FileStorageService:
    """
    文件存储服务
    负责与存储后端（S3）的交互
    """
    
    def __init__(self):
        """初始化存储服务连接"""
        try:
            # 初始化S3客户端
            self.s3_client = boto3.client(
                's3',
                region_name=FileUploadConfig.STORAGE_REGION,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            self.bucket_name = FileUploadConfig.DEFAULT_STORAGE_BUCKET
            logger.info(f"存储服务初始化成功: {self.bucket_name}")
        except Exception as e:
            logger.error(f"存储服务初始化失败: {str(e)}")
            raise
    
    def generate_presigned_upload_url(
        self, 
        key: str, 
        file_size: int,
        mime_type: str,
        expires_in: int = None
    ) -> str:
        """
        生成预签名上传URL
        
        Args:
            key: 存储键名
            file_size: 文件大小
            mime_type: MIME类型
            expires_in: 过期时间（秒）
            
        Returns:
            预签名URL
        """
        try:
            expires_in = expires_in or FileUploadConfig.PRESIGNED_URL_TTL['upload']
            
            # 生成预签名URL
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': mime_type,
                    'ContentLength': file_size,
                },
                ExpiresIn=expires_in
            )
            
            logger.info(f"生成预签名上传URL: {key}")
            return url
            
        except ClientError as e:
            logger.error(f"生成预签名URL失败: {str(e)}")
            raise
    
    def generate_presigned_download_url(
        self, 
        key: str, 
        expires_in: int = None
    ) -> str:
        """
        生成预签名下载URL
        
        Args:
            key: 存储键名
            expires_in: 过期时间（秒）
            
        Returns:
            预签名URL
        """
        try:
            expires_in = expires_in or FileUploadConfig.PRESIGNED_URL_TTL['download']
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ResponseContentDisposition': 'attachment'
                },
                ExpiresIn=expires_in
            )
            
            logger.info(f"生成预签名下载URL: {key}")
            return url
            
        except ClientError as e:
            logger.error(f"生成下载URL失败: {str(e)}")
            raise
    
    def initiate_multipart_upload(
        self, 
        key: str, 
        mime_type: str, 
        file_size: int
    ) -> str:
        """
        初始化分片上传
        
        Args:
            key: 存储键名
            mime_type: MIME类型
            file_size: 文件大小
            
        Returns:
            上传ID
        """
        try:
            response = self.s3_client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                ContentType=mime_type,
            )
            
            upload_id = response['UploadId']
            logger.info(f"初始化分片上传: {key}, upload_id={upload_id}")
            return upload_id
            
        except ClientError as e:
            logger.error(f"初始化分片上传失败: {str(e)}")
            raise
    
    def generate_presigned_upload_part_url(
        self, 
        key: str, 
        part_number: int, 
        upload_id: str
    ) -> str:
        """
        生成分片上传的预签名URL
        
        Args:
            key: 存储键名
            part_number: 分片编号
            upload_id: 上传ID
            
        Returns:
            预签名URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'PartNumber': part_number,
                    'UploadId': upload_id,
                },
                ExpiresIn=FileUploadConfig.PRESIGNED_URL_TTL['upload']
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"生成分片上传URL失败: {str(e)}")
            raise
    
    def complete_multipart_upload(
        self, 
        key: str, 
        upload_id: str, 
        parts: List[Dict[str, Any]]
    ) -> str:
        """
        完成分片上传
        
        Args:
            key: 存储键名
            upload_id: 上传ID
            parts: 分片列表 [{"PartNumber": 1, "ETag": "xxx"}, ...]
            
        Returns:
            文件的ETag
        """
        try:
            response = self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            etag = response['ETag'].replace('"', '')
            logger.info(f"完成分片上传: {key}, etag={etag}")
            return etag
            
        except ClientError as e:
            logger.error(f"完成分片上传失败: {str(e)}")
            self.abort_multipart_upload(key, upload_id)
            raise
    
    def abort_multipart_upload(self, key: str, upload_id: str):
        """
        取消分片上传
        
        Args:
            key: 存储键名
            upload_id: 上传ID
        """
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=key,
                UploadId=upload_id
            )
            logger.info(f"取消分片上传: {key}")
        except ClientError as e:
            logger.error(f"取消分片上传失败: {str(e)}")
    
    def delete_file(self, key: str):
        """
        删除文件
        
        Args:
            key: 存储键名
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"删除文件: {key}")
        except ClientError as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise
    
    def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            key: 存储键名
            
        Returns:
            文件元数据
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return {
                'size': response['ContentLength'],
                'etag': response['ETag'].replace('"', ''),
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
            }
        except ClientError as e:
            logger.error(f"获取文件元数据失败: {str(e)}")
            raise


class FileService:
    """
    文件服务核心类
    提供完整的文件管理功能
    """
    
    def __init__(self):
        """初始化文件服务"""
        self.storage_service = FileStorageService()
        self.cache_timeout = FileUploadConfig.CACHE_TIMEOUTS
    
    def _generate_storage_key(self, user_id: str, filename: str) -> str:
        """
        生成存储键名
        
        Args:
            user_id: 用户ID
            filename: 文件名
            
        Returns:
            存储键名
        """
        timestamp = datetime.now().strftime('%Y/%m/%d')
        secure_filename = FileSecurityValidator.generate_secure_filename(filename)
        return f"{FileUploadConfig.STORAGE_PATH_PREFIX}/{user_id}/{timestamp}/{secure_filename}"
    
    def _calculate_file_hashes(self, file_path: str) -> Tuple[str, str]:
        """
        计算文件的哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[SHA256哈希, MD5校验和]
        """
        sha256_hash = hashlib.sha256()
        md5_hash = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                md5_hash.update(chunk)
        
        return sha256_hash.hexdigest(), md5_hash.hexdigest()
    
    def _determine_file_category(self, mime_type: str) -> str:
        """
        确定文件分类
        
        Args:
            mime_type: MIME类型
            
        Returns:
            文件分类
        """
        if mime_type.startswith('image/'):
            return FileMetadata.FileCategory.IMAGE
        elif mime_type.startswith('video/'):
            return FileMetadata.FileCategory.VIDEO
        elif mime_type.startswith('audio/'):
            return FileMetadata.FileCategory.AUDIO
        elif mime_type in ['application/pdf', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'text/plain', 'text/csv']:
            return FileMetadata.FileCategory.DOCUMENT
        elif mime_type in ['application/zip', 'application/x-rar-compressed', 
                          'application/x-7z-compressed']:
            return FileMetadata.FileCategory.ARCHIVE
        else:
            return FileMetadata.FileCategory.OTHER
    
    def _verify_upload_permission(self, user: User, file_size: int) -> Tuple[bool, str]:
        """
        验证上传权限
        
        Args:
            user: 用户
            file_size: 文件大小
            
        Returns:
            Tuple[是否有权限, 错误消息]
        """
        try:
            # 检查用户状态
            if not user.is_active:
                return False, "用户账户已被禁用"
            
            # 检查总文件大小限制
            current_quota = FileMetadata.objects.filter(
                uploaded_by=user,
                is_deleted=False
            ).aggregate(Sum('file_size'))['file_size__sum'] or 0
            
            available_quota = FileUploadConfig.MAX_FILE_SIZE - current_quota
            if file_size > available_quota:
                return False, f"超出存储配额限制，可用: {available_quota // (1024*1024)}MB"
            
            # 检查并发上传限制
            active_uploads = FileMetadata.objects.filter(
                uploaded_by=user,
                status__in=['uploading', 'processing']
            ).count()
            
            if active_uploads >= FileUploadConfig.MAX_concurrentUploads:
                return False, f"超过并发上传限制 ({FileUploadConfig.MAX_concurrentUploads})"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"权限验证错误: {str(e)}")
            return False, f"权限验证失败: {str(e)}"
    
    def _log_file_audit(self, file_metadata: FileMetadata, action: str, user: User, 
                       success: bool, details: dict = None):
        """
        记录文件审计日志
        
        Args:
            file_metadata: 文件元数据
            action: 操作类型
            user: 用户
            success: 是否成功
            details: 详细信息
        """
        try:
            FileAuditLog.objects.create(
                file_metadata=file_metadata,
                action=action,
                performed_by=user,
                success=success,
                action_details=details or {},
                metadata={
                    'timestamp': timezone.now().isoformat(),
                    'file_id': str(file_metadata.file_id)
                }
            )
        except Exception as e:
            logger.error(f"审计日志记录失败: {str(e)}")
    
    @transaction.atomic
    def initiate_upload(
        self,
        user: User,
        filename: str,
        file_size: int,
        mime_type: str,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        初始化文件上传
        
        Args:
            user: 用户
            filename: 文件名
            file_size: 文件大小
            mime_type: MIME类型
            metadata: 额外元数据
            
        Returns:
            上传初始化信息
        """
        try:
            # 安全检查
            if file_size > FileUploadConfig.MAX_FILE_SIZE:
                raise ValidationError(f"文件大小超过限制 ({FileUploadConfig.MAX_FILE_SIZE // (1024*1024)}MB)")
            
            permissions_ok, perm_error = self._verify_upload_permission(user, file_size)
            if not permissions_ok:
                raise PermissionDenied(perm_error)
            
            # 验证文件类型
            is_valid, validation_error = self._validate_mime_type(mime_type)
            if not is_valid:
                raise ValidationError(validation_error)
            
            # 生成文件元数据
            file_id = f"file_{uuid.uuid4().hex[:16]}"
            storage_key = self._generate_storage_key(str(user.id), filename)
            
            # 创建文件元数据记录
            file_metadata = FileMetadata.objects.create(
                file_id=file_id,
                original_filename=FileSecurityValidator.sanitize_filename(filename),
                stored_filename=FileSecurityValidator.generate_secure_filename(filename),
                file_path=storage_key,
                file_size=file_size,
                file_type=mime_type,
                mime_type=mime_type,
                file_category=self._determine_file_category(mime_type),
                status='uploading',
                storage_provider='s3',
                storage_path=storage_key,
                storage_bucket=self.storage_service.bucket_name,
                uploaded_by=user,
                owner=user,
                metadata=metadata or {},
                visibility='private'
            )
            
            # 决定上传方式
            if file_size <= FileUploadConfig.CHUNK_SIZE:
                # 小文件 - 直接上传
                presigned_url = self.storage_service.generate_presigned_upload_url(
                    key=storage_key,
                    file_size=file_size,
                    mime_type=mime_type
                )
                upload_strategy = 'direct'
            else:
                # 大文件 - 分片上传
                upload_id = self.storage_service.initiate_multipart_upload(
                    key=storage_key,
                    mime_type=mime_type,
                    file_size=file_size
                )
                presigned_url = None
                upload_strategy = 'multipart'
            
            # 记录审计日志
            self._log_file_audit(
                file_metadata=file_metadata,
                action='upload',
                user=user,
                success=True,
                details={
                    'filename': filename,
                    'file_size': file_size,
                    'mime_type': mime_type,
                    'strategy': upload_strategy
                }
            )
            
            return {
                'file_id': file_id,
                'upload_strategy': upload_strategy,
                'presigned_url': presigned_url,
                'storage_key': storage_key,
                'upload_id': upload_id if upload_strategy == 'multipart' else None,
                'chunk_size': FileUploadConfig.CHUNK_SIZE,
                'max_chunks': FileUploadConfig.MAX_CHUNKS,
                'expires_in': FileUploadConfig.PRESIGNED_URL_TTL['upload']
            }
            
        except Exception as e:
            logger.error(f"上传初始化失败: {str(e)}")
            raise
    
    def _validate_mime_type(self, mime_type: str) -> Tuple[bool, str]:
        """验证MIME类型"""
        if mime_type not in FileUploadConfig.ALLOWED_FILE_TYPES:
            return False, f"不支持的文件类型: {mime_type}"
        return True, ""
    
    @transaction.atomic
    def get_upload_part_url(
        self,
        file_id: str,
        part_number: int,
        upload_id: str,
        user: User
    ) -> Dict[str, Any]:
        """
        获取分片上传URL
        
        Args:
            file_id: 文件ID
            part_number: 分片编号
            upload_id: 上传ID
            user: 用户
            
        Returns:
            分片上传信息
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限访问此文件")
            
            if file_metadata.status != 'uploading':
                raise ValidationError(f"文件状态错误: {file_metadata.status}")
            
            # 生成分片上传URL
            presigned_url = self.storage_service.generate_presigned_upload_part_url(
                key=file_metadata.storage_path,
                part_number=part_number,
                upload_id=upload_id
            )
            
            return {
                'presigned_url': presigned_url,
                'part_number': part_number,
                'upload_id': upload_id,
                'expires_in': FileUploadConfig.PRESIGNED_URL_TTL['upload']
            }
            
        except Exception as e:
            logger.error(f"获取分片上传URL失败: {str(e)}")
            raise
    
    @transaction.atomic
    def complete_upload(
        self,
        file_id: str,
        upload_id: str,
        parts: List[Dict[str, Any]],
        user: User
    ) -> Dict[str, Any]:
        """
        完成文件上传（多部分上传）
        
        Args:
            file_id: 文件ID
            upload_id: 上传ID
            parts: 已完成的部分
            user: 用户
            
        Returns:
            完成信息
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限操作此文件")
            
            if file_metadata.status != 'uploading':
                raise ValidationError(f"文件状态错误: {file_metadata.status}")
            
            # 完成分片上传
            etag = self.storage_service.complete_multipart_upload(
                key=file_metadata.storage_path,
                upload_id=upload_id,
                parts=parts
            )
            
            # 更新文件元数据
            file_metadata.etag = etag
            file_metadata.status = 'processing'
            file_metadata.upload_progress = 100
            file_metadata.upload_completed_at = timezone.now()
            file_metadata.save()
            
            # 获取真实的文件信息
            stored_metadata = self.storage_service.get_file_metadata(file_metadata.storage_path)
            
            # 更新文件大小和哈希信息
            file_metadata.file_size = stored_metadata['size']
            file_metadata.etag = stored_metadata['etag']
            file_metadata.status = 'completed'
            file_metadata.save()
            
            # 记录审计日志
            self._log_file_audit(
                file_metadata=file_metadata,
                action='upload',
                user=user,
                success=True,
                details={
                    'parts_count': len(parts),
                    'file_size': file_metadata.file_size,
                    'etag': etag
                }
            )
            
            return {
                'file_id': file_id,
                'status': 'completed',
                'file_size': file_metadata.file_size,
                'etag': etag
            }
            
        except Exception as e:
            logger.error(f"完成上传失败: {str(e)}")
            # 标记上传失败
            try:
                file_metadata.status = 'failed'
                file_metadata.save()
            except:
                pass
            raise
    
    @transaction.atomic
    def create_download_url(
        self,
        file_id: str,
        user: User,
        expires_in: int = None
    ) -> Dict[str, Any]:
        """
        创建文件下载URL
        
        Args:
            file_id: 文件ID
            user: 用户
            expires_in: 过期时间
            
        Returns:
            下载信息
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if not self._check_download_permission(file_metadata, user):
                raise PermissionDenied("无权限下载此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            # 生成预签名下载URL
            presigned_url = self.storage_service.generate_presigned_download_url(
                key=file_metadata.storage_path,
                expires_in=expires_in
            )
            
            # 记录下载审计
            self._log_file_audit(
                file_metadata=file_metadata,
                action='download',
                user=user,
                success=True,
                details={
                    'presigned_url_generated': True,
                    'expires_in': expires_in
                }
            )
            
            # 更新访问计数
            file_metadata.increment_access()
            
            return {
                'file_id': file_id,
                'filename': file_metadata.original_filename,
                'file_size': file_metadata.file_size,
                'mime_type': file_metadata.mime_type,
                'download_url': presigned_url,
                'expires_in': expires_in or FileUploadConfig.PRESIGNED_URL_TTL['download']
            }
            
        except Exception as e:
            logger.error(f"创建下载URL失败: {str(e)}")
            raise
    
    def _check_download_permission(self, file_metadata: FileMetadata, user: User) -> bool:
        """检查下载权限"""
        if file_metadata.owner == user or file_metadata.uploaded_by == user:
            return True
        
        if file_metadata.visibility in ['team', 'public']:
            return True
        
        # 检查资源关联权限
        if file_metadata.related_event_id or file_metadata.related_task_id:
            # 这里可以添加更详细的权限检查
            return True
        
        return False
    
    @transaction.atomic
    def delete_file(self, file_id: str, user: User) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            user: 用户
            
        Returns:
            删除信息
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if file_metadata.owner != user and file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限删除此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            # 软删除
            file_metadata.soft_delete(user)
            
            # 记录审计日志
            self._log_file_audit(
                file_metadata=file_metadata,
                action='delete',
                user=user,
                success=True,
                details={
                    'soft_delete': True
                }
            )
            
            return {
                'file_id': file_id,
                'status': 'deleted',
                'message': '文件已删除'
            }
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise
    
    def get_file_metadata(self, file_id: str, user: User) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            user: 用户
            
        Returns:
            文件元数据
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if not self._check_download_permission(file_metadata, user):
                raise PermissionDenied("无权限访问此文件")
            
            return {
                'file_id': file_metadata.file_id,
                'original_filename': file_metadata.original_filename,
                'file_size': file_metadata.file_size,
                'file_type': file_metadata.file_type,
                'mime_type': file_metadata.mime_type,
                'file_category': file_metadata.file_category,
                'status': file_metadata.status,
                'uploaded_by': str(file_metadata.uploaded_by.id),
                'created_at': file_metadata.created_at.isoformat() if file_metadata.created_at else None,
                'etag': file_metadata.etag,
                'visibility': file_metadata.visibility,
                'tags': file_metadata.tags,
                'category': file_metadata.category,
                'description': file_metadata.description,
                'metadata': file_metadata.metadata,
            }
            
        except Exception as e:
            logger.error(f"获取文件元数据失败: {str(e)}")
            raise
    
    def list_user_files(
        self, 
        user: User, 
        filters: dict = None,
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        列出用户文件
        
        Args:
            user: 用户
            filters: 过滤条件
            page: 页码
            page_size: 每页大小
            
        Returns:
            文件列表
        """
        try:
            queryset = FileMetadata.objects.filter(
                owner=user,
                is_deleted=False
            ).select_related('uploaded_by')
            
            # 应用过滤条件
            if filters:
                if 'category' in filters:
                    queryset = queryset.filter(file_category=filters['category'])
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])
                if 'file_type' in filters:
                    queryset = queryset.filter(file_type__icontains=filters['file_type'])
                if 'search' in filters:
                    queryset = queryset.filter(
                        Q(original_filename__icontains=filters['search']) |
                        Q(description__icontains=filters['search'])
                    )
            
            # 分页
            total = queryset.count()
            start = (page - 1) * page_size
            files = queryset.order_by('-created_at')[start:start + page_size]
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'files': [
                    {
                        'file_id': f.file_id,
                        'original_filename': f.original_filename,
                        'file_size': f.file_size,
                        'file_type': f.file_type,
                        'mime_type': f.mime_type,
                        'file_category': f.file_category,
                        'status': f.status,
                        'created_at': f.created_at.isoformat() if f.created_at else None,
                        'visibility': f.visibility,
                        'tags': f.tags,
                    }
                    for f in files
                ]
            }
            
        except Exception as e:
            logger.error(f"列出用户文件失败: {str(e)}")
            raise
    
    @transaction.atomic
    def create_file_share(
        self, 
        file_id: str, 
        user: User, 
        settings: dict = None
    ) -> Dict[str, Any]:
        """
        创建文件分享
        
        Args:
            file_id: 文件ID
            user: 用户
            settings: 分享设置
            
        Returns:
            分享信息
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if file_metadata.owner != user:
                raise PermissionDenied("无权限分享此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            # 创建分享记录
            share_id = f"share_{uuid.uuid4().hex[:16]}"
            share_key = hashlib.sha256(f"{share_id}{timezone.now().timestamp()}".encode()).hexdigest()
            
            defaults = {
                'share_id': share_id,
                'share_key': share_key,
                'file_metadata': file_metadata,
                'share_url': f"{settings.get('base_url', '')}/api/files/share/{share_id}/",
                'created_by': user,
                'allow_download': settings.get('allow_download', True),
                'allow_preview': settings.get('allow_preview', True),
                'expires_at': settings.get('expires_at'),
                'password_protected': settings.get('password_protected', False),
                'password_hash': settings.get('password_hash', ''),
                'description': settings.get('description', ''),
                'metadata': settings.get('metadata', {}),
            }
            
            share = FileShare.objects.create(**defaults)
            
            # 记录审计日志
            self._log_file_audit(
                file_metadata=file_metadata,
                action='share',
                user=user,
                success=True,
                details={
                    'share_id': share_id,
                    'settings': settings
                }
            )
            
            return {
                'share_id': share_id,
                'share_url': share.share_url,
                'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                'password_protected': share.password_protected,
                'settings': {
                    'allow_download': share.allow_download,
                    'allow_preview': share.allow_preview,
                }
            }
            
        except Exception as e:
            logger.error(f"创建文件分享失败: {str(e)}")
            raise


class FileHealthMonitor:
    """
    文件系统健康检查
    """
    
    @staticmethod
    def check_storage_health() -> Dict[str, Any]:
        """
        检查存储系统健康状态
        
        Returns:
            健康状态信息
        """
        try:
            storage_service = FileStorageService()
            
            # 尝试列出存储桶
            response = storage_service.s3_client.list_objects_v2(
                Bucket=storage_service.bucket_name,
                MaxKeys=1
            )
            
            return {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'bucket': storage_service.bucket_name,
                'region': FileUploadConfig.STORAGE_REGION,
                'response_time': 'fast'
            }
            
        except Exception as e:
            logger.error(f"存储健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }
    
    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        """
        检查数据库健康状态
        
        Returns:
            健康状态信息
        """
        try:
            # 尝试执行简单查询
            file_count = FileMetadata.objects.count()
            
            return {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'total_files': file_count
            }
            
        except Exception as e:
            logger.error(f"数据库健康检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }


# 全局文件服务实例
file_service = FileService()
file_health_monitor = FileHealthMonitor()


def get_file_service() -> FileService:
    """获取文件服务实例"""
    return file_service


def get_file_health_monitor() -> FileHealthMonitor:
    """获取健康监控实例"""
    return file_health_monitor