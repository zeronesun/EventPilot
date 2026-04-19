from .models.user import User, UserRole, ResourceAccess

__all__ = [
    'User', 'UserRole', 'ResourceAccess',
]

# 延迟加载认证类以避免循环导入
def get_jwt_token_generator():
    from .authentication import generate_jwt_token
    return generate_jwt_token

def get_jwt_decoding():
    from .authentication import decode_jwt_token
    return decode_jwt_token

def get_jwt_authentication():
    from .authentication import JWTAuthentication
    return JWTAuthentication