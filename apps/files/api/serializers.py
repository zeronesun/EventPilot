from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    FileMetadata,
    PresignedURL,
    FileShare,
    FileAuditLog,
    FileVersion,
    FilePreviewCache,
)
from ..services import FileUploadConfig

User = get_user_model()


class FileMetadataSerializer(serializers.ModelSerializer):
    """文件元数据序列化器"""
    
    class Meta:
        model = FileMetadata
        fields = [
            'id',
            'file_id',
            'original_filename',
            'stored_filename',
            'file_size',
            'file_type',
            'mime_type',
            'file_category',
            'status',
            'visibility',
            'tags',
            'category',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_id',
            'stored_filename',
            'created_at',
            'updated_at',
        ]


class FileMetadataCompactSerializer(serializers.ModelSerializer):
    """紧凑文件元数据序列化器"""
    
    file_size_human = serializers.SerializerMethodField()
    
    class Meta:
        model = FileMetadata
        fields = [
            'file_id',
            'original_filename',
            'file_size',
            'file_size_human',
            'file_type',
            'file_category',
            'status',
            'created_at',
            'visibility',
        ]
    
    def get_file_size_human(self, obj):
        """获取友好的文件大小显示"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


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
        max_size = 500 * 1024 * 1024
        if value > max_size:
            raise serializers.ValidationError(f"文件大小超过限制 ({max_size // (1024 * 1024)}MB)")
        if value <= 0:
            raise serializers.ValidationError("文件大小必须大于0")
        return value
    
    def validate_mime_type(self, value):
        """验证MIME类型"""
        if value not in FileUploadConfig.ALLOWED_FILE_TYPES:
            raise serializers.ValidationError(f"不支持的文件类型: {value}")
        return value


class FileDownloadRequestSerializer(serializers.Serializer):
    """文件下载请求序列化器"""
    
    file_id = serializers.CharField(max_length=100, required=True)
    expires_in = serializers.IntegerField(min_value=60, max_value=3600, default=3600, required=False)


class FileShareCreateSerializer(serializers.Serializer):
    """创建文件分享序列化器"""
    
    file_id = serializers.CharField(max_length=100, required=True)
    allow_download = serializers.BooleanField(default=True)
    allow_preview = serializers.BooleanField(default=True)
    expires_hours = serializers.IntegerField(min_value=1, max_value=8760, required=False)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)


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
    page = serializers.IntegerField(min_value=1, default=1, required=False)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20, required=False)


class FileUploadResponseSerializer(serializers.Serializer):
    """文件上传响应序列化器"""
    
    file_id = serializers.CharField()
    upload_strategy = serializers.CharField()
    presigned_url = serializers.CharField(required=False, allow_blank=True)
    upload_id = serializers.CharField(required=False, allow_blank=True)
    storage_key = serializers.CharField()
    chunk_size = serializers.IntegerField()
    max_chunks = serializers.IntegerField()
    expires_in = serializers.IntegerField()


class FileDownloadResponseSerializer(serializers.Serializer):
    """文件下载响应序列化器"""
    
    file_id = serializers.CharField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    mime_type = serializers.CharField()
    download_url = serializers.CharField()
    expires_in = serializers.IntegerField()


class FileListResponseSerializer(serializers.Serializer):
    """文件列表响应序列化器"""
    
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    files = FileMetadataCompactSerializer(many=True)


class FileShareResponseSerializer(serializers.Serializer):
    """文件分享响应序列化器"""
    
    share_id = serializers.CharField()
    share_url = serializers.CharField()
    expires_at = serializers.CharField(required=False, allow_null=True)
    password_protected = serializers.BooleanField()
    settings = serializers.DictField()


class FileErrorResponseSerializer(serializers.Serializer):
    """错误响应序列化器"""
    
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


class FileBatchDeleteSerializer(serializers.Serializer):
    """批量删除序列化器"""
    
    file_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1
    )
