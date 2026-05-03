import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class FileMetadata(models.Model):
    """文件元数据模型"""
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

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    file_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)
    
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    mime_type = models.CharField(max_length=150)
    file_category = models.CharField(
        max_length=20,
        choices=FileCategory.choices,
        default=FileCategory.OTHER
    )
    
    storage_provider = models.CharField(max_length=50, default='s3')
    storage_path = models.CharField(max_length=1024)
    storage_bucket = models.CharField(max_length=255)
    etag = models.CharField(max_length=100, blank=True, default='')
    file_hash = models.CharField(max_length=128, blank=True, default='')
    checksum = models.CharField(max_length=64, blank=True, default='')
    
    virus_scanned = models.BooleanField(default=False)
    virus_detected = models.BooleanField(default=False)
    scan_timestamp = models.DateTimeField(blank=True, null=True)
    sensitivity_level = models.CharField(max_length=20, default='normal')
    
    status = models.CharField(
        max_length=20,
        choices=FileStatus.choices,
        default=FileStatus.UPLOADING,
        db_index=True
    )
    upload_progress = models.IntegerField(default=0)
    upload_chunk_count = models.IntegerField(default=0)
    upload_completed_at = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField(default=1)
    
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE
    )
    is_public = models.BooleanField(default=False)
    access_count = models.IntegerField(default=0)
    
    related_event_id = models.UUIDField(blank=True, null=True, db_index=True)
    related_task_id = models.UUIDField(blank=True, null=True, db_index=True)
    related_checklist_id = models.UUIDField(blank=True, null=True, db_index=True)
    related_model_type = models.CharField(blank=True, max_length=50, null=True)
    related_model_id = models.CharField(blank=True, max_length=100, null=True, db_index=True)
    
    tags = models.JSONField(default=list)
    category = models.CharField(blank=True, max_length=100, null=True)
    description = models.TextField(blank=True)
    preview_available = models.BooleanField(default=False)
    preview_path = models.CharField(blank=True, max_length=1024)
    thumbnails = models.JSONField(default=dict)
    
    metadata = models.JSONField(default=dict)
    custom_attributes = models.JSONField(default=dict)
    
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='deleted_files',
        blank=True,
        null=True
    )
    
    storage_quota_used = models.BigIntegerField(default=0)
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        db_index=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_files',
        db_index=True
    )
    parent_file = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='versions',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        verbose_name = '文件元数据'
        verbose_name_plural = '文件元数据'
        db_table = 'files_metadata'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.file_id})"

    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])

    def soft_delete(self, user):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.status = self.FileStatus.DELETED
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'status'])


class FileAuditLog(models.Model):
    """文件审计日志模型"""
    class ActionType(models.TextChoices):
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

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    file_metadata = models.ForeignKey(
        FileMetadata,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        db_index=True
    )
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        db_index=True
    )
    action_details = models.JSONField(default=dict)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='file_audits',
        blank=True,
        null=True,
        db_index=True
    )
    performed_at = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(blank=True, max_length=100)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    previous_state = models.JSONField(blank=True, default=dict, null=True)
    new_state = models.JSONField(blank=True, default=dict, null=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = '文件审计日志'
        verbose_name_plural = '文件审计日志'
        db_table = 'files_audit_logs'
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.action} - {self.file_metadata.original_filename}"


class FileShare(models.Model):
    """文件分享模型"""
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    share_id = models.CharField(max_length=100, unique=True, db_index=True)
    share_url = models.URLField()
    share_key = models.CharField(max_length=256)
    file_metadata = models.ForeignKey(
        FileMetadata,
        on_delete=models.CASCADE,
        related_name='shares',
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_shares',
        db_index=True
    )
    
    allow_download = models.BooleanField(default=True)
    allow_preview = models.BooleanField(default=True)
    permitir_comments = models.BooleanField(default=False)
    allow_reshare = models.BooleanField(default=False)
    password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(blank=True, max_length=256)
    max_downloads = models.IntegerField(blank=True, null=True)
    download_count = models.IntegerField(default=0)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    access_log = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = '文件分享'
        verbose_name_plural = '文件分享'
        db_table = 'files_shares'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.share_id} - {self.file_metadata.original_filename}"

    def is_valid(self):
        """检查分享是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True


class FileVersion(models.Model):
    """文件版本模型"""
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    version_id = models.CharField(max_length=100, unique=True, db_index=True)
    version_number = models.IntegerField()
    file_metadata = models.ForeignKey(
        FileMetadata,
        on_delete=models.CASCADE,
        related_name='file_versions',
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_versions',
        db_index=True
    )
    
    storage_path = models.CharField(max_length=1024)
    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=128)
    checksum = models.CharField(max_length=64)
    change_description = models.TextField(blank=True)
    change_reason = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    replaced_by = models.ForeignKey(
        FileMetadata,
        on_delete=models.SET_NULL,
        related_name='previous_versions',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = '文件版本'
        verbose_name_plural = '文件版本'
        db_table = 'files_versions'
        ordering = ['-version_number']

    def __str__(self):
        return f"v{self.version_number} - {self.file_metadata.original_filename}"


class FilePreviewCache(models.Model):
    """文件预览缓存模型"""
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    file_metadata = models.ForeignKey(
        FileMetadata,
        on_delete=models.CASCADE,
        related_name='preview_caches',
        db_index=True
    )
    
    preview_type = models.CharField(max_length=50)
    preview_path = models.CharField(max_length=1024)
    preview_size = models.JSONField(default=dict)
    preview_format = models.CharField(max_length=50)
    quality = models.CharField(max_length=20, default='medium')
    cache_key = models.CharField(max_length=256, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    size_bytes = models.BigIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    last_accessed_at = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = '文件预览缓存'
        verbose_name_plural = '文件预览缓存'
        db_table = 'files_preview_cache'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.preview_type} - {self.file_metadata.original_filename}"


class PresignedURL(models.Model):
    """预签名URL模型"""
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

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    url_id = models.CharField(max_length=100, unique=True, db_index=True)
    url_type = models.CharField(
        max_length=20,
        choices=URLType.choices,
        db_index=True
    )
    url = models.TextField()
    key = models.CharField(max_length=255)
    signature = models.CharField(max_length=256)
    expires_at = models.DateTimeField(db_index=True)
    max_uses = models.IntegerField(default=1)
    use_count = models.IntegerField(default=0)
    one_time_use = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=URLStatus.choices,
        default=URLStatus.ACTIVE,
        db_index=True
    )
    used_at = models.DateTimeField(blank=True, null=True)
    intended_filename = models.CharField(blank=True, max_length=255)
    intended_file_size = models.BigIntegerField(blank=True, null=True)
    intended_mime_type = models.CharField(blank=True, max_length=150)
    storage_path = models.CharField(blank=True, max_length=1024)
    upload_id = models.CharField(blank=True, max_length=256)
    metadata = models.JSONField(default=dict)
    ip_restrictions = models.JSONField(default=list)
    user_agent_restrictions = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_metadata = models.ForeignKey(
        FileMetadata,
        on_delete=models.CASCADE,
        related_name='presigned_urls',
        blank=True,
        null=True
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presigned_urls',
        db_index=True
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='used_urls',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = '预签名URL'
        verbose_name_plural = '预签名URL'
        db_table = 'files_presigned_urls'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.url_type} - {self.url_id}"
