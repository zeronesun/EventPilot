"""智能搜索引擎 - 基于规则的档案搜索系统"""

from typing import Dict, List, Optional


class IntelligentRecommender:
    """
    智能搜索引擎 - 基于规则的档案搜索系统
    """
    
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


