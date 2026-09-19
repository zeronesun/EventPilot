"""评估服务层"""

from typing import Dict, Any, List, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class EvaluationService:
    """评估服务层"""
    
    @staticmethod
    @transaction.atomic
    def create_evaluation(profile, data: Dict, user: User, request=None) -> Tuple[Any, List[str]]:
        """
        创建评估记录
        """
        from apps.profiles.models import ProfileEvaluation
        
        errors = []
        
        if not data.get('recommendations'):
            errors.append("评估建议不能为空")
        
        if len(errors) > 0:
            return None, errors
        
        evaluation = ProfileEvaluation.objects.create(
            profile=profile,
            evaluator=user,
            credit_score=data.get('credit_score'),
            quality_score=data.get('quality_score'),
            service_quality=data.get('service_quality'),
            response_speed=data.get('response_speed'),
            professional_ability=data.get('professional_ability'),
            evaluation_criteria=data.get('evaluation_criteria', {}),
            risk_assessment=data.get('risk_assessment', ''),
            risk_level=data.get('risk_level'),
            recommendations=data['recommendations'],
            overall_conclusion=data.get('overall_conclusion', ''),
            next_evaluation_date=data.get('next_evaluation_date')
        )
        
        return evaluation, []


