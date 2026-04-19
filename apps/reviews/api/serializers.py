from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review
from apps.events.models import Event

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    """复盘序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'event', 'event_name', 'title', 'status', 'status_display',
            'goal_achievement', 'process_execution', 'cost_control',
            'customer_feedback', 'team_collaboration', 'successes',
            'improvements', 'action_items', 'related_issues', 'created_by',
            'created_by_name', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def validate_event(self, value):
        """验证活动是否存在"""
        if isinstance(value, str):  # UUID字符串
            try:
                Event.objects.get(id=value)
            except Event.DoesNotExist:
                raise serializers.ValidationError("指定的活动不存在")
        return value
    
    def validate_related_issues(self, value):
        """验证相关问题"""
        if not isinstance(value, list):
            raise serializers.ValidationError("相关问题必须是列表格式")
        return value


class ReviewSimpleSerializer(serializers.ModelSerializer):
    """复盘简化序列化器"""
    class Meta:
        model = Review
        fields = ['id', 'event', 'title', 'status', 'completed_at']


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """复盘更新序列化器（部分字段）"""
    
    class Meta:
        model = Review
        fields = [
            'status', 'goal_achievement', 'process_execution', 'cost_control',
            'customer_feedback', 'team_collaboration', 'successes',
            'improvements', 'action_items', 'related_issues'
        ]