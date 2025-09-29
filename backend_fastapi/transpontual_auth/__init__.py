"""
Transpontual Auth - Pacote compartilhado de autenticação
Sistema unificado de JWT para integração entre os sistemas da Transpontual
"""

from .jwt_handler import (
    create_access_token,
    verify_token,
    create_user_payload,
    extract_user_from_payload,
    JWTConfig
)

from .schemas import (
    UserInfo,
    TokenPayload,
    PermissionClaim,
    SystemRole,
    AccessRestrictions
)

__version__ = "1.0.0"
__all__ = [
    "create_access_token",
    "verify_token",
    "create_user_payload",
    "extract_user_from_payload",
    "JWTConfig",
    "UserInfo",
    "TokenPayload",
    "PermissionClaim",
    "SystemRole",
    "AccessRestrictions"
]