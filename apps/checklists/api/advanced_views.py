from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from apps.checklists.models import (
    ChecklistTemplate, ChecklistInstance, ChecklistItem,
    ChecklistVersion, ChecklistVersionComparison,
    ChecklistExport, ChecklistImport,
    ChecklistVerification, ChecklistVerificationDetail, ChecklistVerificationException
)
from apps.checklists.services import (
    checklist_version_service, checklist_export_service, checklist_verification_service
)
from .serializers import (
    ChecklistVersionSerializer, ChecklistVersionComparisonSerializer,
    ChecklistExportSerializer, ChecklistImportSerializer,
    ChecklistVerificationSerializer, ChecklistVerificationDetailSerializer,
    ChecklistVerificationExceptionSerializer
)
import logging

logger = logging.getLogger(__name__)


class ChecklistVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """清单版本视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChecklistVersionSerializer
    filterset_fields = ['template', 'instance', 'is_active', 'version_type']
    search_fields = ['changelog']
    ordering_fields = ['created_at', 'version_number']
    
    def get_queryset(self):
        """获取版本查询集"""
        queryset = ChecklistVersion.objects.select_related('created_by', 'template', 'instance')
        
        # 过滤参数
        template_id = self.request.query_params.get('template')
        instance_id = self.request.query_params.get('instance')
        
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        elif instance_id:
            queryset = queryset.filter(instance_id=instance_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取版本历史"""
        template_id = request.query_params.get('template')
        instance_id = request.query_params.get('instance')
        
        if not template_id and not instance_id:
            return Response(
                {'message': '需要提供template或instance参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        history = checklist_version_service.ChecklistVersionService.get_version_history(
            template_id=template_id,
            instance_id=instance_id
        )
        
        return Response(history)
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """比较两个版本"""
        from_version_id = request.data.get('from_version')
        to_version_id = request.data.get('to_version')
        
        if not from_version_id or not to_version_id:
            return Response(
                {'message': '需要提供from_version和to_version参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from_version = ChecklistVersion.objects.get(id=from_version_id)
            to_version = ChecklistVersion.objects.get(id=to_version_id)
        except ChecklistVersion.DoesNotExist:
            return Response(
                {'message': '版本不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comparison, errors = checklist_version_service.ChecklistVersionService.compare_versions(
            from_version, to_version, request.user
        )
        
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ChecklistVersionComparisonSerializer(comparison)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """回滚到指定版本"""
        version = self.get_object()
        
        success, errors = checklist_version_service.ChecklistVersionService.rollback_to_version(
            version, request.user
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': '回滚成功'})


class ChecklistExportViewSet(viewsets.ModelViewSet):
    """清单导出视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChecklistExportSerializer
    filterset_fields = ['export_format', 'status', 'instance', 'template']
    ordering_fields = ['created_at', 'completed_at']
    
    def get_queryset(self):
        """获取导出查询集"""
        queryset = ChecklistExport.objects.select_related('created_by', 'instance', 'template')
        
        # 用户只能看到自己创建的导出
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """创建导出任务"""
        instance_id = request.data.get('instance_id')
        template_id = request.data.get('template_id')
        export_format = request.data.get('export_format', 'json')
        
        if not instance_id and not template_id:
            return Response(
                {'message': '需要提供instance_id或template_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取目标对象
        try:
            if instance_id:
                from apps.checklists.models import ChecklistInstance
                target = ChecklistInstance.objects.get(id=instance_id)
            else:
                from apps.checklists.models import ChecklistTemplate
                target = ChecklistTemplate.objects.get(id=template_id)
        except Exception as e:
            return Response(
                {'message': f'目标对象不存在: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 创建导出记录
        export = checklist_export_service.ChecklistExportService.create_export_record(
            target=target,
            export_format=export_format,
            created_by=request.user,
            include_items=request.data.get('include_items', True),
            include_attachments=request.data.get('include_attachments', False),
            include_metadata=request.data.get('include_metadata', False)
        )
        
        # 执行导出
        success, errors = False, []
        if export_format == 'csv':
            success, errors = checklist_export_service.ChecklistExportService.export_to_csv(target, export)
        elif export_format == 'excel':
            success, errors = checklist_export_service.ChecklistExportService.export_to_excel(target, export)
        elif export_format == 'pdf':
            success, errors = checklist_export_service.ChecklistExportService.export_to_pdf(target, export)
        elif export_format == 'json':
            success, errors = checklist_export_service.ChecklistExportService.export_to_json(target, export)
        else:
            errors.append(f'不支持的导出格式: {export_format}')
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(export)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载导出文件"""
        export = self.get_object()
        
        if export.status != 'completed':
            return Response(
                {'message': '导出尚未完成'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 实际应用中应该返回文件流
        return Response({
            'message': '文件下载',
            'file_url': export.file_url,
            'file_size': export.file_size,
            'file_format': export.export_format
        })


class ChecklistImportViewSet(viewsets.ModelViewSet):
    """清单导入视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChecklistImportSerializer
    filterset_fields = ['import_format', 'status']
    ordering_fields = ['created_at', 'completed_at']
    
    def get_queryset(self):
        """获取导入查询集"""
        queryset = ChecklistImport.objects.select_related('created_by')
        
        # 用户只能看到自己创建的导入
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """创建导入任务"""
        import_format = request.data.get('import_format')
        file_path = request.data.get('file_path')
        
        if not import_format or not file_path:
            return Response(
                {'message': '需要提供import_format和file_path参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建导入记录
        import_record = checklist_export_service.ChecklistImportService.create_import_record(
            import_format=import_format,
            file_path=file_path,
            created_by=request.user,
            create_template=request.data.get('create_template', False),
            create_instance=request.data.get('create_instance', False),
            update_existing=request.data.get('update_existing', False)
        )
        
        # 执行导入
        success, errors = False, []
        if import_format == 'json':
            success, errors = checklist_export_service.ChecklistImportService.import_from_json(import_record)
        elif import_format == 'csv':
            success, errors = checklist_export_service.ChecklistImportService.import_from_csv(import_record)
        else:
            errors.append(f'不支持的导入格式: {import_format}')
        
        # 更新导入记录
        import_record.status = 'completed' if success else 'failed'
        import_record.completed_at = timezone.now()
        import_record.save()
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(import_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChecklistVerificationViewSet(viewsets.ModelViewSet):
    """清单核验视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChecklistVerificationSerializer
    filterset_fields = ['instance', 'status', 'approval_status', 'requires_approval']
    search_fields = ['notes']
    ordering_fields = ['created_at', 'planned_start_time', 'actual_start_time']
    
    def get_queryset(self):
        """获取核验查询集"""
        queryset = ChecklistVerification.objects.select_related(
            'instance', 'verified_by', 'approved_by'
        ).prefetch_related('details', 'exceptions')
        
        # 权限过滤
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(instance__event__owner=self.request.user) |
                Q(verified_by=self.request.user) |
                Q(approved_by=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """创建核验计划"""
        success, verification, errors = checklist_verification_service.ChecklistVerificationService.create_verification_plan(
            request.data, request.user
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始核验"""
        verification = self.get_object()
        
        success, errors = checklist_verification_service.ChecklistVerificationService.start_verification(
            str(verification.id), request.user
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成核验"""
        verification = self.get_object()
        notes = request.data.get('notes', '')
        
        success, errors = checklist_verification_service.ChecklistVerificationService.complete_verification(
            str(verification.id), request.user, notes
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def request_approval(self, request, pk=None):
        """请求审批"""
        verification = self.get_object()
        
        success, errors = checklist_verification_service.ChecklistVerificationService.request_approval(
            str(verification.id), request.user
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """批准核验"""
        verification = self.get_object()
        comments = request.data.get('comments', '')
        
        success, errors = checklist_verification_service.ChecklistVerificationService.approve_verification(
            str(verification.id), request.user, comments
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝核验"""
        verification = self.get_object()
        reason = request.data.get('reason', '拒绝原因未提供')
        
        success, errors = checklist_verification_service.ChecklistVerificationService.reject_verification(
            str(verification.id), request.user, reason
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(verification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取核验统计信息"""
        verification = self.get_object()
        statistics = checklist_verification_service.ChecklistVerificationService.get_verification_statistics(
            str(verification.id)
        )
        
        return Response(statistics)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """获取核验报告"""
        verification = self.get_object()
        report = checklist_verification_service.ChecklistVerificationService.get_verification_report(
            str(verification.id)
        )
        
        if not report:
            return Response(
                {'message': '生成报告失败'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(report)
    
    @action(detail=True, methods=['post'])
    def record_detail(self, request, pk=None):
        """记录核验详情"""
        verification = self.get_object()
        
        success, errors = checklist_verification_service.ChecklistVerificationService.record_verification_detail(
            verification_id=str(verification.id),
            item_id=request.data.get('item_id'),
            result=request.data.get('result'),
            evidence=request.data.get('evidence', ''),
            verified_by=request.user,
            location=request.data.get('location'),
            attachments=request.data.get('attachments'),
            notes=request.data.get('notes', '')
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': '核验详情记录成功'})


class ChecklistVerificationExceptionViewSet(viewsets.ModelViewSet):
    """清单核验异常视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChecklistVerificationExceptionSerializer
    filterset_fields = ['verification', 'exception_type', 'status', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'severity']
    
    def get_queryset(self):
        """获取异常查询集"""
        queryset = ChecklistVerificationException.objects.select_related(
            'verification', 'checklist_item', 'assigned_to', 'resolved_by'
        )
        
        # 权限过滤
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to=self.request.user) |
                Q(resolved_by=self.request.user) |
                Q(verification__verified_by=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """创建异常"""
        exception, errors = checklist_verification_service.ChecklistVerificationService.create_exception(
            verification_id=request.data.get('verification_id'),
            exception_type=request.data.get('exception_type'),
            title=request.data.get('title'),
            description=request.data.get('description'),
            severity=request.data.get('severity', 'medium'),
            checklist_item_id=request.data.get('checklist_item_id')
        )
        
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(exception)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决异常"""
        exception = self.get_object()
        resolution = request.data.get('resolution')
        
        if not resolution:
            return Response(
                {'message': '需要提供解决方案'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, errors = checklist_verification_service.ChecklistVerificationService.resolve_exception(
            str(exception.id), resolution, request.user
        )
        
        if not success:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(exception)
        return Response(serializer.data)