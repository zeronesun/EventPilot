from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q, F

from .models import KnowledgeEntry
from .serializers import (
    KnowledgeEntrySerializer, KnowledgeEntryListSerializer, 
    KnowledgeEntryUpdateSerializer
)


class KnowledgeEntryViewSet(viewsets.ModelViewSet):
    """知识条目视图集"""
    serializer_class = KnowledgeEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['entry_type', 'category', 'is_public', 'is_verified']
    search_fields = ['title', 'content', 'category']
    ordering_fields = ['-created_at', '-popularity', 'created_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return KnowledgeEntryListSerializer
        elif self.action in ['update', 'partial_update']:
            return KnowledgeEntryUpdateSerializer
        return KnowledgeEntrySerializer
    
    def get_queryset(self):
        """获取知识条目查询集"""
        queryset = KnowledgeEntry.objects.select_related('created_by')
        
        # 只验证通过或创建者的条目，除非是管理员
        if not request.user.is_staff:
            queryset = queryset.filter(
                Q(is_verified=True) | Q(created_by=request.user)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建条目时的额外处理"""
        serializer.save(created_by=self.request.user)
        # 初始流行度为0，已在序列化器中处理
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """获取热门知识条目"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().filter(
            is_verified=True,
            popularity__gt=0
        ).order_by('-popularity')[:limit]
        
        serializer = KnowledgeEntryListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """获取推荐知识（基于相关活动）"""
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'message': '需要指定event_id参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取与指定事件相关的知识
        from apps.events.models import Event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {'message': '活动不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 查找相关活动类型和客户的经验/问题
        queryset = KnowledgeEntry.objects.filter(
            Q(related_events__contains=event_id) |
            Q(entry_type__in=['experience', 'best_practice']),
            is_verified=True
        ).distinct()
        
        # 按流行度排序
        queryset = queryset.order_by('-popularity', '-created_at')[:5]
        
        serializer = KnowledgeEntryListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """验证知识条目（管理员功能）"""
        if not request.user.is_staff:
            return Response(
                {'message': '需要管理员权限'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        entry = self.get_object()
        entry.is_verified = True
        entry.save()
        
        serializer = self.get_serializer(entry)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """增加查看次数"""
        entry = self.get_object()
        entry.popularity = F('popularity') + 1
        from django.db.models import F
        type(entry).objects.filter(id=entry.id).update(popularity=F('popularity') + 1)
        
        serializer = self.get_serializer(entry)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有分类"""
        categories = KnowledgeEntry.objects.filter(
            is_verified=True
        ).values_list('category', flat=True).distinct().exclude(
            category=''
        )
        
        return Response(list(categories))