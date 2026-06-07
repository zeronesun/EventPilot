from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.tasks.models import Task, TaskDependency, CommunicationTask

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    assignee_name = serializers.CharField(source='assignee.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    depends_on = serializers.SerializerMethodField()
    dependents_count = serializers.SerializerMethodField()
    dependency_names = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    is_ready = serializers.SerializerMethodField()
    overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'event', 'event_name', 'title', 'description', 'task_type', 
            'assignee', 'assignee_name', 'status', 'progress', 'due_date', 
            'start_date', 'completed_at', 'created_by', 'created_by_name', 
            'created_at', 'updated_at', 'depends_on', 'dependents_count',
            'dependency_names', 'is_blocked', 'is_ready', 'overdue'
        ]
        read_only_fields = [
            'id', 'progress', 'completed_at', 'created_at', 'updated_at',
            'event_name', 'assignee_name', 'created_by_name', 'dependents_count',
            'dependency_names', 'is_blocked', 'is_ready', 'overdue'
        ]
    
    def get_depends_on(self, obj):
        """获取依赖任务"""
        dependencies = obj.dependencies.all()
        return [
            {
                'id': str(dep.depends_on.id),
                'title': dep.depends_on.title,
                'status': dep.depends_on.status
            }
            for dep in dependencies
        ]
    
    def get_dependents_count(self, obj):
        """获取依赖此任务的其他任务数量"""
        return TaskDependency.objects.filter(depends_on=obj).count()
    
    def get_dependency_names(self, obj):
        """获取依赖任务的名称列表"""
        dependencies = obj.dependencies.all()
        return [dep.depends_on.title for dep in dependencies]
    
    def get_is_blocked(self, obj):
        """检查是否被阻塞"""
        return obj.status == 'blocked'
    
    def get_is_ready(self, obj):
        """检查是否就绪"""
        return obj.status == 'ready'
    
    def get_overdue(self, obj):
        """检查是否逾期"""
        if obj.due_date and obj.status not in ['completed', 'cancelled']:
            return obj.due_date < timezone.now()
        return False
    
    def validate_due_date(self, value):
        """验证截止日期"""
        if value:
            if hasattr(self, 'instance') and self.instance.start_date:
                if value < self.instance.start_date:
                    raise serializers.ValidationError("截止日期不能早于开始日期")
        return value
    
    def validate_start_date(self, value):
        """验证开始日期"""
        if value:
            if hasattr(self, 'instance') and self.instance.due_date:
                if value > self.instance.due_date:
                    raise serializers.ValidationError("开始日期不能晚于截止日期")
        return value
    
    def validate_progress(self, value):
        """验证进度百分比"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("进度必须在0-100之间")
        return value
    
    def validate_title(self, value):
        """验证标题"""
        if not value or not value.strip():
            raise serializers.ValidationError("标题不能为空")
        if len(value.strip()) > 255:
            raise serializers.ValidationError("标题长度不能超过255个字符")
        return value.strip()
    
    def validate_task_type(self, value):
        """验证任务类型"""
        valid_types = [choice[0] for choice in Task.TaskType.choices]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的任务类型: {value}")
        return value
    
    def validate_status(self, value):
        """验证状态"""
        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"无效的状态: {value}")
        return value
    
    def validate(self, data):
        """综合验证"""
        start_date = data.get('start_date')
        due_date = data.get('due_date')
        
        # 验证日期逻辑
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError("开始日期不能晚于截止日期")
        
        return data


class TaskDependencySerializer(serializers.ModelSerializer):
    """任务依赖序列化器"""
    task_title = serializers.CharField(source='task.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    depends_on_status = serializers.CharField(source='depends_on.status', read_only=True)
    
    class Meta:
        model = TaskDependency
        fields = [
            'task', 'task_title', 'depends_on', 'depends_on_title', 
            'depends_on_status', 'created_at'
        ]
        read_only_fields = ['created_at', 'task_title', 'depends_on_title', 'depends_on_status']
    
    def validate(self, data):
        """验证循环依赖"""
        task = data.get('task')
        depends_on = data.get('depends_on')
        
        if task and depends_on and task.id == depends_on.id:
            raise serializers.ValidationError("任务不能依赖自己")
        
        return data


class CommunicationTaskSerializer(serializers.ModelSerializer):
    """沟通任务序列化器"""
    task_id = serializers.UUIDField(write_only=True, required=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_status = serializers.CharField(source='task.status', read_only=True)

    class Meta:
        model = CommunicationTask
        fields = [
            'id', 'task_id', 'task_title', 'task_status', 'content', 'requirements',
            'communicators', 'conclusion_files', 'is_closed'
        ]
        read_only_fields = ['id', 'task_title', 'task_status']

    def validate_task_id(self, value):
        """验证任务ID"""
        from apps.tasks.models import Task
        if not Task.objects.filter(id=value).exists():
            raise serializers.ValidationError("指定的任务不存在")
        return value

    def create(self, validated_data):
        """创建沟通任务"""
        from apps.tasks.models import Task
        task_id = validated_data.pop('task_id')
        task = Task.objects.get(id=task_id)
        return CommunicationTask.objects.create(task=task, **validated_data)
    
    def validate_communicators(self, value):
        """验证联系人列表"""
        if not isinstance(value, list):
            raise serializers.ValidationError("联系人必须是列表")
        # 允许空列表
        if len(value) > 20:
            raise serializers.ValidationError("联系人数量不能超过20个")

        # 验证联系人格式
        for contact in value:
            if not isinstance(contact, dict):
                raise serializers.ValidationError("每个联系人必须是对象")
            if 'name' not in contact:
                raise serializers.ValidationError("联系人必须包含name字段")
            if not contact['name'].strip():
                raise serializers.ValidationError("联系人名称不能为空")

        return value
    
    def validate_conclusion_files(self, value):
        """验证结论文件列表"""
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("结论文件必须是列表")
            if len(value) > 10:
                raise serializers.ValidationError("结论文件数量不能超过10个")
        return value
    
    def validate_content(self, value):
        """验证沟通内容"""
        if not value or not value.strip():
            raise serializers.ValidationError("沟通内容不能为空")
        return value.strip()
    
    def validate(self, data):
        """综合验证"""
        # 如果标记为已闭环，必须有结论文件
        if data.get('is_closed', False):
            conclusion_files = data.get('conclusion_files', [])
            if not conclusion_files or len(conclusion_files) == 0:
                raise serializers.ValidationError("已闭环的沟通任务必须包含结论文件")
        
        return data


class TaskSimpleSerializer(serializers.ModelSerializer):
    """任务简化序列化器"""
    overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'task_type', 'status', 'progress', 'due_date', 'overdue']
    
    def get_overdue(self, obj):
        """检查是否逾期"""
        if obj.due_date and obj.status not in ['completed', 'cancelled']:
            return obj.due_date < timezone.now()
        return False


class TaskCreateSerializer(serializers.Serializer):
    """任务创建专用序列化器"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    task_type = serializers.ChoiceField(choices=Task.TaskType.choices, default='planning')
    assignee_id = serializers.UUIDField(required=False, allow_null=True)
    event_id = serializers.UUIDField(required=False, allow_null=True)
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    depends_on = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_title(self, value):
        """验证标题"""
        if not value or not value.strip():
            raise serializers.ValidationError("标题不能为空")
        return value.strip()
    
    def validate_event_id(self, value):
        """验证活动ID"""
        if value is None:
            return value
        from apps.events.models import Event
        if not Event.objects.filter(id=value).exists():
            raise serializers.ValidationError("指定的活动不存在")
        return value
    
    def validate_assignee_id(self, value):
        """验证分配负责人ID"""
        if value:
            if not User.objects.filter(id=value).exists():
                raise serializers.ValidationError("指定的用户不存在")
        return value
    
    def validate_depends_on(self, value):
        """验证依赖任务ID列表"""
        if value:
            from apps.events.models import Event
            # 确保所有依赖任务都属于同一个活动
            event_id = self.initial_data.get('event_id')
            if event_id:
                valid_count = Task.objects.filter(
                    id__in=value, 
                    event__id=event_id
                ).count()
                if valid_count != len(value):
                    raise serializers.ValidationError(
                        "某些依赖任务不存在或不属于指定的活动"
                    )
        return value
    
    def validate(self, data):
        """综合验证"""
        start_date = data.get('start_date')
        due_date = data.get('due_date')
        
        # 验证日期逻辑
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError("开始日期不能晚于截止日期")
        
        # 验证循环依赖
        task_id = self.context.get('task_id') if hasattr(self, 'context') else None
        depends_on = data.get('depends_on', [])
        if task_id and depends_on:
            if task_id in depends_on:
                raise serializers.ValidationError("任务不能依赖自己")
        
        return data


