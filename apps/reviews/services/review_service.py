"""复盘服务层 - 复盘业务逻辑"""

from typing import Dict, List, Any
from django.utils import timezone


class ReviewService:
    """复盘服务层 - 处理复盘业务逻辑"""

    @staticmethod
    def complete_review(review) -> int:
        """
        完成复盘，并自动提取经验到知识库

        Returns:
            int: 创建的知识条目数量
        """
        review.status = 'completed'
        review.completed_at = timezone.now()
        review.save()

        # 自动提取经验到知识库
        return ReviewService._extract_to_knowledge(review)

    @staticmethod
    def _extract_to_knowledge(review) -> int:
        """
        提取复盘中的经验到知识库

        Returns:
            int: 创建的知识条目数量
        """
        from apps.knowledge.models import KnowledgeEntry

        extracted_count = 0

        # 提取成功经验
        if review.successes:
            KnowledgeEntry.objects.create(
                entry_type='best_practice',
                title=f"{review.event.name}成功经验",
                content=review.successes,
                related_events=[str(review.event.id)],
                tags=[review.event.type],
                created_by=review.created_by
            )
            extracted_count += 1

        # 提取待改进项
        if review.improvements:
            KnowledgeEntry.objects.create(
                entry_type='issue',
                title=f"{review.event.name}需改进项",
                content=review.improvements,
                related_events=[str(review.event.id)],
                tags=['improvement', review.event.type],
                created_by=review.created_by
            )
            extracted_count += 1

        return extracted_count

    @staticmethod
    def get_dashboard_data():
        """
        获取复盘仪表盘数据
        """
        from apps.reviews.models import Review

        queryset = Review.objects.select_related('event').prefetch_related('event__tasks', 'event__budget_items')

        total_reviews = queryset.count()
        completed_reviews = queryset.filter(status='completed').count()

        # 按活动类型统计
        by_type = {}
        for review in queryset:
            type_key = review.event.type
            if type_key not in by_type:
                by_type[type_key] = 0
            by_type[type_key] += 1

        return {
            'total': total_reviews,
            'completed': completed_reviews,
            'completion_rate': round(completed_reviews / total_reviews * 100, 1) if total_reviews > 0 else 0,
            'by_type': by_type
        }

    @staticmethod
    def get_insights(review) -> Dict[str, Any]:
        """
        获取复盘洞察分析
        """
        insights = {
            'summary': {
                'title': review.title,
                'event_name': review.event.name,
                'status': review.status,
                'completion_rate': ReviewService._calculate_completion_rate(review)
            },
            'dimensions': {
                'goal_achievement': ReviewService._analyze_text(review.goal_achievement),
                'process_execution': ReviewService._analyze_text(review.process_execution),
                'cost_control': ReviewService._analyze_text(review.cost_control),
                'customer_feedback': ReviewService._analyze_text(review.customer_feedback),
                'team_collaboration': ReviewService._analyze_text(review.team_collaboration)
            },
            'action_items': ReviewService._extract_action_items(review.action_items),
            'improvements': ReviewService._extract_improvements(review.improvements)
        }
        return insights

    @staticmethod
    def _calculate_completion_rate(review) -> float:
        """
        计算完成率（基于各个维度的完整性）
        """
        dimensions = [
            review.goal_achievement, review.process_execution, review.cost_control,
            review.customer_feedback, review.team_collaboration
        ]
        completed = sum(1 for dim in dimensions if dim and dim.strip())
        total = len(dimensions)
        return round(completed / total * 100, 1) if total > 0 else 0

    @staticmethod
    def _analyze_text(text) -> Dict[str, Any]:
        """
        分析文本内容（简单实现）
        """
        if not text or not text.strip():
            return {'status': 'empty', 'word_count': 0}

        words = text.split()
        return {
            'status': 'filled',
            'word_count': len(words),
            'has_content': True
        }

    @staticmethod
    def _extract_action_items(text) -> List[str]:
        """
        提取行动项（简单实现）
        """
        if not text:
            return []

        # 简单的行分割提取
        lines = text.split('\n')
        action_items = []

        # 查找以"-"开头的行动项
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                action_items.append(line[1:].strip())

        return action_items

    @staticmethod
    def _extract_improvements(text) -> List[str]:
        """
        提取改进点（简单实现）
        """
        if not text:
            return []

        # 简单的关键词匹配
        improvement_keywords = ['需要改进', '应该', '建议']
        improvements = []

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in improvement_keywords):
                improvements.append(line)

        return improvements
