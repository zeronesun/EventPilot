from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate, ChecklistInstance, ChecklistItem

User = get_user_model()


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    """核验清单模板序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ChecklistTemplate
        fields = [
            'id', 'name', 'description', 'event_types', 'is_default',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChecklistItemTemplateSerializer(serializers.ModelSerializer):
    """核验清单项模板序列化器"""
    
    class Meta:
        model = ChecklistItemTemplate
        fields = ['id', 'template', 'title', 'description', 'required', 'order']
        read_only_fields = ['id']


class ChecklistInstanceSerializer(serializers.ModelSerializer):
    """核验清单实例序列化器"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistInstance
        fields = [
            'id', 'event', 'template', 'template_name', 'name', 'status',
            'items_count', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'items_count', 'created_at', 'updated_at', 'completed_at']
    
    def get_items_count(self, obj):
        """获取清单项数量"""
        return obj.items.count()


class ChecklistItemSerializer(serializers.ModelSerializer):
    """核验清单项序列化器"""
    checked_by_name = serializers.CharField(source='checked_by.username', read_only=True)
    template_title = serializers.CharField(source='template_item.title', read_only=True)
    
    class Meta:
        model = ChecklistItem
        fields = [
            'id', 'instance', 'template_item', 'template_title', 'title', 'notes',
            'attachments', 'status', 'checked_by', 'checked_by_name', 
            'checked_at', 'location', 'offline_pending', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'checked_at', 'created_at', 'updated_at']
    
    def validate_status(self, value):
        """验证核验状态"""
        valid_statuses = [choice[0] for choice in ChecklistItem.CheckStatus.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"无效的状态，可选值: {valid_statuses}")
        return value


class ChecklistItemUpdateSerializer(serializers.ModelSerializer):
    """核验清单项更新序列化器（简化版）"""
    
    class Meta:
        model = ChecklistItem
        fields = ['status', 'notes', 'attachments', 'checked_by']

    def validate_status(self, value):
        """验证核验状态"""
        if value not in ['pending', 'in_progress', 'passed', 'failed', 'skipped']:
            raise serializers.ValidationError("无效的状态")
        return value