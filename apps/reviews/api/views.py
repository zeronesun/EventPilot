from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apps.reviews.models import Review
from apps.reviews.services import ReviewService
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
        
        # 完成复盘并自动提取经验到知识库
        extracted_count = ReviewService.complete_review(review)
        
        return Response(
            {
                'message': '复盘已完成',
                'extracted_knowledge_entries': extracted_count
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """获取复盘仪表盘数据"""
        return Response(ReviewService.get_dashboard_data())
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """获取复盘洞察分析"""
        review = self.get_object()
        return Response(ReviewService.get_insights(review))
