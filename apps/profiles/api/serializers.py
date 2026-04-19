from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, ProfileEventAssociation

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """关联方档案序列化器"""
    profile_type_display = serializers.CharField(source='get_profile_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    events = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'profile_type', 'profile_type_display', 'name', 'contact_info',
            'cooperation_history', 'notes', 'tags', 'rating', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_events(self, obj):
        """获取关联的活动列表"""
        associations = obj.event_associations.all()
        return [
            {
                'event_id': str(assoc.event.id),
                'event_name': assoc.event.name,
                'role': assoc.role
            }
            for assoc in associations
        ]
    
    def validate_rating(self, value):
        """验证评分"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("评分必须在1-5之间")
        return value
    
    def validate_contact_info(self, value):
        """验证联系信息"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("联系信息必须是字典格式")
        
        # 简单验证：确保包含必要字段
        if 'email' not in value and 'phone' not in value:
            raise serializers.ValidationError("联系信息必须包含email或phone")
        
        return value


class ProfileSimpleSerializer(serializers.ModelSerializer):
    """档案简化序列化器（用于选择器等）"""
    
    class Meta:
        model = Profile
        fields = ['id', 'profile_type', 'name', 'rating']


class ProfileEventAssociationSerializer(serializers.ModelSerializer):
    """档案-活动关联序列化器"""
    
    class Meta:
        model = ProfileEventAssociation
        fields = ['profile', 'event', 'role']
        read_only_fields = ['created_at']


class ProfileListSerializer(serializers.ModelSerializer):
    """档案列表序列化器（带筛选字段）"""
    profile_type_display = serializers.CharField(source='get_profile_type_display', read_only=True)
    associated_events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'profile_type', 'profile_type_display', 'name',
            'tags', 'rating', 'associated_events_count'
        ]
    
    def get_associated_events_count(self, obj):
        """获取关联活动数量"""
        return obj.event_associations.count()