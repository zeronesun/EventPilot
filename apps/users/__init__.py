# 延迟加载所有认证相关类以避免循环导入
def get_models():
    """延迟加载模型以避免循环导入"""
    from .models.user import User, UserRole, ResourceAccess
    return User, UserRole, ResourceAccess

def get_jwt_token_generator():
    from .authentication import generate_jwt_token
    return generate_jwt_token

def get_jwt_decoding():
    from .authentication import decode_jwt_token
    return decode_jwt_token

def get_jwt_authentication():
    from .authentication import JWTAuthentication
    return JWTAuthentication

__all__ = []  # 不在顶层导入，使用延迟加载