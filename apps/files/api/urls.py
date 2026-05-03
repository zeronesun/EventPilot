from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import FileViewSet, FileShareViewSet, FileHealthViewSet

router = DefaultRouter()
router.register(r'', FileViewSet, basename='file')

urlpatterns = [
    path('share/<str:pk>/', FileShareViewSet.as_view({'get': 'retrieve'}), name='file-share'),
    path('health/', FileHealthViewSet.as_view({'get': 'health'}), name='file-health'),
    path('', include(router.urls)),
]
