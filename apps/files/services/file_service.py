import os
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import mimetypes
import time
import json

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from ..models import (
    FileMetadata,
    PresignedURL,
    FileShare,
    FileAuditLog,
    FileVersion,
    FilePreviewCache,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class FileUploadConfig:
    """文件上传配置"""
    ALLOWED_FILE_TYPES = {
        'application/pdf': {'extensions': ['.pdf'], 'max_size': 50 * 1024 * 1024},
        'application/msword': {'extensions': ['.doc'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'extensions': ['.docx'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.ms-excel': {'extensions': ['.xls'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {'extensions': ['.xlsx'], 'max_size': 10 * 1024 * 1024},
        'application/vnd.ms-powerpoint': {'extensions': ['.ppt'], 'max_size': 20 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': {'extensions': ['.pptx'], 'max_size': 20 * 1024 * 1024},
        'text/plain': {'extensions': ['.txt'], 'max_size': 5 * 1024 * 1024},
        'text/csv': {'extensions': ['.csv'], 'max_size': 5 * 1024 * 1024},
        'image/jpeg': {'extensions': ['.jpg', '.jpeg'], 'max_size': 20 * 1024 * 1024},
        'image/png': {'extensions': ['.png'], 'max_size': 20 * 1024 * 1024},
        'image/gif': {'extensions': ['.gif'], 'max_size': 10 * 1024 * 1024},
        'image/webp': {'extensions': ['.webp'], 'max_size': 20 * 1024 * 1024},
        'image/svg+xml': {'extensions': ['.svg'], 'max_size': 5 * 1024 * 1024},
        'image/bmp': {'extensions': ['.bmp'], 'max_size': 10 * 1024 * 1024},
        'video/mp4': {'extensions': ['.mp4'], 'max_size': 500 * 1024 * 1024},
        'video/quicktime': {'extensions': ['.mov'], 'max_size': 500 * 1024 * 1024},
        'video/avi': {'extensions': ['.avi'], 'max_size': 200 * 1024 * 1024},
        'video/webm': {'extensions': ['.webm'], 'max_size': 200 * 1024 * 1024},
        'audio/mpeg': {'extensions': ['.mp3'], 'max_size': 50 * 1024 * 1024},
        'audio/wav': {'extensions': ['.wav'], 'max_size': 50 * 1024 * 1024},
        'audio/ogg': {'extensions': ['.ogg'], 'max_size': 50 * 1024 * 1024},
        'audio/flac': {'extensions': ['.flac'], 'max_size': 50 * 1024 * 1024},
        'application/zip': {'extensions': ['.zip'], 'max_size': 200 * 1024 * 1024},
        'application/x-rar-compressed': {'extensions': ['.rar'], 'max_size': 200 * 1024 * 1024},
        'application/x-7z-compressed': {'extensions': ['.7z'], 'max_size': 200 * 1024 * 1024},
        'application/x-tar': {'extensions': ['.tar'], 'max_size': 200 * 1024 * 1024},
        'application/gzip': {'extensions': ['.gz'], 'max_size': 200 * 1024 * 1024},
    }
    
    PRESIGNED_URL_TTL = {
        'upload': 900,
        'download': 3600,
        'preview': 7200,
    }
    
    DEFAULT_STORAGE_BUCKET = os.getenv('S3_BUCKET_NAME', 'eventpilot-files')
    STORAGE_REGION = os.getenv('AWS_REGION', 'us-east-1')
    STORAGE_PATH_PREFIX = os.getenv('STORAGE_PATH_PREFIX', 'files')
    
    MAX_FILE_SIZE = 500 * 1024 * 1024
    MAX_CONCURRENT_UPLOADS = 5
    
    CHUNK_SIZE = 8 * 1024 * 1024
    MAX_CHUNKS = 100


class FileSecurityValidator:
    """文件安全验证器"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        safe_filename = filename.replace('/', '').replace('\\', '').replace('..', '')
        safe_filename = ''.join(c for c in safe_filename if c.isprintable() and c not in '<>:"|?*\x00-\x1f')
        if len(safe_filename) > 255:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:255 - len(ext)] + ext
        return safe_filename.strip()
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """生成安全的存储文件名"""
        safe_name = FileSecurityValidator.sanitize_filename(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_id = uuid.uuid4().hex[:8]
        name, ext = os.path.splitext(safe_name)
        return f"{timestamp}_{random_id}_{name}{ext}"


class FileStorageService:
    """文件存储服务 - 使用Django默认存储"""
    
    def __init__(self):
        self.storage = default_storage
    
    def _generate_storage_key(self, user_id: str, filename: str) -> str:
        """生成存储键"""
        timestamp = datetime.now().strftime('%Y/%m/%d')
        secure_filename = FileSecurityValidator.generate_secure_filename(filename)
        return f"{FileUploadConfig.STORAGE_PATH_PREFIX}/{user_id}/{timestamp}/{secure_filename}"
    
    def save_file(self, key: str, content: bytes, content_type: str = None) -> str:
        """保存文件"""
        try:
            file_content = ContentFile(content)
            saved_path = self.storage.save(key, file_content)
            logger.info(f"文件保存成功: {saved_path}")
            return saved_path
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise
    
    def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """获取文件访问URL"""
        try:
            if hasattr(self.storage, 'url'):
                url = self.storage.url(key)
                return url
            return f"/media/{key}"
        except Exception as e:
            logger.error(f"获取文件URL失败: {str(e)}")
            raise
    
    def delete_file(self, key: str) -> bool:
        """删除文件"""
        try:
            if self.storage.exists(key):
                self.storage.delete(key)
                logger.info(f"文件删除成功: {key}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def file_exists(self, key: str) -> bool:
        """检查文件是否存在"""
        return self.storage.exists(key)
    
    def get_file_size(self, key: str) -> int:
        """获取文件大小"""
        try:
            return self.storage.size(key)
        except Exception:
            return 0


class FileService:
    """文件服务核心类"""
    
    def __init__(self):
        self.storage_service = FileStorageService()
        self.cache_timeout = FileUploadConfig.CACHE_TIMEOUTS if hasattr(FileUploadConfig, 'CACHE_TIMEOUTS') else {'presigned_url': 900, 'file_metadata': 3600, 'preview_cache': 86400, 'share_link': 7200}
    
    def _determine_file_category(self, mime_type: str) -> str:
        """确定文件分类"""
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
    
    def _log_file_audit(self, file_metadata: FileMetadata, action: str, user: User,
                       success: bool, details: dict = None):
        """记录文件审计日志"""
        try:
            FileAuditLog.objects.create(
                file_metadata=file_metadata,
                action=action,
                performed_by=user,
                success=success,
                action_details=details or {},
                metadata={'timestamp': timezone.now().isoformat(), 'file_id': str(file_metadata.file_id)}
            )
        except Exception as e:
            logger.error(f"审计日志记录失败: {str(e)}")
    
    @transaction.atomic
    def initiate_upload(self, user: User, filename: str, file_size: int,
                       mime_type: str, metadata: dict = None) -> Dict[str, Any]:
        """初始化文件上传"""
        try:
            if file_size > FileUploadConfig.MAX_FILE_SIZE:
                raise ValidationError(f"文件大小超过限制 ({FileUploadConfig.MAX_FILE_SIZE // (1024 * 1024)}MB)")
            
            if mime_type not in FileUploadConfig.ALLOWED_FILE_TYPES:
                raise ValidationError(f"不支持的文件类型: {mime_type}")
            
            file_id = f"file_{uuid.uuid4().hex[:16]}"
            storage_key = self.storage_service._generate_storage_key(str(user.id), filename)
            
            file_metadata = FileMetadata.objects.create(
                file_id=file_id,
                original_filename=FileSecurityValidator.sanitize_filename(filename),
                stored_filename=FileSecurityValidator.generate_secure_filename(filename),
                file_path=storage_key,
                file_size=file_size,
                file_type=mime_type,
                mime_type=mime_type,
                file_category=self._determine_file_category(mime_type),
                status=FileMetadata.FileStatus.UPLOADING,
                storage_provider='local',
                storage_path=storage_key,
                storage_bucket='local_storage',
                uploaded_by=user,
                owner=user,
                metadata=metadata or {},
                visibility=FileMetadata.Visibility.PRIVATE
            )
            
            self._log_file_audit(
                file_metadata=file_metadata,
                action='upload',
                user=user,
                success=True,
                details={'filename': filename, 'file_size': file_size, 'mime_type': mime_type}
            )
            
            return {
                'file_id': file_id,
                'upload_strategy': 'direct',
                'presigned_url': '',
                'storage_key': storage_key,
                'chunk_size': FileUploadConfig.CHUNK_SIZE,
                'max_chunks': FileUploadConfig.MAX_CHUNKS,
                'expires_in': FileUploadConfig.PRESIGNED_URL_TTL['upload']
            }
            
        except Exception as e:
            logger.error(f"上传初始化失败: {str(e)}")
            raise
    
    def get_upload_part_url(self, file_id: str, part_number: int, upload_id: str, user: User) -> Dict[str, Any]:
        """获取分片上传的预签名URL"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            if file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限操作此文件")
            
            return {
                'presigned_url': '',
                'part_number': part_number,
                'upload_id': upload_id,
                'expires_in': FileUploadConfig.PRESIGNED_URL_TTL['upload']
            }
            
        except Exception as e:
            logger.error(f"获取分片上传URL失败: {str(e)}")
            raise
    
    @transaction.atomic
    def direct_upload(self, user: User, file_obj, filename: str = None) -> Dict[str, Any]:
        """直接上传文件（单文件上传）"""
        try:
            logger.info("开始处理文件上传")
            
            # 读取文件内容
            file_content = file_obj.read()
            file_size = len(file_content)
            logger.info(f"文件大小: {file_size} bytes")
            
            # 检查文件大小
            if file_size > FileUploadConfig.MAX_FILE_SIZE:
                raise ValidationError(f"文件大小超过限制 ({FileUploadConfig.MAX_FILE_SIZE // (1024 * 1024)}MB)")
            
            # 确定MIME类型
            mime_type = file_obj.content_type or 'application/octet-stream'
            logger.info(f"MIME类型: {mime_type}")
            
            # 如果MIME类型不在列表中，尝试通过文件扩展名推断
            if mime_type not in FileUploadConfig.ALLOWED_FILE_TYPES:
                logger.warning(f"MIME类型 {mime_type} 不在允许列表中，尝试通过扩展名推断")
                actual_filename = filename or file_obj.name
                ext = os.path.splitext(actual_filename)[1].lower()
                
                # 尝试找到匹配的扩展名
                found_mime_type = None
                for mt, config in FileUploadConfig.ALLOWED_FILE_TYPES.items():
                    if ext in config.get('extensions', []):
                        found_mime_type = mt
                        logger.info(f"通过扩展名 {ext} 找到匹配的 MIME 类型: {found_mime_type}")
                        break
                
                if found_mime_type:
                    mime_type = found_mime_type
                else:
                    # 如果找不到匹配的，设置为默认类型
                    mime_type = 'application/octet-stream'
                    logger.warning(f"使用默认 MIME 类型: {mime_type}")
            
            # 使用上传时的文件名或文件对象的名称
            actual_filename = filename or file_obj.name
            logger.info(f"文件名: {actual_filename}")
            
            # 创建文件元数据
            file_id = f"file_{uuid.uuid4().hex[:16]}"
            storage_key = self.storage_service._generate_storage_key(str(user.id), actual_filename)
            logger.info(f"存储键: {storage_key}")
            
            file_metadata = FileMetadata.objects.create(
                file_id=file_id,
                original_filename=FileSecurityValidator.sanitize_filename(actual_filename),
                stored_filename=FileSecurityValidator.generate_secure_filename(actual_filename),
                file_path=storage_key,
                file_size=file_size,
                file_type=mime_type,
                mime_type=mime_type,
                file_category=self._determine_file_category(mime_type),
                status=FileMetadata.FileStatus.UPLOADING,
                storage_provider='local',
                storage_path=storage_key,
                storage_bucket='local_storage',
                uploaded_by=user,
                owner=user,
                metadata={}
            )
            
            logger.info(f"文件元数据已创建: {file_id}")
            
            # 保存文件
            saved_path = self.storage_service.save_file(storage_key, file_content, mime_type)
            logger.info(f"文件已保存到: {saved_path}")
            
            # 更新文件状态
            file_metadata.status = FileMetadata.FileStatus.COMPLETED
            file_metadata.upload_progress = 100
            file_metadata.upload_completed_at = timezone.now()
            file_metadata.etag = hashlib.md5(file_content).hexdigest()
            file_metadata.save()
            
            logger.info(f"文件状态已更新为完成")
            
            self._log_file_audit(
                file_metadata=file_metadata,
                action='upload',
                user=user,
                success=True,
                details={'file_size': file_size}
            )
            
            return {
                'file_id': file_id,
                'status': 'completed',
                'file_size': file_size,
                'filename': file_metadata.original_filename
            }
            
        except Exception as e:
            logger.exception(f"直接上传失败: {str(e)}")
            raise

    @transaction.atomic
    def complete_upload(self, file_id: str, user: User, parts: list = None, file_content: bytes = None) -> Dict[str, Any]:
        """完成文件上传"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            if file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限操作此文件")
            
            if file_content:
                saved_path = self.storage_service.save_file(
                    file_metadata.storage_path,
                    file_content,
                    file_metadata.mime_type
                )
                file_metadata.file_size = self.storage_service.get_file_size(saved_path)
                file_metadata.etag = hashlib.md5(file_content).hexdigest() if file_content else ''
            
            file_metadata.status = FileMetadata.FileStatus.COMPLETED
            file_metadata.upload_progress = 100
            file_metadata.upload_completed_at = timezone.now()
            file_metadata.save()
            
            self._log_file_audit(
                file_metadata=file_metadata,
                action='upload',
                user=user,
                success=True,
                details={'file_size': file_metadata.file_size}
            )
            
            return {
                'file_id': file_id,
                'status': 'completed',
                'file_size': file_metadata.file_size
            }
            
        except Exception as e:
            logger.error(f"完成上传失败: {str(e)}")
            try:
                file_metadata.status = FileMetadata.FileStatus.FAILED
                file_metadata.save()
            except:
                pass
            raise
    
    def get_file_metadata(self, file_id: str, user: User) -> Dict[str, Any]:
        """获取文件元数据"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
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
                'visibility': file_metadata.visibility,
                'tags': file_metadata.tags,
                'category': file_metadata.category,
                'description': file_metadata.description,
                'metadata': file_metadata.metadata,
            }
            
        except Exception as e:
            logger.error(f"获取文件元数据失败: {str(e)}")
            raise
    
    def _check_download_permission(self, file_metadata: FileMetadata, user: User) -> bool:
        """检查下载权限"""
        if file_metadata.owner == user or file_metadata.uploaded_by == user:
            return True
        
        if file_metadata.visibility in [FileMetadata.Visibility.TEAM, FileMetadata.Visibility.PUBLIC]:
            return True
        
        return False
    
    @transaction.atomic
    def create_download_url(self, file_id: str, user: User, expires_in: int = 3600) -> Dict[str, Any]:
        """创建文件下载URL"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            if not self._check_download_permission(file_metadata, user):
                raise PermissionDenied("无权限下载此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            download_url = self.storage_service.get_file_url(
                file_metadata.storage_path,
                expires_in
            )
            
            self._log_file_audit(
                file_metadata=file_metadata,
                action='download',
                user=user,
                success=True,
                details={'presigned_url_generated': True, 'expires_in': expires_in}
            )
            
            file_metadata.increment_access()
            
            return {
                'file_id': file_id,
                'filename': file_metadata.original_filename,
                'file_size': file_metadata.file_size,
                'mime_type': file_metadata.mime_type,
                'download_url': download_url,
                'expires_in': expires_in or FileUploadConfig.PRESIGNED_URL_TTL['download']
            }
            
        except Exception as e:
            logger.error(f"创建下载URL失败: {str(e)}")
            raise
    
    @transaction.atomic
    def delete_file(self, file_id: str, user: User) -> Dict[str, Any]:
        """删除文件"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            if file_metadata.owner != user and file_metadata.uploaded_by != user:
                raise PermissionDenied("无权限删除此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            file_metadata.soft_delete(user)
            
            self._log_file_audit(
                file_metadata=file_metadata,
                action='delete',
                user=user,
                success=True,
                details={'soft_delete': True}
            )
            
            return {
                'file_id': file_id,
                'status': 'deleted',
                'message': '文件已删除'
            }
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            raise
    
    def list_user_files(self, user: User, filters: dict = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """列出用户文件"""
        try:
            queryset = FileMetadata.objects.filter(
                owner=user,
                is_deleted=False
            ).select_related('uploaded_by')
            
            if filters:
                if 'category' in filters:
                    queryset = queryset.filter(file_category=filters['category'])
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])
                if 'file_type' in filters:
                    queryset = queryset.filter(file_type__icontains=filters['file_type'])
                if 'search' in filters:
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(original_filename__icontains=search_term) |
                        Q(description__icontains=search_term)
                    )
            
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
    def create_file_share(self, file_id: str, user: User, settings: dict = None) -> Dict[str, Any]:
        """创建文件分享"""
        settings = settings or {}
        try:
            logger.info(f"开始创建分享: file_id={file_id}, user={user.username}")

            # Step 1: 获取文件元数据
            try:
                file_metadata = FileMetadata.objects.select_related('owner').get(file_id=file_id)
            except FileMetadata.DoesNotExist:
                raise ValidationError("文件不存在")

            # Step 2: 权限检查
            if file_metadata.owner != user:
                raise PermissionDenied(f"无权限分享此文件 (文件所有者: {file_metadata.owner.username})")

            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除，无法分享")

            # Step 3: 构建分享数据
            share_id = f"share_{uuid.uuid4().hex[:16]}"
            share_key = hashlib.sha256(f"{share_id}{timezone.now().timestamp()}".encode()).hexdigest()

            base_url = settings.get('base_url', '') or 'http://localhost:8000'
            share_url = f"{base_url.rstrip('/')}/api/files/share/{share_id}/"
            logger.info(f"分享URL: {share_url}")

            expires_at = settings.get('expires_at')
            if not expires_at:
                expires_hours = settings.get('expires_hours')
                if expires_hours:
                    expires_at = timezone.now() + timezone.timedelta(hours=int(expires_hours))

            defaults = {
                'share_id': share_id,
                'share_key': share_key,
                'file_metadata': file_metadata,
                'share_url': share_url,
                'created_by': user,
                'allow_download': bool(settings.get('allow_download', True)),
                'allow_preview': bool(settings.get('allow_preview', True)),
                'permitir_comments': bool(settings.get('permitir_comments', False)),
                'allow_reshare': bool(settings.get('allow_reshare', False)),
                'password_protected': bool(settings.get('password_protected', False)),
                'password_hash': str(settings.get('password_hash', '')) or '',
                'expires_at': expires_at,
                'description': str(settings.get('description', '')) or '',
                'is_active': True,
            }

            # Step 4: 创建分享记录
            try:
                share = FileShare.objects.create(**defaults)
                logger.info(f"分享记录已创建: share_id={share_id}, pk={share.pk}")
            except Exception as db_error:
                logger.error(f"数据库创建分享失败: {type(db_error).__name__}: {db_error}")
                raise ValidationError(f"创建分享记录失败: {str(db_error)}")

            # Step 5: 记录审计日志（不阻塞主流程）
            try:
                audit_details = {'share_id': share_id}
                if settings.get('expires_at'):
                    audit_details['expires_at'] = settings['expires_at'].isoformat() if hasattr(settings['expires_at'], 'isoformat') else str(settings['expires_at'])
                self._log_file_audit(
                    file_metadata=file_metadata,
                    action='share',
                    user=user,
                    success=True,
                    details=audit_details
                )
            except Exception as log_err:
                logger.warning(f"审计日志记录失败(不影响): {log_err}")

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

        except (ValidationError, PermissionDenied):
            raise
        except Exception as e:
            logger.error(f"创建文件分享失败: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValidationError(f"创建分享链接失败: {str(e)}")


class FileHealthMonitor:
    """文件系统健康检查"""
    
    @staticmethod
    def check_storage_health() -> Dict[str, Any]:
        """检查存储系统健康状态"""
        try:
            storage_service = FileStorageService()
            return {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'bucket': 'local_storage',
                'region': 'local',
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
        """检查数据库健康状态"""
        try:
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


file_service = FileService()
file_health_monitor = FileHealthMonitor()


def get_file_service() -> FileService:
    """获取文件服务实例"""
    return file_service


def get_file_health_monitor() -> FileHealthMonitor:
    """获取健康监控实例"""
    return file_health_monitor
