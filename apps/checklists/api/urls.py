from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'checklists'

router = DefaultRouter()
router.register(r'templates', views.ChecklistTemplateViewSet, basename='checklist-template')
router.register(r'item-templates', views.ChecklistItemTemplateViewSet, basename='checklist-item-template')
router.register(r'instances', views.ChecklistInstanceViewSet, basename='checklist-instance')
router.register(r'items', views.ChecklistItemViewSet, basename='checklist-item')

urlpatterns = [
    path('', include(router.urls)),
    path('instances/<str:instance_id>/report/', views.ChecklistReportGenerator, name='checklist-report'),
]