"""知识库服务层 - 知识条目业务逻辑"""

from typing import List
from django.db.models import F
from django.contrib.auth import get_user_model

User = get_user_model()


class KnowledgeService:
    """知识库服务层 - 处理知识条目业务逻辑"""

    @staticmethod
    def create_entry(serializer) -> object:
        """
        创建知识条目时的额外处理
        """
        user = User.objects.first() if User.objects.exists() else None
        return serializer.save(created_by=user, popularity=0)

    @staticmethod
    def get_popular(queryset, limit: int = 10):
        """
        获取热门知识条目
        """
        return queryset.filter(
            is_verified=True,
            popularity__gt=0
        ).order_by('-popularity')[:limit]

    @staticmethod
    def verify_entry(entry) -> object:
        """
        验证知识条目（管理员功能）
        """
        entry.is_verified = True
        entry.save()
        return entry

    @staticmethod
    def increment_view(entry) -> object:
        """
        增加查看次数
        """
        from apps.knowledge.models import KnowledgeEntry
        KnowledgeEntry.objects.filter(id=entry.id).update(
            popularity=F('popularity') + 1
        )
        entry.refresh_from_db()
        return entry

    @staticmethod
    def get_categories() -> List[str]:
        """
        获取所有分类
        """
        from apps.knowledge.models import KnowledgeEntry
        return KnowledgeEntry.objects.filter(
            is_verified=True
        ).values_list('category', flat=True).distinct().exclude(
            category=''
        )
