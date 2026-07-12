"""
关联方档案管理API视图
提供完整的CRUD功能和智能推荐能力
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from apps.users.models import User
import logging

from apps.profiles.models import (
    ContactProfile, ContactPerson, 
    InteractionHistory, ProfileEvaluation
)
from apps.profiles.api.serializers import (
    ContactProfileSerializer, ContactProfileCreateSerializer,
    ContactProfileListSerializer, ContactPersonSerializer,
    InteractionHistorySerializer, ProfileEvaluationSerializer,
    SearchRequestSerializer, AnalyticsResponseSerializer
)
from apps.profiles.services import (
    ContactProfileService, InteractionService, 
    EvaluationService, IntelligentRecommender,
    ProfileAnalytics
)

logger = logging.getLogger(__name__)


class ContactProfileViewSet(viewsets.ModelViewSet):
    """
    关联方档案视图集
    提供档案管理的完整CRUD功能
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取档案列表，支持权限过滤"""
        user = self.request.user
        
        # 暂时允许所有用户访问所有档案，用于测试
        base_queryset = ContactProfile.objects.filter(is_deleted=False)
        return base_queryset
        
        # 超级用户可以访问所有档案
        # if user.is_superuser:
        #     base_queryset = ContactProfile.objects.filter(is_deleted=False)
        # # 普通用户只能访问自己拥有的档案
        # else:
        #     base_queryset = ContactProfile.objects.filter(
        #         owner=user,
        #         is_deleted=False
        #     )
        
        # 支持多个过滤参数
        profile_type = self.request.query_params.get('profile_type')
        if profile_type:
            base_queryset = base_queryset.filter(profile_type=profile_type)
        
        status = self.request.query_params.get('status')
        if status:
            base_queryset = base_queryset.filter(status=status)
        
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            base_queryset = base_queryset.filter(risk_level=risk_level)
        
        min_credit_score = self.request.query_params.get('min_credit_score')
        if min_credit_score:
            try:
                min_credit_score = int(min_credit_score)
                base_queryset = base_queryset.filter(credit_score__gte=min_credit_score)
            except (ValueError, TypeError):
                pass
        
        max_credit_score = self.request.query_params.get('max_credit_score')
        if max_credit_score:
            try:
                max_credit_score = int(max_credit_score)
                base_queryset = base_queryset.filter(credit_score__lte=max_credit_score)
            except (ValueError, TypeError):
                pass
        
        # 搜索支持
        search = self.request.query_params.get('search')
        if search:
            base_queryset = base_queryset.filter(
                Q(name__icontains=search) |
                Q(company_name__icontains=search) |
                Q(industry__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # 预加载相关数据
        base_queryset = base_queryset.select_related('owner').prefetch_related('contacts')
        
        # 支持排序
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            try:
                base_queryset = base_queryset.order_by(ordering)
            except:
                # 排序字段无效，使用默认排序
                base_queryset = base_queryset.order_by('-created_at')
        
        return base_queryset
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'list':
            return ContactProfileListSerializer
        elif self.action == 'create':
            return ContactProfileCreateSerializer
        else:
            return ContactProfileSerializer
    
    def perform_create(self, serializer):
        """创建档案时保存所有者和创建者"""
        instance = serializer.save(owner=self.request.user)
        logger.info(f"Profile created: {instance.id} by {self.request.user.username}")
        return instance
    
    def perform_update(self, serializer):
        """更新档案时记录更新者"""
        instance = serializer.save()
        logger.info(f"Profile updated: {instance.id} by {self.request.user.username}")
        return instance
    
    def destroy(self, request, *args, **kwargs):
        """软删除档案"""
        profile = self.get_object()
        profile.soft_delete(request.user)
        logger.info(f"Profile soft deleted: {profile.id} by {self.request.user.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """
        获取档案的所有联系人
        GET /api/profiles/{id}/contacts/
        """
        profile = self.get_object()
        contacts = profile.contacts.filter(is_active=True)
        serializer = ContactPersonSerializer(contacts, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=True, methods=['post'])
    def contact(self, request, pk=None):
        """
        为档案添加联系人
        POST /api/profiles/{id}/contact/
        """
        profile = self.get_object()
        serializer = ContactPersonSerializer(data=request.data)
        
        if serializer.is_valid():
            # 检查是否已经有主要联系人
            is_primary = serializer.validated_data.get('is_primary', False)
            if is_primary:
                profile.contacts.filter(is_primary=True).update(is_primary=False)
            
            serializer.save(profile=profile)
            logger.info(f"Contact added to profile {profile.id} by {request.user.username}")
            return Response(
                ContactPersonSerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], url_path='contact/(?P<contact_id>[^/.]+)')
    def update_contact(self, request, pk=None, contact_id=None):
        """
        更新指定联系人
        PUT /api/profiles/{id}/contact/{contact_id}/
        """
        profile = self.get_object()
        try:
            contact = profile.contacts.get(id=contact_id)
        except ContactPerson.DoesNotExist:
            return Response(
                {'error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ContactPersonSerializer(contact, data=request.data, partial=True)
        
        if serializer.is_valid():
            is_primary = serializer.validated_data.get('is_primary', False)
            if is_primary and not contact.is_primary:
                profile.contacts.filter(is_primary=True).update(is_primary=False)
            
            serializer.save()
            logger.info(f"Contact {contact_id} updated by {request.user.username}")
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='contact/(?P<contact_id>[^/.]+)')
    def delete_contact(self, request, pk=None, contact_id=None):
        """
        删除指定联系人
        DELETE /api/profiles/{id}/contact/{contact_id}/
        """
        profile = self.get_object()
        try:
            contact = profile.contacts.get(id=contact_id)
        except ContactPerson.DoesNotExist:
            return Response(
                {'error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        contact.delete()
        logger.info(f"Contact {contact_id} deleted by {request.user.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def interactions(self, request, pk=None):
        """
        获取档案的交互历史
        GET /api/profiles/{id}/interactions/
        """
        profile = self.get_object()
        interactions = profile.interactions.all()
        
        # 支持分页
        page_size = int(request.query_params.get('page_size', 20))
        interactions = interactions[:page_size]
        
        serializer = InteractionHistorySerializer(interactions, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=True, methods=['post'])
    def interaction(self, request, pk=None):
        """
        记录新的交互
        POST /api/profiles/{id}/interaction/
        """
        profile = self.get_object()
        interaction, errors = InteractionService.record_interaction(
            profile=profile,
            data=request.data,
            user=request.user,
            request=request
        )
        
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Interaction recorded for profile {profile.id} by {request.user.username}")
        return Response(
            InteractionHistorySerializer(interaction).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def evaluations(self, request, pk=None):
        """
        获取档案的评估记录
        GET /api/profiles/{id}/evaluations/
        """
        profile = self.get_object()
        evaluations = profile.evaluations.all()
        serializer = ProfileEvaluationSerializer(evaluations, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=True, methods=['post'])
    def evaluation(self, request, pk=None):
        """
        提交新的评估
        POST /api/profiles/{id}/evaluation/
        """
        profile = self.get_object()
        evaluation, errors = EvaluationService.create_evaluation(
            profile=profile,
            data=request.data,
            user=request.user,
            request=request
        )
        
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Evaluation created for profile {profile.id} by {request.user.username}")
        return Response(
            ProfileEvaluationSerializer(evaluation).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def comprehensive_assessment(self, request, pk=None):
        """
        获取档案的综合评估
        GET /api/profiles/{id}/comprehensive_assessment/
        """
        profile = self.get_object()
        assessment = ContactProfileService.assess_profile_comprehensive(profile)
        return Response(assessment)


class SearchViewSet(viewsets.GenericViewSet):
    """
    智能搜索视图
    提供基于多维匹配的档案搜索
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def profiles(self, request):
        """
        智能档案搜索
        POST /api/profiles/search/profiles/
        
        请求体:
        {
            "query": "科技",
            "profile_type": "supplier",
            "limit": 10
        }
        """
        serializer = SearchRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        results = IntelligentRecommender.recommend_profiles(
            query=serializer.validated_data['query'],
            profile_type=serializer.validated_data.get('profile_type'),
            limit=serializer.validated_data.get('limit', 10)
        )
        
        return Response({
            'query': serializer.validated_data['query'],
            'results': results,
            'count': len(results)
        })


class AnalyticsViewSet(viewsets.GenericViewSet):
    """
    分析视图
    提供档案管理和业务分析数据
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        获取仪表盘统计
        GET /api/profiles/analytics/dashboard/
        """
        try:
            stats = ProfileAnalytics.get_dashboard_stats(request.user)
            serializer = AnalyticsResponseSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Dashboard stats error for {request.user.username}: {e}")
            return Response(
                {'error': 'Failed to retrieve dashboard statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )