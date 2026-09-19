"""交互历史服务层"""

from typing import Dict, Any, List, Tuple
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class InteractionService:
    """交互历史服务层"""
    
    @staticmethod
    @transaction.atomic
    def record_interaction(profile, data: Dict, user: User, request=None) -> Tuple[Any, List[str]]:
        """
        记录新的交互历史
        """
        from apps.profiles.models import InteractionHistory
        
        errors = []
        
        if not data.get('title'):
            errors.append("交互标题不能为空")
        
        if not data.get('interaction_type'):
            errors.append("交互类型不能为空")
        
        if len(errors) > 0:
            return None, errors
        
        interaction = InteractionHistory.objects.create(
            profile=profile,
            interaction_type=data['interaction_type'],
            title=data['title'],
            description=data.get('description', ''),
            related_event_id=data.get('related_event_id'),
            related_project_id=data.get('related_project_id'),
            metadata=data.get('metadata', {}),
            satisfaction_score=data.get('satisfaction_score'),
            outcome_status=data.get('outcome_status'),
            interaction_date=data.get('interaction_date', timezone.now()),
            created_by=user
        )
        
        return interaction, []
    
    @staticmethod
    def get_interaction_statistics(profile, days: int = 365) -> Dict[str, Any]:
        """
        获取档案的交互统计信息
        """
        from apps.profiles.models import InteractionHistory
        from django.db.models import Count, Avg
        
        cutoff_date = timezone.now() - timedelta(days=days)
        interactions = InteractionHistory.objects.filter(
            profile=profile,
            interaction_date__gte=cutoff_date
        )
        
        # 按类型统计
        type_stats = interactions.values('interaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 满意度统计
        satisfaction_stats = interactions.filter(
            satisfaction_score__isnull=False
        ).aggregate(
            avg_score=Avg('satisfaction_score'),
            count=Count('id')
        )
        
        # 时间趋势
        monthly_stats = {}
        for i in range(12):
            month_start = timezone.now() - timedelta(days=30*i)
            month_end = timezone.now() - timedelta(days=30*(i+1))
            count = interactions.filter(
                interaction_date__range=(month_end, month_start)
            ).count()
            monthly_stats[month_start.strftime('%Y-%m')] = count
        
        return {
            'total_interactions': interactions.count(),
            'by_type': list(type_stats),
            'average_satisfaction': satisfaction_stats['avg_score'],
            'satisfaction_count': satisfaction_stats['count'],
            'monthly_trend': monthly_stats
        }


