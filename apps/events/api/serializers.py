from rest_framework import serializers
from apps.events.models import Event, BudgetItem


class EventSerializer(serializers.ModelSerializer):
    """活动序列化器"""
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'type', 'description', 'start_date', 'end_date',
            'client', 'client_contact', 'estimated_budget', 'actual_budget',
            'budget_variance', 'status', 'owner', 'created_at', 'updated_at',
            'completed_at'
        ]
        read_only_fields = [
            'id', 'actual_budget', 'budget_variance', 'created_at', 
            'updated_at', 'completed_at'
        ]
    
    def validate(self, data):
        """验证活动数据"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("结束时间必须大于开始时间")
        
        return data
    
    def validate_estimated_budget(self, value):
        """验证预算金额"""
        if value is not None and value < 0:
            raise serializers.ValidationError("预估预算不能为负数")
        return value


class EventListSerializer(serializers.ModelSerializer):
    """活动列表序列化器（简化版）"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'type', 'start_date', 'end_date', 'client',
            'estimated_budget', 'actual_budget', 'budget_variance', 
            'status', 'owner_name', 'tasks_count', 'created_at'
        ]
    
    def get_tasks_count(self, obj):
        """获取任务数量"""
        return obj.tasks.count()


class BudgetItemSerializer(serializers.ModelSerializer):
    """预算明细序列化器"""
    
    class Meta:
        model = BudgetItem
        fields = [
            'id', 'event', 'category_name', 'name', 'estimated_amount',
            'actual_amount', 'variance', 'responsible', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'variance', 'created_at', 'updated_at']
    
    def validate_estimated_amount(self, value):
        """验证预算金额"""
        if value is not None and value < 0:
            raise serializers.ValidationError("预估金额不能为负数")
        return value