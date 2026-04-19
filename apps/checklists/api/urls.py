from django.urls import path, include
from . import views
from . import advanced_views
from rest_framework.routers import DefaultRouter

app_name = 'checklists'

# 基础路由
router = DefaultRouter()
router.register(r'templates', views.ChecklistTemplateViewSet, basename='checklist-template')
router.register(r'item-templates', views.ChecklistItemTemplateViewSet, basename='checklist-item-template')
router.register(r'instances', views.ChecklistInstanceViewSet, basename='checklist-instance')
router.register(r'items', views.ChecklistItemViewSet, basename='checklist-item')

# 高级功能路由
advanced_router = DefaultRouter()
advanced_router.register(r'versions', advanced_views.ChecklistVersionViewSet, basename='checklist-version')
advanced_router.register(r'exports', advanced_views.ChecklistExportViewSet, basename='checklist-export')
advanced_router.register(r'imports', advanced_views.ChecklistImportViewSet, basename='checklist-import')
advanced_router.register(r'verifications', advanced_views.ChecklistVerificationViewSet, basename='checklist-verification')
advanced_router.register(r'exceptions', advanced_views.ChecklistVerificationExceptionViewSet, basename='checklist-exception')

urlpatterns = [
    path('', include(router.urls)),
    path('advanced/', include(advanced_router.urls)),
    path('instances/<str:instance_id>/report/', views.ChecklistInstanceViewSet.as_view({'get': 'report'}), name='checklist-report'),
    path('events/<str:event_id>/summary/', views.ChecklistReportGenerator.generate_summary, name='checklist-event-summary'),
]