from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q, F
from django.core.cache import cache
from django.utils import timezone

from apps.events.models import Event, BudgetItem, EventParticipant, EventTemplate
from apps.events.services.event_service import EventService
from .serializers import (
    EventSerializer, EventListSerializer, EventCreateSerializer,
    EventUpdateSerializer, EventStatisticsSerializer, EventRiskAssessmentSerializer,
    EventParticipantSerializer, BudgetItemSerializer, EventTemplateSerializer
)
from api.exceptions import custom_exception_handler


class EventViewSet(viewsets.ModelViewSet):
    """活动视图集 - 完整CRUD功能"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'type', 'owner']
    search_fields = ['name', 'description', 'client']
    ordering_fields = ['created_at', 'start_date', 'name', '-created_at']
    
    def get_queryset(self):
        """获取活动查询集"""
        user = self.request.user
        
        if user.is_superuser:
            queryset = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items', 'participants')
        else:
            queryset = Event.objects.select_related('owner').prefetch_related('tasks', 'budget_items', 'participants').filter(
                Q(owner=user) | Q(participants__user=user)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return EventListSerializer
        elif self.action == 'create':
            return EventCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EventUpdateSerializer
        return EventSerializer
    
    def list(self, request, *args, **kwargs):
        """活动列表"""
        try:
            queryset = self.get_queryset()
            
            # 应用service层的过滤
            filters = {}
            if 'status' in request.query_params:
                filters['status'] = request.query_params['status']
            if 'type' in request.query_params:
                filters['type'] = request.query_params['type']
            if 'search' in request.query_params:
                filters['search'] = request.query_params['search']
            if 'start_date_from' in request.query_params:
                filters['start_date_from'] = request.query_params['start_date_from']
            if 'start_date_to' in request.query_params:
                filters['start_date_to'] = request.query_params['start_date_to']
            
            if filters:
                queryset = EventService.get_events_filter(request.user, filters)
            
            # 分页
            from rest_framework.pagination import PageNumberPagination
            paginator = PageNumberPagination()
            paginator.page_size = request.query_params.get('page_size', 20)
            result_page = paginator.paginate_queryset(queryset, request)
            
            serializer = self.get_serializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取活动列表失败: {e}")
            return Response(
                {'error': {'code': 'LIST_ERROR', 'message': '获取活动列表失败'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """创建活动"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 使用service层创建
            data = serializer.validated_data
            budget_items = data.pop('budget_items', [])
            
            event, errors = EventService.create_event(
                data=data,
                owner=request.user,
                request=request
            )
            
            if errors:
                return Response(
                    {'error': {'code': 'CREATION_ERROR', 'message': errors}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 序列化响应
            response_serializer = EventSerializer(event)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"创建活动失败: {e}")
            return Response(
                {'error': {'code': 'CREATION_ERROR', 'message': str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, *args, **kwargs):
        """获取活动详情"""
        try:
            instance = self.get_object()
            
            # 检查缓存
            cache_key = f'event:{instance.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            serializer = self.get_serializer(instance)
            data = serializer.data
            
            # 缓存5分钟
            cache.set(cache_key, data, 300)
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"获取活动详情失败: {e}")
            return Response(
                {'error': {'code': 'RETRIEVE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """更新活动"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # 使用service层更新
            data = serializer.validated_data
            budget_items = data.pop('budget_items', None)
            
            update_data = {**data}
            if budget_items is not None:
                update_data['budget_items'] = budget_items
            
            success, errors = EventService.update_event(
                event=instance,
                update_data=update_data,
                request=request
            )
            
            if not success:
                return Response(
                    {'error': {'code': 'UPDATE_ERROR', 'message': errors}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 重新获取并序列化
            instance.refresh_from_db()
            response_serializer = EventSerializer(instance)
            
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"更新活动失败: {e}")
            return Response(
                {'error': {'code': 'UPDATE_ERROR', 'message': str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """删除活动"""
        try:
            instance = self.get_object()
            
            # 默认软删除
            soft_delete = request.query_params.get('hard', 'false').lower() == 'false'
            
            success, errors = EventService.delete_event(
                event=instance,
                soft_delete=soft_delete,
                request=request
            )
            
            if not success:
                return Response(
                    {'error': {'code': 'DELETE_ERROR', 'message': errors}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {'message': '活动删除成功'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"删除活动失败: {e}")
            return Response(
                {'error': {'code': 'DELETE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取活动统计数据"""
        try:
            event = self.get_object()
            
            # 检查缓存
            cache_key = f'event:{event.id}:statistics'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            # 获取统计数据
            stats = EventService.get_event_statistics(event)
            
            # 验证数据
            serializer = EventStatisticsSerializer(data=stats)
            if not serializer.is_valid():
                return Response(
                    {'error': {'code': 'STATISTICS_ERROR', 'message': '统计数据格式错误'}},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 缓存10分钟
            cache.set(cache_key, stats, 600)
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"获取活动统计失败: {e}")
            return Response(
                {'error': {'code': 'STATISTICS_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def risk(self, request, pk=None):
        """获取活动风险评估"""
        try:
            event = self.get_object()
            
            # 检查缓存
            cache_key = f'event:{event.id}:risk'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            # 获取风险评估
            risk = EventService.assess_event_risk(event)
            
            # 验证数据
            serializer = EventRiskAssessmentSerializer(data=risk)
            if not serializer.is_valid():
                return Response(
                    {'error': {'code': 'RISK_ASSESSMENT_ERROR', 'message': '风险评估数据格式错误'}},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 缓存15分钟
            cache.set(cache_key, risk, 900)
            
            return Response(risk)
            
        except Exception as e:
            logger.error(f"活动风险评估失败: {e}")
            return Response(
                {'error': {'code': 'RISK_ASSESSMENT_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """标记活动为完成"""
        try:
            event = self.get_object()
            success, errors = EventService.complete_event(event, request=request)
            
            if not success:
                return Response(
                    {'error': {'code': 'COMPLETE_ERROR', 'message': errors}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({'message': '活动已完成'})
            
        except Exception as e:
            logger.error(f"完成活动失败: {e}")
            return Response(
                {'error': {'code': 'COMPLETE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """变更活动状态"""
        try:
            event = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': {'code': 'VALIDATION_ERROR', 'message': '状态参数不能为空'}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success, errors = EventService.change_event_status(event, new_status, request=request)
            
            if not success:
                return Response(
                    {'error': {'code': 'STATUS_CHANGE_ERROR', 'message': errors}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({'message': '状态已变更', 'new_status': new_status})
            
        except Exception as e:
            logger.error(f"变更活动状态失败: {e}")
            return Response(
                {'error': {'code': 'STATUS_CHANGE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get', 'post', 'delete'])
    def participants(self, request, pk=None):
        """管理活动参与者"""
        try:
            event = self.get_object()
            
            if request.method == 'GET':
                # 获取参与者列表
                participants = EventParticipant.objects.filter(event=event, active=True)
                serializer = EventParticipantSerializer(participants, many=True)
                return Response(serializer.data)
            
            elif request.method == 'POST':
                # 添加参与者
                user_id = request.data.get('user_id')
                role = request.data.get('role', 'executor')
                
                if not user_id:
                    return Response(
                        {'error': {'code': 'VALIDATION_ERROR', 'message': '用户ID不能为空'}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 检查用户是否存在
                from apps.users.models import User
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response(
                        {'error': {'code': 'VALIDATION_ERROR', 'message': '用户不存在'}},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # 创建参与者
                participant, created = EventParticipant.objects.get_or_create(
                    event=event,
                    user=user,
                    defaults={'role': role}
                )
                
                if not created:
                    participant.active = True
                    participant.role = role
                    participant.save()
                
                serializer = EventParticipantSerializer(participant)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            elif request.method == 'DELETE':
                # 移除参与者
                user_id = request.data.get('user_id')
                
                if not user_id:
                    return Response(
                        {'error': {'code': 'VALIDATION_ERROR', 'message': '用户ID不能为空'}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                participant = EventParticipant.objects.filter(event=event, user_id=user_id).first()
                if not participant:
                    return Response(
                        {'error': {'code': 'NOT_FOUND_ERROR', 'message': '参与者不存在'}},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                participant.active = False
                participant.save()
                
                return Response({'message': '参与者已移除'})
                
        except Exception as e:
            logger.error(f"管理参与者失败: {e}")
            return Response(
                {'error': {'code': 'PARTICIPANTS_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def template(self, request):
        """获取活动模板"""
        try:
            category = request.query_params.get('category')
            queryset = EventTemplate.objects.filter(is_active=True)
            
            if category:
                queryset = queryset.filter(category=category)
            
            serializer = EventTemplateSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"获取活动模板失败: {e}")
            return Response(
                {'error': {'code': 'TEMPLATE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """使用模板创建活动"""
        try:
            event = self.get_object()
            template_id = request.data.get('template_id')
            
            if not template_id:
                return Response(
                    {'error': {'code': 'VALIDATION_ERROR', 'message': '模板ID不能为空'}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            template = EventTemplate.objects.filter(id=template_id, is_active=True).first()
            if not template:
                return Response(
                    {'error': {'code': 'NOT_FOUND_ERROR', 'message': '模板不存在或已禁用'}},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 应用模板
            template.usage_count += 1
            template.save()
            
            # 创建预算项
            if template.budget_templates:
                for budget_template in template.budget_templates:
                    BudgetItem.objects.create(
                        event=event,
                        category_name=budget_template.get('category_name', '未分类'),
                        name=budget_template['name'],
                        estimated_amount=budget_template.get('estimated_amount', 0),
                        actual_amount=0,
                        variance=budget_template.get('estimated_amount', 0),
                        status='pending'
                    )
            
            # 刷新预算
            EventService._refresh_event_budget(event)
            
            return Response({'message': '模板应用成功'})
            
        except Exception as e:
            logger.error(f"应用模板失败: {e}")
            return Response(
                {'error': {'code': 'TEMPLATE_ERROR', 'message': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BudgetItemViewSet(viewsets.ModelViewSet):
    """预算明细视图集"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取预算明细查询集"""
        event_id = self.request.query_params.get('event')
        queryset = BudgetItem.objects.all()
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建预算明细时的额外处理"""
        serializer.save()
        # 触发预算重新计算（可以优化为异步）
        self._update_event_budget(serializer.instance.event)
    
    def perform_update(self, serializer):
        """更新预算明细时的额外处理"""
        serializer.save()
        self._update_event_budget(serializer.instance.event)
    
    def _update_event_budget(self, event):
        """更新活动的预算汇总"""
        budget_items = event.budget_items.all()
        
        event.estimated_budget = sum(
            item.estimated_amount for item in budget_items
        )
        event.actual_budget = sum(
            item.actual_amount for item in budget_items
        )
        event.budget_variance = event.estimated_budget - event.actual_budget
        event.save()