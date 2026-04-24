# from django.contrib import admin  # 暂时禁用admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin (暂时禁用)
    # path('admin/', admin.site.urls),

    # 健康检查和系统信息（api 模块）
    path('api/health/', include('api.urls')),

    # 应用API路由 - 直接注册
    path('api/', include('apps.users.api.urls')),
    path('api/', include('apps.events.api.urls')),
    path('api/', include('apps.tasks.api.urls')),
    path('api/', include('apps.checklists.api.urls')),
    path('api/', include('apps.files.api.urls')),        # 文件上传系统
    path('api/', include('apps.profiles.api.urls')),      # Phase 3 - 关联方档案管理

    # 未启用的模块
    # path('api/', include('apps.knowledge.api.urls')),
    # path('api/', include('apps.reviews.api.urls')),

    # API文档（后续集成）
    # path('api/docs/', include('rest_framework.urls')),

]

# 开发环境媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)