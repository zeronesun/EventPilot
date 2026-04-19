#!/usr/bin/env python3
import os
import sys

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

try:
    import django
    django.setup()
    print("✅ Django setup successful!")
    
    # Check if we can import our models
    from apps.users.models import User, UserRole, ResourceAccess
    print(f"✅ User models imported successfully!")
    
    # Check other modules
    from apps.events.models import Event, BudgetItem
    print(f"✅ Event models imported successfully!")
    
    from apps.tasks.models import Task, TaskDependency, CommunicationTask
    print(f"✅ Task models imported successfully!")
    
    print("\n🎉 All core models are ready to use!")
    
except Exception as e:
    print(f"❌ Error during import: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()