from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, BudgetItemViewSet

app_name = 'events'

router = DefaultRouter()
router.register(r'', EventViewSet, basename='event')
router.register(r'budget-items', BudgetItemViewSet, basename='budget-item')

urlpatterns = [
    path('dashboard_analytics/', EventViewSet.as_view({'get': 'dashboard_analytics'}), name='event-dashboard-analytics'),
    path('', include(router.urls)),
]