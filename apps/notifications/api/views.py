from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from ..services import NotificationService


class NotificationViewSet(viewsets.ViewSet):
    """
    通知视图集

    提供：
    - 列表查询
    - 未读数量
    - 标记已读（单个/批量）
    - 删除
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        获取通知列表

        GET /api/notifications/
        Query参数:
            - type: 通知类型筛选
            - read: 阅读状态 (true/false/不填=全部)
            - page: 页码 (默认1)
            - page_size: 每页大小 (默认20)
        """
        try:
            # 获取查询参数
            notification_type = request.query_params.get('type')
            read_param = request.query_params.get('read')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            # 处理read参数
            if read_param is not None:
                if read_param.lower() == 'true':
                    read = True
                elif read_param.lower() == 'false':
                    read = False
                else:
                    read = None
            else:
                read = None

            result = NotificationService.get_user_notifications(
                user=request.user,
                read=read,
                type=notification_type,
                page=page,
                page_size=page_size
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'获取通知列表失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def unread_count(self, request):
        """
        获取未读通知数量

        GET /api/notifications/unread_count/
        """
        try:
            count = NotificationService.get_unread_count(request.user)
            return Response({'unread_count': count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'获取未读数量失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['POST'])
    def mark_read(self, request, pk=None):
        """
        标记单个通知为已读

        POST /api/notifications/{id}/mark_read/
        """
        try:
            success = NotificationService.mark_as_read(notification_id=pk)

            if success:
                return Response(
                    {'message': '标记已读成功'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': '通知不存在或标记失败'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return Response(
                {'error': f'标记已读失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['POST'])
    def bulk_mark_read(self, request):
        """
        批量标记已读

        POST /api/notifications/bulk_mark_read/
        Body:
            {
                "notification_ids": ["id1", "id2"], // 可选，不填则全部标记
            }
        """
        try:
            notification_ids = request.data.get('notification_ids')

            count = NotificationService.bulk_mark_as_read(
                user=request.user,
                notification_ids=notification_ids
            )

            return Response(
                {'message': f'成功标记 {count} 条为已读'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': f'批量标记已读失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['DELETE'])
    def delete(self, request, pk=None):
        """
        删除通知

        DELETE /api/notifications/{id}/delete/
        """
        try:
            success = NotificationService.delete_notification(notification_id=pk)

            if success:
                return Response(
                    {'message': '删除成功'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': '通知不存在或删除失败'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return Response(
                {'error': f'删除失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        """
        获取通知统计信息

        GET /api/notifications/statistics/
        返回: 各类型各状态的通知数量
        """
        try:
            queryset = Notification.objects.filter(user=request.user)

            # 总数统计
            total = queryset.count()

            # 状态统计
            unread_count = queryset.filter(read=False).count()
            read_count = queryset.filter(read=True).count()

            # 类型统计
            type_stats = queryset.values('type').annotate(
                count=Count('id')
            )

            # 来源统计
            source_stats = queryset.values('source').annotate(
                count=Count('id')
            )

            return Response({
                'total': total,
                'unread': unread_count,
                'read': read_count,
                'by_type': list(type_stats),
                'by_source': list(source_stats)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'获取统计信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
