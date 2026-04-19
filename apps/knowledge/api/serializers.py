from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import KnowledgeEntry

User = get_user_model()


class KnowledgeEntrySerializer(serializers.ModelSerializer):
    """知识条目序列化器"""
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeEntry
        fields = [
            'id', 'entry_type', 'entry_type_display', 'title', 'content', 'content_preview',
            'tags', 'category', 'related_events', 'related_tasks', 'is_public', 
            'is_verified', 'popularity', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'popularity', 'created_at', 'updated_at']
    
    def get_content_preview(self, obj):
        """获取内容预览（前200字符）"""
        return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
    
    def validate_tags(self, value):
        """验证标签"""
        if not isinstance(value, list):
            raise serializers.ValidationError("标签必须是列表格式")
        if len(value) > 10:
            raise serializers.ValidationError("标签不能超过10个")
        return value
    
    def validate_related_events(self, value):
        """验证关联活动"""
        if not isinstance(value, list):
            raise serializers.ValidationError("关联活动必须是列表格式")
        return value
    
    def validate_related_tasks(self, value):
        """验证关联任务"""
        if not isinstance(value, list):
            raise serializers.ValidationError("关联任务必须是列表格式")
        return value
    
    def create(self, validated_data):
        """创建时自动设置初始流行度"""
        validated_data['popularity'] = 0
        return super().create(validated_data)


class KnowledgeEntryListSerializer(serializers.ModelSerializer):
    """知识条目列表序列化器（简化版）"""
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)
    author_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KnowledgeEntry
        fields = [
            'id', 'entry_type', 'entry_type_display', 'title', 'category',
            'tags', 'is_public', 'is_verified', 'popularity',
            'author_name', 'created_at'
        ]


class KnowledgeEntryUpdateSerializer(serializers.ModelSerializer):
    """知识条目更新序列化器（部分字段）"""
    
    class Meta:
        model = KnowledgeEntry
        fields = ['title', 'content', 'tags', 'category', 'is_public', 'is_verified']