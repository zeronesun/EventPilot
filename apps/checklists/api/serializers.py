from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.checklists.models import (
    ChecklistTemplate, ChecklistItemTemplate, ChecklistInstance, ChecklistItem,
    ChecklistVersion, ChecklistVersionComparison, ChecklistExport, ChecklistImport,
    ChecklistVerification, ChecklistVerificationDetail, ChecklistVerificationException
)
from apps.checklists.services.checklist_service import ChecklistService

User = get_user_model()


class ChecklistItemTemplateSerializer(serializers.ModelSerializer):
    """核验清单项模板序列化器"""
    
    class Meta:
        model = ChecklistItemTemplate
        fields = [
            'id', 'template', 'title', 'description', 'required', 
            'order', 'weight', 'status', 'metadata'
        ]
        read_only_fields = ['id']

    def validate_weight(self, value):
        """验证权重"""
        if value < ChecklistService.ITEM_WEIGHT_RANGE[0] or value > ChecklistService.ITEM_WEIGHT_RANGE[1]:
            raise serializers.ValidationError(
                f'权重必须在{ChecklistService.ITEM_WEIGHT_RANGE[0]}-{ChecklistService.ITEM_WEIGHT_RANGE[1]}之间'
            )
        return value
    
    def validate_status(self, value):
        """验证状态"""
        if value not in ['active', 'inactive']:
            raise serializers.ValidationError('状态必须是active或inactive')
        return value


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    """核验清单模板序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    items = ChecklistItemTemplateSerializer(many=True, required=False)
    items_count = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistTemplate
        fields = [
            'id', 'name', 'description', 'checklist_type', 'event_types', 
            'version', 'status', 'category', 'tags', 'metadata',
            'is_default', 'created_by', 'created_by_name', 'created_at', 'updated_at',
            'items', 'items_count', 'statistics'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'items_count', 'statistics']
    
    def get_items_count(self, obj):
        """获取清单项数量"""
        return obj.items.count()
    
    def get_statistics(self, obj):
        """获取模板统计信息"""
        try:
            return ChecklistService.get_template_statistics(obj)
        except Exception as e:
            return {'error': str(e)}
    
    def validate_status(self, value):
        """验证模板状态"""
        if value not in ChecklistService.TEMPLATE_STATUS:
            raise serializers.ValidationError(
                f'模板状态无效，有效值：{", ".join(ChecklistService.TEMPLATE_STATUS)}'
            )
        return value
    
    def validate_checklist_type(self, value):
        """验证清单类型"""
        if value not in ChecklistService.CHECKLIST_TYPES:
            raise serializers.ValidationError(
                f'清单类型无效，有效值：{", ".join(ChecklistService.CHECKLIST_TYPES.keys())}'
            )
        return value
    
    def create(self, validated_data):
        """创建模板"""
        items_data = validated_data.pop('items', None)
        
        template, errors = ChecklistService.create_template(validated_data, self.context['request'].user)
        
        if errors:
            raise serializers.ValidationError({'errors': errors})
        
        # 处理清单项
        if items_data:
            ChecklistService._create_template_items(template, items_data)
        
        return template
    
    def update(self, instance, validated_data):
        """更新模板"""
        items_data = validated_data.pop('items', None)
        
        # 处理清单项更新
        if items_data is not None:
            validated_data['items'] = items_data
        
        success, errors = ChecklistService.update_template(instance, validated_data, self.context['request'].user)
        
        if not success:
            raise serializers.ValidationError({'errors': errors})
        
        return instance


class ChecklistItemSerializer(serializers.ModelSerializer):
    """核验清单项序列化器"""
    checked_by_name = serializers.CharField(source='checked_by.username', read_only=True)
    template_title = serializers.CharField(source='template_item.title', read_only=True, allow_null=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistItem
        fields = [
            'id', 'instance', 'template_item', 'template_title', 
            'title', 'description', 'required', 'order', 'weight',
            'status', 'notes', 'attachments', 'checked_by', 'checked_by_name', 
            'checked_at', 'location', 'offline_pending', 'metadata',
            'created_at', 'updated_at', 'completion_percentage'
        ]
        read_only_fields = ['id', 'checked_at', 'created_at', 'updated_at', 'completion_percentage']
    
    def get_completion_percentage(self, obj):
        """获取完成百分比（基于状态）"""
        if obj.status == 'passed':
            return 100
        elif obj.status == 'failed':
            return 0
        elif obj.status == 'skipped':
            return 100
        elif obj.status == 'in_progress':
            return 50
        else:
            return 0
    
    def validate_status(self, value):
        """验证核验状态"""
        valid_statuses = [choice[0] for choice in ChecklistItem.CheckStatus.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"无效的状态，可选值：{valid_statuses}")
        return value
    
    def validate_weight(self, value):
        """验证权重"""
        if value < ChecklistService.ITEM_WEIGHT_RANGE[0] or value > ChecklistService.ITEM_WEIGHT_RANGE[1]:
            raise serializers.ValidationError(
                f'权重必须在{ChecklistService.ITEM_WEIGHT_RANGE[0]}-{ChecklistService.ITEM_WEIGHT_RANGE[1]}之间'
            )
        return value


class ChecklistItemUpdateSerializer(serializers.ModelSerializer):
    """核验清单项更新序列化器（简化版）"""
    
    class Meta:
        model = ChecklistItem
        fields = ['status', 'notes', 'attachments', 'location', 'metadata']

    def validate_status(self, value):
        """验证核验状态"""
        valid_statuses = ['pending', 'in_progress', 'passed', 'failed', 'skipped']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"无效的状态，可选值：{valid_statuses}")
        return value


class ChecklistInstanceSerializer(serializers.ModelSerializer):
    """核验清单实例序列化器"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    items = ChecklistItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    completion_percentage = serializers.FloatField(read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_id = serializers.UUIDField(source='event.id', read_only=True)
    
    class Meta:
        model = ChecklistInstance
        fields = [
            'id', 'event', 'event_id', 'event_name', 'template', 'template_name', 
            'name', 'status', 'completion_rate', 'completion_percentage',
            'items_count', 'items', 'progress', 'metadata',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'completion_rate', 'items_count', 'created_at', 'updated_at', 'completed_at']
    
    def get_items_count(self, obj):
        """获取清单项数量"""
        return obj.items.count()
    
    def get_progress(self, obj):
        """获取进度信息"""
        try:
            return ChecklistService.get_instance_progress(obj)
        except Exception as e:
            return {'error': str(e)}
    
    def validate_status(self, value):
        """验证实例状态"""
        if value not in ['incomplete', 'in_progress', 'pending_review', 'completed', 'cancelled']:
            raise serializers.ValidationError('状态无效')
        return value
    
    def create(self, validated_data):
        """创建清单实例"""
        instance, errors = ChecklistService.create_instance(validated_data, self.context['request'].user)
        
        if not instance:
            raise serializers.ValidationError({'errors': errors})
        
        return instance
    
    def update(self, instance, validated_data):
        """更新清单实例"""
        success, errors = ChecklistService.update_instance(instance, validated_data, self.context['request'].user)
        
        if not success:
            raise serializers.ValidationError({'errors': errors})
        
        return instance


