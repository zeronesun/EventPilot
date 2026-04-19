from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.knowledge import views as knowledge_views

app_name = 'knowledge'

router = DefaultRouter()
router.register(r'knowledge', knowledge_views.KnowledgeEntryViewSet, basename='knowledge')

urlpatterns = [
    path('', include(router.urls)),
]