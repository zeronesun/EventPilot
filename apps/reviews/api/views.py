from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q
from django.utils import timezone

from .models import Review
from .serializers import (
    ReviewSerializer, ReviewSimpleSerializer, ReviewUpdateSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    """复盘视图集"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['status', 'event']
    search_fields = ['title', 'goal_achievement', 'process_execution', 'successes']
    ordering_fields = ['-created_at', '-completed_at', 'created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return ReviewSimpleSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """获取复盘查询集"""
        return Review.objects.select_related('event', 'created_by')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成复盘"""
        review = self.get_object()
        
        if review.status == 'completed':
            return Response(
                {'message': '复盘已完成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if review.status != 'in_progress':
            return Response(
                {'message': '只能处理进行中状态的复盘'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.status = 'completed'
        review.completed_at = timezone.now()
        review.save()
        
        # 自动提取经验到知识库
        self._extract_to_knowledge(review)
        
        return Response({'message': '复盘已完成，相关经验已提取到知识库'})
    
    def _extract_to_knowledge(self, review):
        """提取复盘中的经验到知识库"""
        from .models import KnowledgeEntry
        
        # 提取成功经验
        if review.successes:
            KnowledgeEntry.objects.create(
                entry_type='best_practice',
                title=f"{review.event.name}成功经验",
                content=review.successes,
                related_events=[review.event.id],
                event_type=review.event.type,
                created_by=review.created_by
            )
        
        # 提取待改进项
        if review.improvements:
            KnowledgeEntry.objects.create(
                entry_type='issue',
                title=f"{review.event.name}需改进项",
                content=review.improvements,
                related_events=[review.event.id],
                event_type=review.event.type,
                tags=['improvement', review.event.type],
                created_by=review.created_by
            )
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """获取复盘仪表盘数据"""
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
        
        return Response({
            'total': total_reviews,
            'completed': completed_reviews,
            'completion_rate': round(completed_reviews / total_reviews * 100, 1) if total_reviews > 0 else 0,
            'by_type': by_type
        })
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """获取复盘洞察分析"""
        review = self.get_object()
        
        insights = {
            'summary': {
                'title': review.title,
                'event_name': review.event.name,
                'status': review.status,
                'completion_rate': self._calculate_completion_rate(review)
            },
            'dimensions': {
                'goal_achievement': self._analyze_text(review.goal_achievement),
                'process_execution': self._analyze_text(review.process_execution),
                'cost_control': self._analyze_text(review.cost_control),
                'customer_feedback': self._analyze_text(review.customer_feedback),
                'team_collaboration': self._analyze_text(review.team_collaboration)
            },
            'action_items': self._extract_action_items(review.action_items),
            'improvements': self._extract_improvements(review.improvements)
        }
        
        return Response(insights)
    
    def _calculate_completion_rate(self, review):
        """计算完成率（基于各个维度的完整性）"""
        dimensions = [
            review.goal_achievement, review.process_execution, review.cost_control,
            review.customer_feedback, review.team_collaboration
        ]
        completed = sum(1 for dim in dimensions if dim and dim.strip())
        total = len(dimensions)
        return round(completed / total * 100, 1) if total > 0 else 0
    
    def _analyze_text(self, text):
        """分析文本内容（简单实现）"""
        if not text or not text.strip():
            return {'status': 'empty', 'word_count': 0}
        
        words = text.split()
        return {
            'status': 'filled',
            'word_count': len(words),
            'has_content': True
        }
    
    def _extract_action_items(self, text):
        """提取行动项（简单实现）"""
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
    
    def _extract_improvements(self, text):
        """提取改进点（简单实现）"""
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