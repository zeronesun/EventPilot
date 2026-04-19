from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reviews import views as review_views

app_name = 'reviews'

router = DefaultRouter()
router.register(r'reviews', review_views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]