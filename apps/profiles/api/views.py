from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q

from .models import Profile, ProfileEventAssociation
from .serializers import (
    ProfileSerializer, ProfileSimpleSerializer, ProfileEventAssociationSerializer, 
    ProfileListSerializer
)


class ProfileViewSet(viewsets.ModelViewSet):
    """关联方档案视图集"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['profile_type', 'rating', 'created_by']
    search_fields = ['name', 'contact_info', 'cooperation_history']
    ordering_fields = ['-created_at', 'created_at', '-rating', 'rating']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return ProfileListSerializer
        return ProfileSerializer
    
    def get_queryset(self):
        """获取档案查询集"""
        return Profile.objects.select_related('created_by').prefetch_related('event_associations')
    
    def perform_create(self, serializer):
        """创建档案时的额外处理"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """获取档案关联的活动列表"""
        profile = self.get_object()
        associations = profile.event_associations.select_related('event')
        
        events_data = []
        for assoc in associations:
            events_data.append({
                'event_id': str(assoc.event.id),
                'event_name': assoc.event.name,
                'event_date': assoc.event.start_date.isoformat() if assoc.event.start_date else None,
                'role': assoc.role,
                'created_at': assoc.created_at.isoformat()
            })
        
        return Response(events_data)
    
    @action(detail=True, methods=['post'])
    def add_to_event(self, request, pk=None):
        """将档案添加到活动"""
        profile = self.get_object()
        event_id = request.data.get('event_id')
        event_role = request.data.get('role', '')
        
        if not event_id:
            return Response(
                {'message': '需要指定event_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.events.models import Event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {'message': '活动不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查是否已经关联
        if profile.event_associations.filter(event=event).exists():
            return Response(
                {'message': '档案已经关联到该活动'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建关联
        ProfileEventAssociation.objects.create(
            profile=profile,
            event=event,
            role=event_role
        )
        
        return Response({'message': '档案已添加到活动'})
    
    @action(detail=True, methods=['post'])
    def remove_from_event(self, request, pk=None):
        """将档案从活动中移除"""
        profile = self.get_object()
        event_id = request.data.get('event_id')
        
        if not event_id:
            return Response(
                {'message': '需要指定event_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            association = profile.event_associations.get(event_id=event_id)
            association.delete()
        except ProfileEventAssociation.DoesNotExist:
            return Response(
                {'message': '关联不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({'message': '档案已从活动移除'})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """高级档案搜索"""
        query = request.query_params.get('q', '')
        profile_type = request.query_params.get('profile_type')
        
        queryset = Profile.objects.filter(is_verified=True)
        
        # 构建搜索条件
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(contact_info__icontains=query) |
                Q(cooperation_history__icontains=query) |
                Q(tags__contains=query)
            )
        
        if profile_type:
            queryset = queryset.filter(profile_type=profile_type)
        
        # 按评分排序
        queryset = queryset.order_by('-rating', '-created_at')
        
        serializer = ProfileSimpleSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def increment_popularity(self, request, pk=None):
        """增加档案流行度（用户查看时调用）"""
        profile = self.get_object()
        profile.rating = min(5, profile.rating + 1) if profile.rating else 1
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)