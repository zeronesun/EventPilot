import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.checklists.models import (
    ChecklistTemplate, ChecklistInstance, ChecklistItem,
    ChecklistVersion, ChecklistVersionComparison
)

User = get_user_model()
logger = logging.getLogger(__name__)


class ChecklistVersionService:
    """清单版本管理服务"""
    
    @staticmethod
    def create_version_number(current_version: str, version_type: str = 'patch') -> str:
        """生成新的版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) != 3:
                return '1.0.0'
            
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            
            if version_type == 'major':
                major += 1
                minor = 0
                patch = 0
            elif version_type == 'minor':
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            return f"{major}.{minor}.{patch}"
        except Exception as e:
            logger.error(f"生成版本号失败: {e}")
            return '1.0.0'
    
    @staticmethod
    @transaction.atomic
    def create_template_version(template: ChecklistTemplate, version_type: str = 'patch',
                                  changelog: str = '', created_by=None) -> Tuple[ChecklistVersion, List[str]]:
        """创建模板版本"""
        errors = []
        
        try:
            # 获取当前最新版本
            latest_version = template.versions.filter(is_active=True).first()
            current_version = latest_version.version_number if latest_version else '0.0.0'
            
            # 生成新版本号
            new_version_number = ChecklistVersionService.create_version_number(current_version, version_type)
            
            # 创建数据快照
            snapshot = {
                'template_id': str(template.id),
                'name': template.name,
                'description': template.description,
                'checklist_type': template.checklist_type,
                'event_types': template.event_types,
                'tags': template.tags,
                'items': [
                    {
                        'id': str(item.id),
                        'title': item.title,
                        'description': item.description,
                        'required': item.required,
                        'order': item.order,
                        'weight': item.weight,
                        'status': item.status,
                    }
                    for item in template.items.all()
                ]
            }
            
            # 创建版本记录
            version = ChecklistVersion.objects.create(
                template=template,
                version_number=new_version_number,
                version_type=version_type,
                changelog=changelog,
                snapshot=snapshot,
                is_active=True,
                created_by=created_by
            )
            
            # 将旧版本标记为非激活
            if latest_version:
                latest_version.is_active = False
                latest_version.save()
            
            logger.info(f"模板版本创建成功: {template.name} v{new_version_number}")
            return version, []
            
        except Exception as e:
            logger.error(f"创建模板版本失败: {e}")
            errors.append(f"创建模板版本失败: {str(e)}")
            return None, errors
    
    @staticmethod
    @transaction.atomic
    def create_instance_version(instance: ChecklistInstance, version_type: str = 'patch',
                                  changelog: str = '', created_by=None) -> Tuple[ChecklistVersion, List[str]]:
        """创建实例版本"""
        errors = []
        
        try:
            # 获取当前最新版本
            latest_version = instance.versions.filter(is_active=True).first()
            current_version = latest_version.version_number if latest_version else '0.0.0'
            
            # 生成新版本号
            new_version_number = ChecklistVersionService.create_version_number(current_version, version_type)
            
            # 创建数据快照
            snapshot = {
                'instance_id': str(instance.id),
                'name': instance.name,
                'status': instance.status,
                'completion_rate': instance.completion_rate,
                'items': [
                    {
                        'id': str(item.id),
                        'title': item.title,
                        'status': item.status,
                        'required': item.required,
                        'order': item.order,
                        'weight': item.weight,
                        'notes': item.notes,
                    }
                    for item in instance.items.all()
                ]
            }
            
            # 创建版本记录
            version = ChecklistVersion.objects.create(
                instance=instance,
                version_number=new_version_number,
                version_type=version_type,
                changelog=changelog,
                snapshot=snapshot,
                is_active=True,
                created_by=created_by
            )
            
            # 将旧版本标记为非激活
            if latest_version:
                latest_version.is_active = False
                latest_version.save()
            
            logger.info(f"实例版本创建成功: {instance.name} v{new_version_number}")
            return version, []
            
        except Exception as e:
            logger.error(f"创建实例版本失败: {e}")
            errors.append(f"创建实例版本失败: {str(e)}")
            return None, errors
    
    @staticmethod
    def compare_versions(from_version: ChecklistVersion, to_version: ChecklistVersion,
                          created_by=None) -> Tuple[ChecklistVersionComparison, List[str]]:
        """比较两个版本"""
        errors = []
        
        try:
            from_snapshot = from_version.snapshot
            to_snapshot = to_version.snapshot
            
            # 比较差异
            differences = {
                'version_change': f"{from_version.version_number} -> {to_version.version_number}",
                'field_changes': [],
                'item_changes': {
                    'added': [],
                    'removed': [],
                    'modified': [],
                    'unchanged': []
                }
            }
            
            # 如果是模板版本
            if from_snapshot.get('template_id') and to_snapshot.get('template_id'):
                # 比较字段
                fields_to_compare = ['name', 'description', 'checklist_type', 'tags']
                for field in fields_to_compare:
                    if from_snapshot.get(field) != to_snapshot.get(field):
                        differences['field_changes'].append({
                            'field': field,
                            'from': from_snapshot.get(field),
                            'to': to_snapshot.get(field)
                        })
                
                # 比较清单项
                from_items = {item['id']: item for item in from_snapshot.get('items', [])}
                to_items = {item['id']: item for item in to_snapshot.get('items', [])}
                
                # 新增的项
                for item_id, item in to_items.items():
                    if item_id not in from_items:
                        differences['item_changes']['added'].append(item)
                
                # 删除的项
                for item_id, item in from_items.items():
                    if item_id not in to_items:
                        differences['item_changes']['removed'].append(item)
                
                # 修改的项
                for item_id in from_items:
                    if item_id in to_items:
                        from_item = from_items[item_id]
                        to_item = to_items[item_id]
                        
                        # 检查关键字段是否变化
                        changed_fields = []
                        for field in ['title', 'description', 'required', 'weight', 'status']:
                            if from_item.get(field) != to_item.get(field):
                                changed_fields.append({
                                    'field': field,
                                    'from': from_item.get(field),
                                    'to': to_item.get(field)
                                })
                        
                        if changed_fields:
                            differences['item_changes']['modified'].append({
                                'item_id': item_id,
                                'changes': changed_fields
                            })
                        else:
                            differences['item_changes']['unchanged'].append(item_id)
            
            # 生成对比摘要
            summary_parts = []
            if differences['field_changes']:
                summary_parts.append(f"{len(differences['field_changes'])} 个字段变更")
            if differences['item_changes']['added']:
                summary_parts.append(f"{len(differences['item_changes']['added'])} 个新项")
            if differences['item_changes']['removed']:
                summary_parts.append(f"{len(differences['item_changes']['removed'])} 个删除项")
            if differences['item_changes']['modified']:
                summary_parts.append(f"{len(differences['item_changes']['modified'])} 个修改项")
            
            summary = ', '.join(summary_parts) if summary_parts else '无变更'
            
            # 创建对比记录
            comparison = ChecklistVersionComparison.objects.create(
                from_version=from_version,
                to_version=to_version,
                differences=differences,
                summary=summary,
                created_by=created_by
            )
            
            logger.info(f"版本对比完成: {from_version.version_number} -> {to_version.version_number}")
            return comparison, []
            
        except Exception as e:
            logger.error(f"版本对比失败: {e}")
            errors.append(f"版本对比失败: {str(e)}")
            return None, errors
    
    @staticmethod
    @transaction.atomic
    def rollback_to_version(version: ChecklistVersion, rolled_back_by=None) -> Tuple[bool, List[str]]:
        """回滚到指定版本"""
        errors = []
        
        try:
            # 检查版本是否存在
            if not version.is_active:
                errors.append('只能回滚到已激活的版本')
                return False, errors
            
            snapshot = version.snapshot
            
            # 如果是模板版本
            if version.template:
                template = version.template
                
                # 更新模板基本信息
                template.name = snapshot.get('name')
                template.description = snapshot.get('description')
                template.checklist_type = snapshot.get('checklist_type')
                template.event_types = snapshot.get('event_types', [])
                template.tags = snapshot.get('tags', [])
                
                # 重建模板项
                template.items.all().delete()
                
                for item_data in snapshot.get('items', []):
                    from apps.checklists.models import ChecklistItemTemplate
                    ChecklistItemTemplate.objects.create(
                        template=template,
                        title=item_data.get('title'),
                        description=item_data.get('description', ''),
                        required=item_data.get('required', True),
                        order=item_data.get('order', 0),
                        weight=item_data.get('weight', 1),
                        status=item_data.get('status', 'active')
                    )
                
                template.save()
                
                # 创建回滚版本记录
                new_version_number = ChecklistVersionService.create_version_number(
                    version.version_number, 'patch'
                )
                
                ChecklistVersion.objects.create(
                    template=template,
                    version_number=new_version_number,
                    version_type='patch',
                    changelog=f'回滚到版本 {version.version_number}',
                    snapshot=snapshot,
                    is_rollback=True,
                    is_active=True,
                    created_by=rolled_back_by
                )
                
                # 标记原版本为非激活
                version.is_active = False
                version.save()
                
                templateVersion = template.version
                templateVersion.version = new_version_number
                templateVersion.save()
                
                logger.info(f"模板回滚成功: {template.name} -> v{version.version_number}")
                return True, []
            
            # 如果是实例版本
            elif version.instance:
                instance = version.instance
                
                # 更新实例基本信息
                instance.name = snapshot.get('name')
                instance.status = snapshot.get('status')
                instance.completion_rate = snapshot.get('completion_rate', 0.0)
                
                # 重建实例项
                from apps.checklists.models import ChecklistItem
                instance.items.all().delete()
                
                for item_data in snapshot.get('items', []):
                    ChecklistItem.objects.create(
                        instance=instance,
                        title=item_data.get('title'),
                        description=item_data.get('description', ''),
                        required=item_data.get('required', True),
                        order=item_data.get('order', 0),
                        weight=item_data.get('weight', 1),
                        status=item_data.get('status', 'pending'),
                        notes=item_data.get('notes', '')
                    )
                
                instance.save()
                
                # 创建回滚版本记录
                new_version_number = ChecklistVersionService.create_version_number(
                    version.version_number, 'patch'
                )
                
                ChecklistVersion.objects.create(
                    instance=instance,
                    version_number=new_version_number,
                    version_type='patch',
                    changelog=f'回滚到版本 {version.version_number}',
                    snapshot=snapshot,
                    is_rollback=True,
                    is_active=True,
                    created_by=rolled_back_by
                )
                
                # 标记原版本为非激活
                version.is_active = False
                version.save()
                
                logger.info(f"实例回滚成功: {instance.name} -> v{version.version_number}")
                return True, []
            
            errors.append('版本必须关联到模板或实例')
            return False, errors
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            errors.append(f"回滚失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def get_version_history(template_id: str = None, instance_id: str = None) -> List[Dict]:
        """获取版本历史"""
        try:
            if template_id:
                versions = ChecklistVersion.objects.filter(
                    template_id=template_id
                ).order_by('-created_at')
            elif instance_id:
                versions = ChecklistVersion.objects.filter(
                    instance_id=instance_id
                ).order_by('-created_at')
            else:
                return []
            
            return [
                {
                    'id': str(version.id),
                    'version_number': version.version_number,
                    'version_type': version.version_type,
                    'changelog': version.changelog,
                    'is_active': version.is_active,
                    'is_rollback': version.is_rollback,
                    'created_at': version.created_at.isoformat() if version.created_at else None,
                    'created_by': version.created_by.username if version.created_by else None,
                }
                for version in versions
            ]
            
        except Exception as e:
            logger.error(f"获取版本历史失败: {e}")
            return []