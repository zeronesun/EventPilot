import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Q, Count, Sum, F, QuerySet
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

from apps.events.models import Event, BudgetItem
from apps.tasks.models import Task

logger = logging.getLogger(__name__)


class EventService:
    """活动管理服务层 - 处理活动CRUD操作的业务逻辑"""
    
    # 活动状态流转规则
    STATUS_TRANSITIONS = {
        Event.Status.PLANNING: [Event.Status.EXECUTING, Event.Status.CANCELLED],
        Event.Status.EXECUTING: [Event.Status.COMPLETED, Event.Status.CANCELLED],
        Event.Status.COMPLETED: [Event.Status.REVIEWED],
        Event.Status.REVIEWED: [],
        Event.Status.CANCELLED: [],
    }
    
    # 活动类型配置
    EVENT_TYPES = {
        'conference': '会议',
        'exhibition': '展会',
        'performance': '演出',
        'party': '派对',
        'training': '培训',
        'other': '其他',
    }
    
    # 预算警戒阈值 (百分比)
    BUDGET_WARNING_THRESHOLD = 80
    BUDGET_CRITICAL_THRESHOLD = 100
    
    # 风险评估配置
    RISK_FACTORS = {
        'duration': {'short': 3, 'long': 30},  # 天数
        'budget': {'low': 10000, 'high': 1000000},  # 金额
        'tasks': {'min': 10, 'max': 100},
    }
    
    @staticmethod
    def validate_event_data(data: Dict, partial: bool = False) -> Tuple[bool, List[str]]:
        """验证活动数据

        Args:
            data: 待验证的数据字典
            partial: 是否为部分更新（部分更新时不强制要求空字段）
        """
        errors = []

        # 名称验证
        name = data.get('name')
        if name:
            if len(name) < 3:
                errors.append('活动名称长度至少3位')
            elif len(name) > 255:
                errors.append('活动名称长度不能超过255位')
        elif not partial:
            errors.append('活动名称不能为空')

        # 类型验证
        event_type = data.get('type')
        if event_type:
            if event_type not in EventService.EVENT_TYPES:
                errors.append(f'活动类型无效，有效值：{", ".join(EventService.EVENT_TYPES.keys())}')
        elif not partial:
            errors.append('活动类型不能为空')

        # 时间验证
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # 部分更新时不强制要求时间字段
        if not partial or (start_date or end_date):
            if start_date and not end_date:
                errors.append('结束时间不能为空')
            elif end_date and not start_date:
                errors.append('开始时间不能为空')

            if start_date and end_date:
                try:
                    if isinstance(start_date, str):
                        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if isinstance(end_date, str):
                        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                    if end_date <= start_date:
                        errors.append('结束时间必须大于开始时间')
                except (ValueError, TypeError) as e:
                    errors.append('时间格式不正确')

        # 预算验证
        estimated_budget = data.get('estimated_budget')
        if estimated_budget is not None:
            if estimated_budget < 0:
                errors.append('预估预算不能为负数')
            elif estimated_budget > 10000000:
                errors.append('预估预算金额过大，请确认')

        # 负责人验证
        owner = data.get('owner') or data.get('owner_id')
        if not owner and not partial:
            errors.append('负责人不能为空')

        return len(errors) == 0, errors
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Tuple[bool, List[str]]:
        """验证状态流转是否符合规则"""
        errors = []
        
        if current_status == new_status:
            errors.append('状态未变更')
            return False, errors
        
        allowed_transitions = EventService.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_transitions:
            errors.append(f'状态流转无效：{current_status} -> {new_status}')
            errors.append(f'允许的流转：{", ".join([t for t in allowed_transitions])}')
            return False, errors
        
        return True, errors
    
    @staticmethod
    @transaction.atomic
    def create_event(data: Dict, owner, request=None) -> Tuple[Event, List[str]]:
        """创建新活动"""
        errors = []
        
        try:
            # 验证数据
            is_valid, validation_errors = EventService.validate_event_data(data)
            if not is_valid:
                return None, validation_errors
            
            # 创建活动
            event = Event.objects.create(
                name=data['name'],
                type=data['type'],
                description=data.get('description', ''),
                start_date=data['start_date'],
                end_date=data['end_date'],
                client=data.get('client', ''),
                client_contact=data.get('client_contact', ''),
                estimated_budget=data.get('estimated_budget', 0),
                status=Event.Status.PLANNING,
                owner=owner,
            )
            
            # 初始化预算明细
            if data.get('budget_items'):
                for item_data in data['budget_items']:
                    BudgetItem.objects.create(
                        event=event,
                        category_name=item_data.get('category_name', '未分类'),
                        name=item_data['name'],
                        estimated_amount=item_data['estimated_amount'],
                        actual_amount=0,
                        variance=item_data['estimated_amount'],
                        responsible=owner if item_data.get('is_responsible') else None,
                        status='pending'
                    )
            
            # 刷新预算汇总
            EventService._refresh_event_budget(event)
            
            # 记录活动日志
            EventService._log_event_activity(event, 'created', request)
            
            logger.info(f"活动创建成功: {event.name} (ID: {event.id})")
            return event, []
            
        except Exception as e:
            logger.error(f"创建活动失败: {e}")
            errors.append(f"创建活动失败: {str(e)}")
            return None, errors
    
    @staticmethod
    @transaction.atomic
    def update_event(event: Event, update_data: Dict, request=None) -> Tuple[bool, List[str]]:
        """更新活动信息"""
        errors = []
        
        try:
            # 状态单独处理
            new_status = update_data.get('status')
            if new_status:
                is_valid, status_errors = EventService.validate_status_transition(
                    event.status, new_status
                )
                if not is_valid:
                    return False, status_errors
                
                event.status = new_status
                if new_status == Event.Status.COMPLETED:
                    event.completed_at = timezone.now()
                    update_data.pop('status', None)  # 移除已处理的字段
            
            # 验证更新的数据
            is_valid, validation_errors = EventService.validate_event_data(
                {
                    **{
                        'name': event.name,
                        'type': event.type,
                        'start_date': event.start_date,
                        'end_date': event.end_date,
                        'owner': event.owner_id,
                    },
                    **update_data
                },
                partial=True  # 更新操作是部分更新
            )
            if not is_valid:
                return False, validation_errors
            
            # 更新活动信息
            for field, value in update_data.items():
                if hasattr(event, field) and value is not None:
                    setattr(event, field, value)
            
            event.save()
            
            # 处理预算项更新
            if 'budget_items' in update_data:
                EventService._update_budget_items(event, update_data['budget_items'])
                EventService._refresh_event_budget(event)
            
            # 记录活动日志
            EventService._log_event_activity(event, 'updated', request, details={
                'updated_fields': list(update_data.keys()),
            })
            
            # 清除相关缓存
            EventService._clear_event_cache(event.id)
            
            logger.info(f"活动更新成功: {event.name} (ID: {event.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"更新活动失败: {e}")
            errors.append(f"更新活动失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def delete_event(event: Event, soft_delete: bool = True, skip_task_checks: bool = False, request=None) -> Tuple[bool, List[str]]:
        """删除活动"""
        errors = []

        try:
            # 前置校验：检查是否可以删除（允许删除已取消的活动）
            if not skip_task_checks:
                if event.status == Event.Status.EXECUTING and event.tasks.filter(status='in_progress').exists():
                    errors.append('活动执行中且有正在进行的任务，无法删除')
                    logger.warning(f"删除活动失败: Event={event.pk} 在执行中且有进行中任务")
                    return False, errors

                if event.tasks.filter(status='in_progress').exists():
                    errors.append('活动中有正在进行的任务，无法删除')
                    logger.warning(f"删除活动失败: Event={event.pk} 有进行中任务")
                    return False, errors

            if soft_delete:
                # 软删除
                event.status = Event.Status.CANCELLED
                if not event.completed_at:
                    event.completed_at = timezone.now()
                event.save()

                EventService._log_event_activity(event, 'soft_deleted', request)
                logger.info(f"活动软删除成功: {event.name} (ID: {event.id})")
            else:
                # 硬删除前再次检查任务关联（避免级联风险）
                task_count = event.tasks.count()
                if task_count > 0:
                    if not skip_task_checks:
                        errors.append(f'活动关联了 {task_count} 个任务，无法硬删除。请使用 skip_task_checks 参数明确跳过此检查（高级操作，可能导致数据不一致）。')
                        logger.error(f"硬删除受阻: Event={event.pk} 有关联任务 {task_count} 个")
                        return False, errors
                    else:
                        logger.warning(f"跳过任务检查并执行硬删除: Event={event.pk} 有关联任务 {task_count} 个")

                # 硬删除
                event_name = event.name
                event_id = str(event.id)

                # 删除关联数据
                event.budget_items.all().delete()
                event.tasks.all().delete()

                # 删除活动
                event.delete()

                EventService._log_event_activity(
                    event, 'hard_deleted', request,
                    details={'event_name': event_name, 'event_id': event_id}
                )
                logger.info(f"活动硬删除成功: {event_name} (ID: {event_id})")

            # 清除缓存
            EventService._clear_event_cache(event.id)

            return True, []

        except Exception as e:
            logger.error(f"删除活动失败: Event={event.pk if not hasattr(event, '_state') else event.id}, Error={e}", exc_info=True)
            errors.append(f"删除活动失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def get_event_statistics(event: Event) -> Dict[str, Any]:
        """获取活动统计信息"""
        try:
            # 任务统计
            tasks_queryset = event.tasks.all()
            tasks_by_status = dict(
                tasks_queryset.values('status').annotate(count=Count('id'))
                .values_list('status', 'count')
            )
            
            tasks_by_type = dict(
                tasks_queryset.values('task_type').annotate(count=Count('id'))
                .values_list('task_type', 'count')
            )
            
            # 预算统计
            budget_queryset = event.budget_items.all()
            budget_stats = {
                'estimated_total': budget_queryset.aggregate(total=Sum('estimated_amount'))['total'] or 0,
                'actual_total': budget_queryset.aggregate(total=Sum('actual_amount'))['total'] or 0,
                'variance_total': budget_queryset.aggregate(total=Sum('variance'))['total'] or 0,
                'items_count': budget_queryset.count(),
            }
            
            # 进度统计
            total_tasks = tasks_queryset.count()
            completed_tasks = tasks_queryset.filter(status='completed').count()
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # 预算使用率
            budget_usage_rate = 0
            if event.estimated_budget and event.estimated_budget > 0:
                budget_usage_rate = (event.actual_budget / event.estimated_budget * 100)
            
            return {
                'tasks': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'in_progress': tasks_by_status.get('in_progress', 0),
                    'pending': tasks_by_status.get('pending', 0),
                    'by_status': tasks_by_status,
                    'by_type': tasks_by_type,
                    'progress_percentage': round(progress_percentage, 2),
                },
                'budget': {
                    'estimated_total': float(budget_stats['estimated_total']),
                    'actual_total': float(budget_stats['actual_total']),
                    'variance_total': float(budget_stats['variance_total']),
                    'items_count': budget_stats['items_count'],
                    'usage_rate': round(budget_usage_rate, 2),
                    'status': EventService._get_budget_status(budget_usage_rate),
                },
                'timeline': {
                    'start_date': event.start_date.isoformat() if event.start_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'completed_at': event.completed_at.isoformat() if event.completed_at else None,
                    'days_remaining': EventService._get_days_remaining(event),
                    'is_overdue': EventService._is_overdue(event),
                },
            }
            
        except Exception as e:
            logger.error(f"获取活动统计失败: {e}")
            return {}
    
    @staticmethod
    def assess_event_risk(event: Event) -> Dict[str, Any]:
        """评估活动风险"""
        try:
            risk_factors = []
            risk_level = 'low'
            
            # 1. 时间风险
            duration_days = (event.end_date - event.start_date).days if event.start_date and event.end_date else 0
            if duration_days < EventService.RISK_FACTORS['duration']['short']:
                risk_factors.append({
                    'type': 'time',
                    'level': 'high',
                    'message': '活动时间过短，可能导致准备不足'
                })
            elif duration_days > EventService.RISK_FACTORS['duration']['long']:
                risk_factors.append({
                    'type': 'time',
                    'level': 'medium',
                    'message': '活动时间较长，增加执行复杂度'
                })
            
            # 2. 预算风险
            if event.estimated_budget:
                if event.actual_budget > event.estimated_budget:
                    variance_rate = (event.actual_budget - event.estimated_budget) / event.estimated_budget * 100
                    risk_factors.append({
                        'type': 'budget',
                        'level': high if variance_rate > 20 else 'medium',
                        'message': f'预算超支 {variance_rate:.2f}%'
                    })
            
            # 3. 任务风险
            total_tasks = event.tasks.count()
            if total_tasks > EventService.RISK_FACTORS['tasks']['max']:
                risk_factors.append({
                    'type': 'tasks',
                    'level': 'medium',
                    'message': '任务数量过多，可能影响执行效率'
                })
            elif total_tasks < EventService.RISK_FACTORS['tasks']['min']:
                risk_factors.append({
                    'type': 'tasks',
                    'level': 'low',
                    'message': '任务数量偏少，建议细化任务'
                })
            
            # 4. 进度风险
            if event.status == Event.Status.EXECUTING:
                completed_tasks = event.tasks.filter(status='completed').count()
                progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                days_remaining = EventService._get_days_remaining(event)
                
                if days_remaining and days_remaining < 7 and progress < 80:
                    risk_factors.append({
                        'type': 'progress',
                        'level': 'high',
                        'message': '时间紧迫，进度滞后'
                    })
            
            # 5. 负责人风险
            owner_workload = Event.objects.filter(
                owner=event.owner,
                status__in=[Event.Status.PLANNING, Event.Status.EXECUTING]
            ).count()
            
            if owner_workload > 5:
                risk_factors.append({
                    'type': 'owner',
                    'level': 'medium',
                    'message': f'负责人当前负责 {owner_workload} 个活动，工作负荷较重'
                })
            
            # 计算总体风险等级
            high_risks = [r for r in risk_factors if r['level'] == 'high']
            medium_risks = [r for r in risk_factors if r['level'] == 'medium']
            
            if high_risks:
                risk_level = 'high'
            elif medium_risks:
                risk_level = 'medium'
            
            return {
                'level': risk_level,
                'factors': risk_factors,
                'recommendations': EventService._get_risk_recommendations(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"活动风险评估失败: {e}")
            return {'level': 'unknown', 'factors': [], 'recommendations': []}
    
    @staticmethod
    def get_events_filter(user, filters: Dict = None) -> QuerySet:
        """获取过滤后的活动列表"""
        queryset = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items')
        
        # 权限过滤：用户只能看到自己拥有的或参与的
        if not user.is_superuser:
            queryset = queryset.filter(Q(owner=user) | Q(participants=user))
        
        # 应用过滤
        if filters:
            # 状态过滤
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            # 类型过滤
            if 'type' in filters:
                queryset = queryset.filter(type=filters['type'])
            
            # 负责人过滤
            if 'owner' in filters:
                queryset = queryset.filter(owner_id=filters['owner'])
            
            # 时间范围过滤
            if 'start_date_from' in filters:
                queryset = queryset.filter(start_date__gte=filters['start_date_from'])
            
            if 'start_date_to' in filters:
                queryset = queryset.filter(start_date__lte=filters['start_date_to'])
            
            # 搜索
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(client__icontains=search_term)
                )
        
        return queryset
    
    @staticmethod
    def _update_budget_items(event: Event, budget_items_data: List[Dict]):
        """更新预算项"""
        # 获取现有budget_items的ID
        existing_ids = set(event.budget_items.values_list('id', flat=True))
        
        # 处理新的或更新的预算项
        for item_data in budget_items_data:
            item_id = item_data.get('id')
            
            if item_id and item_id in existing_ids:
                # 更新现有项
                BudgetItem.objects.filter(id=item_id).update(
                    category_name=item_data.get('category_name'),
                    name=item_data.get('name'),
                    estimated_amount=item_data.get('estimated_amount'),
                    actual_amount=item_data.get('actual_amount', 0),
                    status=item_data.get('status', 'pending')
                )
                existing_ids.remove(item_id)
            else:
                # 创建新项
                BudgetItem.objects.create(
                    event=event,
                    category_name=item_data.get('category_name', '未分类'),
                    name=item_data['name'],
                    estimated_amount=item_data['estimated_amount'],
                    actual_amount=0,
                    variance=item_data['estimated_amount'],
                    status='pending'
                )
        
        # 删除不存在的项
        if existing_ids:
            event.budget_items.filter(id__in=existing_ids).delete()
    
    @staticmethod
    def _refresh_event_budget(event: Event):
        """刷新活动预算汇总"""
        budget_items = event.budget_items.all()
        
        event.estimated_budget = sum(item.estimated_amount for item in budget_items) or 0
        event.actual_budget = sum(item.actual_amount for item in budget_items) or 0
        event.budget_variance = event.estimated_budget - event.actual_budget
        event.save()
    
    @staticmethod
    def _get_budget_status(usage_rate: float) -> str:
        """获取预算状态"""
        if usage_rate >= 100:
            return 'critical'
        elif usage_rate >= EventService.BUDGET_WARNING_THRESHOLD:
            return 'warning'
        else:
            return 'healthy'
    
    @staticmethod
    def _get_days_remaining(event: Event) -> Optional[int]:
        """获取剩余天数"""
        if not event.end_date or event.status == Event.Status.COMPLETED:
            return None
        
        remaining = (event.end_date.date() - timezone.now().date()).days
        return max(0, remaining)
    
    @staticmethod
    def _is_overdue(event: Event) -> bool:
        """检查是否超期"""
        if event.status in [Event.Status.COMPLETED, Event.Status.CANCELLED]:
            return False
        
        if not event.end_date:
            return False
        
        return timezone.now() > event.end_date
    
    @staticmethod
    def _get_risk_recommendations(risk_factors: List[Dict]) -> List[str]:
        """获取风险建议"""
        recommendations = []
        
        risk_types = {r['type'] for r in risk_factors}
        
        if 'time' in risk_types:
            recommendations.append('建议重新评估活动时间安排，必要时调整计划')
        
        if 'budget' in risk_types:
            recommendations.append('建议审查预算使用情况，优化资源配置')
        
        if 'progress' in risk_factors:
            recommendations.append('建议调整任务优先级，集中资源完成关键任务')
        
        if 'owner' in risk_factors:
            recommendations.append('建议考虑分担或重新分配活动负责人')
        
        if not recommendations:
            recommendations.append('活动风险可控，继续保持当前执行计划')
        
        return recommendations
    
    @staticmethod
    def _log_event_activity(event: Event, action: str, request=None, details: Dict = None):
        """记录活动操作日志"""
        if not request:
            return
        
        try:
            from apps.users.services.user_service import UserService
            
            ip_address, user_agent = UserService.get_client_info(request)
            
            UserService.log_user_activity(
                user=request.user if hasattr(request, 'user') else event.owner,
                activity_type=f'event_{action}',
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    'event_id': str(event.id),
                    'event_name': event.name,
                    'action': action,
                    **(details or {})
                }
            )
        except Exception as e:
            logger.error(f"记录活动日志失败: {e}")
    
    @staticmethod
    def _clear_event_cache(event_id: str):
        """清除活动相关缓存"""
        cache_keys = [
            f'event:{event_id}',
            f'event:{event_id}:statistics',
            f'event:{event_id}:risk',
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    def complete_event(event: Event, request=None) -> Tuple[bool, List[str]]:
        """完成活动"""
        errors = []
        
        try:
            # 检查状态
            if event.status == Event.Status.COMPLETED:
                errors.append('活动已完成')
                return False, errors
            
            if event.status == Event.Status.CANCELLED:
                errors.append('活动已取消，无法完成')
                return False, errors
            
            # 检查任务完成情况
            total_tasks = event.tasks.count()
            completed_tasks = event.tasks.filter(status='completed').count()
            
            if total_tasks > 0 and completed_tasks < total_tasks:
                errors.append(f'还有 {total_tasks - completed_tasks} 个任务未完成')
                return False, errors
            
            # 更新状态
            with transaction.atomic():
                event.status = Event.Status.COMPLETED
                event.completed_at = timezone.now()
                event.save()
                
                EventService._log_event_activity(event, 'completed', request, details={
                    'tasks_completed': completed_tasks,
                    'total_tasks': total_tasks
                })
                
                # 清除缓存
                EventService._clear_event_cache(str(event.id))
                
                logger.info(f"活动完成: {event.name} (ID: {event.id})")
                return True, []
                
        except Exception as e:
            logger.error(f"完成活动失败: {e}")
            errors.append(f"完成活动失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def change_event_status(event: Event, new_status: str, request=None) -> Tuple[bool, List[str]]:
        """变更活动状态"""
        errors = []
        
        try:
            is_valid, status_errors = EventService.validate_status_transition(
                event.status, new_status
            )
            
            if not is_valid:
                return False, status_errors
            
            with transaction.atomic():
                old_status = event.status
                event.status = new_status
                
                if new_status == Event.Status.COMPLETED:
                    event.completed_at = timezone.now()
                
                event.save()
                
                EventService._log_event_activity(event, 'status_changed', request, details={
                    'old_status': old_status,
                    'new_status': new_status
                })
                
                # 清除缓存
                EventService._clear_event_cache(str(event.id))
                
                logger.info(f"活动状态变更: {event.name} {old_status} -> {new_status}")
                return True, []
                
        except Exception as e:
            logger.error(f"变更活动状态失败: {e}")
            errors.append(f"变更活动状态失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def get_dashboard_analytics(user, filters: Dict = None) -> Dict[str, Any]:
        """
        获取活动数据分析仪表盘
        用于跨活动统计、趋势分析、对比分析
        """
        try:
            # 获取用户权限范围内的活动
            if user.is_superuser:
                base_query = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items')
            else:
                base_query = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items').filter(
                    Q(owner=user) | Q(participants=user)
                ).distinct()
            
            # 应用过滤
            if filters:
                if 'status' in filters:
                    base_query = base_query.filter(status=filters['status'])
                if 'type' in filters:
                    base_query = base_query.filter(type=filters['type'])
                if 'start_date_from' in filters:
                    base_query = base_query.filter(start_date__gte=filters['start_date_from'])
                if 'start_date_to' in filters:
                    base_query = base_query.filter(start_date__lte=filters['start_date_to'])
            
            all_events = base_query
            
            # 1. 总体统计
            total_events = all_events.count()
            total_tasks = Task.objects.filter(event__in=all_events).count()
            total_budget = all_events.aggregate(
                total=Sum('estimated_budget')
            )['total'] or 0
            total_actual_budget = all_events.aggregate(
                total=Sum('actual_budget')
            )['total'] or 0
            
            # 2. 按状态统计
            status_stats = {}
            for status_choice in Event.Status.values:
                count = all_events.filter(status=status_choice).count()
                status_stats[status_choice] = {
                    'count': count,
                    'percentage': round(count / total_events * 100, 2) if total_events > 0 else 0
                }
            
            # 3. 按类型统计
            type_stats = {}
            for type_key, type_name in EventService.EVENT_TYPES.items():
                count = all_events.filter(type=type_key).count()
                if count > 0:
                    type_stats[type_key] = {
                        'name': type_name,
                        'count': count,
                        'percentage': round(count / total_events * 100, 2) if total_events > 0 else 0
                    }
            
            # 4. 任务完成率统计
            completed_tasks = Task.objects.filter(
                event__in=all_events,
                status='completed'
            ).count()
            task_completion_rate = round(
                completed_tasks / total_tasks * 100, 2
            ) if total_tasks > 0 else 0
            
            # 5. 预算分析
            budget_variance = total_budget - total_actual_budget
            budget_variance_rate = round(
                (budget_variance / total_budget * 100) if total_budget > 0 else 0, 2
            )
            
            # 6. 活动趋势（按月统计）
            from django.db.models.functions import TruncMonth
            monthly_stats = all_events.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id'),
                total_budget=Sum('estimated_budget')
            ).order_by('month')

            # 取最近12个月（在Python中切片，避免负数索引错误）
            monthly_stats_list = list(monthly_stats)
            if len(monthly_stats_list) > 12:
                monthly_stats_list = monthly_stats_list[-12:]

            monthly_trend = [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else None,
                    'count': item['count'],
                    'total_budget': float(item['total_budget'] or 0)
                }
                for item in monthly_stats_list
            ]
            
            # 7. 高风险活动
            high_risk_events = []
            for event in all_events.filter(status='executing'):
                risk = EventService.assess_event_risk(event)
                if risk['level'] == 'high':
                    high_risk_events.append({
                        'id': str(event.id),
                        'name': event.name,
                        'risk_level': risk['level'],
                        'factors_count': len(risk['factors'])
                    })
            
            # 8. 即将到期活动
            upcoming_deadlines = []
            threshold_date = timezone.now() + timedelta(days=7)
            for event in all_events.filter(status='executing', end_date__lte=threshold_date):
                days_remaining = (event.end_date.date() - timezone.now().date()).days
                upcoming_deadlines.append({
                    'id': str(event.id),
                    'name': event.name,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'days_remaining': days_remaining
                })
            
            # 9. TOP活跃负责人
            owner_stats = all_events.values('owner__username').annotate(
                count=Count('id'),
                total_budget=Sum('estimated_budget')
            ).order_by('-count')[:5]
            
            top_owners = [
                {
                    'username': stat['owner__username'] or '未知',
                    'event_count': stat['count'],
                    'total_budget': float(stat['total_budget'] or 0)
                }
                for stat in owner_stats
            ]
            
            # 10. 任务类型分布
            task_type_stats = {}
            for task_type in Task.TaskType.values:
                count = Task.objects.filter(
                    event__in=all_events,
                    task_type=task_type
                ).count()
                task_type_stats[task_type] = {
                    'count': count,
                    'percentage': round(count / total_tasks * 100, 2) if total_tasks > 0 else 0
                }
            
            return {
                'overview': {
                    'total_events': total_events,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'task_completion_rate': task_completion_rate,
                    'total_estimated_budget': float(total_budget),
                    'total_actual_budget': float(total_actual_budget),
                    'budget_variance': float(budget_variance),
                    'budget_variance_rate': budget_variance_rate,
                },
                'status_distribution': status_stats,
                'type_distribution': type_stats,
                'task_type_distribution': task_type_stats,
                'monthly_trend': monthly_trend,
                'high_risk_events': high_risk_events,
                'upcoming_deadlines': upcoming_deadlines,
                'top_owners': top_owners,
                'generated_at': timezone.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"获取活动仪表盘数据失败: {e}")
            return {
                'overview': {},
                'status_distribution': {},
                'type_distribution': {},
                'task_type_distribution': {},
                'monthly_trend': [],
                'high_risk_events': [],
                'upcoming_deadlines': [],
                'top_owners': [],
                'error': str(e)
            }