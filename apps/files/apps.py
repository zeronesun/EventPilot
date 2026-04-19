from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.files'
    verbose_name = '文件管理'
    
    def ready(self):
        from apps.files.services import file_service
        return super().ready()