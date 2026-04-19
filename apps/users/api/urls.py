from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, BulkUpdateStatusView, BulkAssignRolesView, 
    BulkDeleteView, UserImportView, UserStatisticsView, 
    InactiveUsersView, RoleListView
)
from . import jwt_views

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT认证端点
    path('auth/login/', jwt_views.jwt_login, name='jwt-login'),
    path('auth/refresh/', jwt_views.jwt_refresh, name='jwt-refresh'),
    path('auth/verify/', jwt_views.jwt_verify, name='jwt-verify'),
    
    # 用户管理端点
    path('', include(router.urls)),
    
    # 批量操作端点
    path('users/bulk/update-status/', 
         BulkUpdateStatusView.as_view(), 
         name='bulk-update-status'),
    path('users/bulk/assign-roles/', 
         BulkAssignRolesView.as_view(), 
         name='bulk-assign-roles'),
    path('users/bulk/delete/', 
         BulkDeleteView.as_view(), 
         name='bulk-delete'),
    
    # 用户导入
    path('users/import/', UserImportView.as_view(), name='user-import'),
    
    # 统计和报告
    path('users/statistics/', UserStatisticsView.as_view(), name='user-statistics'),
    path('users/inactive/', InactiveUsersView.as_view(), name='inactive-users'),
    
    # 角色列表
    path('roles/', RoleListView.as_view(), name='roles'),
]