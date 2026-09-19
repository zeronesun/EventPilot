"""档案分析服务"""

from typing import Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileAnalytics:
    """档案分析服务"""
    
    @staticmethod
    def get_dashboard_stats(user: User) -> Dict[str, Any]:
        """
        获取档案管理仪表盘统计
        """
        from apps.profiles.models import ContactProfile, InteractionHistory, ProfileEvaluation
        
        # 用户权限范围内的档案
        if user.is_superuser:
            base_query = ContactProfile.objects.filter(is_deleted=False)
        else:
            base_query = ContactProfile.objects.filter(
                owner=user,
                is_deleted=False
            )
        
        # 总体统计
        total_profiles = base_query.count()
        
        # 按类型统计
        type_stats = {}
        for pt in ContactProfile.ProfileType.values:
            count = base_query.filter(profile_type=pt).count()
            type_stats[pt] = count
        
        # 按状态统计
        status_stats = {}
        for st in ContactProfile.Status.values:
            count = base_query.filter(status=st).count()
            status_stats[st] = count
        
        # 评分统计
        avg_credit = base_query.aggregate(
            avg=models.Avg('credit_score'),
            avg_quality=models.Avg('quality_score')
        )
        
        # 风险分布
        risk_levels = {}
        for rl in ['low', 'medium', 'high']:
            count = base_query.filter(risk_level=rl).count()
            risk_levels[rl] = count
        
        # 最近交互统计
        recent_interactions = InteractionHistory.objects.filter(
            interaction_date__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return {
            'total_profiles': total_profiles,
            'by_type': type_stats,
            'by_status': status_stats,
            'average_scores': {
                'credit': avg_credit['avg'] or 0,
                'quality': avg_credit['avg_quality'] or 0
            },
            'risk_distribution': risk_levels,
            'recent_interactions': recent_interactions,
            'high_risk_count': risk_levels.get('high', 0),
            'high_score_count': base_query.filter(credit_score__gte=80).count()
        }