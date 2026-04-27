from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
]
