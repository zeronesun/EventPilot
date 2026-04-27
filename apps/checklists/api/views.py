from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
from django.db.models import Q

from apps.checklists.models import ChecklistTemplate, ChecklistItemTemplate, ChecklistInstance, ChecklistItem
from apps.checklists.services.checklist_service import ChecklistService
from .serializers import (
    ChecklistTemplateSerializer, ChecklistTemplateDetailSerializer,
    ChecklistItemTemplateSerializer, ChecklistInstanceSerializer, 
    ChecklistInstanceDetailSerializer, ChecklistItemSerializer, 
    ChecklistItemUpdateSerializer, ChecklistReportSerializer, ChecklistSummarySerializer
)
class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """核验清单模板视图集"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['checklist_type', 'status', 'is_default', 'event_types']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'name']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action in ['retrieve', 'list']:
            return ChecklistTemplateDetailSerializer
        return ChecklistTemplateSerializer
    
    def get_queryset(self):
        """获取模板查询集"""
        queryset = ChecklistService.get_templates_filter(
            self.request.user, 
            self.request.query_params
        )
        return queryset
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布模板"""
        template = self.get_object()
        
        if template.status == 'published':
            return Response(
                {'message': '模板已发布'},
                status=status.HTTP_200_OK
            )
        
        template.status = 'published'
        template.save()
        
        return Response({'message': '模板发布成功'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档模板"""
        template = self.get_object()
        
        if template.status == 'archived':
            return Response(
                {'message': '模板已归档'},
                status=status.HTTP_200_OK
            )
        
        template.status = 'archived'
        template.save()
        
        return Response({'message': '模板归档成功'})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取模板统计信息"""
        template = self.get_object()
        statistics = ChecklistService.get_template_statistics(template)
        return Response(statistics)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """复制模板"""
        template = self.get_object()
        
        # 创建新模板
        new_template_data = {
            'name': f"{template.name} (副本)",
            'description': template.description,
            'checklist_type': template.checklist_type,
            'event_types': template.event_types,
            'version': '1.0.0',
            'status': 'draft',
            'tags': template.tags,
            'metadata': template.metadata,
        }
        
        new_template, errors = ChecklistService.create_template(
            new_template_data, 
            request.user
        )
        
        if errors:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 复制模板项
        items_data = []
        for item in template.items.all():
            items_data.append({
                'title': item.title,
                'description': item.description,
                'required': item.required,
                'order': item.order,
                'weight': item.weight,
                'status': item.status,
                'metadata': item.metadata,
            })
        
        ChecklistService._create_template_items(new_template, items_data)
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
class ChecklistItemTemplateViewSet(viewsets.ModelViewSet):
    """核验清单项模板视图集"""
    serializer_class = ChecklistItemTemplateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['template', 'required', 'status']
    
    def get_queryset(self):
        """获取清单项模板查询集"""
        template_id = self.request.query_params.get('template')
        queryset = ChecklistItemTemplate.objects.select_related('template')
        
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        return queryset.order_by('order')
class ChecklistInstanceViewSet(viewsets.ModelViewSet):
    """核验清单实例视图集"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['event', 'status', 'template']
    search_fields = ['name', 'event__name']
    ordering_fields = ['created_at', 'updated_at', 'name']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action in ['retrieve']:
            return ChecklistInstanceDetailSerializer
        return ChecklistInstanceSerializer
    
    def get_queryset(self):
        """获取清单实例查询集"""
        queryset = ChecklistService.get_instances_filter(
            self.request.user,
            self.request.query_params
        )
        return queryset
    
    
    def list(self, request, *args, **kwargs):
        """列出清单实例"""
        return super().list(request, *args, **kwargs)
    
    
    def instantiate_from_template(self, request):
        """从模板创建清单实例"""
        template_id = request.data.get('template_id') or request.data.get('template')
        event_id = request.data.get('event_id') or request.data.get('event')
        
        if not template_id:
            return Response(
                {'message': '需要指定模板ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not event_id:
            return Response(
                {'message': '需要指定活动ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建实例数据
        instance_data = {
            'event_id': event_id,
            'template_id': template_id,
            'name': request.data.get('name'),
            'metadata': request.data.get('metadata', {}),
        }
        
        success, instance, errors = ChecklistService.create_instance(instance_data, request.user)
        
        if not success:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST if errors else status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
    def complete(self, request, pk=None):
        """完成清单实例"""
        instance = self.get_object()
        
        success, errors = ChecklistService.complete_instance(instance, request.user)
        
        if not success:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    
    def cancel(self, request, pk=None):
        """取消清单实例"""
        instance = self.get_object()
        reason = request.data.get('reason', '')
        
        success, errors = ChecklistService.cancel_instance(instance, request.user, reason)
        
        if not success:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    
    def progress(self, request, pk=None):
        """获取实例进度"""
        instance = self.get_object()
        progress = ChecklistService.get_instance_progress(instance)
        return Response(progress)
    
    
    def report(self, request, pk=None):
        """导出实例报告"""
        instance = self.get_object()
        report = ChecklistService.export_instance_report(str(instance.id))
        
        if not report:
            return Response(
                {'message': '生成报告失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = ChecklistReportSerializer(data=report)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
class ChecklistItemViewSet(viewsets.ModelViewSet):
    """核验清单项视图集"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['instance', 'status', 'required']
    search_fields = ['title', 'notes']
    ordering_fields = ['order', 'created_at', 'checked_at']
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action in ['update', 'partial_update', 'check']:
            return ChecklistItemUpdateSerializer
        return ChecklistItemSerializer
    
    def get_queryset(self):
        """获取清单项查询集"""
        instance_id = self.request.query_params.get('instance')
        queryset = ChecklistItem.objects.select_related('checked_by', 'template_item', 'instance')
        
        if instance_id:
            queryset = queryset.filter(instance_id=instance_id)
        
        return queryset.order_by('order')
    
    
    def check(self, request, pk=None):
        """执行核验操作"""
        item = self.get_object()
        
        # 获取核验数据
        item_status = request.data.get('status', 'pending')
        notes = request.data.get('notes', '')
        attachments = request.data.get('attachments')
        location = request.data.get('location')
        
        # 更新清单项状态
        success, errors = ChecklistService.update_item_status(
            str(item.id),
            item_status,
            request.user,
            notes,
            attachments,
            location
        )
        
        if not success:
            return Response(
                {'errors': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 重新获取更新后的项
        updated_item = ChecklistItem.objects.get(id=item.id)
        serializer = ChecklistItemSerializer(updated_item)
        return Response(serializer.data)
    
    
    def attachment(self, request, pk=None):
        """上传附件"""
        item = self.get_object()
        attachment_data = request.data.get('attachment')
        
        if not attachment_data:
            return Response(
                {'message': '需要提供attachment数据'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 添加附件
        if not item.attachments:
            item.attachments = []
        
        item.attachments.append(attachment_data)
        item.save()
        
        return Response({'message': '附件已添加', 'attachments': item.attachments})
    
    
    def bulk_update(self, request):
        """批量更新清单项状态"""
        item_ids = request.data.get('item_ids', [])
        item_status = request.data.get('status', 'pending')
        notes = request.data.get('notes', '')
        
        if not item_ids:
            return Response(
                {'message': '需要提供要更新的清单项ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        for item_id in item_ids:
            success, item_errors = ChecklistService.update_item_status(
                item_id,
                item_status,
                request.user,
                notes
            )
            
            if success:
                results.append(item_id)
            else:
                errors.append({'item_id': item_id, 'errors': item_errors})
        
        return Response({
            'message': f'成功更新 {len(results)} 个清单项',
            'success_count': len(results),
            'error_count': len(errors),
            'errors': errors
        })
    
    
    def by_instance(self, request):
        """按实例获取清单项"""
        instance_id = request.query_params.get('instance')
        
        if not instance_id:
            return Response(
                {'message': '需要指定instance参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = ChecklistItem.objects.filter(instance_id=instance_id).order_by('order')
        serializer = ChecklistItemSerializer(items, many=True)
        return Response(serializer.data)
class ChecklistReportGenerator:
    """核验清单报告生成器"""
    
    @staticmethod
    
    def generate_summary(event_id):
        """生成活动清单摘要"""
        summary = ChecklistService.get_checklist_summary(event_id)
        serializer = ChecklistSummarySerializer(data=summary)
        serializer.is_valid(raise_exception=True)
        return serializer.data
    
    @staticmethod
    
    def generate_report(instance_id):
        """生成实例报告"""
        report = ChecklistService.export_instance_report(instance_id)
        if report:
            serializer = ChecklistReportSerializer(data=report)
            serializer.is_valid(raise_exception=True)
            return serializer.data
        return None