"""关联方档案服务层 - 档案CRUD业务逻辑"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class ContactProfileService:
    """关联方档案服务层 - 处理档案CRUD操作的业务逻辑"""
    
    @staticmethod
    @transaction.atomic
    def create_profile(data: Dict, owner: User, request=None) -> Tuple[Any, List[str]]:
        """
        创建新的关联方档案
        """
        from apps.profiles.models import ContactProfile
        from apps.users.services.user_service import UserService
        
        errors = []
        
        # 数据验证
        if not data.get('name'):
            errors.append("档案名称不能为空")
        
        if len(errors) > 0:
            return None, errors
        
        # 创建档案
        profile = ContactProfile.objects.create(
            profile_type=data.get('profile_type', 'client'),
            name=data['name'],
            company_name=data.get('company_name', ''),
            legal_person=data.get('legal_person', ''),
            registration_number=data.get('registration_number', ''),
            contact_info=data.get('contact_info', {}),
            industry=data.get('industry', ''),
            business_scope=data.get('business_scope', ''),
            tags=data.get('tags', []),
            status=data.get('status', 'prospective'),
            credit_score=data.get('credit_score', 0),
            quality_score=data.get('quality_score', 0),
            risk_level=data.get('risk_level', 'medium'),
            owner=owner
        )
        
        # 记录审计日志
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT')
        
        UserService.log_user_activity(
            user=owner,
            activity_type='profile_created',
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                'profile_id': str(profile.id),
                'profile_name': profile.name,
                'profile_type': profile.profile_type
            }
        )
        
        return profile, []
    
    @staticmethod
    @transaction.atomic
    def update_profile(profile, data: Dict, user: User, request=None) -> Tuple[Any, List[str]]:
        """
        更新关联方档案
        """
        errors = []
        
        # 数据验证
        if 'name' in data and not data['name']:
            errors.append("档案名称不能为空")
        
        if len(errors) > 0:
            return None, errors
        
        # 更新字段
        updatable_fields = [
            'name', 'company_name', 'legal_person', 'registration_number',
            'contact_info', 'industry', 'business_scope', 'tags', 'status',
            'credit_score', 'quality_score', 'risk_level'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        profile.save()
        
        # 记录审计日志
        from apps.users.services.user_service import UserService
        
        ip_address = request.META.get('REMOTE_ADDR') if request else None
        user_agent = request.META.get('HTTP_USER_AGENT') if request else None
        
        UserService.log_user_activity(
            user=user,
            activity_type='profile_updated',
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                'profile_id': str(profile.id),
                'profile_name': profile.name,
                'changed_fields': list(data.keys())
            }
        )
        
        return profile, []
    
    @staticmethod
    def get_filters(profile_type: Optional[str] = None, status: Optional[str] = None,
                   min_credit_score: Optional[int] = None, max_credit_score: Optional[int] = None,
                   risk_level: Optional[str] = None, search: Optional[str] = None) -> Dict:
        """
        构建档案查询过滤器
        """
        from apps.profiles.models import ContactProfile
        
        filters = {}
        
        if profile_type:
            filters['profile_type'] = profile_type
        
        if status:
            filters['status'] = status
        
        if risk_level:
            filters['risk_level'] = risk_level
        
        if min_credit_score is not None:
            filters['credit_score__gte'] = min_credit_score
        
        if max_credit_score is not None:
            filters['credit_score__lte'] = max_credit_score
        
        # 搜索过滤
        search_filter = None
        if search:
            from django.db.models import Q
            search_filter = Q(
                Q(name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(industry__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return filters, search_filter
    
    @staticmethod
    def assess_profile_comprehensive(profile) -> Dict[str, Any]:
        """
        综合评估档案质量
        """
        from apps.profiles.models import InteractionHistory, ProfileEvaluation
        
        # 获取交互历史统计
        recent_interactions = InteractionHistory.objects.filter(
            profile=profile,
            interaction_date__gte=timezone.now() - timedelta(days=365)
        )
        
        interaction_stats = {
            'total_count': recent_interactions.count(),
            'event_count': recent_interactions.filter(interaction_type='event').count(),
            'contract_count': recent_interactions.filter(interaction_type='contract').count(),
            'communication_count': recent_interactions.filter(interaction_type='communication').count(),
        }
        
        # 获取最新评估
        latest_evaluation = profile.evaluations.first()
        
        # 计算综合评分
        aggregate_score = profile.calculate_aggregate_score()
        
        # 风险因素识别
        risk_factors = []
        if profile.risk_level in ['high']:
            risk_factors.append("高风险等级")
        if profile.credit_score < 50:
            risk_factors.append("信用评分偏低")
        if profile.quality_score < 50:
            risk_factors.append("质量评分偏低")
        
        # 识别优势
        strengths = []
        if profile.credit_score >= 80:
            strengths.append("高信用度")
        if profile.quality_score >= 80:
            strengths.append("高质量服务")
        if interaction_stats['total_count'] >= 10:
            strengths.append("频繁合作")
        if profile.status == 'active':
            strengths.append("活跃合作")
        
        return {
            'aggregate_score': aggregate_score,
            'interaction_stats': interaction_stats,
            'latest_evaluation': latest_evaluation.id if latest_evaluation else None,
            'risk_factors': risk_factors,
            'strengths': strengths,
            'recommendation': ContactProfileService._get_recommendation(profile, interaction_stats)
        }
    
    @staticmethod
    def _get_recommendation(profile, interaction_stats: Dict) -> str:
        """
        获取合作建议
        """
        if profile.status == 'blacklisted':
            return "建议规避合作"
        
        if profile.risk_level == 'high':
            return "高风险需谨慎，建议深度评估"
        
        if profile.credit_score >= 80 and profile.quality_score >= 80:
            return "优秀合作对象，建议优先考虑"
        
        if interaction_stats['total_count'] >= 5:
            return "有一定合作基础，可持续观察"
        
        return "可考虑合作，建议小规模试点"


