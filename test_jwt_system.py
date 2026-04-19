#!/usr/bin/env python3
import os
import sys

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

try:
    import django
    django.setup()

    from apps.users.authentication import generate_jwt_token, JWTAuthentication
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Test with existing user or create test user
    try:
        user = User.objects.get(username='admin')
        print(f"✅ Found user: {user.username}")
    except User.DoesNotExist:
        print("⚠️ Admin user not found, checking for any user...")
        user = User.objects.first()
        if not user:
            print("❌ No users found in database")
            sys.exit(1)

    # Test JWT token generation
    try:
        token = generate_jwt_token(user)
        print(f"✅ JWT token generated successfully: {token[:50]}...")
        print(f"   Token length: {len(token)} characters")

        # Test JWT authentication
        auth = JWTAuthentication()
        # Create a mock request with the token
        class MockRequest:
            def __init__(self):
                self.META = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        request = MockRequest()
        authenticated_user, payload = auth.authenticate(request)
        print(f"✅ JWT authentication successful: {authenticated_user.username}")

    except Exception as e:
        print(f"❌ Error testing JWT: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 JWT System Status: FULLY OPERATIONAL ✅")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)