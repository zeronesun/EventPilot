from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tasks.models import Task, TaskDependency, CommunicationTask

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    assignee_name = serializers.CharField(source='assignee.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    depends_on = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'event', 'title', 'description', 'task_type', 'assignee',
            'assignee_name', 'status', 'progress', 'due_date', 'start_date',
            'completed_at', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'progress', 'completed_at', 'created_at', 'updated_at'
        ]
    
    def get_depends_on(self, obj):
        """获取依赖任务"""
        dependencies = obj.dependencies.all()
        return [dep.depends_on.id for dep in dependencies]
    
    def validate_duedate(self, value):
        """验证截止日期"""
        if value and not self.instance.start_date and value < self.instance.start_date:
            raise serializers.ValidationError("截止日期不能早于开始日期")
        return value
    
    def validate_progress(self, value):
        """验证进度百分比"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("进度必须在0-100之间")
        return value


class TaskDependencySerializer(serializers.ModelSerializer):
    """任务依赖序列化器"""

    class Meta:
        model = TaskDependency
        fields = ['task', 'depends_on', 'created_at']
        read_only_fields = ['created_at']


class CommunicationTaskSerializer(serializers.ModelSerializer):
    """沟通任务序列化器"""
    
    class Meta:
        model = CommunicationTask
        fields = [
            'id', 'task', 'content', 'requirements', 'communicators',
            'conclusion_files', 'is_closed'
        ]
    
    def validate_communicators(self, value):
        """验证联系人列表"""
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("联系人为必填项")
        return value


class TaskSimpleSerializer(serializers.ModelSerializer):
    """任务简化序列化器"""
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'task_type', 'status', 'progress', 'due_date']