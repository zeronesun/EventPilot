from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q, F
from django.contrib.auth import get_user_model

from apps.knowledge.models import KnowledgeEntry
from .serializers import (
    KnowledgeEntrySerializer, KnowledgeEntryListSerializer, 
    KnowledgeEntryUpdateSerializer
)

User = get_user_model()


class KnowledgeEntryViewSet(viewsets.ModelViewSet):
    """
    知识条目视图集
    """
    serializer_class = KnowledgeEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['entry_type', 'category', 'is_public', 'is_verified']
    search_fields = ['title', 'content', 'category']
    
    def get_serializer_class(self):
        """
        根据操作选择序列化器
        """
        if self.action == 'list':
            return KnowledgeEntryListSerializer
        elif self.action in ['update', 'partial_update']:
            return KnowledgeEntryUpdateSerializer
        return KnowledgeEntrySerializer
    
    def get_queryset(self):
        """
        获取知识条目查询集
        """
        queryset = KnowledgeEntry.objects.select_related('created_by')
        return queryset
    
    def perform_create(self, serializer):
        """
        创建条目时的额外处理
        """
        user = User.objects.first() if User.objects.exists() else None
        serializer.save(created_by=user, popularity=0)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        获取热门知识条目
        """
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().filter(
            is_verified=True,
            popularity__gt=0
        ).order_by('-popularity')[:limit]
        
        serializer = KnowledgeEntryListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        验证知识条目（管理员功能）
        """
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
        """
        增加查看次数
        """
        entry = self.get_object()
        KnowledgeEntry.objects.filter(id=entry.id).update(
            popularity=F('popularity') + 1
        )
        
        entry.refresh_from_db()
        serializer = self.get_serializer(entry)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        获取所有分类
        """
        categories = KnowledgeEntry.objects.filter(
            is_verified=True
        ).values_list('category', flat=True).distinct().exclude(
            category=''
        )
        
        return Response(list(categories))