import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Q, Count, Sum, F, QuerySet, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.checklists.models import (
    ChecklistTemplate, ChecklistItemTemplate, 
    ChecklistInstance, ChecklistItem
)
from apps.events.models import Event

User = get_user_model()
logger = logging.getLogger(__name__)


class ChecklistService:
    """清单管理服务层 - 处理清单CRUD操作的业务逻辑"""
    
    # 清单状态流转规则
    STATUS_TRANSITIONS = {
        'incomplete': ['in_progress', 'cancelled'],
        'in_progress': ['pending_review', 'completed', 'cancelled'],
        'pending_review': ['completed', 'in_progress', 'cancelled'],
        'completed': [],
        'cancelled': [],
    }
    
    # 清单模板状态
    TEMPLATE_STATUS = ['draft', 'published', 'archived']
    
    # 清单类型配置
    CHECKLIST_TYPES = {
        'pre_event': '活动前检查',
        'during_event': '活动中检查',
        'post_event': '活动后检查',
        'daily': '日常检查',
        'weekly': '周检查',
        'monthly': '月检查',
        'custom': '自定义检查',
    }
    
    # 清单项权重范围
    ITEM_WEIGHT_RANGE = (1, 100)
    
    # 完成度阈值
    COMPLETION_WARNING_THRESHOLD = 80
    COMPLETION_CRITICAL_THRESHOLD = 95
    
    @staticmethod
    def validate_template_data(data: Dict, partial: bool = False) -> Tuple[bool, List[str]]:
        """验证清单模板数据

        Args:
            data: 待验证的数据字典
            partial: 是否为部分更新（部分更新时不强制要求空字段）
        """
        errors = []

        # 名称验证
        name = data.get('name')
        if name:
            if len(name) < 3:
                errors.append('模板名称长度至少3位')
            elif len(name) > 255:
                errors.append('模板名称长度不能超过255位')
        elif not partial:
            errors.append('模板名称不能为空')

        # 描述验证
        description = data.get('description', '')
        if len(description) > 2000:
            errors.append('模板描述长度不能超过2000位')

        # 类型验证
        checklist_type = data.get('checklist_type')
        if checklist_type:
            if checklist_type not in ChecklistService.CHECKLIST_TYPES:
                errors.append(f'清单类型无效，有效值：{", ".join(ChecklistService.CHECKLIST_TYPES.keys())}')
        elif not partial:
            errors.append('清单类型不能为空')

        # 活动类型验证
        event_types = data.get('event_types', [])
        if not isinstance(event_types, list):
            errors.append('活动类型必须是列表格式')
        elif not event_types and not partial:
            errors.append('活动类型不能为空')

        # 版本验证
        version = data.get('version')
        if version and len(str(version)) > 50:
            errors.append('版本号长度不能超过50位')

        # 清单项验证
        items = data.get('items', [])
        if not isinstance(items, list):
            errors.append('清单项必须是列表格式')
        else:
            for idx, item in enumerate(items):
                item_errors = ChecklistService._validate_template_item(item, idx)
                errors.extend(item_errors)

        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_template_item(item: Dict, index: int) -> List[str]:
        """验证清单模板项数据"""
        errors = []
        prefix = f'清单项[{index}]'
        
        # 标题验证
        title = item.get('title')
        if not title or len(title) < 2:
            errors.append(f'{prefix}: 标题长度至少2位')
        elif len(title) > 500:
            errors.append(f'{prefix}: 标题长度不能超过500位')
        
        # 描述验证
        description = item.get('description', '')
        if len(description) > 1000:
            errors.append(f'{prefix}: 描述长度不能超过1000位')
        
        # 权重验证
        weight = item.get('weight', 1)
        try:
            weight = int(weight)
            if weight < ChecklistService.ITEM_WEIGHT_RANGE[0] or weight > ChecklistService.ITEM_WEIGHT_RANGE[1]:
                errors.append(f'{prefix}: 权重必须在{ChecklistService.ITEM_WEIGHT_RANGE[0]}-{ChecklistService.ITEM_WEIGHT_RANGE[1]}之间')
        except (ValueError, TypeError):
            errors.append(f'{prefix}: 权重必须是整数')
        
        # 排序验证
        order = item.get('order', 0)
        try:
            int(order)
        except (ValueError, TypeError):
            errors.append(f'{prefix}: 排序必须是整数')
        
        # 状态验证
        status = item.get('status', 'active')
        if status not in ['active', 'inactive']:
            errors.append(f'{prefix}: 状态必须是active或inactive')
        
        return errors
    
    @staticmethod
    def validate_instance_data(data: Dict, partial: bool = False) -> Tuple[bool, List[str]]:
        """验证清单实例数据

        Args:
            data: 待验证的数据字典
            partial: 是否为部分更新（部分更新时不强制要求空字段）
        """
        errors = []

        # 名称验证
        name = data.get('name')
        if name:
            if len(name) < 3:
                errors.append('实例名称长度至少3位')
            elif len(name) > 255:
                errors.append('实例名称长度不能超过255位')
        elif not partial:
            errors.append('实例名称不能为空')

        # 活动ID验证
        event_id = data.get('event_id') or data.get('event')
        if not event_id and not partial:
            errors.append('活动ID不能为空')

        # 模板ID验证
        template_id = data.get('template_id') or data.get('template')
        if not template_id and not partial:
            errors.append('模板ID不能为空')

        return len(errors) == 0, errors
    
    @staticmethod
    @transaction.atomic
    def create_template(data: Dict, created_by) -> Tuple[ChecklistTemplate, List[str]]:
        """创建清单模板"""
        errors = []
        
        try:
            # 验证数据
            is_valid, validation_errors = ChecklistService.validate_template_data(data)
            if not is_valid:
                return None, validation_errors
            
            # 创建模板
            template = ChecklistTemplate.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                checklist_type=data.get('checklist_type', 'custom'),
                event_types=data.get('event_types', []),
                version=data.get('version', '1.0.0'),
                status=data.get('status', 'draft'),
                is_default=data.get('is_default', False),
                created_by=created_by,
                tags=data.get('tags', []),
                # 元数据
                metadata=data.get('metadata', {}),
            )
            
            # 创建模板项
            items = data.get('items', [])
            if items:
                ChecklistService._create_template_items(template, items)
            
            # 记录日志
            ChecklistService._log_template_activity(template, 'created', created_by)
            
            logger.info(f"清单模板创建成功: {template.name} (ID: {template.id})")
            return template, []
            
        except Exception as e:
            logger.error(f"创建清单模板失败: {e}")
            errors.append(f"创建清单模板失败: {str(e)}")
            return None, errors
    
    @staticmethod
    def _create_template_items(template: ChecklistTemplate, items: List[Dict]):
        """创建模板项"""
        for idx, item_data in enumerate(items):
            ChecklistItemTemplate.objects.create(
                template=template,
                title=item_data.get('title'),
                description=item_data.get('description', ''),
                required=item_data.get('required', True),
                order=item_data.get('order', idx),
                weight=item_data.get('weight', 1),
                status=item_data.get('status', 'active'),
                metadata=item_data.get('metadata', {}),
            )
    
    @staticmethod
    @transaction.atomic
    def update_template(template: ChecklistTemplate, update_data: Dict, updated_by) -> Tuple[bool, List[str]]:
        """更新清单模板"""
        errors = []

        try:
            # 验证更新的数据（部分更新）
            is_valid, validation_errors = ChecklistService.validate_template_data(update_data, partial=True)
            if not is_valid:
                return False, validation_errors

            # 状态验证
            new_status = update_data.get('status')
            if new_status and new_status not in ChecklistService.TEMPLATE_STATUS:
                errors.append(f'模板状态无效，有效值：{", ".join(ChecklistService.TEMPLATE_STATUS)}')
                return False, errors

            # 版本变更验证
            current_version = template.version
            new_version = update_data.get('version')
            if new_version and new_version != current_version:
                # 可以在这里添加版本变更的验证逻辑
                logger.info(f"模板版本变更: {template.name} {current_version} -> {new_version}")

            # 更新模板基本信息
            allowed_fields = ['name', 'description', 'checklist_type', 'event_types',
                           'status', 'is_default', 'tags', 'metadata', 'version']

            for field in allowed_fields:
                if field in update_data:
                    setattr(template, field, update_data[field])

            # 处理模板项更新
            if 'items' in update_data:
                ChecklistService._update_template_items(template, update_data['items'])

            template.save()

            # 记录日志
            ChecklistService._log_template_activity(template, 'updated', updated_by, {
                'updated_fields': list(update_data.keys())
            })

            # 清除缓存
            ChecklistService._clear_template_cache(template.id)

            logger.info(f"清单模板更新成功: {template.name} (ID: {template.id})")
            return True, []

        except Exception as e:
            logger.error(f"更新清单模板失败: {e}")
            errors.append(f"更新清单模板失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def _update_template_items(template: ChecklistTemplate, items_data: List[Dict]):
        """更新模板项"""
        # 获取现有项的ID
        existing_ids = set(template.items.values_list('id', flat=True))
        
        # 处理新的或更新的项
        for idx, item_data in enumerate(items_data):
            item_id = item_data.get('id')
            
            if item_id and item_id in existing_ids:
                # 更新现有项
                ChecklistItemTemplate.objects.filter(id=item_id).update(
                    title=item_data.get('title'),
                    description=item_data.get('description', ''),
                    required=item_data.get('required', True),
                    order=item_data.get('order', idx),
                    weight=item_data.get('weight', 1),
                    status=item_data.get('status', 'active'),
                    metadata=item_data.get('metadata', {}),
                )
                existing_ids.remove(item_id)
            else:
                # 创建新项
                ChecklistItemTemplate.objects.create(
                    template=template,
                    title=item_data.get('title'),
                    description=item_data.get('description', ''),
                    required=item_data.get('required', True),
                    order=item_data.get('order', idx),
                    weight=item_data.get('weight', 1),
                    status=item_data.get('status', 'active'),
                    metadata=item_data.get('metadata', {}),
                )
        
        # 删除不存在的项
        if existing_ids:
            template.items.filter(id__in=existing_ids).delete()
    
    @staticmethod
    @transaction.atomic
    def create_instance(data: Dict, created_by) -> Tuple[ChecklistInstance, List[str]]:
        """创建清单实例"""
        errors = []
        
        try:
            # 验证数据
            is_valid, validation_errors = ChecklistService.validate_instance_data(data)
            if not is_valid:
                return None, validation_errors
            
            # 获取活动
            event_id = data.get('event_id') or data.get('event')
            
            # 如果已经是Event对象，直接使用
            if isinstance(event_id, Event):
                event = event_id
            else:
                try:
                    event = Event.objects.get(id=event_id)
                except Event.DoesNotExist:
                    errors.append('活动不存在')
                    return None, errors
            
            # 获取模板
            template_id = data.get('template_id') or data.get('template')
            
            # 如果已经是ChecklistTemplate对象,直接使用
            if isinstance(template_id, ChecklistTemplate):
                template = template_id
            else:
                try:
                    template = ChecklistTemplate.objects.get(id=template_id)
                except ChecklistTemplate.DoesNotExist:
                    errors.append('模板不存在')
                    return None, errors
            
            # 创建实例
            instance = ChecklistInstance.objects.create(
                event=event,
                template=template,
                name=data.get('name', f"{event.name} - {template.name}"),
                status=data.get('status', 'incomplete'),
                metadata=data.get('metadata', {}),
            )
            
            # 从模板创建实例项
            ChecklistService._create_instance_items(instance, template)
            
            # 记录日志
            ChecklistService._log_instance_activity(instance, 'created', created_by)
            
            logger.info(f"清单实例创建成功: {instance.name} (ID: {instance.id})")
            return instance, []
            
        except Exception as e:
            logger.error(f"创建清单实例失败: {e}")
            errors.append(f"创建清单实例失败: {str(e)}")
            return None, errors
    
    @staticmethod
    def _create_instance_items(instance: ChecklistInstance, template: ChecklistTemplate):
        """从模板创建实例项"""
        template_items = template.items.filter(status='active').order_by('order')
        
        for template_item in template_items:
            ChecklistItem.objects.create(
                instance=instance,
                template_item=template_item,
                title=template_item.title,
                description=template_item.description,
                required=template_item.required,
                order=template_item.order,
                weight=template_item.weight,
                status='pending',
                metadata=template_item.metadata,
            )
    
    @staticmethod
    @transaction.atomic
    def update_instance(instance: ChecklistInstance, update_data: Dict, updated_by) -> Tuple[bool, List[str]]:
        """更新清单实例"""
        errors = []

        try:
            # 验证更新的数据（部分更新）
            is_valid, validation_errors = ChecklistService.validate_instance_data(update_data, partial=True)
            if not is_valid:
                return False, validation_errors

            # 状态验证
            new_status = update_data.get('status')
            if new_status:
                is_valid, status_errors = ChecklistService.validate_status_transition(
                    instance.status, new_status
                )
                if not is_valid:
                    return False, status_errors

                # 更新完成时间
                if new_status in ['completed', 'pending_review']:
                    instance.completed_at = timezone.now()

            # 更新实例信息
            allowed_fields = ['name', 'status', 'metadata']
            for field in allowed_fields:
                if field in update_data:
                    setattr(instance, field, update_data[field])

            instance.save()

            # 记录日志
            ChecklistService._log_instance_activity(instance, 'updated', updated_by, {
                'updated_fields': list(update_data.keys())
            })

            # 清除缓存
            ChecklistService._clear_instance_cache(instance.id)

            logger.info(f"清单实例更新成功: {instance.name} (ID: {instance.id})")
            return True, []

        except Exception as e:
            logger.error(f"更新清单实例失败: {e}")
            errors.append(f"更新清单实例失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def update_item_status(item_id: str, status: str, checked_by, notes: str = '', 
                          attachments: List = None, location: Dict = None) -> Tuple[bool, List[str]]:
        """更新清单项状态"""
        errors = []
        
        try:
            # 获取清单项
            try:
                item = ChecklistItem.objects.select_for_update().get(id=item_id)
            except ChecklistItem.DoesNotExist:
                errors.append('清单项不存在')
                return False, errors
            
            # 验证状态
            valid_statuses = ['pending', 'in_progress', 'passed', 'failed', 'skipped']
            if status not in valid_statuses:
                errors.append(f'无效的状态，有效值：{", ".join(valid_statuses)}')
                return False, errors
            
            # 更新清单项
            item.status = status
            
            # 如果状态是完成状态，记录检查人
            if status in ['passed', 'failed']:
                item.checked_by = checked_by
                item.checked_at = timezone.now()
            
            # 更新其他字段
            if notes is not None:
                item.notes = notes
            
            if attachments is not None:
                item.attachments = attachments
            
            if location is not None:
                item.location = location
            
            # 清除离线同步标记
            item.offline_pending = False
            
            item.save()
            
            # 更新实例状态
            ChecklistService._update_instance_completion(item.instance)
            
            # 记录日志
            ChecklistService._log_item_activity(item, 'status_updated', checked_by, {
                'status': status,
                'notes': notes
            })
            
            # 清除缓存
            ChecklistService._clear_instance_cache(item.instance.id)
            
            logger.info(f"清单项状态更新成功: item_id={item_id}, status={status}")
            return True, []
            
        except Exception as e:
            logger.error(f"更新清单项状态失败: {e}")
            errors.append(f"更新清单项状态失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def _update_instance_completion(instance: ChecklistInstance):
        """更新实例完成状态"""
        # 获取所有项的状态
        items = instance.items.all()
        total_items = items.count()
        
        if total_items == 0:
            return
        
        # 统计各状态数量
        status_counts = items.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}
        
        passed_count = status_dict.get('passed', 0)
        failed_count = status_dict.get('failed', 0)
        skipped_count = status_dict.get('skipped', 0)
        pending_count = status_dict.get('pending', 0)
        in_progress_count = status_dict.get('in_progress', 0)
        
        # 计算完成度（考虑权重）
        completed_items = instance.items.filter(status__in=['passed', 'failed', 'skipped'])
        weighted_completion = sum(item.weight for item in completed_items)
        total_weight = sum(item.weight for item in items)
        completion_rate = (weighted_completion / total_weight * 100) if total_weight > 0 else 0
        
        # 更新实例完成度
        instance.completion_rate = round(completion_rate, 2)
        
        # 更新实例状态
        if instance.status != 'completed' and instance.status != 'cancelled':
            if pending_count == 0 and in_progress_count == 0:
                instance.status = 'completed'
                instance.completed_at = timezone.now()
            elif in_progress_count > 0:
                instance.status = 'in_progress'
            elif passed_count > 0 or failed_count > 0:
                instance.status = 'in_progress'
        
        instance.save()
    
    @staticmethod
    def get_instance_progress(instance: ChecklistInstance) -> Dict[str, Any]:
        """获取实例进度信息"""
        items = instance.items.all()
        total_items = items.count()
        
        if total_items == 0:
            return {
                'total_items': 0,
                'completed_items': 0,
                'completion_rate': 0,
                'by_status': {},
                'by_weight': {
                    'completed': 0,
                    'total': 0,
                    'rate': 0
                }
            }
        
        # 按状态统计
        status_counts = items.values('status').annotate(count=Count('id'))
        by_status = {item['status']: item['count'] for item in status_counts}
        
        completed_items = by_status.get('passed', 0) + by_status.get('failed', 0) + by_status.get('skipped', 0)
        
        # 按权重计算
        completed_weighted = sum(
            item.weight for item in items.filter(status__in=['passed', 'failed', 'skipped'])
        )
        total_weight = sum(item.weight for item in items)
        
        return {
            'total_items': total_items,
            'completed_items': completed_items,
            'completion_rate': instance.completion_rate,
            'by_status': {
                'pending': by_status.get('pending', 0),
                'in_progress': by_status.get('in_progress', 0),
                'passed': by_status.get('passed', 0),
                'failed': by_status.get('failed', 0),
                'skipped': by_status.get('skipped', 0),
            },
            'by_weight': {
                'completed': completed_weighted,
                'total': total_weight,
                'rate': round(completed_weighted / total_weight * 100, 2) if total_weight > 0 else 0
            }
        }
    
    @staticmethod
    def get_template_statistics(template: ChecklistTemplate) -> Dict[str, Any]:
        """获取模板统计信息"""
        # 统计实例数量
        instance_count = ChecklistInstance.objects.filter(template=template).count()
        
        # 统计各类状态的实例
        status_stats = ChecklistInstance.objects.filter(template=template).values('status').annotate(
            count=Count('id')
        )
        
        # 平均完成度
        completed_instances = ChecklistInstance.objects.filter(
            template=template,
            status='completed'
        )
        avg_completion = completed_instances.aggregate(
            avg=Sum('completion_rate') / Count('id')
        )['avg'] or 0
        
        return {
            'total_instances': instance_count,
            'by_status': {stat['status']: stat['count'] for stat in status_stats},
            'average_completion_rate': round(avg_completion, 2),
            'items_count': template.items.count()
        }
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Tuple[bool, List[str]]:
        """验证状态流转是否符合规则"""
        errors = []
        
        if current_status == new_status:
            errors.append('状态未变更')
            return False, errors
        
        allowed_transitions = ChecklistService.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_transitions:
            errors.append(f'状态流转无效：{current_status} -> {new_status}')
            errors.append(f'允许的流转：{", ".join([t for t in allowed_transitions])}')
            return False, errors
        
        return True, errors
    
    @staticmethod
    def get_templates_filter(user, filters: Dict = None) -> QuerySet:
        """获取过滤后的模板列表"""
        queryset = ChecklistTemplate.objects.select_related('created_by').prefetch_related('items')
        
        # 权限过滤：默认模板对所有用户可见，登录用户可看到自己创建的，超级用户可看到所有
        if user.is_authenticated:
            if not user.is_superuser:
                queryset = queryset.filter(Q(created_by=user) | Q(is_default=True))
        else:
            # 未认证用户只能看到默认模板
            queryset = queryset.filter(is_default=True)
        
        # 应用过滤
        if filters:
            # 状态过滤
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            # 类型过滤
            if 'checklist_type' in filters:
                queryset = queryset.filter(checklist_type=filters['checklist_type'])
            
            # 活动类型过滤
            if 'event_types__contains' in filters:
                queryset = queryset.filter(event_types__contains=filters['event_types__contains'])
            
            # 搜索
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(tags__icontains=search_term)
                )
        
        return queryset
    
    @staticmethod
    def get_instances_filter(user, filters: Dict = None) -> QuerySet:
        """获取过滤后的实例列表"""
        queryset = ChecklistInstance.objects.select_related(
            'template', 'event'
        ).prefetch_related('items')
        
        # 权限过滤：未认证用户无法访问实例
        if user.is_authenticated:
            if not user.is_superuser:
                queryset = queryset.filter(event__owner=user)
        else:
            # 未认证用户无权访问实例，返回空查询集
            return queryset.none()
        
        # 应用过滤
        if filters:
            # 活动过滤
            if 'event' in filters:
                queryset = queryset.filter(event_id=filters['event'])
            
            # 模板过滤
            if 'template' in filters:
                queryset = queryset.filter(template_id=filters['template'])
            
            # 状态过滤
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            # 搜索
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(event__name__icontains=search_term)
                )
        
        return queryset
    
    @staticmethod
    def _log_template_activity(template: ChecklistTemplate, action: str, user, details: Dict = None):
        """记录模板操作日志"""
        try:
            from apps.users.services.user_service import UserService
            
            UserService.log_user_activity(
                user=user,
                activity_type=f'checklist_template_{action}',
                ip_address='127.0.0.1',  # 需要从request获取
                user_agent='EventPilot System',
                details={
                    'template_id': str(template.id),
                    'template_name': template.name,
                    'action': action,
                    **(details or {})
                }
            )
        except Exception as e:
            logger.error(f"记录模板日志失败: {e}")
    
    @staticmethod
    def _log_instance_activity(instance: ChecklistInstance, action: str, user, details: Dict = None):
        """记录实例操作日志"""
        try:
            from apps.users.services.user_service import UserService
            
            UserService.log_user_activity(
                user=user,
                activity_type=f'checklist_instance_{action}',
                ip_address='127.0.0.1',
                user_agent='EventPilot System',
                details={
                    'instance_id': str(instance.id),
                    'instance_name': instance.name,
                    'event_id': str(instance.event.id),
                    'action': action,
                    **(details or {})
                }
            )
        except Exception as e:
            logger.error(f"记录实例日志失败: {e}")
    
    @staticmethod
    def _log_item_activity(item: ChecklistItem, action: str, user, details: Dict = None):
        """记录清单项操作日志"""
        try:
            from apps.users.services.user_service import UserService
            
            UserService.log_user_activity(
                user=user,
                activity_type=f'checklist_item_{action}',
                ip_address='127.0.0.1',
                user_agent='EventPilot System',
                details={
                    'item_id': str(item.id),
                    'item_title': item.title,
                    'instance_id': str(item.instance.id),
                    'action': action,
                    **(details or {})
                }
            )
        except Exception as e:
            logger.error(f"记录清单项日志失败: {e}")
    
    @staticmethod
    def _clear_template_cache(template_id):
        """清除模板相关缓存"""
        cache_keys = [
            f'checklist:template:{template_id}',
            f'checklist:template:{template_id}:statistics',
            f'checklist:template:{template_id}:items',
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    def _clear_instance_cache(instance_id):
        """清除实例相关缓存"""
        cache_keys = [
            f'checklist:instance:{instance_id}',
            f'checklist:instance:{instance_id}:progress',
            f'checklist:instance:{instance_id}:items',
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    @transaction.atomic
    def complete_instance(instance: ChecklistInstance, completed_by) -> Tuple[bool, List[str]]:
        """完成清单实例"""
        errors = []
        
        try:
            if instance.status == 'completed':
                errors.append('清单实例已完成')
                return False, errors
            
            if instance.status == 'cancelled':
                errors.append('清单实例已取消，无法完成')
                return False, errors
            
            # 检查必填项是否完成
            required_items = instance.items.filter(required=True)
            completed_required = required_items.filter(status__in=['passed', 'failed']).count()
            
            if completed_required < required_items.count():
                pending_required = required_items.count() - completed_required
                errors.append(f'还有 {pending_required} 个必填项未完成')
                return False, errors
            
            # 更新状态
            instance.status = 'completed'
            instance.completed_at = timezone.now()
            instance.save()
            
            # 记录日志
            ChecklistService._log_instance_activity(instance, 'completed', completed_by)
            
            # 清除缓存
            ChecklistService._clear_instance_cache(instance.id)
            
            logger.info(f"清单实例完成: {instance.name} (ID: {instance.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"完成清单实例失败: {e}")
            errors.append(f"完成清单实例失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def cancel_instance(instance: ChecklistInstance, cancelled_by, reason: str = '') -> Tuple[bool, List[str]]:
        """取消清单实例"""
        errors = []
        
        try:
            if instance.status == 'cancelled':
                errors.append('清单实例已取消')
                return False, errors
            
            if instance.status == 'completed':
                errors.append('清单实例已完成，无法取消')
                return False, errors
            
            # 更新状态
            instance.status = 'cancelled'
            instance.metadata['cancellation_reason'] = reason
            instance.metadata['cancelled_at'] = timezone.now().isoformat()
            instance.metadata['cancelled_by'] = cancelled_by.id
            instance.save()
            
            # 记录日志
            ChecklistService._log_instance_activity(instance, 'cancelled', cancelled_by, {
                'reason': reason
            })
            
            # 清除缓存
            ChecklistService._clear_instance_cache(instance.id)
            
            logger.info(f"清单实例取消: {instance.name} (ID: {instance.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"取消清单实例失败: {e}")
            errors.append(f"取消清单实例失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def get_completion_warnings(instance: ChecklistInstance) -> List[Dict]:
        """获取完成度警告"""
        warnings = []
        progress = ChecklistService.get_instance_progress(instance)
        completion_rate = progress.get('completion_rate', 0)
        
        if completion_rate < ChecklistService.COMPLETION_WARNING_THRESHOLD:
            warnings.append({
                'type': 'low_completion',
                'level': 'warning',
                'message': f'清单完成度较低 ({completion_rate}%)',
                'threshold': ChecklistService.COMPLETION_WARNING_THRESHOLD
            })
        
        # 检查是否有超时的清单项
        overdue_items = instance.items.filter(
            status__in=['pending', 'in_progress']
        )
        
        if overdue_items.count() > 0:
            warnings.append({
                'type': 'overdue_items',
                'level': 'warning',
                'message': f'有 {overdue_items.count()} 个清单项未完成',
                'count': overdue_items.count()
            })
        
        return warnings
    
    @staticmethod
    def export_instance_report(instance_id: str) -> Optional[Dict]:
        """导出实例报告"""
        try:
            instance = ChecklistInstance.objects.select_related(
                'template', 'event', 'event__owner'
            ).prefetch_related('items').get(id=instance_id)
            
            # 获取进度信息
            progress = ChecklistService.get_instance_progress(instance)
            
            # 生成报告
            report = {
                'instance': {
                    'id': str(instance.id),
                    'name': instance.name,
                    'status': instance.status,
                    'completion_rate': instance.completion_rate,
                    'created_at': instance.created_at.isoformat() if instance.created_at else None,
                    'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
                },
                'event': {
                    'id': str(instance.event.id),
                    'name': instance.event.name,
                    'owner': instance.event.owner.username if instance.event.owner else None,
                },
                'template': {
                    'id': str(instance.template.id),
                    'name': instance.template.name,
                },
                'progress': progress,
                'items': []
            }
            
            # 详细项
            for item in instance.items.all():
                report['items'].append({
                    'id': str(item.id),
                    'title': item.title,
                    'status': item.status,
                    'required': item.required,
                    'weight': item.weight,
                    'notes': item.notes,
                    'checked_by': item.checked_by.username if item.checked_by else None,
                    'checked_at': item.checked_at.isoformat() if item.checked_at else None,
                })
            
            return report
            
        except ChecklistInstance.DoesNotExist:
            logger.error(f"实例不存在: {instance_id}")
            return None
        except Exception as e:
            logger.error(f"导出实例报告失败: {e}")
            return None
    
    @staticmethod
    def get_checklist_summary(event_id: str) -> Dict[str, Any]:
        """获取活动清单摘要"""
        try:
            instances = ChecklistInstance.objects.filter(event_id=event_id)
            
            total_instances = instances.count()
            completed_instances = instances.filter(status='completed').count()
            in_progress_instances = instances.filter(status='in_progress').count()
            
            average_completion = instances.aggregate(
                avg=Sum('completion_rate') / Count('id')
            )['avg'] or 0
            
            # 获取所有实例的最新活动
            recent_items = []
            for instance in instances:
                recent_item = instance.items.filter(
                    checked_at__isnull=False
                ).order_by('-checked_at').first()
                
                if recent_item:
                    recent_items.append({
                        'instance_name': instance.name,
                        'item_title': recent_item.title,
                        'status': recent_item.status,
                        'checked_at': recent_item.checked_at.isoformat() if recent_item.checked_at else None,
                    })
            
            return {
                'total_instances': total_instances,
                'completed_instances': completed_instances,
                'in_progress_instances': in_progress_instances,
                'average_completion_rate': round(average_completion, 2),
                'recent_activity': recent_items[:10]  # 限制10条
            }
            
        except Exception as e:
            logger.error(f"获取清单摘要失败: {e}")
            return {}
