import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import hashlib
import uuid
import json
from datetime import datetime

User = get_user_model()


class FileMetadata(models.Model):
    """
    企业级文件元数据模型
    存储文件的所有元数据信息，支持预签名URL架构
    """
    class FileCategory(models.TextChoices):
        DOCUMENT = 'document', '文档'
        IMAGE = 'image', '图片'
        VIDEO = 'video', '视频'
        AUDIO = 'audio', '音频'
        ARCHIVE = 'archive', '压缩包'
        OTHER = 'other', '其他'
    
    class FileStatus(models.TextChoices):
        UPLOADING = 'uploading', '上传中'
        PROCESSING = 'processing', '处理中'
        COMPLETED = 'completed', '完成'
        FAILED = 'failed', '失败'
        DELETED = 'deleted', '已删除'
        QUARANTINE = 'quarantine', '隔离'
    
    class Visibility(models.TextChoices):
        PRIVATE = 'private', '私有'
        TEAM = 'team', '团队可见'
        PUBLIC = 'public', '公开'
        SHARED = 'shared', '共享'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # 基本文件信息
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    mime_type = models.CharField(max_length=150)
    file_category = models.CharField(max_length=20, choices=FileCategory.choices)
    
    # 存储信息
    storage_provider = models.CharField(max_length=50, default='s3')
    storage_path = models.CharField(max_length=1024)
    storage_bucket = models.CharField(max_length=255)
    etag = models.CharField(max_length=100)
    
    # 文件安全
    file_hash = models.CharField(max_length=128)  # SHA256哈希
    checksum = models.CharField(max_length=64)    # MD5校验和
    virus_scanned = models.BooleanField(default=False)
    virus_detected = models.BooleanField(default=False)
    scan_timestamp = models.DateTimeField(null=True, blank=True)
    sensitivity_level = models.CharField(max_length=20, default='normal')
    
    # 状态和流程
    status = models.CharField(max_length=20, choices=FileStatus.choices, default='uploading')
    upload_progress = models.IntegerField(default=0)
    upload_chunk_count = models.IntegerField(default=0)
    upload_completed_at = models.DateTimeField(null=True, blank=True)
    
    # 版本控制
    version = models.IntegerField(default=1)
    parent_file = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versions')
    
    # 可见性和权限
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default='private')
    is_public = models.BooleanField(default=False)
    access_count = models.IntegerField(default=0)
    
    # 所有者信息
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_files')
    
    # 关联信息
    related_event_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_task_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_checklist_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_model_type = models.CharField(max_length=50, null=True, blank=True)
    related_model_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    # 分类和标签
    tags = models.JSONField(default=list)
    category = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # 预览和缩略图
    preview_available = models.BooleanField(default=False)
    preview_path = models.CharField(max_length=1024, blank=True)
    thumbnails = models.JSONField(default=dict)
    
    # 元数据
    metadata = models.JSONField(default=dict)
    custom_attributes = models.JSONField(default=dict)
    
    # 生命周期
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_files')
    
    # 存储配额
    storage_quota_used = models.BigIntegerField(default=0)
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'files_metadata'
        verbose_name = '文件元数据'
        verbose_name_plural = '文件元数据'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file_id']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
            models.Index(fields=['file_category']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.file_id})"
    
    def calculate_file_hash(self):
        """计算文件哈希值（SHA256）"""
        if self.storage_path:
            return self.file_hash
        return hashlib.sha256(self.file_id.encode()).hexdigest()
    
    def calculate_checksum(self):
        """计算文件的MD5校验和"""
        return hashlib.md5(self.file_id.encode()).hexdigest()
    
    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])
    
    def soft_delete(self, user):
        """软删除文件"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class PresignedURL(models.Model):
    """
    预签名URL模型
    管理文件上传和下载的预签名URL
    """
    class URLType(models.TextChoices):
        UPLOAD = 'upload', '上传'
        DOWNLOAD = 'download', '下载'
        PREVIEW = 'preview', '预览'
    
    class URLStatus(models.TextChoices):
        ACTIVE = 'active', '活跃'
        USED = 'used', '已使用'
        EXPIRED = 'expired', '已过期'
        CANCELLED = 'cancelled', '已取消'
        FAILED = 'failed', '失败'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # 关联文件
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='presigned_urls', null=True, blank=True)
    
    # URL信息
    url_type = models.CharField(max_length=20, choices=URLType.choices)
    url = models.TextField()
    key = models.CharField(max_length=255)
    
    # 安全策略
    signature = models.CharField(max_length=256)
    expires_at = models.DateTimeField(db_index=True)
    max_uses = models.IntegerField(default=1)
    use_count = models.IntegerField(default=0)
    one_time_use = models.BooleanField(default=True)
    
    # 状态
    status = models.CharField(max_length=20, choices=URLStatus.choices, default='active')
    
    # 用户信息
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presigned_urls')
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_urls')
    used_at = models.DateTimeField(null=True, blank=True)
    
    # 文件信息（用于上传URL）
    intended_filename = models.CharField(max_length=255, blank=True)
    intended_file_size = models.BigIntegerField(null=True, blank=True)
    intended_mime_type = models.CharField(max_length=150, blank=True)
    
    # 存储信息
    storage_path = models.CharField(max_length=1024, blank=True)
    upload_id = models.CharField(max_length=256, blank=True)
    
    # 元数据
    metadata = models.JSONField(default=dict)
    
    # 限制和检查
    ip_restrictions = models.JSONField(default=list)
    user_agent_restrictions = models.JSONField(default=list)
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files_presigned_urls'
        verbose_name = '预签名URL'
        verbose_name_plural = '预签名URL'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['url_id']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.url_type} URL - {self.url_id}"
    
    def is_valid(self):
        """检查URL是否有效"""
        if self.status != 'active':
            return False
        if timezone.now() > self.expires_at:
            self.mark_expired()
            return False
        if self.one_time_use and self.use_count >= self.max_uses:
            self.mark_used()
            return False
        return True
    
    def mark_used(self, user=None):
        """标记URL为已使用"""
        self.status = 'used'
        self.use_count += 1
        self.used_at = timezone.now()
        if user:
            self.used_by = user
        self.save(update_fields=['status', 'use_count', 'used_at', 'used_by'])
    
    def mark_expired(self):
        """标记URL为已过期"""
        if self.status == 'active':
            self.status = 'expired'
            self.save(update_fields=['status'])
    
    def mark_cancelled(self):
        """标记URL为已取消"""
        if self.status == 'active':
            self.status = 'cancelled'
            self.save(update_fields=['status'])


class FileShare(models.Model):
    """
    文件分享模型
    管理文件分享链接和权限
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='shares')
    
    # 分享信息
    share_url = models.URLField()
    share_key = models.CharField(max_length=256)
    
    # 权限设置
    allow_download = models.BooleanField(default=True)
    allow_preview = models.BooleanField(default=True)
    permitir_comments = models.BooleanField(default=False)
    allow_reshare = models.BooleanField(default=False)
    
    # 访问控制
    password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=256, blank=True)
    max_downloads = models.IntegerField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    
    # 有效期
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # 创建者
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_shares')
    
    # 访问记录
    access_log = models.JSONField(default=list)
    
    # 状态
    is_active = models.BooleanField(default=True)
    
    # 元数据
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'files_shares'
        verbose_name = '文件分享'
        verbose_name_plural = '文件分享'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['share_id']),
            models.Index(fields=['file_metadata']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"Share {self.share_id} - {self.file_metadata.original_filename}"
    
    def increment_download(self):
        """增加下载计数"""
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        
        self.download_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['download_count', 'last_accessed_at'])
        return True
    
    def is_valid(self):
        """检查分享是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True


class FileAuditLog(models.Model):
    """
    文件审计日志模型
    记录所有文件操作的审计日志
    """
    class Action(models.TextChoices):
        UPLOAD = 'upload', '上传'
        DOWNLOAD = 'download', '下载'
        DELETE = 'delete', '删除'
        SHARE = 'share', '分享'
        VIEW = 'view', '查看'
        EDIT = 'edit', '编辑'
        MOVE = 'move', '移动'
        COPY = 'copy', '复制'
        RESTORE = 'restore', '恢复'
        QUARANTINE = 'quarantine', '隔离'
        SCAN = 'scan', '扫描'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='audit_logs')
    
    # 操作信息
    action = models.CharField(max_length=20, choices=Action.choices)
    action_details = models.JSONField(default=dict)
    
    # 用户信息
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='file_audits')
    performed_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # 请求信息
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    
    # 结果
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # 变更追踪
    previous_state = models.JSONField(default=dict, null=True, blank=True)
    new_state = models.JSONField(default=dict, null=True, blank=True)
    
    # 元数据
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'files_audit_logs'
        verbose_name = '文件审计日志'
        verbose_name_plural = '文件审计日志'
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['file_metadata']),
            models.Index(fields=['performed_by']),
            models.Index(fields=['action']),
            models.Index(fields=['performed_at']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.performed_by} on {self.performed_at}"


class FileVersion(models.Model):
    """
    文件版本模型
    管理文件的历史版本
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # 关联文件
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='file_versions')
    
    # 版本信息
    version_number = models.IntegerField()
    
    # 存储信息
    storage_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=128)
    checksum = models.CharField(max_length=64)
    
    # 变更信息
    change_description = models.TextField(blank=True)
    change_reason = models.TextField(blank=True)
    replaced_by = models.ForeignKey(FileMetadata, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_versions')
    
    # 创建者
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_versions')
    created_at = models.DateTimeField(default=timezone.now)
    
    # 状态
    is_current = models.BooleanField(default=False)
    
    # 元数据
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'files_versions'
        verbose_name = '文件版本'
        verbose_name_plural = '文件版本'
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['version_id']),
            models.Index(fields=['file_metadata']),
            models.Index(fields=['version_number']),
        ]
    
    def __str__(self):
        return f"Version {self.version_number} of {self.file_metadata.original_filename}"


class FilePreviewCache(models.Model):
    """
    文件预览缓存模型
    缓存文件预览结果
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    file_metadata = models.ForeignKey(FileMetadata, on_delete=models.CASCADE, related_name='preview_caches')
    
    # 预览信息
    preview_type = models.CharField(max_length=50)
    preview_path = models.CharField(max_length=1024)
    
    # 预览元数据
    preview_size = models.JSONField(default=dict)
    preview_format = models.CharField(max_length=50)
    quality = models.CharField(max_length=20, default='medium')
    
    # 缓存控制
    cache_key = models.CharField(max_length=256, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    size_bytes = models.BigIntegerField(default=0)
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now)
    last_accessed_at = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'files_preview_cache'
        verbose_name = '文件预览缓存'
        verbose_name_plural = '文件预览缓存'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['file_metadata']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Preview {self.preview_type} for {self.file_metadata.original_filename}"
    
    def increment_access(self):
        """增加预览访问计数"""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])