class ChecklistTemplateDetailSerializer(ChecklistTemplateSerializer):
    """清单模板详情序列化器（包含完整的清单项信息）"""
    items = ChecklistItemTemplateSerializer(many=True)
    
    class Meta(ChecklistTemplateSerializer.Meta):
        fields = ChecklistTemplateSerializer.Meta.fields


class ChecklistInstanceDetailSerializer(ChecklistInstanceSerializer):
    """清单实例详情序列化器（包含完整的清单项信息）"""
    warnings = serializers.SerializerMethodField()
    
    class Meta(ChecklistInstanceSerializer.Meta):
        fields = ChecklistInstanceSerializer.Meta.fields + ['warnings']
    
    def get_warnings(self, obj):
        """获取警告信息"""
        try:
            return ChecklistService.get_completion_warnings(obj)
        except Exception as e:
            return [{'type': 'error', 'message': str(e)}]


class ChecklistReportSerializer(serializers.Serializer):
    """清单报告序列化器"""
    instance = serializers.DictField()
    event = serializers.DictField()
    template = serializers.DictField()
    progress = serializers.DictField()
    items = serializers.ListField()


class ChecklistSummarySerializer(serializers.Serializer):
    """清单摘要序列化器"""
    total_instances = serializers.IntegerField()
    completed_instances = serializers.IntegerField()
    in_progress_instances = serializers.IntegerField()
    average_completion_rate = serializers.FloatField()
    recent_activity = serializers.ListField()


