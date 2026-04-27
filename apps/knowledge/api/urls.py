from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.knowledge.api.views import KnowledgeEntryViewSet

app_name = 'knowledge'

router = DefaultRouter()
router.register(r'knowledge', KnowledgeEntryViewSet, basename='knowledge')

urlpatterns = [
    path('', include(router.urls)),
]