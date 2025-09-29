"""
Schemas compartilhados para autenticação entre sistemas Transpontual
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


class SystemRole(str, Enum):
    """Roles específicos dos sistemas"""
    # Sistema de Frotas
    FROTAS_ADMIN = "frotas:admin"
    FROTAS_GESTOR = "frotas:gestor"
    FROTAS_OPERADOR = "frotas:operador"
    FROTAS_VIEWER = "frotas:viewer"

    # Dashboard Baker
    BAKER_ADMIN = "baker:admin"
    BAKER_FINANCEIRO = "baker:financeiro"
    BAKER_OPERADOR = "baker:operador"
    BAKER_VIEWER = "baker:viewer"

    # Sistema Financeiro
    FINANCEIRO_ADMIN = "financeiro:admin"
    FINANCEIRO_GESTOR = "financeiro:gestor"
    FINANCEIRO_OPERADOR = "financeiro:operador"
    FINANCEIRO_VIEWER = "financeiro:viewer"


class PermissionClaim(BaseModel):
    """Estrutura de permissões específicas por sistema"""
    frotas: Optional[Dict[str, List[str]]] = None
    baker: Optional[Dict[str, List[str]]] = None
    financeiro: Optional[Dict[str, List[str]]] = None

    class Config:
        json_encoders = {
            dict: lambda v: v or {}
        }


class UserInfo(BaseModel):
    """Informações padronizadas do usuário"""
    id: Union[int, str]
    email: EmailStr
    username: Optional[str] = None
    nome: str
    papel: Optional[str] = None  # Para compatibilidade com sistemas legados
    ativo: bool = True
    sistema_origem: str  # 'frotas', 'baker', 'financeiro'


class AccessRestrictions(BaseModel):
    """Restrições de acesso específicas"""
    ip_allowed: Optional[List[str]] = None
    horario_inicio: Optional[str] = None  # HH:MM
    horario_fim: Optional[str] = None     # HH:MM
    dias_semana: Optional[List[int]] = None  # 0-6 (Segunda=0, Domingo=6)
    bloqueado: bool = False
    motivo_bloqueio: Optional[str] = None


class TokenPayload(BaseModel):
    """Payload padronizado do JWT Token"""
    # Campos obrigatórios do JWT
    sub: str  # User ID como string
    user_info: UserInfo  # Informações completas do usuário
    exp: datetime
    iat: datetime
    iss: str = "transpontual"
    aud: str = "transpontual"

    # Campos específicos da Transpontual
    roles: List[SystemRole]
    permissoes: PermissionClaim
    restricoes: Optional[AccessRestrictions] = None
    sessao_id: Optional[str] = None

    # Metadados
    ip_origem: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UserInfo: lambda v: v.dict(),
            PermissionClaim: lambda v: v.dict(),
            AccessRestrictions: lambda v: v.dict() if v else None
        }


class LoginRequest(BaseModel):
    """Request de login padronizado"""
    email: EmailStr
    password: str
    remember_me: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TokenResponse(BaseModel):
    """Response padronizada do token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: UserInfo
    roles: List[SystemRole]
    permissoes: PermissionClaim


class SystemNavigationLink(BaseModel):
    """Link para navegação entre sistemas"""
    sistema: str
    url: str
    nome: str
    descricao: Optional[str] = None
    requer_roles: Optional[List[SystemRole]] = None
    ativo: bool = True


class SSO_LoginRequest(BaseModel):
    """Request de login via SSO"""
    jwt_token: str
    redirect_url: Optional[str] = None
    sistema_destino: str


class SecurityAuditLog(BaseModel):
    """Log de auditoria de segurança"""
    evento: str
    usuario_id: Optional[Union[int, str]] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    sistema: str
    timestamp: datetime
    detalhes: Optional[Dict] = None
    sucesso: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }