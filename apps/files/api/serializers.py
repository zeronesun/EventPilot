from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    FileMetadata, PresignedURL, FileShare, FileAuditLog, 
    FileVersion, FilePreviewCache
)

User = get_user_model()


class FileMetadataSerializer(serializers.ModelSerializer):
    """文件元数据序列化器"""
    
    class Meta:
        model = FileMetadata
        fields = [
            'id', 'file_id', 'original_filename', 'stored_filename',
            'file_size', 'file_type', 'mime_type', 'file_category',
            'storage_provider', 'storage_path', 'storage_bucket',
            'etag', 'virus_scanned', 'virus_detected',
            'status', 'upload_progress', 'version', 'visibility',
            'uploaded_by', 'owner', 'tags', 'category', 'description',
            'preview_available', 'is_deleted', 'created_at', 'updated_at',
            'last_accessed_at', 'expires_at', 'metadata', 'custom_attributes'
        ]
        read_only_fields = [
            'id', 'file_id', 'stored_filename', 'storage_path',
            'storage_bucket', 'etag', 'file_hash', 'checksum',
            'upload_completed_at', 'version', 'access_count',
            'is_deleted', 'deleted_at', 'created_at', 'updated_at', 'owner', 'uploaded_by'
        ]

class FileMetadataCompactSerializer(serializers.ModelSerializer):
    """紧凑文件元数据序列化器（用于列表和批量操作）"""
    
    class Meta:
        model = FileMetadata
        fields = [
            'file_id', 'original_filename', 'file_size', 'file_type',
            'file_category', 'status', 'created_at', 'visibility'
        ]
        
    def to_representation(self, instance):
        """自定义输出格式，添加友好的文件大小显示"""
        data = super().to_representation(instance)
        # 添加友好的文件大小显示
        if data.get('file_size'):
            size = data['file_size']
            if size < 1024:
                data['file_size_human'] = f"{size} B"
            elif size < 1024 * 1024:
                data['file_size_human'] = f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                data['file_size_human'] = f"{size / (1024 * 1024):.1f} MB"
            else:
                data['file_size_human'] = f"{size / (1024 * 1024 * 1024):.2f} GB"
        
        return data

# 修复原有的FileMetadataSerializer
def FileMetadataSerializerFix():
    """创建修复后的序列化器"""
    from rest_framework import serializers
    
    class FixedFileMetadataSerializer(serializers.ModelSerializer):
        class Meta:
            model = FileMetadata
            fields = [
                'file_id', 'original_filename', 'file_size', 'file_type',
                'mime_type', 'file_category', 'status', 'created_at',
                'visibility', 'tags', 'category', 'description'
            ]
        read_only_fields = ['file_id', 'file_size']
    
    return FixedFileMetadataSerializer


class FileUploadInitiateSerializer(serializers.Serializer):
    """文件上传初始化序列化器"""
    
    filename = serializers.CharField(max_length=255, required=True)
    file_size = serializers.IntegerField(required=True, min_value=1)
    mime_type = serializers.CharField(max_length=150, required=True)
    metadata = serializers.DictField(required=False, default=dict)
    
    def validate_filename(self, value):
        """验证文件名"""
        if not value or len(value) > 255:
            raise serializers.ValidationError("文件名长度必须在1-255字符之间")
        return value
    
    def validate_file_size(self, value):
        """验证文件大小"""
        # 限制总文件大小为500MB
        max_size = 500 * 1024 * 1024
        if value > max_size:
            raise serializers.ValidationError(
                f"文件大小超过限制 ({max_size // (1024*1024)}MB)"
            )
        if value <= 0:
            raise serializers.ValidationError("文件大小必须大于0")
        return value
    
    def validate_mime_type(self, value):
        """验证MIME类型"""
        from ..services import FileUploadConfig
        if value not in FileUploadConfig.ALLOWED_FILE_TYPES:
            raise serializers.ValidationError(f"不支持的文件类型: {value}")
        return value
    
    def validate(self, attrs):
        """进行整体验证"""
        from ..services import FileUploadConfig
        mime_type = attrs.get('mime_type')
        file_size = attrs.get('file_size')
        filename = attrs.get('filename')
        
        # 检查特定类型的大小限制
        if mime_type in FileUploadConfig.ALLOWED_FILE_TYPES:
            type_config = FileUploadConfig.ALLOWED_FILE_TYPES[mime_type]
            if file_size > type_config['max_size']:
                raise serializers.ValidationError(
                    f"{mime_type} 文件大小不能超过 {type_config['max_size'] // (1024*1024)}MB"
                )
        
        return attrs


class FileUploadPartSerializer(serializers.Serializer):
    """分片上传序列化器"""
    
    file_id = serializers.UUIDField(required=True)
    part_number = serializers.IntegerField(required=True, min_value=1)
    upload_id = serializers.CharField(max_length=256, required=True)
    
    def validate_part_number(self, value):
        """验证分片编号"""
        from . import FileUploadConfig
        if value > FileUploadConfig.MAX_CHUNKS:
            raise serializers.ValidationError(
                f"分片编号不能超过 {FileUploadConfig.MAX_CHUNKS}"
            )
        return value


class FileUploadCompleteSerializer(serializers.Serializer):
    """完成上传序列化器"""
    
    file_id = serializers.UUIDField(required=False)
    file_id_key = serializers.CharField(max_length=100, required=True)
    upload_id = serializers.CharField(max_length=256, required=True)
    parts = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    
    def validate_parts(self, value):
        """验证分片信息"""
        if not value:
            raise serializers.ValidationError("分片信息不能为空")
        
        # 验证每个分片的格式
        for part in value:
            if 'PartNumber' not in part or 'ETag' not in part:
                raise serializers.ValidationError("分片信息格式错误，必须包含 PartNumber 和 ETag")
        
        # 确保分片编号连续且从1开始
        sorted_parts = sorted(value, key=lambda x: x['PartNumber'])
        expected_numbers = list(range(1, len(sorted_parts) + 1))
        actual_numbers = [part['PartNumber'] for part in sorted_parts]
        
        if actual_numbers != expected_numbers:
            raise serializers.ValidationError("分片编号必须连续且从1开始")
        
        return sorted_parts
    
    def validate(self, attrs):
        """整体验证"""
        file_id_key = attrs.get('file_id_key')
        parts = attrs.get('parts')
        
        # 查找文件元数据
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id_key)
            attrs['file_id'] = file_metadata.id
        except FileMetadata.DoesNotExist:
            raise serializers.ValidationError("文件不存在")
        
        return attrs


class PresignedURLSerializer(serializers.ModelSerializer):
    """预签名URL序列化器"""
    
    class Meta:
        model = PresignedURL
        fields = [
            'id', 'url_id', 'url_type', 'url', 'expires_at',
            'max_uses', 'use_count', 'one_time_use', 'status',
            'requested_by', 'used_by', 'used_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'url_id', 'url', 'signature', 'status', 'used_by', 'used_at'
        ]


class FileShareSerializer(serializers.ModelSerializer):
    """文件分享序列化器"""
    
    class Meta:
        model = FileShare
        fields = [
            'id', 'share_id', 'share_url', 'allow_download',
            'allow_preview', 'permitir_comments', 'allow_reshare',
            'password_protected', 'max_downloads', 'download_count',
            'expires_at', 'created_by', 'description', 'metadata',
            'is_active', 'created_at', 'last_accessed_at'
        ]
        read_only_fields = [
            'id', 'share_id', 'share_url', 'download_count',
            'created_at', 'last_accessed_at'
        ]


class FileShareCreateSerializer(serializers.Serializer):
    """创建文件分享序列化器"""
    
    file_id = serializers.CharField(max_length=100, required=True)
    allow_download = serializers.BooleanField(default=True)
    allow_preview = serializers.BooleanField(default=True)
    permitir_comments = serializers.BooleanField(default=False)
    allow_reshare = serializers.BooleanField(default=False)
    password_protected = serializers.BooleanField(default=False)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True)
    expires_hours = serializers.IntegerField(min_value=1, max_value=8760, required=False)  # 最多1年
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_password(self, value):
        """验证密码"""
        if self.initial_data.get('password_protected') and not value:
            raise serializers.ValidationError("密码保护需要设置密码")
        return value
    
    def validate(self, attrs):
        """整体验证"""
        file_id = attrs.get('file_id')
        
        # 检查文件是否存在
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            if file_metadata.is_deleted:
                raise serializers.ValidationError("文件已被删除，无法分享")
        except FileMetadata.DoesNotExist:
            raise serializers.ValidationError("文件不存在")
        
        return attrs


class FileDownloadRequestSerializer(serializers.Serializer):
    """文件下载请求序列化器"""
    
    file_id = serializers.CharField(max_length=100, required=True)
    expires_in = serializers.IntegerField(min_value=60, max_value=3600, default=3600)


class FileDeleteSerializer(serializers.Serializer):
    """文件删除序列化器"""
    
    file_id = serializers.CharField(max_length=100, required=True)


class FileListFilterSerializer(serializers.Serializer):
    """文件列表过滤序列化器"""
    
    category = serializers.ChoiceField(
        choices=['document', 'image', 'video', 'audio', 'archive', 'other'],
        required=False
    )
    status = serializers.ChoiceField(
        choices=['uploading', 'processing', 'completed', 'failed', 'deleted'],
        required=False
    )
    file_type = serializers.CharField(max_length=100, required=False)
    search = serializers.CharField(max_length=255, required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)


class FileAuditLogSerializer(serializers.ModelSerializer):
    """文件审计日志序列化器"""
    
    class Meta:
        model = FileAuditLog
        fields = [
            'id', 'file_metadata', 'action', 'action_details',
            'performed_by', 'performed_at', 'ip_address',
            'user_agent', 'success', 'error_message'
        ]
        read_only_fields = [
            'id', 'performed_at'
        ]


class FileVersionSerializer(serializers.ModelSerializer):
    """文件版本序列化器"""
    
    class Meta:
        model = FileVersion
        fields = [
            'id', 'version_id', 'version_number', 'file_size',
            'file_hash', 'checksum', 'change_description',
            'created_by', 'created_at', 'is_current', 'metadata'
        ]
        read_only_fields = [
            'id', 'version_id', 'created_at'
        ]


class FileHealthCheckSerializer(serializers.Serializer):
    """健康检查序列化器"""
    
    status = serializers.CharField()
    timestamp = serializers.CharField()
    details = serializers.DictField(required=False)


class FileUploadResponseSerializer(serializers.Serializer):
    """文件上传响应序列化器"""
    
    file_id = serializers.CharField()
    upload_strategy = serializers.CharField()
    presigned_url = serializers.URLField(required=False, allow_null=True)
    storage_key = serializers.CharField()
    upload_id = serializers.CharField(required=False, allow_null=True)
    chunk_size = serializers.IntegerField(default=8 * 1024 * 1024)
    max_chunks = serializers.IntegerField(default=100)
    expires_in = serializers.IntegerField()


class FileDownloadResponseSerializer(serializers.Serializer):
    """文件下载响应序列化器"""
    
    file_id = serializers.CharField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    mime_type = serializers.CharField()
    download_url = serializers.URLField()
    expires_in = serializers.IntegerField()


class FileListResponseSerializer(serializers.Serializer):
    """文件列表响应序列化器"""
    
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    files = FileMetadataSerializer(many=True)


class FileShareResponseSerializer(serializers.Serializer):
    """文件分享响应序列化器"""
    
    share_id = serializers.CharField()
    share_url = serializers.URLField()
    expires_at = serializers.CharField(required=False, allow_null=True)
    password_protected = serializers.BooleanField()
    settings = serializers.DictField()


class FileErrorResponseSerializer(serializers.Serializer):
    """错误响应序列化器"""
    
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


class FileMetadataCompactSerializer(serializers.Serializer):
    """紧凑文件元数据序列化器（用于列表和批量操作）"""
    
    file_id = serializers.CharField()
    original_filename = serializers.CharField()
    file_size = serializers.IntegerField()
    file_type = serializers.CharField()
    file_category = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    visibility = serializers.CharField()


class FileBatchDeleteSerializer(serializers.Serializer):
    """批量删除序列化器"""
    
    file_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1
    )
    
    def validate_file_ids(self, value):
        """验证文件ID列表"""
        if len(value) > 100:
            raise serializers.ValidationError("一次最多删除100个文件")
        
        # 检查所有文件是否存在
        existing_files = FileMetadata.objects.filter(
            file_id__in=value
        ).count()
        
        if existing_files != len(value):
            raise serializers.ValidationError("部分文件不存在")
        
        return value


class FileBatchShareSerializer(serializers.Serializer):
    """批量分享序列化器"""
    
    file_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=10  # 最多分享10个文件
    )
    allow_download = serializers.BooleanField(default=True)
    allow_preview = serializers.BooleanField(default=True)
    expires_hours = serializers.IntegerField(min_value=1, max_value=8760, default=168)  # 默认7天
    
    def validate_file_ids(self, value):
        """验证文件ID列表"""
        if len(value) > 10:
            raise serializers.ValidationError("一次最多分享10个文件")
        return value


class FileSearchSerializer(serializers.Serializer):
    """文件搜索序列化器"""
    
    query = serializers.CharField(max_length=255, required=True)
    category = serializers.CharField(required=False)
    file_type = serializers.CharField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    size_min = serializers.IntegerField(required=False)
    size_max = serializers.IntegerField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=50, default=20)


class FileStatsSerializer(serializers.Serializer):
    """文件统计序列化器"""
    
    total_files = serializers.IntegerField()
    total_size = serializers.IntegerField()
    by_category = serializers.DictField()
    by_status = serializers.DictField()
    by_type = serializers.DictField()
    recent_uploads = serializers.IntegerField()
    storage_used = serializers.IntegerField()
    storage_available = serializers.IntegerField()


class FileQuotaSerializer(serializers.Serializer):
    """存储配额序列化器"""
    
    total_quota = serializers.IntegerField()
    used_quota = serializers.IntegerField()
    available_quota =  serializers.IntegerField()
    quota_percentage = serializers.FloatField()
    file_count = serializers.IntegerField()