class TaskUpdateSerializer(serializers.Serializer):
    """任务更新专用序列化器"""
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    task_type = serializers.ChoiceField(choices=Task.TaskType.choices, required=False)
    assignee_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Task.Status.choices, required=False)
    progress = serializers.IntegerField(min_value=0, max_value=100, required=False)
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    depends_on = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_progress(self, value):
        """验证进度百分比"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("进度必须在0-100之间")
        return value
    
    def validate_assignee_id(self, value):
        """验证分配负责人ID"""
        if value:
            if not User.objects.filter(id=value).exists():
                raise serializers.ValidationError("指定的用户不存在")
        return value
    
    def validate(self, data):
        """综合验证"""
        start_date = data.get('start_date')
        due_date = data.get('due_date')
        
        # 验证日期逻辑
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError("开始日期不能晚于截止日期")
        
        # 状态转换验证
        status = data.get('status')
        if status:
            valid_transitions = {
                'pending': ['ready', 'in_progress', 'cancelled', 'blocked'],
                'ready': ['pending', 'in_progress', 'cancelled', 'blocked'],
                'in_progress': ['pending', 'ready', 'completed', 'cancelled', 'blocked'],
                'completed': ['in_progress', 'cancelled'],
                'cancelled': ['pending', 'ready', 'in_progress'],
                'blocked': ['pending', 'ready'],
            }
            
            # 需要获取当前任务的状态
            task_id = self.context.get('task_id')
            if task_id:
                try:
                    task = Task.objects.get(id=task_id)
                    if status not in valid_transitions.get(task.status, []):
                        raise serializers.ValidationError(
                            f"无效的状态转换: {task.status} -> {status}"
                        )
                except Task.DoesNotExist:
                    pass
        
        # 状态和进度一致性检查
        if data.get('status') == 'completed' and 'progress' in data:
            if data['progress'] != 100:
                raise serializers.ValidationError("已完成任务的进度必须为100%")
        
        if data.get('progress', 0) == 100 and data.get('status') not in [None, 'completed']:
            data['status'] = 'completed'
        
        return data


class TaskBulkUpdateSerializer(serializers.Serializer):
    """任务批量更新序列化器"""
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    status = serializers.ChoiceField(choices=Task.Status.choices)
    
    def validate_task_ids(self, value):
        """验证任务ID列表"""
        valid_count = Task.objects.filter(id__in=value).count()
        if valid_count != len(value):
            raise serializers.ValidationError(
                f"某些任务不存在 (提供了{len(value)}个，找到{valid_count}个)"
            )
        return value


class TaskBulkDeleteSerializer(serializers.Serializer):
    """任务批量删除序列化器"""
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )

    def validate_task_ids(self, value):
        """验证任务ID列表"""
        valid_count = Task.objects.filter(id__in=value).count()
        if valid_count != len(value):
            raise serializers.ValidationError(
                f"某些任务不存在 (提供了{len(value)}个，找到{valid_count}个)"
            )
        return value