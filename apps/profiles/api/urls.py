from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.profiles import views as profile_views

app_name = 'profiles'

router = DefaultRouter()
router.register(r'profiles', profile_views.ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]