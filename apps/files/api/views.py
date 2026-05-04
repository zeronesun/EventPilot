"""文件管理API视图集"""

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import FileResponse, HttpResponse
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count
import logging

from ..models import (
    FileMetadata,
    FileShare,
    FileAuditLog,
)
from .serializers import (
    FileMetadataSerializer,
    FileUploadInitiateSerializer,
    FileDownloadRequestSerializer,
    FileListFilterSerializer,
    FileShareCreateSerializer,
    FileBatchDeleteSerializer,
    FileUploadResponseSerializer,
    FileDownloadResponseSerializer,
    FileListResponseSerializer,
    FileShareResponseSerializer,
    FileErrorResponseSerializer,
    FileMetadataCompactSerializer,
)
from ..services import (
    FileService,
    FileUploadConfig,
    FileHealthMonitor,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class FileViewSet(viewsets.ViewSet):
    """文件管理视图集"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_service = FileService()
        self.upload_config = FileUploadConfig()
    
    @action(detail=False, methods=['get'])
    def test(self, request):
        """测试端点"""
        logger.info(f"====> FileViewSet.test 被调用!")
        return Response({'status': 'ok', 'message': '文件管理API工作正常'})
    
    def create(self, request):
        """上传文件（直接上传）"""
        logger.info(f"====> FileViewSet.create 被调用!")
        logger.info(f"收到上传请求，FILES: {list(request.FILES.keys())}, DATA: {list(request.data.keys())}")
        
        try:
            if 'file' not in request.FILES:
                logger.warning("没有文件在请求中")
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'file_required',
                        'message': '请选择要上传的文件',
                        'details': {}
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file_obj = request.FILES['file']
            filename = request.data.get('filename', file_obj.name)
            logger.info(f"文件名: {filename}, 大小: {file_obj.size}, 类型: {file_obj.content_type}")
            
            result = self.file_service.direct_upload(
                user=request.user,
                file_obj=file_obj,
                filename=filename
            )
            
            logger.info(f"文件上传成功，file_id: {result.get('file_id')}")
            return Response(result, status=status.HTTP_201_CREATED)
            
        except (ValidationError, PermissionDenied) as e:
            logger.warning(f"验证失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'upload_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"上传文件失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '上传文件失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request):
        """列出用户文件"""
        try:
            serializer = FileListFilterSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filters = serializer.validated_data
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 20)
            
            result = self.file_service.list_user_files(
                user=request.user,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            # 直接返回字典结果，避免 ModelSerializer 序列化字典时的类型错误
            return Response(result)
            
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '获取文件列表失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def initiate_upload(self, request):
        """初始化文件上传"""
        try:
            serializer = FileUploadInitiateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '上传参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.file_service.initiate_upload(
                user=request.user,
                **serializer.validated_data
            )

            # 直接返回字典结果
            return Response(result, status=status.HTTP_201_CREATED)
            
        except (ValidationError, PermissionDenied) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'upload_init_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"上传初始化失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '上传初始化失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_file(self, request, pk=None):
        """直接下载文件"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=pk, is_deleted=False)
            
            if file_metadata.owner != request.user:
                return Response(
                    {'error': 'permission_denied', 'message': '无权限访问此文件'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from django.conf import settings
            
            file_path = os.path.join(settings.MEDIA_ROOT, file_metadata.storage_path)
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return Response(
                    {'error': 'not_found', 'message': '文件不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=file_metadata.original_filename
            )
            
            response['Content-Type'] = file_metadata.mime_type or 'application/octet-stream'
            response['Content-Length'] = str(file_metadata.file_size)
            
            logger.info(f"文件下载成功: {pk}, 文件名: {file_metadata.original_filename}")
            
            return response
            
        except FileMetadata.DoesNotExist:
            return Response(
                {'error': 'not_found', 'message': '文件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"文件下载失败: {str(e)}")
            return Response(
                {'error': 'internal_error', 'message': f'下载失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def upload_part(self, request, pk=None):
        """获取分片上传的预签名URL"""
        try:
            part_number = request.data.get('part_number')
            upload_id = request.data.get('upload_id')
            
            if not part_number or not upload_id:
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': 'part_number和upload_id是必填参数',
                        'details': {}
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.file_service.get_upload_part_url(
                file_id=pk,
                part_number=int(part_number),
                upload_id=upload_id,
                user=request.user
            )
            
            return Response(result)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'upload_part_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"获取分片上传URL失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '获取分片上传URL失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete_upload(self, request, pk=None):
        """完成文件上传"""
        try:
            result = self.file_service.complete_upload(
                file_id=pk,
                user=request.user,
                parts=request.data.get('parts', [])
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'upload_complete_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"完成上传失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '完成上传失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """获取文件详细信息"""
        try:
            file_metadata = self.file_service.get_file_metadata(
                file_id=pk,
                user=request.user
            )
            
            return Response(file_metadata)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'file_not_found',
                    'message': '文件不存在或无权限访问',
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"获取文件详情失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '获取文件详情失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def partial_update(self, request, pk=None):
        """更新文件元数据"""
        try:
            file_metadata = FileMetadata.objects.get(file_id=pk)
            
            if file_metadata.owner != request.user:
                raise PermissionDenied("无权限修改此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            updatable_fields = ['description', 'tags', 'category', 'visibility']
            
            for field in updatable_fields:
                if field in request.data:
                    setattr(file_metadata, field, request.data[field])
            
            file_metadata.save()
            
            self.file_service._log_file_audit(
                file_metadata=file_metadata,
                action='edit',
                user=request.user,
                success=True,
                details=request.data
            )
            
            return Response(FileMetadataSerializer(file_metadata).data)
            
        except (ValidationError, PermissionDenied) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'permission_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_403_FORBIDDEN
            )
        except FileMetadata.DoesNotExist:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'file_not_found',
                    'message': '文件不存在',
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"更新文件失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '更新文件失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """删除文件"""
        try:
            result = self.file_service.delete_file(
                file_id=pk,
                user=request.user
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except PermissionDenied as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'permission_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_403_FORBIDDEN
            )
        except NotFound:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'file_not_found',
                    'message': '文件不存在',
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '删除文件失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """生成文件下载URL"""
        try:
            # 使用 dict() 安全转换 QueryDict
            request_data = dict(request.data)
            request_data['file_id'] = pk

            serializer = FileDownloadRequestSerializer(data=request_data)
            if not serializer.is_valid():
                logger.warning(f"下载参数验证失败: {serializer.errors}")
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '下载请求参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = self.file_service.create_download_url(
                file_id=pk,
                user=request.user,
                expires_in=serializer.validated_data.get('expires_in', 3600)
            )

            return Response(result)

        except PermissionDenied as e:
            logger.warning(f"下载权限不足: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'permission_denied',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            logger.warning(f"下载验证失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'validation_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"创建下载URL失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '创建下载URL失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """创建文件分享链接"""
        try:
            # 使用 dict() 安全转换 QueryDict，避免展开问题
            request_data = dict(request.data)
            request_data['file_id'] = pk

            serializer = FileShareCreateSerializer(data=request_data)
            if not serializer.is_valid():
                logger.warning(f"分享参数验证失败: {serializer.errors}")
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '分享参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )

            share_settings = {
                'allow_download': serializer.validated_data.get('allow_download', True),
                'allow_preview': serializer.validated_data.get('allow_preview', True),
                'expires_at': None,
                'description': serializer.validated_data.get('description', ''),
                'base_url': request.build_absolute_uri('/api'),
            }

            expires_hours = serializer.validated_data.get('expires_hours')
            if expires_hours:
                share_settings['expires_at'] = timezone.now() + timezone.timedelta(hours=expires_hours)

            result = self.file_service.create_file_share(
                file_id=pk,
                user=request.user,
                settings=share_settings
            )

            return Response(result, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            logger.warning(f"分享权限不足: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'permission_denied',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            logger.warning(f"分享验证失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'validation_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"创建分享链接失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '创建分享链接失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def revoke_share(self, request, pk=None):
        """取消文件分享"""
        try:
            from ..models import FileShare

            try:
                file_metadata = FileMetadata.objects.get(file_id=pk)
            except FileMetadata.DoesNotExist:
                raise NotFound("文件不存在")

            if file_metadata.owner != request.user:
                raise PermissionDenied("无权限操作此文件的分享")

            # 文件 owner 可取消该文件的所有活跃分享（不限制 created_by）
            revoked_count = FileShare.objects.filter(
                file_metadata=file_metadata,
                is_active=True
            ).update(is_active=False)

            if revoked_count == 0:
                raise ValidationError("没有找到可取消的分享链接（可能已过期或已取消）")

            self.file_service._log_file_audit(
                file_metadata=file_metadata,
                action='revoke_share',
                user=request.user,
                success=True,
                details={'revoked_count': revoked_count}
            )

            return Response({
                'success': True,
                'revoked_count': revoked_count,
                'message': f'已取消 {revoked_count} 个分享链接'
            })

        except NotFound as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'file_not_found',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'permission_denied',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'validation_error',
                    'message': str(e),
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"取消分享失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '取消分享失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除文件"""
        try:
            serializer = FileBatchDeleteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '批量删除参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file_ids = serializer.validated_data['file_ids']
            deleted_count = 0
            failed_count = 0
            errors = []
            
            for file_id in file_ids:
                try:
                    self.file_service.delete_file(file_id=file_id, user=request.user)
                    deleted_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append({file_id: str(e)})
            
            return Response({
                'success': True,
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"批量删除失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '批量删除失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取文件统计数据"""
        try:
            queryset = FileMetadata.objects.filter(
                owner=request.user,
                is_deleted=False
            )
            
            total_files = queryset.count()
            total_size = queryset.aggregate(Sum('file_size'))['file_size__sum'] or 0
            
            by_category = {}
            for category_choice in FileMetadata.FileCategory.choices:
                category = category_choice[0]
                count = queryset.filter(file_category=category).count()
                if count > 0:
                    by_category[category] = count
            
            by_status = {}
            for status_choice in FileMetadata.FileStatus.choices:
                st = status_choice[0]
                count = queryset.filter(status=st).count()
                if count > 0:
                    by_status[st] = count
            
            by_type = {}
            type_counts = queryset.values('file_type').annotate(count=Count('id'))
            for item in type_counts:
                by_type[item['file_type']] = item['count']
            
            recent_date = timezone.now() - timezone.timedelta(days=7)
            recent_uploads = queryset.filter(created_at__gte=recent_date).count()
            
            total_quota = FileUploadConfig.MAX_FILE_SIZE
            storage_used = total_size
            storage_available = total_quota - storage_used
            quota_percentage = (storage_used / total_quota * 100) if total_quota > 0 else 0
            
            return Response({
                'total_files': total_files,
                'total_size': total_size,
                'by_category': by_category,
                'by_status': by_status,
                'by_type': by_type,
                'recent_uploads': recent_uploads,
                'storage_used': storage_used,
                'storage_available': storage_available,
                'quota_percentage': round(quota_percentage, 2)
            })
            
        except Exception as e:
            logger.error(f"获取文件统计失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '获取文件统计失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(never_cache, name='dispatch')
class FileShareViewSet(viewsets.ViewSet):
    """文件分享视图集"""
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_service = FileService()
    
    def retrieve(self, request, pk=None):
        """通过分享链接访问文件"""
        try:
            share = FileShare.objects.select_related('file_metadata').get(
                share_id=pk,
                is_active=True
            )
            
            if not share.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'share_expired',
                        'message': '分享链接已过期或已达到下载限制',
                        'details': {}
                    }).data,
                    status=status.HTTP_410_GONE
                )
            
            file_metadata = share.file_metadata
            
            try:
                download_result = self.file_service.create_download_url(
                    file_id=file_metadata.file_id,
                    user=share.created_by,
                    expires_in=3600
                )
                download_url = download_result['download_url']
            except Exception as e:
                logger.error(f"生成下载URL失败: {str(e)}")
                download_url = None
            
            share.download_count += 1
            share.last_accessed_at = timezone.now()
            share.save(update_fields=['download_count', 'last_accessed_at'])
            
            return Response({
                'file_id': file_metadata.file_id,
                'original_filename': file_metadata.original_filename,
                'file_size': file_metadata.file_size,
                'file_type': file_metadata.file_type,
                'mime_type': file_metadata.mime_type,
                'file_category': file_metadata.file_category,
                'download_url': download_url,
                'allow_download': share.allow_download,
                'allow_preview': share.allow_preview,
                'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                'share_info': {
                    'share_id': share.share_id,
                    'download_count': share.download_count,
                    'max_downloads': share.max_downloads
                }
            })
            
        except FileShare.DoesNotExist:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'share_not_found',
                    'message': '分享链接不存在或已被删除',
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"访问分享链接失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '访问分享链接失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(never_cache, name='dispatch')
class FileHealthViewSet(viewsets.ViewSet):
    """文件系统健康检查视图集"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """系统健康检查"""
        try:
            health_monitor = FileHealthMonitor()
            
            storage_health = health_monitor.check_storage_health()
            database_health = health_monitor.check_database_health()
            
            overall_health = 'healthy'
            if storage_health['status'] != 'healthy' or database_health['status'] != 'healthy':
                overall_health = 'unhealthy'
            
            return Response({
                'status': overall_health,
                'timestamp': timezone.now().isoformat(),
                'components': {
                    'storage': storage_health,
                    'database': database_health
                }
            }, status=status.HTTP_200_OK if overall_health == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'health_check_error',
                    'message': '健康检查失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