# 清单版本相关序列化器
class ChecklistVersionSerializer(serializers.ModelSerializer):
    """清单版本序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ChecklistVersion
        fields = [
            'id', 'template', 'instance', 'version_number', 'version_type',
            'changelog', 'changes', 'is_active', 'is_rollback',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by_name', 'created_at']
    
    def validate_version_type(self, value):
        """验证版本类型"""
        valid_types = ['major', 'minor', 'patch']
        if value not in valid_types:
            raise serializers.ValidationError(f'版本类型无效，有效值：{", ".join(valid_types)}')
        return value


class ChecklistVersionComparisonSerializer(serializers.ModelSerializer):
    """清单版本对比序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    from_version_number = serializers.CharField(source='from_version.version_number', read_only=True)
    to_version_number = serializers.CharField(source='to_version.version_number', read_only=True)
    
    class Meta:
        model = ChecklistVersionComparison
        fields = [
            'id', 'from_version', 'to_version', 'from_version_number', 
            'to_version_number', 'differences', 'summary', 'created_by', 
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by_name', 'created_at']


# 清单导出相关序列化器
class ChecklistExportSerializer(serializers.ModelSerializer):
    """清单导出序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    instance_name = serializers.CharField(source='instance.name', read_only=True, allow_null=True)
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ChecklistExport
        fields = [
            'id', 'instance', 'template', 'instance_name', 'template_name',
            'export_format', 'include_items', 'include_attachments', 
            'include_metadata', 'status', 'file_path', 'file_url', 
            'file_size', 'error_message', 'created_by', 'created_by_name',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'file_path', 'file_url', 
                          'file_size', 'error_message', 'created_by_name', 
                          'created_at', 'completed_at']
    
    def validate_export_format(self, value):
        """验证导出格式"""
        valid_formats = ['csv', 'excel', 'pdf', 'json']
        if value not in valid_formats:
            raise serializers.ValidationError(f'导出格式无效，有效值：{", ".join(valid_formats)}')
        return value


class ChecklistImportSerializer(serializers.ModelSerializer):
    """清单导入序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ChecklistImport
        fields = [
            'id', 'import_format', 'file_path', 'file_size',
            'create_template', 'create_instance', 'update_existing',
            'status', 'total_records', 'processed_records', 
            'success_records', 'failed_records', 'error_message',
            'validation_errors', 'created_by', 'created_by_name',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'total_records', 'processed_records',
                          'success_records', 'failed_records', 'error_message',
                          'validation_errors', 'created_by_name', 'created_at', 
                          'completed_at']


# 清单核验相关序列化器
class ChecklistVerificationSerializer(serializers.ModelSerializer):
    """清单核验序列化器"""
    instance_name = serializers.CharField(source='instance.name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ChecklistVerification
        fields = [
            'id', 'instance', 'instance_name', 'planned_start_time',
            'planned_end_time', 'actual_start_time', 'actual_end_time',
            'status', 'approval_status', 'total_items', 'verified_items',
            'passed_items', 'failed_items', 'requires_approval',
            'verified_by', 'verified_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'rejection_reason', 'has_exceptions', 
            'exception_details', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified_by_name', 'approved_by_name', 
                          'approved_at', 'created_at', 'updated_at']
    
    def validate_status(self, value):
        """验证核验状态"""
        valid_statuses = [
            'pending', 'in_progress', 'on_hold', 
            'completed', 'failed', 'cancelled'
        ]
        if value not in valid_statuses:
            raise serializers.ValidationError(f'状态无效，有效值：{", ".join(valid_statuses)}')
        return value
    
    def validate_approval_status(self, value):
        """验证审批状态"""
        valid_statuses = ['not_required', 'pending', 'approved', 'rejected']
        if value not in valid_statuses:
            raise serializers.ValidationError(f'审批状态无效，有效值：{", ".join(valid_statuses)}')
        return value


class ChecklistVerificationDetailSerializer(serializers.ModelSerializer):
    """清单核验详情序列化器"""
    item_title = serializers.CharField(source='checklist_item.title', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ChecklistVerificationDetail
        fields = [
            'id', 'verification', 'checklist_item', 'item_title',
            'status', 'result', 'evidence', 'attachments',
            'verified_at', 'location', 'verified_by', 'verified_by_name',
            'notes', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'verified_at', 'created_at']


class ChecklistVerificationExceptionSerializer(serializers.ModelSerializer):
    """清单核验异常序列化器"""
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)
    item_title = serializers.CharField(source='checklist_item.title', read_only=True, allow_null=True)
    
    class Meta:
        model = ChecklistVerificationException
        fields = [
            'id', 'verification', 'checklist_item', 'item_title',
            'exception_type', 'status', 'title', 'description',
            'severity', 'assigned_to', 'assigned_to_name',
            'resolution', 'resolved_by', 'resolved_by_name',
            'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'resolved_at', 'created_at', 'updated_at']
    
    def validate_exception_type(self, value):
        """验证异常类型"""
        valid_types = [
            'missing_item', 'failed_validation', 'timeout',
            'access_denied', 'system_error', 'other'
        ]
        if value not in valid_types:
            raise serializers.ValidationError(f'异常类型无效，有效值：{", ".join(valid_types)}')
        return value
    
    def validate_status(self, value):
        """验证异常状态"""
        valid_statuses = ['open', 'in_progress', 'resolved', 'ignored']
        if value not in valid_statuses:
            raise serializers.ValidationError(f'状态无效，有效值：{", ".join(valid_statuses)}')
        return value
