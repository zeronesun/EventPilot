from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone

from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate, ChecklistInstance, ChecklistItem
from .serializers import (
    ChecklistTemplateSerializer, ChecklistItemTemplateSerializer, 
    ChecklistInstanceSerializer, ChecklistItemSerializer, ChecklistItemUpdateSerializer
)


class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """核验清单模板视图集"""
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['event_types', 'is_default']
    search_fields = ['name', 'description']
    
    def perform_create(self, serializer):
        """创建模板时的额外处理"""
        serializer.save(created_by=self.request.user)


class ChecklistItemTemplateViewSet(viewsets.ModelViewSet):
    """核验清单项模板视图集"""
    serializer_class = ChecklistItemTemplateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['template', 'required']
    
    def get_queryset(self):
        """获取清单项模板查询集"""
        template_id = self.request.query_params.get('template')
        queryset = ChecklistItemTemplate.objects.all()
        
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        return queryset


class ChecklistInstanceViewSet(viewsets.ModelViewSet):
    """核验清单实例视图集"""
    serializer_class = ChecklistInstanceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['event', 'status', 'template']
    
    def get_queryset(self):
        """获取清单实例查询集"""
        return ChecklistInstance.objects.select_related('template', 'event').prefetch_related('items')
    
    @action(detail=True, methods=['post'])
    def instantiate_from_template(self, request, template_id):
        """从模板创建清单实例"""
        try:
            template = ChecklistTemplate.objects.get(id=template_id)
        except ChecklistTemplate.DoesNotExist:
            return Response(
                {'message': '模板不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        event_id = request.data.get('event')
        if not event_id:
            return Response(
                {'message': '需要指定活动ID'},
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
        
        # 创建清单实例
        instance = ChecklistInstance.objects.create(
            event=event,
            template=template,
            name=f"{event.name} - {template.name}"
        )
        
        # 复制模板项
        template_items = template.items.all()
        for template_item in template_items:
            ChecklistItem.objects.create(
                instance=instance,
                template_item=template_item,
                title=template_item.title,
                status='pending'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChecklistItemViewSet(viewsets.ModelViewSet):
    """核验清单项视图集"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action in ['update', 'partial_update']:
            return ChecklistItemUpdateSerializer
        return ChecklistItemSerializer
    
    def get_queryset(self):
        """获取清单项查询集"""
        instance_id = self.request.query_params.get('instance')
        queryset = ChecklistItem.objects.select_related('checked_by', 'template_item')
        
        if instance_id:
            queryset = queryset.filter(instance_id=instance_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def check(self, request, pk=None):
        """执行核验操作"""
        item = self.get_object()
        
        serializer = ChecklistItemUpdateSerializer(
            item, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # 如果状态是完成，设置检查人和检查时间
        if 'status' in serializer.validated_data and serializer.validated_data['status'] in ['passed', 'failed']:
            serializer.validated_data['checked_by'] = request.user
            serializer.validated_data['checked_at'] = timezone.now()
        
        serializer.save()
        
        # 检查是否所有项都已完成，更新实例状态
        self._update_instance_status(item.instance)
        
        return Response(serializer.data)
    
    def _update_instance_status(self, instance):
        """更新清单实例状态"""
        all_items = instance.items.count()
        completed_items = instance.items.filter(
            status__in=['passed', 'failed', 'skipped']
        ).count()
        
        if all_items == completed_items and all_items > 0:
            instance.status = 'completed'
            instance.completed_at = timezone.now()
            instance.save()
        
        # 重置离线同步标记
        item.offline_pending = False
        item.save()
    
    @action(detail=True, methods=['post'])
    def attachment(self, request, pk=None):
        """上传附件"""
        item = self.get_object()
        attachment_data = request.data.get('attachment')
        
        if not attachment_data:
            return Response(
                {'message': '需要提供attachment数据'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 这里可以处理文件上传逻辑
        # 暂时将附件信息添加到attachments字段
        if not item.attachments:
            item.attachments = []
        
        item.attachments.append(attachment_data)
        item.save()
        
        return Response({'message': '附件已添加'})


class ChecklistReportGenerator:
    """核验清单报告生成器"""
    
    @staticmethod
    def generate_report(instance_id):
        """生成核验报告"""
        try:
            instance = ChecklistInstance.objects.get(id=instance_id)
        except ChecklistInstance.DoesNotExist:
            return None
        
        # 统计
        all_items = instance.items.count()
        passed_items = instance.items.filter(status='passed').count()
        failed_items = instance.items.filter(status='failed').count()
        skipped_items = instance.items.filter(status='skipped').count()
        pending_items = instance.items.filter(status='pending').count()
        
        report = {
            'instance': {
                'id': instance.id,
                'name': instance.name,
                'event': instance.event.name,
                'completed_at': instance.completed_at.isoformat() if instance.completed_at else None
            },
            'summary': {
                'total': all_items,
                'passed': passed_items,
                'failed': failed_items,
                'skipped': skipped_items,
                'pending': pending_items,
                'completion_rate': round(passed_items / all_items * 100, 1) if all_items > 0 else 0
            },
            'items': []
        }
        
        # 详细项
        for item in instance.items.all():
            report['items'].append({
                'title': item.title,
                'status': item.status,
                'notes': item.notes,
                'checked_by': item.checked_by.username if item.checked_by else None,
                'checked_at': item.checked_at.isoformat() if item.checked_at else None
            })
        
        return report