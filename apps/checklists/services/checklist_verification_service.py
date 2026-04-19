import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction
from django.db.models import Q, Count, Sum, F, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.checklists.models import (
    ChecklistTemplate, ChecklistInstance, ChecklistItem,
    ChecklistVerification, ChecklistVerificationDetail, ChecklistVerificationException
)

User = get_user_model()
logger = logging.getLogger(__name__)


class ChecklistVerificationService:
    """清单核验服务"""
    
    @staticmethod
    def validate_verification_plan(data: Dict) -> Tuple[bool, List[str]]:
        """验证核验计划"""
        errors = []
        
        # 必填字段验证
        if not data.get('instance_id'):
            errors.append('实例ID不能为空')
        
        if not data.get('planned_start_time'):
            errors.append('计划开始时间不能为空')
        
        if not data.get('planned_end_time'):
            errors.append('计划结束时间不能为空')
        
        # 时间验证
        try:
            start_time = data['planned_start_time']
            end_time = data['planned_end_time']
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if start_time >= end_time:
                errors.append('计划结束时间必须晚于开始时间')
        except Exception as e:
            errors.append(f'时间格式错误: {str(e)}')
        
        return len(errors) == 0, errors
    
    @staticmethod
    @transaction.atomic
    def create_verification_plan(data: Dict, created_by) -> Tuple[ChecklistVerification, List[str]]:
        """创建核验计划"""
        errors = []
        
        try:
            # 验证数据
            is_valid, validation_errors = ChecklistVerificationService.validate_verification_plan(data)
            if not is_valid:
                return None, validation_errors
            
            # 获取实例
            try:
                instance = ChecklistInstance.objects.get(id=data['instance_id'])
            except ChecklistInstance.DoesNotExist:
                errors.append('清单实例不存在')
                return None, errors
            
            # 检查是否已有进行中的核验
            existing_verification = ChecklistVerification.objects.filter(
                instance=instance,
                status__in=['pending', 'in_progress']
            ).first()
            
            if existing_verification:
                errors.append(f'该实例已有进行中的核验 (ID: {existing_verification.id})')
                return None, errors
            
            # 解析时间
            try:
                planned_start_time = data['planned_start_time']
                planned_end_time = data['planned_end_time']
                
                if isinstance(planned_start_time, str):
                    planned_start_time = datetime.fromisoformat(planned_start_time.replace('Z', '+00:00'))
                if isinstance(planned_end_time, str):
                    planned_end_time = datetime.fromisoformat(planned_end_time.replace('Z', '+00:00'))
                
                # 转换为带时区的datetime
                if timezone.is_naive(planned_start_time):
                    planned_start_time = timezone.make_aware(planned_start_time)
                if timezone.is_naive(planned_end_time):
                    planned_end_time = timezone.make_aware(planned_end_time)
            except Exception as e:
                errors.append(f'时间解析错误: {str(e)}')
                return None, errors
            
            # 创建核验记录
            verification = ChecklistVerification.objects.create(
                instance=instance,
                planned_start_time=planned_start_time,
                planned_end_time=planned_end_time,
                status='pending',
                requires_approval=data.get('requires_approval', False),
                total_items=instance.items.count(),
                verified_by=created_by if data.get('start_immediately') else None,
                notes=data.get('notes', ''),
            )
            
            # 如果需要立即开始
            if data.get('start_immediately'):
                verification.actual_start_time = timezone.now()
                verification.status = 'in_progress'
                verification.save()
            
            logger.info(f"核验计划创建成功: {instance.name} (ID: {verification.id})")
            return verification, []
            
        except Exception as e:
            logger.error(f"创建核验计划失败: {e}")
            errors.append(f"创建核验计划失败: {str(e)}")
            return None, errors
    
    @staticmethod
    @transaction.atomic
    def start_verification(verification_id: str, started_by) -> Tuple[bool, List[str]]:
        """开始核验"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.select_for_update().get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查状态
            if verification.status != 'pending':
                errors.append(f'核验状态不是待核验，当前状态: {verification.status}')
                return False, errors
            
            # 更新状态
            verification.status = 'in_progress'
            verification.actual_start_time = timezone.now()
            verification.verified_by = started_by
            verification.save()
            
            logger.info(f"核验开始: {verification.instance.name} (ID: {verification.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"开始核验失败: {e}")
            errors.append(f"开始核验失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def record_verification_detail(verification_id: str, item_id: str, 
                                    result: str, evidence: str = '',
                                    verified_by=None, location: Dict = None,
                                    attachments: List = None, notes: str = '') -> Tuple[bool, List[str]]:
        """记录核验详情"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查状态
            if verification.status != 'in_progress':
                errors.append(f'核验状态不是进行中，当前状态: {verification.status}')
                return False, errors
            
            # 获取清单项
            try:
                item = ChecklistItem.objects.get(id=item_id)
            except ChecklistItem.DoesNotExist:
                errors.append('清单项不存在')
                return False, errors
            
            # 创建核验详情
            detail = ChecklistVerificationDetail.objects.create(
                verification=verification,
                checklist_item=item,
                status='completed' if result in ['passed', 'failed'] else 'pending',
                result=result,
                evidence=evidence,
                attachments=attachments or [],
                verified_at=timezone.now(),
                verified_by=verified_by,
                location=location or {},
                notes=notes,
            )
            
            # 更新清单项状态
            item.status = result
            item.notes = notes
            if attachments:
                item.attachments = attachments
            if location:
                item.location = location
            item.checked_at = timezone.now()
            if verified_by:
                item.checked_by = verified_by
            item.save()
            
            # 更新核验统计
            ChecklistVerificationService._update_verification_stats(verification)
            
            logger.info(f"核验详情记录成功: {item.title} = {result}")
            return True, []
            
        except Exception as e:
            logger.error(f"记录核验详情失败: {e}")
            errors.append(f"记录核验详情失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def _update_verification_stats(verification: ChecklistVerification):
        """更新核验统计信息"""
        # 获取所有核验详情
        details = verification.details.all()
        
        verification.verified_items = details.count()
        verification.passed_items = details.filter(result='passed').count()
        verification.failed_items = details.filter(result='failed').count()
        verification.save()
    
    @staticmethod
    @transaction.atomic
    def complete_verification(verification_id: str, completed_by,
                               notes: str = '') -> Tuple[bool, List[str]]:
        """完成核验"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.select_for_update().get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查状态
            if verification.status != 'in_progress':
                errors.append(f'核验状态不是进行中，当前状态: {verification.status}')
                return False, errors
            
            # 检查是否所有项都已完成
            if verification.verified_items < verification.total_items:
                pending_count = verification.total_items - verification.verified_items
                errors.append(f'还有 {pending_count} 个清单项未完成核验')
                return False, errors
            
            # 更新状态
            verification.status = 'completed'
            verification.actual_end_time = timezone.now()
            verification.notes = notes
            verification.save()
            
            # 更新实例状态
            from apps.checklists.services.checklist_service import ChecklistService
            ChecklistService.complete_instance(verification.instance, completed_by)
            
            logger.info(f"核验完成: {verification.instance.name} (ID: {verification.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"完成核验失败: {e}")
            errors.append(f"完成核验失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def request_approval(verification_id: str, requested_by) -> Tuple[bool, List[str]]:
        """请求审批"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查状态
            if verification.status != 'completed':
                errors.append(f'只有已完成的核验才能请求审批，当前状态: {verification.status}')
                return False, errors
            
            if not verification.requires_approval:
                errors.append('该核验不需要审批')
                return False, errors
            
            # 更新审批状态
            verification.approval_status = 'pending'
            verification.save()
            
            logger.info(f"核验审批请求: {verification.instance.name} (ID: {verification.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"请求审批失败: {e}")
            errors.append(f"请求审批失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def approve_verification(verification_id: str, approved_by, 
                            comments: str = '') -> Tuple[bool, List[str]]:
        """批准核验"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.select_for_update().get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查审批状态
            if verification.approval_status != 'pending':
                errors.append(f'核验审批状态不是待审批，当前状态: {verification.approval_status}')
                return False, errors
            
            # 更新审批信息
            verification.approval_status = 'approved'
            verification.approved_by = approved_by
            verification.approved_at = timezone.now()
            verification.save()
            
            logger.info(f"核验已批准: {verification.instance.name} (ID: {verification.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"批准核验失败: {e}")
            errors.append(f"批准核验失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def reject_verification(verification_id: str, rejected_by, 
                             reason: str) -> Tuple[bool, List[str]]:
        """拒绝核验"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.select_for_update().get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return False, errors
            
            # 检查审批状态
            if verification.approval_status != 'pending':
                errors.append(f'核验审批状态不是待审批，当前状态: {verification.approval_status}')
                return False, errors
            
            # 更新审批信息
            verification.approval_status = 'rejected'
            verification.rejection_reason = reason
            verification.approved_by = rejected_by
            verification.approved_at = timezone.now()
            verification.save()
            
            logger.info(f"核验已拒绝: {verification.instance.name} (ID: {verification.id}), 原因: {reason}")
            return True, []
            
        except Exception as e:
            logger.error(f"拒绝核验失败: {e}")
            errors.append(f"拒绝核验失败: {str(e)}")
            return False, errors
    
    @staticmethod
    @transaction.atomic
    def create_exception(verification_id: str, exception_type: str, 
                          title: str, description: str, severity: str,
                          checklist_item_id: str = None) -> Tuple[ChecklistVerificationException, List[str]]:
        """创建核验异常"""
        errors = []
        
        try:
            # 获取核验记录
            try:
                verification = ChecklistVerification.objects.get(id=verification_id)
            except ChecklistVerification.DoesNotExist:
                errors.append('核验记录不存在')
                return None, errors
            
            # 获取清单项（如果提供）
            checklist_item = None
            if checklist_item_id:
                try:
                    checklist_item = ChecklistItem.objects.get(id=checklist_item_id)
                except ChecklistItem.DoesNotExist:
                    errors.append('清单项不存在')
                    return None, errors
            
            # 创建异常记录
            exception = ChecklistVerificationException.objects.create(
                verification=verification,
                exception_type=exception_type,
                status='open',
                title=title,
                description=description,
                severity=severity,
                checklist_item=checklist_item
            )
            
            # 更新核验记录的异常标记
            verification.has_exceptions = True
            verification.exception_details.append({
                'exception_id': str(exception.id),
                'type': exception_type,
                'title': title,
                'created_at': timezone.now().isoformat()
            })
            verification.save()
            
            logger.info(f"核验异常创建成功: {title} (ID: {exception.id})")
            return exception, []
            
        except Exception as e:
            logger.error(f"创建核验异常失败: {e}")
            errors.append(f"创建核验异常失败: {str(e)}")
            return None, errors
    
    @staticmethod
    @transaction.atomic
    def resolve_exception(exception_id: str, resolution: str, 
                           resolved_by) -> Tuple[bool, List[str]]:
        """解决异常"""
        errors = []
        
        try:
            # 获取异常记录
            try:
                exception = ChecklistVerificationException.objects.select_for_update().get(id=exception_id)
            except ChecklistVerificationException.DoesNotExist:
                errors.append('异常记录不存在')
                return False, errors
            
            # 更新异常状态
            exception.status = 'resolved'
            exception.resolution = resolution
            exception.resolved_by = resolved_by
            exception.resolved_at = timezone.now()
            exception.save()
            
            # 检查是否还有未解决的异常
            verification = exception.verification
            open_exceptions = verification.exceptions.filter(status='open')
            
            if not open_exceptions.exists():
                verification.has_exceptions = False
                verification.save()
            
            logger.info(f"异常已解决: {exception.title} (ID: {exception.id})")
            return True, []
            
        except Exception as e:
            logger.error(f"解决异常失败: {e}")
            errors.append(f"解决异常失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def get_verification_statistics(verification_id: str) -> Dict[str, Any]:
        """获取核验统计信息"""
        try:
            verification = ChecklistVerification.objects.get(id=verification_id)
            
            stats = {
                'verification_id': str(verification.id),
                'instance_name': verification.instance.name,
                'total_items': verification.total_items,
                'verified_items': verification.verified_items,
                'passed_items': verification.passed_items,
                'failed_items': verification.failed_items,
                'pass_rate': round(verification.passed_items / verification.total_items * 100, 2) if verification.total_items > 0 else 0,
                'status': verification.status,
                'approval_status': verification.approval_status,
                'has_exceptions': verification.has_exceptions,
                'exception_count': verification.exceptions.count(),
                'planned_duration': None,
                'actual_duration': None,
            }
            
            # 计算计划持续时间
            if verification.planned_start_time and verification.planned_end_time:
                planned_duration = verification.planned_end_time - verification.planned_start_time
                stats['planned_duration'] = planned_duration.total_seconds()
            
            # 计算实际持续时间
            if verification.actual_start_time and verification.actual_end_time:
                actual_duration = verification.actual_end_time - verification.actual_start_time
                stats['actual_duration'] = actual_duration.total_seconds()
            
            return stats
            
        except ChecklistVerification.DoesNotExist:
            logger.error(f"核验记录不存在: {verification_id}")
            return {}
        except Exception as e:
            logger.error(f"获取核验统计信息失败: {e}")
            return {}
    
    @staticmethod
    def get_verification_report(verification_id: str) -> Optional[Dict]:
        """获取核验报告"""
        try:
            verification = ChecklistVerification.objects.select_related(
                'instance', 'instance__template', 'instance__event',
                'verified_by', 'approved_by'
            ).prefetch_related('details', 'details__checklist_item').get(id=verification_id)
            
            report = {
                'verification': {
                    'id': str(verification.id),
                    'status': verification.status,
                    'approval_status': verification.approval_status,
                    'requires_approval': verification.requires_approval,
                    'planned_start_time': verification.planned_start_time.isoformat(),
                    'planned_end_time': verification.planned_end_time.isoformat(),
                    'actual_start_time': verification.actual_start_time.isoformat() if verification.actual_start_time else None,
                    'actual_end_time': verification.actual_end_time.isoformat() if verification.actual_end_time else None,
                },
                'instance': {
                    'id': str(verification.instance.id),
                    'name': verification.instance.name,
                    'status': verification.instance.status,
                    'completion_rate': verification.instance.completion_rate,
                },
                'template': {
                    'id': str(verification.instance.template.id),
                    'name': verification.instance.template.name,
                },
                'statistics': ChecklistVerificationService.get_verification_statistics(verification_id),
                'details': [],
                'exceptions': []
            }
            
            # 核验详情
            for detail in verification.details.all():
                report['details'].append({
                    'item_id': str(detail.checklist_item.id),
                    'item_title': detail.checklist_item.title,
                    'result': detail.result,
                    'evidence': detail.evidence,
                    'verified_by': detail.verified_by.username if detail.verified_by else None,
                    'verified_at': detail.verified_at.isoformat(),
                    'notes': detail.notes,
                })
            
            # 异常信息
            for exception in verification.exceptions.all():
                report['exceptions'].append({
                    'id': str(exception.id),
                    'type': exception.exception_type,
                    'title': exception.title,
                    'description': exception.description,
                    'severity': exception.severity,
                    'status': exception.status,
                    'assigned_to': exception.assigned_to.username if exception.assigned_to else None,
                    'resolution': exception.resolution,
                })
            
            return report
            
        except ChecklistVerification.DoesNotExist:
            logger.error(f"核验记录不存在: {verification_id}")
            return None
        except Exception as e:
            logger.error(f"获取核验报告失败: {e}")
            return None