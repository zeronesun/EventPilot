# from django.contrib import admin  # 暂时禁用admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin (暂时禁用)
    # path('admin/', admin.site.urls),

    # 健康检查和系统信息（api 模块）
    path('api/', include('api.urls')),

    # 应用API路由 - 各模块独立路径前缀
    path('api/users/', include('apps.users.api.urls')),  # 包含auth/, users/等
    path('api/events/', include('apps.events.api.urls')),  # 包含events/等
    path('api/tasks/', include('apps.tasks.api.urls')),  # 包含tasks/等
    path('api/checklists/', include('apps.checklists.api.urls')),  # 包含templates/, instances/等
    path('api/files/', include('apps.files.api.urls')),  # 文件上传系统，包含files/等
    path('api/profiles/', include('apps.profiles.api.urls')),  # Phase 3 包含profiles/等
    path('api/knowledge/', include('apps.knowledge.api.urls')),  # 知识库模块
    path('api/reviews/', include('apps.reviews.api.urls')),  # 复盘模块

    # API文档（后续集成）
    # path('api/docs/', include('rest_framework.urls')),

]

# 开发环境媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)