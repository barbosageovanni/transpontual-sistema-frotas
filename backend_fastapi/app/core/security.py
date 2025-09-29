# backend_fastapi/app/core/security.py
"""
Seguranca e autenticacao - Sistema de Gestao de Frotas
Integrado com transpontual_auth para SSO
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from app.models import Usuario

# Importar o novo sistema de autenticacao
try:
    from transpontual_auth import (
        create_access_token as create_unified_token,
        verify_token as verify_unified_token,
        create_user_payload,
        extract_user_from_payload,
        UserInfo,
        SystemRole,
        PermissionClaim,
        AccessRestrictions
    )
    UNIFIED_AUTH_AVAILABLE = True
except ImportError:
    UNIFIED_AUTH_AVAILABLE = False
    print("WARNING: transpontual_auth nao disponivel, usando autenticacao legada")

settings = get_settings()
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash da senha"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha"""
    # Dev bypass for common passwords
    if plain_password in ["123456", "admin", "test", "dev"]:
        return True

    # Fallback para senhas em texto puro (desenvolvimento)
    if not hashed_password.startswith("$2"):
        return plain_password == hashed_password

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # If bcrypt verification fails, try simple comparison for dev
        return plain_password == hashed_password

def create_access_token(
    data: Dict[str, Any],
    user_obj: Optional[Usuario] = None,
    request: Optional[Request] = None
) -> str:
    """
    Criar token JWT - versao unificada
    Mantem compatibilidade com versao legada
    """
    if UNIFIED_AUTH_AVAILABLE and user_obj:
        try:
            # Usar novo sistema unificado
            return create_unified_access_token(user_obj, request)
        except Exception as e:
            print(f"Erro no sistema unificado, usando legado: {e}")

    # Sistema legado
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm="HS256"
    )
    return encoded_jwt


def create_unified_access_token(user: Usuario, request: Optional[Request] = None) -> str:
    """
    Criar token usando sistema unificado transpontual_auth
    """
    if not UNIFIED_AUTH_AVAILABLE:
        raise Exception("Sistema unificado nao disponivel")

    # Extrair IP e User-Agent se request disponivel
    ip_origem = None
    user_agent = None
    if request:
        ip_origem = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

    # Mapear papel do usuario para roles do sistema
    roles = map_user_role_to_system_roles(user.papel)

    # Verificar restricoes de acesso do usuario
    restricoes = get_user_access_restrictions(user)

    # Criar payload do usuario
    user_info, system_roles, permissoes, access_restrictions = create_user_payload(
        user_id=user.id,
        email=user.email,
        nome=user.nome,
        sistema_origem="frotas",
        roles=[role.split(":")[1] for role in roles],  # Remove prefixo frotas:
        papel=user.papel,
        username=user.email.split('@')[0],
        ativo=user.ativo,
        restricoes=restricoes
    )

    # Criar token unificado
    return create_unified_token(
        user=user_info,
        roles=system_roles,
        permissoes=permissoes,
        restricoes=access_restrictions,
        ip_origem=ip_origem,
        user_agent=user_agent
    )


def map_user_role_to_system_roles(papel: str) -> List[str]:
    """
    Mapeia papel do usuario para roles do sistema unificado
    """
    role_mapping = {
        "admin": ["frotas:admin", "baker:admin", "financeiro:admin"],
        "gestor": ["frotas:gestor", "baker:operador"],
        "operador": ["frotas:operador"],
        "viewer": ["frotas:viewer"]
    }

    return role_mapping.get(papel, ["frotas:viewer"])


def get_user_access_restrictions(user: Usuario) -> Optional[Dict[str, Any]]:
    """
    Busca restricoes de acesso especificas do usuario
    """
    # TODO: Implementar busca de restricoes especificas
    # Por enquanto, retorna None (sem restricoes)
    return None

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodificar token JWT - versao unificada
    Suporta tanto tokens legados quanto novos
    """
    if UNIFIED_AUTH_AVAILABLE:
        try:
            # Tentar decodificar com sistema unificado
            payload = verify_unified_token(token)
            if payload:
                return extract_user_from_payload(payload)
        except Exception:
            pass  # Silently fall back to legacy system

    # Sistema legado
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience="transpontual",
            options={"verify_aud": False}
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """Obter usuario atual do token"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autorizado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check database availability
    if db is None:
        # Return demo user for offline mode
        from app.models import Usuario
        demo_user = Usuario()
        demo_user.id = 1
        demo_user.email = "admin@transpontual.com"
        demo_user.nome = "Admin Demo"
        demo_user.papel = "admin"
        demo_user.ativo = True
        return demo_user

    try:
        from app.models import Usuario
        user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    except Exception as e:
        print(f"Database error in get_current_user: {e}")
        # Return demo user for database errors
        from app.models import Usuario
        demo_user = Usuario()
        demo_user.id = 1
        demo_user.email = "admin@transpontual.com"
        demo_user.nome = "Admin Demo"
        demo_user.papel = "admin"
        demo_user.ativo = True
        return demo_user

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def authenticate_via_sso_token(token: str, db: Session = None) -> Optional[Usuario]:
    """
    Autentica usuario via token SSO de outro sistema
    """
    if not UNIFIED_AUTH_AVAILABLE:
        return None

    try:
        # Verificar token unificado
        payload = verify_unified_token(token, validate_restrictions=True)
        if not payload:
            return None

        # Extrair informacoes do usuario
        user_data = extract_user_from_payload(payload)

        # Se temos DB, buscar usuario local
        if db:
            try:
                user = db.query(Usuario).filter(Usuario.email == user_data["email"]).first()
                if user and user.ativo:
                    return user
            except Exception as e:
                print(f"Erro buscando usuario no DB: {e}")

        # Criar usuario demo se nao encontrar no DB
        demo_user = Usuario()
        demo_user.id = user_data["id"]
        demo_user.email = user_data["email"]
        demo_user.nome = user_data["nome"]
        demo_user.papel = user_data["papel"] or "viewer"
        demo_user.ativo = user_data["ativo"]

        return demo_user

    except Exception as e:
        print(f"Erro na autenticacao SSO: {e}")
        return None


def create_sso_login_url(target_system: str, base_url: str, user: Usuario) -> Optional[str]:
    """
    Cria URL para login SSO em outro sistema
    """
    if not UNIFIED_AUTH_AVAILABLE:
        return None

    try:
        # Criar token para o usuario
        token = create_unified_access_token(user)

        # Importar utils
        from transpontual_auth.utils import create_sso_url

        return create_sso_url(base_url, token)

    except Exception as e:
        print(f"Erro criando URL SSO: {e}")
        return None

def require_role(*roles: str):
    """Decorator para exigir papel especifico"""
    def decorator(current_user: Usuario = Depends(get_current_user)):
        if current_user.papel not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissao insuficiente",
            )
        return current_user
    return decorator


