from django.db.models import Count, Sum
from .models import Event, BudgetItem
from apps.tasks.models import Task, TaskDependency


def get_event_statistics(event_id):
    """
    获取活动统计数据
    """
    activities that are included in the statistical analysis
    tasks and budget items
    """
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return None
    
    tasks_queryset = event.tasks.all()
    budget_queryset = event.budget_items.all()
    
    stats = {
        'tasks': {
            'total': tasks_queryset.count(),
            'by_status': {},
            'by_type': {},
        },
        'budget': {
            'estimated_total': 0,
            'actual_total': 0,
            'variance_total': 0,
            'items_count': 0,
        }
    }
    
    # 任务统计
    for status_choice in Task.Status.choices:
        status_value = status_choice[0]
        count = tasks_queryset.filter(status=status_value).count()
        stats['tasks']['by_status'][status_value] = count
    
    for type_choice in Task.TaskType.choices:
        type_value = type_choice[0]
        count = tasks_queryset.filter(task_type=type_value).count()
        stats['tasks']['by_type'][type_value] = count
    
    # 预算统计
    budget_summary = budget_queryset.aggregate(
        estimated_total=Sum('estimated_amount'),
        actual_total=Sum('actual_amount'),
        variance_total=Sum('variance'),
        items_count=Count('id')
    )
    stats['budget']['estimated_total'] = budget_summary['estimated_total'] or 0
    stats['budget']['actual_total'] = budget_summary['actual_total'] or 0
    stats['budget']['variance_total'] = budget_summary['variance_total'] or 0
    stats['budget']['items_count'] = budget_summary['items_count'] or 0
    
    return stats


def update_event_budget(event):
    """
    更新活动的预算汇总
    根据所有预算明细重新计算预算汇总
    """
    budget_items = event.budget_items.all()
    
    event.estimated_budget = sum(
        item.estimated_amount for item in budget_items
    )
    event.actual_budget = sum(
        item.actual_amount for item in budget_items
    )
    event.budget_variance = event.estimated_budget - event.actual_budget
    event.save()
    
    return event


def update_dependent_task_status(completed_task):
    """
    更新依赖的后续任务状态
    当一个任务完成时，检查是否有依赖该任务的后续任务需要更新状态
    """
    dependents = TaskDependency.objects.filter(depends_on=completed_task)
    
    for dep in dependents:
        dependent_task = dep.task
        
        # 检查该任务的所有依赖是否都已完成
        all_dependencies = TaskDependency.objects.filter(task=dependent_task)
        all_completed = all(
            d.depends_on.status == 'completed' for d in all_dependencies
        )
        
        if all_completed and dependent_task.status == 'pending':
            dependent_task.status = 'ready'
            dependent_task.save()


def complete_checklist_instance(instance):
    """
    完成核验清单实例
    检查所有项是否都已完成，如果是则标记实例为完成
    """
    all_items = instance.items.count()
    completed_items = instance.items.filter(
        status__in=['passed', 'failed', 'skipped']
    ).count()
    
    if all_items == completed_items and all_items > 0:
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.save()
    
    return instance


def auto_extract_knowledge_from_review(review):
    """
    从复盘自动提取知识条目
    将成功经验和待改进项转为知识条目
    """
    from .models import KnowledgeEntry
    
    extracted_count = 0
    
    # 提取成功经验
    if review.successes:
        KnowledgeEntry.objects.create(
            entry_type='best_practice',
            title=f"{review.event.name}成功经验",
            content=review.successes,
            related_events=[review.event.id],
            event_type=review.event.type,
            tags=['success', review.event.type],
            created_by=review.created_by,
            is_verified=False  # 需要管理员验证
        )
        extracted_count += 1
    
    # 提取待改进项
    if review.improvements:
        KnowledgeEntry.objects.create(
            entry_type='issue',
            title=f"{review.event.name}需改进项",
            content=review.improvements,
            related_events=[review.event.id],
            event_type=review.event.type,
            tags=['improvement', review.event.type],
            created_by=review.created_by,
            is_verified=False
        )
        extracted_count += 1
    
    return extracted_count


def validate_profile_contact_data(contact_info):
    """
    验证档案联系信息
    """
    required_fields = ['email', 'phone']
    optional_fields = ['name', 'organization', 'wechat', 'address']
    
    if not isinstance(contact_info, dict):
        return False, "联系信息必须是字典格式"
    
    # 检查至少有一个联系方式
    has_required = any(field in contact_info for field in required_fields)
    if not has_required:
        return False, f"联系信息必须包含以下字段之一: {required_fields}"
    
    return True, None


def get_related_events_for_profile(profile):
    """
    获取档案关联的所有活动
    """
    associations = profile.event_associations.select_related('event').order_by('-created_at')
    
    events_data = []
    for assoc in associations:
        events_data.append({
            'event_id': str(assoc.event.id),
            'event_name': assoc.event.name,
            'event_type': assoc.event.type,
            'event_date': assoc.event.start_date.isoformat() if assoc.event.start_date else None,
            'event_status': assoc.event.status,
            'role': assoc.role,
            'created_at': assoc.created_at.isoformat()
        })
    
    return events_data


def get_knowledge_recommendations(event_id, limit=5):
    """
    获取基于活动的知识推荐
    通过活动类型和相关活动ID查找相关的知识条目
    """
    from .models import KnowledgeEntry
    from apps.events.models import Event
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return []
    
    # 多种推荐策略:
    # 1. 直接相关（通过related_events字段）
    # 2. 同类型的最佳实践
    # 3. 同类型的问题历史
    
    queryset = KnowledgeEntry.objects.filter(
        is_verified=True
    ).distinct()
    
    # 策略1：直接相关
    direct_related = queryset.filter(related_events__contains=event_id)
    
    # 策略2：同类型最佳实践
    best_practices = queryset.filter(
        entry_type='best_practice',
        category=event.type
    )
    
    # 策略3：同类型问题
    issues = queryset.filter(
        entry_type='issue',
        tags__contains=event.type
    )
    
    # 合并结果并去重
    recommended_ids = set()
    if direct_related.exists():
        recommended_ids.update(direct_related.values_list('id', flat=True))
    if best_practices.exists():
        recommended_ids.update(best_practices.values_list('id', flat=True)[:limit])
    if issues.exists():
        recommended_ids.update(issues.values_list('id', flat=True)[:limit])
    
    # 获取推荐数据
    recommended = KnowledgeEntry.objects.filter(
        id__in=recommended_ids
    ).order_by('-popularity', '-created_at')[:limit]
    
    from .serializers import KnowledgeEntryListSerializer
    serializer = KnowledgeEntryListSerializer(recommended, many=True)
    return serializer.data