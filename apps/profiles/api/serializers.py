from rest_framework import serializers, serializers
from django.utils import timezone
import uuid


class ContactProfileSerializer(serializers.ModelSerializer):
    """关联方档案序列化器"""
    
    id = serializers.UUIDField(read_only=True)
    aggregate_score = serializers.SerializerMethodField()
    profile_type_display = serializers.CharField(source='get_profile_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    class Meta:
        from apps.profiles.models import ContactProfile
        model = ContactProfile
        fields = [
            'id', 'profile_type', 'profile_type_display', 'name', 'company_name',
            'legal_person', 'registration_number', 'contact_info', 'industry',
            'business_scope', 'tags', 'status', 'status_display', 'credit_score',
            'quality_score', 'risk_level', 'risk_level_display', 'aggregate_score',
            'is_deleted', 'created_at', 'updated_at', 'last_contact_date'
        ]
        read_only_fields = ['id', 'aggregate_score', 'is_deleted']
    
    def get_aggregate_score(self, obj):
        """获取综合评分"""
        return obj.calculate_aggregate_score()


class ContactProfileCreateSerializer(serializers.ModelSerializer):
    """创建档案序列化器"""
    
    class Meta:
        from apps.profiles.models import ContactProfile
        model = ContactProfile
        fields = [
            'profile_type', 'name', 'company_name', 'legal_person', 'registration_number',
            'contact_info', 'industry', 'business_scope', 'tags', 'status',
            'credit_score', 'quality_score', 'risk_level'
        ]
    
    def validate_profile_type(self, value):
        """验证档案类型"""
        from apps.profiles.models import ContactProfile
        valid_types = [pt[0] for pt in ContactProfile.ProfileType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的档案类型。可选: {', '.join(valid_types)}")
        return value
    
    def validate_credit_score(self, value):
        """验证信用评分范围"""
        if self.instance is None or value != self.instance.credit_score:
            if not 0 <= value <= 100:
                raise serializers.ValidationError("信用评分必须在0-100之间")
        return value
    
    def validate_quality_score(self, value):
        """验证质量评分范围"""
        if self.instance is None or value != self.instance.quality_score:
            if not 0 <= value <= 100:
                raise serializers.ValidationError("质量评分必须在0-100之间")
        return value
    
    def validate_risk_level(self, value):
        """验证风险等级"""
        from apps.profiles.models import ContactProfile
        valid_levels = [level[0] for level in ['low', 'medium', 'high']]
        if value not in valid_levels:
            raise serializers.ValidationError(f"无效的风险等级。可选: {', '.join(valid_levels)}")
        return value


class ContactProfileListSerializer(serializers.ModelSerializer):
    """档案列表序列化器 - 精简版"""
    
    id = serializers.UUIDField(read_only=True)
    aggregate_score = serializers.SerializerMethodField()
    profile_type_display = serializers.CharField(source='get_profile_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    primary_contact_name = serializers.SerializerMethodField()
    
    class Meta:
        from apps.profiles.models import ContactProfile
        model = ContactProfile
        fields = [
            'id', 'profile_type', 'profile_type_display', 'name', 'company_name',
            'status', 'status_display', 'credit_score', 'quality_score',
            'risk_level', 'aggregate_score', 'primary_contact_name', 'created_at'
        ]
        read_only_fields = ['id', 'aggregate_score']
    
    def get_aggregate_score(self, obj):
        return obj.calculate_aggregate_score()
    
    def get_primary_contact_name(self, obj):
        primary = obj.get_primary_contact()
        return primary.name if primary else None


class ContactPersonSerializer(serializers.ModelSerializer):
    """联系人序列化器"""
    
    id = serializers.UUIDField(read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    
    class Meta:
        from apps.profiles.models import ContactPerson
        model = ContactPerson
        fields = [
            'id', 'profile', 'name', 'position', 'position_display',
            'position_other', 'contact_info', 'is_primary', 'is_active',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'profile']
    
    def validate(self, data):
        """验证联系人数据"""
        # 如果设置为主要联系人，确保该档案没有其他主要联系人
        is_primary = data.get('is_primary', False)
        if is_primary and not self.instance:
            from apps.profiles.models import ContactPerson
            # 对于新联系人，profile字段可能在验证阶段还没有related object
            # 这个验证将在view层处理
            pass
        return data


class InteractionHistorySerializer(serializers.ModelSerializer):
    """交互历史序列化器"""
    
    id = serializers.UUIDField(read_only=True)
    interaction_type_display = serializers.CharField(source='get_interaction_type_display', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    
    class Meta:
        from apps.profiles.models import InteractionHistory
        model = InteractionHistory
        fields = [
            'id', 'profile', 'profile_name', 'interaction_type', 'interaction_type_display',
            'title', 'description', 'related_event_id', 'related_project_id',
            'metadata', 'satisfaction_score', 'outcome_status', 'interaction_date',
            'created_at'
        ]
        read_only_fields = ['id', 'profile', 'profile_name']
    
    def validate_satisfaction_score(self, value):
        """验证满意度评分"""
        if value is not None:
            if not 1 <= value <= 5:
                raise serializers.ValidationError("满意度评分必须在1-5之间")
        return value


class ProfileEvaluationSerializer(serializers.ModelSerializer):
    """档案评估序列化器"""
    
    id = serializers.UUIDField(read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    evaluator_name = serializers.CharField(source='evaluator.username', read_only=True)
    
    class Meta:
        from apps.profiles.models import ProfileEvaluation
        model = ProfileEvaluation
        fields = [
            'id', 'profile', 'profile_name', 'evaluator', 'evaluator_name',
            'evaluation_date', 'credit_score', 'quality_score', 'service_quality',
            'response_speed', 'professional_ability', 'evaluation_criteria',
            'risk_assessment', 'risk_level', 'recommendations', 'overall_conclusion',
            'next_evaluation_date'
        ]
        read_only_fields = ['id', 'profile', 'profile_name', 'evaluator', 'evaluator_name']
    
    def validate_credit_score(self, value):
        """验证信用评分"""
        if value is not None:
            if not 0 <= value <= 100:
                raise serializers.ValidationError("信用评分必须在0-100之间")
        return value
    
    def validate_quality_score(self, value):
        """验证质量评分"""
        if value is not None:
            if not 0 <= value <= 100:
                raise serializers.ValidationError("质量评分必须在0-100之间")
        return value
    
    def validate_service_quality(self, value):
        """验证服务质量"""
        if value is not None:
            if not 1 <= value <= 5:
                raise serializers.ValidationError("服务质量评分必须在1-5之间")
        return value
    
    def validate_recommendations(self, value):
        """确保评估建议不为空"""
        if not value or not value.strip():
            raise serializers.ValidationError("评估建议不能为空")
        return value


class RecommendationRequestSerializer(serializers.Serializer):
    """智能推荐请求序列化器"""
    
    profile_type = serializers.ChoiceField(
        choices=['client', 'supplier', 'partner'],
        required=False,
        default='supplier'
    )
    event_type = serializers.CharField(required=False, allow_blank=True)
    min_credit_score = serializers.IntegerField(required=False, min_value=0, max_value=100)
    max_risk_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        required=False
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class RecommendationResponseSerializer(serializers.Serializer):
    """智能推荐响应序列化器"""
    
    profile_id = serializers.CharField()
    name = serializers.CharField()
    company_name = serializers.CharField(allow_null=True)
    profile_type = serializers.CharField()
    recommendation_score = serializers.IntegerField()
    reasons = serializers.ListField()
    credit_score = serializers.IntegerField()
    quality_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    primary_contact = serializers.CharField(allow_null=True)


class SearchRequestSerializer(serializers.Serializer):
    """搜索请求序列化器"""
    
    query = serializers.CharField(required=True, min_length=2)
    profile_type = serializers.ChoiceField(
        choices=['client', 'supplier', 'partner'],
        required=False
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)


class AnalyticsResponseSerializer(serializers.Serializer):
    """分析响应序列化器"""
    
    total_profiles = serializers.IntegerField()
    by_type = serializers.DictField()
    by_status = serializers.DictField()
    average_scores = serializers.DictField()
    risk_distribution = serializers.DictField()
    recent_interactions = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    high_score_count = serializers.IntegerField()


# 引入models以避免循环引用
from apps.profiles.models import (
    ContactProfile, ContactPerson, 
    InteractionHistory, ProfileEvaluation
)