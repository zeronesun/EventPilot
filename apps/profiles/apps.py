"""
关联方档案管理应用配置
"""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.profiles'
    verbose_name = '关联方档案管理'
    
    def ready(self):
        # 导入信号处理器（如果需要）
        pass