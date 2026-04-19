# -*- coding: utf-8 -*-
from pathlib import Path
import os

# 动态加载环境特定的配置
DEPLOYMENT_MODE = os.getenv('DJANGO_SETTINGS_MODULE', 'base')

if DEPLOYMENT_MODE == 'config.settings.development':
    from .development import *  # noqa
elif DEPLOYMENT_MODE == 'config.settings.production':
    from .production import *  # noqa
else:
    from .base import *  # noqa