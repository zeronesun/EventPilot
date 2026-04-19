"""
文件管理API视图集
提供完整的文件上传、下载、管理等功能
"""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum
import logging

from ..models import (
    FileMetadata, FileShare, FileAuditLog, FileVersion
)
from ..api.serializers import (
    FileMetadataSerializer, FileUploadInitiateSerializer,
    FileUploadPartSerializer, FileUploadCompleteSerializer,
    FileDownloadRequestSerializer, FileDeleteSerializer,
    FileListFilterSerializer, FileShareCreateSerializer,
    FileBatchDeleteSerializer, FileBatchShareSerializer,
    FileSearchSerializer, FileStatsSerializer, FileQuotaSerializer,
    FileUploadResponseSerializer, FileDownloadResponseSerializer,
    FileListResponseSerializer, FileShareResponseSerializer,
    FileErrorResponseSerializer, FileMetadataCompactSerializer
)
from ..services import (
    FileService, FileUploadConfig, FileHealthMonitor,
    FileSecurityValidator
)

User = get_user_model()

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class FileViewSet(viewsets.ViewSet):
    """
    文件管理视图集
    提供完整的文件管理功能
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_service = FileService()
        self.upload_config = FileUploadConfig()
    
    def list(self, request):
        """
        列出用户文件
        
        GET /api/files/
        """
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
            page = filters.pop('page')
            page_size = filters.pop('page_size')
            
            result = self.file_service.list_user_files(
                user=request.user,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            return Response(FileListResponseSerializer(result).data)
            
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '获取文件列表失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """
        初始化文件上传
        
        POST /api/files/
        
        请求体:
        {
            "filename": "test.pdf",
            "file_size": 12345678,
            "mime_type": "application/pdf",
            "metadata": {}
        }
        """
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
            
            return Response(
                FileUploadResponseSerializer(result).data,
                status=status.HTTP_201_CREATED
            )
            
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
    
    def retrieve(self, request, file_id=None):
        """
        获取文件详细信息
        
        GET /api/files/{file_id}/
        """
        try:
            file_metadata = self.file_service.get_file_metadata(
                file_id=file_id,
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
    
    def partial_update(self, request, file_id=None):
        """
        更新文件元数据
        
        PATCH /api/files/{file_id}/
        """
        try:
            file_metadata = FileMetadata.objects.get(file_id=file_id)
            
            # 权限验证
            if file_metadata.owner != request.user:
                raise PermissionDenied("无权限修改此文件")
            
            if file_metadata.is_deleted:
                raise ValidationError("文件已被删除")
            
            # 更新可修改的字段
            updatable_fields = [
                'description', 'tags', 'category', 'visibility', 
                'metadata', 'custom_attributes'
            ]
            
            for field in updatable_fields:
                if field in request.data:
                    setattr(file_metadata, field, request.data[field])
            
            file_metadata.save()
            
            # 记录审计日志
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
    
    def destroy(self, request, file_id=None):
        """
        删除文件
        
        DELETE /api/files/{file_id}/
        """
        try:
            result = self.file_service.delete_file(
                file_id=file_id,
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
    def download(self, request, file_id=None):
        """
        生成文件下载URL
        
        POST /api/files/{file_id}/download/
        
        请求体:
        {
            "file_id": "xxx",
            "expires_in": 3600
        }
        """
        try:
            serializer = FileDownloadRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '下载请求参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.file_service.create_download_url(
                file_id=file_id,
                user=request.user,
                expires_in=serializer.validated_data.get('expires_in', 3600)
            )
            
            return Response(FileDownloadResponseSerializer(result).data)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'download_error',
                    'message': '无法下载文件',
                    'details': {}
                }).data,
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"生成下载URL失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '生成下载URL失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def upload_part(self, request, file_id=None):
        """
        获取分片上传URL（大文件分片上传）
        
        POST /api/files/{file_id}/upload_part/
        """
        try:
            serializer = FileUploadPartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '分片上传参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.file_service.get_upload_part_url(
                file_id=file_id,
                **serializer.validated_data,
                user=request.user
            )
            
            return Response(result)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'upload_part_error',
                    'message': '无法获取分片上传URL',
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
    def complete_upload(self, request, file_id=None):
        """
        完成文件上传（确认分片上传完成）
        
        POST /api/files/{file_id}/complete_upload/
        """
        try:
            serializer = FileUploadCompleteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '完成上传参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.file_service.complete_upload(
                file_id=serializer.validated_data['file_id_key'],
                upload_id=serializer.validated_data['upload_id'],
                parts=serializer.validated_data['parts'],
                user=request.user
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'complete_upload_error',
                    'message': '完成上传失败',
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
    
    @action(detail=True, methods=['post'])
    def share(self, request, file_id=None):
        """
        创建文件分享链接
        
        POST /api/files/{file_id}/share/
        """
        try:
            serializer = FileShareCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '分享参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取分享设置
            share_settings = {
                'allow_download': serializer.validated_data.get('allow_download', True),
                'allow_preview': serializer.validated_data.get('allow_preview', True),
                'permitir_comments': serializer.validated_data.get('permitir_comments', False),
                'allow_reshare': serializer.validated_data.get('allow_reshare', False),
                'password_protected': serializer.validated_data.get('password_protected', False),
                'expires_at': None,
                'description': serializer.validated_data.get('description', ''),
                'metadata': {}
            }
            
            # 处理过期时间
            expires_hours = serializer.validated_data.get('expires_hours')
            if expires_hours:
                share_settings['expires_at'] = timezone.now() + timezone.timedelta(hours=expires_hours)
            
            # 处理密码保护
            if share_settings['password_protected']:
                from django.contrib.auth.hashers import make_password
                password = serializer.validated_data.get('password')
                share_settings['password_hash'] = make_password(password)
            
            # 获取基础URL
            base_url = request.build_absolute_uri('/api/files/')
            share_settings['base_url'] = base_url
            
            result = self.file_service.create_file_share(
                file_id=file_id,
                user=request.user,
                settings=share_settings
            )
            
            return Response(FileShareResponseSerializer(result).data, status=status.HTTP_201_CREATED)
            
        except (ValidationError, PermissionDenied, NotFound) as e:
            return Response(
                FileErrorResponseSerializer({
                    'error': 'share_error',
                    'message': '无法创建分享链接',
                    'details': {}
                }).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"创建分享链接失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '创建分享链接失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        批量删除文件
        
        POST /api/files/batch_delete/
        """
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
    
    @action(detail=False, methods=['post'])
    def batch_share(self, request):
        """
        批量分享文件
        
        POST /api/files/batch_share/
        """
        try:
            serializer = FileBatchShareSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '批量分享参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file_ids = serializer.validated_data['file_ids']
            share_results = []
            
            base_url = request.build_absolute_uri('/api/files/')
            
            for file_id in file_ids:
                try:
                    share_settings = {
                        'allow_download': serializer.validated_data.get('allow_download', True),
                        'allow_preview': serializer.validated_data.get('allow_preview', True),
                        'expires_at': timezone.now() + timezone.timedelta(
                            hours=serializer.validated_data.get('expires_hours', 168)
                        ),
                        'base_url': base_url,
                        'metadata': {}
                    }
                    
                    result = self.file_service.create_file_share(
                        file_id=file_id,
                        user=request.user,
                        settings=share_settings
                    )
                    
                    share_results.append({
                        'file_id': file_id,
                        'share_url': result['share_url'],
                        'success': True
                    })
                    
                except Exception as e:
                    share_results.append({
                        'file_id': file_id,
                        'success': False,
                        'error': str(e)
                    })
            
            return Response({
                'success': True,
                'total': len(file_ids),
                'successful': len([r for r in share_results if r['success']]),
                'failed': len([r for r in share_results if not r['success']]),
                'results': share_results
            })
            
        except Exception as e:
            logger.error(f"批量分享失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '批量分享失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        搜索文件
        
        GET /api/files/search/?query=test&category=document
        """
        try:
            serializer = FileSearchSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'validation_error',
                        'message': '搜索参数验证失败',
                        'details': serializer.errors
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 实现搜索逻辑
            query = serializer.validated_data['query']
            filters = {}
            
            if 'category' in serializer.validated_data:
                filters['category'] = serializer.validated_data['category']
            
            if 'file_type' in serializer.validated_data:
                filters['file_type'] = serializer.validated_data['file_type']
            
            page = serializer.validated_data.get('page', 1)
            page_size = serializer.validated_data.get('page_size', 20)
            
            # 执行搜索
            result = self.file_service.list_user_files(
                user=request.user,
                filters={'search': query, **filters},
                page=page,
                page_size=page_size
            )
            
            return Response(FileListResponseSerializer(result).data)
            
        except Exception as e:
            logger.error(f"搜索文件失败: {str(e)}")
            return Response(
                FileErrorResponseSerializer({
                    'error': 'internal_error',
                    'message': '搜索文件失败',
                    'details': {'error': str(e)}
                }).data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        获取文件统计数据
        
        GET /api/files/stats/
        """
        try:
            # 获取用户文件统计
            queryset = FileMetadata.objects.filter(
                owner=request.user,
                is_deleted=False
            )
            
            total_files = queryset.count()
            total_size = queryset.aggregate(Sum('file_size'))['file_size__sum'] or 0
            
            # 按分类统计
            by_category = {}
            for category_choice in FileMetadata.FileCategory.choices:
                category = category_choice[0]
                count = queryset.filter(file_category=category).count()
                if count > 0:
                    by_category[category] = count
            
            # 按状态统计
            by_status = {}
            for status_choice in FileMetadata.FileStatus.choices:
                status = status_choice[0]
                count = queryset.filter(status=status).count()
                if count > 0:
                    by_status[status] = count
            
            # 按类型统计
            by_type = {}
            type_counts = queryset.values('file_type').annotate(count=Count('id'))
            for item in type_counts:
                by_type[item['file_type']] = item['count']
            
            # 最近上传（7天内）
            recent_date = timezone.now() - timezone.timedelta(days=7)
            recent_uploads = queryset.filter(created_at__gte=recent_date).count()
            
            # 存储配额
            total_quota = self.upload_config.MAX_FILE_SIZE
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
    """
    文件分享视图集
    处理公共分享链接访问
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_service = FileService()
    
    def retrieve(self, request, share_id=None):
        """
        通过分享链接访问文件
        
        GET /api/files/share/{share_id}/
        """
        try:
            # 查找分享记录
            share = FileShare.objects.select_related('file_metadata').get(
                share_id=share_id,
                is_active=True
            )
            
            # 验证分享有效性
            if not share.is_valid():
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'share_expired',
                        'message': '分享链接已过期或已达到下载限制',
                        'details': {}
                    }).data,
                    status=status.HTTP_410_GONE
                )
            
            # 检查密码保护
            if share.password_protected:
                provided_password = request.query_params.get('password', '')
                from django.contrib.auth.hashers import check_password
                if not check_password(provided_password, share.password_hash):
                    return Response(
                        FileErrorResponseSerializer({
                            'error': 'password_required',
                            'message': '需要密码才能访问此文件',
                            'details': {}
                        }).data,
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # 获取文件信息
            file_metadata = share.file_metadata
            
            # 生成预签名下载URL
            try:
                download_url = self.file_service.storage_service.generate_presigned_download_url(
                    key=file_metadata.storage_path,
                    expires_in=3600  # 1小时
                )
            except Exception as e:
                logger.error(f"生成下载URL失败: {str(e)}")
                return Response(
                    FileErrorResponseSerializer({
                        'error': 'download_error',
                        'message': '无法生成下载链接',
                        'details': {}
                    }).data,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 更新分享统计
            share.download_count += 1
            share.last_accessed_at = timezone.now()
            share.save(update_fields=['download_count', 'last_accessed_at'])
            
            # 记录访问日志
            self.file_service._log_file_audit(
                file_metadata=file_metadata,
                action='download',
                user=None,  # 公共分享可能没有用户
                success=True,
                details={
                    'via_share': share_id,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': request.META.get('REMOTE_ADDR', '')
                }
            )
            
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
    """
    文件系统健康检查视图集
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        系统健康检查
        
        GET /api/files/health/
        """
        try:
            health_monitor = FileHealthMonitor()
            
            # 检查存储健康
            storage_health = health_monitor.check_storage_health()
            
            # 检查数据库健康
            database_health = health_monitor.check_database_health()
            
            # 系统健康状态
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