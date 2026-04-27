from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reviews.api.views import ReviewViewSet

app_name = 'reviews'

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]