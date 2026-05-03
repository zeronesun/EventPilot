from rest_framework import serializers
from django.db.models import Count, Sum, Q
from apps.events.models import Event, BudgetItem, EventParticipant, EventTemplate


class BudgetItemSerializer(serializers.ModelSerializer):
    """预算明细序列化器"""
    responsible_name = serializers.CharField(source='responsible.username', read_only=True, allow_null=True)
    
    class Meta:
        model = BudgetItem
        fields = [
            'id', 'event', 'category_name', 'name', 'estimated_amount',
            'actual_amount', 'variance', 'responsible', 'responsible_name',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'variance', 'created_at', 'updated_at']
    
    def validate_estimated_amount(self, value):
        """验证预算金额"""
        if value is not None and value < 0:
            raise serializers.ValidationError("预估金额不能为负数")
        return value


class EventParticipantSerializer(serializers.ModelSerializer):
    """活动参与者序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = EventParticipant
        fields = [
            'id', 'event', 'user', 'user_name', 'user_email',
            'role', 'joined_at', 'active'
        ]
        read_only_fields = ['id', 'joined_at']


class EventSerializer(serializers.ModelSerializer):
    """活动序列化器"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    
    # 计算字段
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    budget_usage_rate = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    
    # 嵌套序列化
    budget_items = BudgetItemSerializer(many=True, read_only=True)
    participants = EventParticipantSerializer(source='eventparticipant_set', many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'type', 'description', 'start_date', 'end_date',
            'client', 'client_contact', 'estimated_budget', 'actual_budget',
            'budget_variance', 'status', 'owner', 'owner_name', 'owner_email',
            'created_at', 'updated_at', 'completed_at',
            'tasks_count', 'completed_tasks_count', 'progress_percentage',
            'budget_usage_rate', 'participants_count',
            'budget_items', 'participants'
        ]
        read_only_fields = [
            'id', 'actual_budget', 'budget_variance', 'created_at', 
            'updated_at', 'completed_at', 'progress_percentage', 'budget_usage_rate'
        ]
    
    def validate(self, data):
        """验证活动数据"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("结束时间必须大于开始时间")
        
        # 阶段性验证：状态转换
        if 'status' in data and self.instance:
            from apps.events.services.event_service import EventService
            is_valid, errors = EventService.validate_status_transition(
                self.instance.status, data['status']
            )
            if not is_valid:
                raise serializers.ValidationError({'status': errors})
        
        return data
    
    def validate_estimated_budget(self, value):
        """验证预算金额"""
        if value is not None and value < 0:
            raise serializers.ValidationError("预估预算不能为负数")
        return value
    
    def validate_type(self, value):
        """验证活动类型"""
        from apps.events.services.event_service import EventService
        valid_types = list(EventService.EVENT_TYPES.keys())
        if value not in valid_types:
            raise serializers.ValidationError(f"活动类型无效，有效值：{', '.join(valid_types)}")
        return value
    
    def get_tasks_count(self, obj):
        """获取任务总数"""
        return obj.tasks.count()
    
    def get_completed_tasks_count(self, obj):
        """获取已完成任务数"""
        return obj.tasks.filter(status='completed').count()
    
    def get_progress_percentage(self, obj):
        """获取进度百分比"""
        tasks_count = self.get_tasks_count(obj)
        if tasks_count == 0:
            return 0
        completed = self.get_completed_tasks_count(obj)
        return round((completed / tasks_count) * 100, 2)
    
    def get_budget_usage_rate(self, obj):
        """获取预算使用率"""
        if obj.estimated_budget and obj.estimated_budget > 0:
            return round((obj.actual_budget / obj.estimated_budget) * 100, 2)
        return 0
    
    def get_participants_count(self, obj):
        """获取参与者数量"""
        return obj.eventparticipant_set.filter(active=True).count()


class EventCreateSerializer(serializers.ModelSerializer):
    """活动创建序列化器"""
    budget_items = BudgetItemSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Event
        fields = [
            'name', 'type', 'description', 'start_date', 'end_date',
            'client', 'client_contact', 'estimated_budget',
            'budget_items'
        ]
    
    def validate(self, data):
        """验证创建数据"""
        from apps.events.services.event_service import EventService
        
        # 添加owner
        if 'owner' not in data and 'owner_id' not in data:
            data['owner'] = self.context['request'].user
        
        # 使用service验证
        is_valid, errors = EventService.validate_event_data(data)
        if not is_valid:
            raise serializers.ValidationError({'non_field_errors': errors})
        
        return data


class EventUpdateSerializer(serializers.ModelSerializer):
    """活动更新序列化器"""
    budget_items = BudgetItemSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Event
        fields = [
            'name', 'type', 'description', 'start_date', 'end_date',
            'client', 'client_contact', 'estimated_budget', 'status',
            'budget_items'
        ]
    
    def validate(self, data):
        """验证更新数据"""
        from apps.events.services.event_service import EventService
        
        # 合并现有数据和更新数据
        update_data = {
            'name': data.get('name', self.instance.name),
            'type': data.get('type', self.instance.type),
            'start_date': data.get('start_date', self.instance.start_date),
            'end_date': data.get('end_date', self.instance.end_date),
        }
        
        # 安全获取 owner_id
        try:
            owner_id = self.instance.owner_id
            if owner_id:
                update_data['owner_id'] = str(owner_id)
        except Exception:
            pass
        
        # 添加可选字段
        if 'estimated_budget' in data:
            update_data['estimated_budget'] = data['estimated_budget']
        
        is_valid, errors = EventService.validate_event_data(update_data)
        
        if not is_valid:
            raise serializers.ValidationError({'non_field_errors': errors})
        
        return data


class EventListSerializer(serializers.ModelSerializer):
    """活动列表序列化器（简化版）"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    tasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    budget_usage_rate = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'type', 'start_date', 'end_date', 'client',
            'estimated_budget', 'actual_budget', 'budget_variance',
            'status', 'owner_name', 'owner_email', 'tasks_count',
            'progress_percentage', 'budget_usage_rate', 'is_overdue',
            'created_at'
        ]
    
    def get_tasks_count(self, obj):
        """获取任务数量"""
        return obj.tasks.count()
    
    def get_progress_percentage(self, obj):
        """获取进度百分比"""
        tasks_count = self.get_tasks_count(obj)
        if tasks_count == 0:
            return 0
        return round((obj.tasks.filter(status='completed').count() / tasks_count) * 100, 2)
    
    def get_budget_usage_rate(self, obj):
        """获取预算使用率"""
        if obj.estimated_budget and obj.estimated_budget > 0:
            return round((obj.actual_budget / obj.estimated_budget) * 100, 2)
        return 0
    
    def get_is_overdue(self, obj):
        """检查是否超期"""
        from apps.events.services.event_service import EventService
        return EventService._is_overdue(obj)


class EventStatisticsSerializer(serializers.Serializer):
    """活动统计序列化器"""
    tasks = serializers.DictField()
    budget = serializers.DictField()
    timeline = serializers.DictField()


class EventRiskAssessmentSerializer(serializers.Serializer):
    """活动风险评估序列化器"""
    level = serializers.CharField(max_length=20)
    factors = serializers.ListField(child=serializers.DictField())
    recommendations = serializers.ListField(child=serializers.CharField())


class EventTemplateSerializer(serializers.ModelSerializer):
    """活动模板序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    usage_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = EventTemplate
        fields = [
            'id', 'name', 'category', 'description', 'default_duration_days',
            'default_budget', 'task_templates', 'budget_templates',
            'usage_count', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']