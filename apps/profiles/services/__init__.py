"""
关联方档案服务层
规则基智能推荐系统实现
"""

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


class IntelligentRecommender:
    """
    智能推荐引擎 - 基于规则的推荐系统
    不使用大模型API，完全自主可控
    """
    
    @staticmethod
    def recommend_suppliers(event_requirements: Dict, limit: int = 10) -> List[Dict]:
        """
        智能供应商推荐 - 基于业务规则
        """
        from apps.profiles.models import ContactProfile, InteractionHistory
        
        print("[Intelligent Recommender] 开始智能供应商推荐...")
        
        # 获取活跃的供应商档案
        suppliers = ContactProfile.objects.filter(
            profile_type='supplier',
            status='active',
            is_deleted=False
        ).select_related('owner').prefetch_related('contacts')
        
        recommendations = []
        
        for supplier in suppliers:
            score = 0
            reasons = []
            
            # 规则1: 历史合作记录 (权重30%)
            past_coop = InteractionHistory.objects.filter(
                profile=supplier,
                interaction_type='event'
            ).count()
            
            if past_coop > 0:
                coop_score = min(past_coop * 3, 30)  # 最多30分
                if past_coop >= 5:
                    reasons.append(f"丰富合作经验 ({past_coop}次)")
                score += coop_score
            
            # 规则2: 评分和满意度 (权重25%)
            if supplier.quality_score > 0:
                quality_score = (supplier.quality_score / 100) * 25  # 0-25分
                if supplier.quality_score >= 80:
                    reasons.append("高质量服务交付")
                score += quality_score
            
            # 规则3: 信用评估 (权重20%)
            if supplier.credit_score > 0:
                credit_score = (supplier.credit_score / 100) * 20
                if supplier.credit_score >= 80:
                    reasons.append("信用记录优秀")
                score += credit_score
            
            # 规则4: 风险等级评估 (权重15%)
            if supplier.risk_level == 'low':
                score += 15
                reasons.append("低风险等级")
            elif supplier.risk_level == 'medium':
                score += 8
            
            # 规则5: 业务类型匹配 (权重10%)
            required_type = event_requirements.get('type', '')
            if required_type and required_type in supplier.tags:
                score += 10
                reasons.append(f"{required_type}业务匹配度高")
            
            # 规则6: 近期活跃度 (可选加分)
            recent_activity = InteractionHistory.objects.filter(
                profile=supplier,
                interaction_date__gte=timezone.now() - timedelta(days=90)
            ).count()
            
            if recent_activity >= 3:
                score += 5  # 额外加分
                reasons.append("近期合作活跃")
            
            # 如果总分>0，加入推荐列表
            if score > 0:
                primary_contact = supplier.get_primary_contact()
                recommendations.append({
                    'profile': supplier,
                    'recommendation_score': score,
                    'reasons': reasons,
                    'primary_contact': primary_contact.name if primary_contact else None
                })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        # 返回前N个
        results = []
        for rec in recommendations[:limit]:
            profile = rec['profile']
            results.append({
                'profile_id': str(profile.id),
                'name': profile.name,
                'company_name': profile.company_name,
                'profile_type': profile.profile_type,
                'recommendation_score': rec['recommendation_score'],
                'reasons': rec['reasons'],
                'credit_score': profile.credit_score,
                'quality_score': profile.quality_score,
                'risk_level': profile.risk_level,
                'primary_contact': rec['primary_contact']
            })
        
        print(f"[Intelligent Recommender] 推荐完成，返回 {len(results)} 个结果")
        return results
    
    @staticmethod
    def recommend_profiles(query: str, profile_type: Optional[str] = None, 
                          limit: int = 10) -> List[Dict]:
        """
        智能档案搜索 - 基于多维匹配规则
        """
        from apps.profiles.models import ContactProfile
        from django.db.models import Q
        
        base_query = ContactProfile.objects.filter(
            is_deleted=False
        )
        
        # 类型过滤
        if profile_type:
            base_query = base_query.filter(profile_type=profile_type)
        
        # 搜索关键词匹配
        if query:
            search_query = Q(
                Q(name__icontains=query) |
                Q(company_name__icontains=query) |
                Q(industry__icontains=query)
            )
            base_query = base_query.filter(search_query)
        
        # 按相关度和评分排序
        results = []
        for profile in base_query[:limit * 2]:  # 获取更多候选
            relevance_score = 0
            
            # 名称匹配度
            if query and query.lower() in profile.name.lower():
                relevance_score += 50
            if query and profile.company_name and query.lower() in profile.company_name.lower():
                relevance_score += 30
            
            # 综合评分加成
            relevance_score += profile.calculate_aggregate_score() * 0.2
            
            # 活跃状态加成
            if profile.status == 'active':
                relevance_score += 10
            
            results.append({
                'profile': profile,
                'relevance_score': relevance_score
            })
        
        # 排序并返回
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        formatted_results = []
        for item in results[:limit]:
            profile = item['profile']
            formatted_results.append({
                'profile_id': str(profile.id),
                'name': profile.name,
                'company_name': profile.company_name,
                'profile_type': profile.profile_type,
                'status': profile.status,
                'credit_score': profile.credit_score,
                'quality_score': profile.quality_score,
                'relevance_score': item['relevance_score']
            })
        
        return formatted_results


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