"""
Utilitários compartilhados para autenticação Transpontual
"""

import os
import hashlib
import secrets
from typing import Dict, Optional, List
from urllib.parse import urlencode, urlparse, parse_qs


def generate_session_id() -> str:
    """Gera ID de sessão único"""
    return secrets.token_urlsafe(32)


def hash_ip_for_logging(ip: str) -> str:
    """Hash do IP para logs de segurança (LGPD compliance)"""
    if not ip:
        return "unknown"

    salt = os.getenv("IP_HASH_SALT", "transpontual-salt")
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:16]


def create_sso_url(
    base_url: str,
    jwt_token: str,
    redirect_path: Optional[str] = None,
    extra_params: Optional[Dict[str, str]] = None
) -> str:
    """
    Cria URL para SSO com token JWT
    """
    params = {"jwt_token": jwt_token}

    if redirect_path:
        params["redirect"] = redirect_path

    if extra_params:
        params.update(extra_params)

    query_string = urlencode(params)
    separator = "&" if "?" in base_url else "?"

    return f"{base_url}{separator}{query_string}"


def extract_token_from_url(url: str) -> Optional[str]:
    """
    Extrai token JWT de uma URL
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    jwt_tokens = query_params.get("jwt_token", [])
    return jwt_tokens[0] if jwt_tokens else None


def get_system_urls() -> Dict[str, str]:
    """
    Retorna URLs dos sistemas da Transpontual
    """
    return {
        "frotas_api": os.getenv("FROTAS_API_URL", "http://localhost:8005"),
        "frotas_dashboard": os.getenv("FROTAS_DASHBOARD_URL", "http://localhost:8050"),
        "baker_dashboard": os.getenv("BAKER_DASHBOARD_URL", "http://localhost:5000"),
        "financial_api": os.getenv("FINANCIAL_API_URL", "http://localhost:8001"),
        "financial_dashboard": os.getenv("FINANCIAL_DASHBOARD_URL", "http://localhost:3000")
    }


def create_navigation_links(user_roles: List[str]) -> List[Dict[str, str]]:
    """
    Cria links de navegação baseados nas roles do usuário
    """
    links = []
    urls = get_system_urls()

    # Link para Sistema de Frotas
    if any(role.startswith("frotas:") for role in user_roles):
        links.append({
            "name": "Sistema de Frotas",
            "description": "Gestão de veículos e motoristas",
            "url": urls["frotas_dashboard"],
            "icon": "truck",
            "system": "frotas"
        })

    # Link para Dashboard Baker
    if any(role.startswith("baker:") for role in user_roles):
        links.append({
            "name": "Dashboard Baker",
            "description": "Painel administrativo e financeiro",
            "url": urls["baker_dashboard"],
            "icon": "dashboard",
            "system": "baker"
        })

    # Link para Sistema Financeiro
    if any(role.startswith("financeiro:") for role in user_roles):
        links.append({
            "name": "Sistema Financeiro",
            "description": "Gestão financeira e contábil",
            "url": urls["financial_dashboard"],
            "icon": "attach_money",
            "system": "financeiro"
        })

    return links


def validate_origin_system(token_payload: Dict, expected_system: str) -> bool:
    """
    Valida se o token veio do sistema esperado
    """
    if not token_payload or not token_payload.get("sub"):
        return False

    user_info = token_payload["sub"]
    return user_info.get("sistema_origem") == expected_system


def get_user_friendly_role(role: str) -> str:
    """
    Converte role técnica para nome amigável
    """
    role_map = {
        "frotas:admin": "Administrador de Frotas",
        "frotas:gestor": "Gestor de Frotas",
        "frotas:operador": "Operador de Frotas",
        "frotas:viewer": "Visualizador de Frotas",
        "baker:admin": "Administrador Baker",
        "baker:financeiro": "Financeiro Baker",
        "baker:operador": "Operador Baker",
        "baker:viewer": "Visualizador Baker",
        "financeiro:admin": "Administrador Financeiro",
        "financeiro:gestor": "Gestor Financeiro",
        "financeiro:operador": "Operador Financeiro",
        "financeiro:viewer": "Visualizador Financeiro"
    }

    return role_map.get(role, role)


def check_system_availability(system_url: str, timeout: int = 3) -> bool:
    """
    Verifica se um sistema está disponível
    """
    try:
        import requests

        # Tenta algumas rotas comuns
        test_paths = ["/health", "/docs", "/"]

        for path in test_paths:
            try:
                url = f"{system_url.rstrip('/')}{path}"
                response = requests.get(url, timeout=timeout)
                if response.status_code in [200, 404]:  # 404 também indica que está rodando
                    return True
            except:
                continue

        return False
    except ImportError:
        # requests não disponível
        return True  # Assume disponível
    except Exception:
        return False


def log_cross_system_navigation(
    user_id: str,
    from_system: str,
    to_system: str,
    success: bool,
    details: Optional[Dict] = None
):
    """
    Log de navegação entre sistemas
    """
    import logging
    logger = logging.getLogger(__name__)

    log_data = {
        "event": "CROSS_SYSTEM_NAVIGATION",
        "user_id": user_id,
        "from_system": from_system,
        "to_system": to_system,
        "success": success,
        "details": details or {}
    }

    logger.info(f"SSO_NAV: {log_data}")


def sanitize_redirect_url(url: str, allowed_domains: List[str]) -> Optional[str]:
    """
    Sanitiza URL de redirect para prevenir ataques
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)

        # Só permite URLs relativas ou de domínios permitidos
        if not parsed.netloc:  # URL relativa
            return url

        # Verifica se o domínio está na lista permitida
        for allowed_domain in allowed_domains:
            if parsed.netloc.endswith(allowed_domain):
                return url

        return None
    except Exception:
        return None


def create_cross_system_menu(user_roles: List[str], current_system: str) -> List[Dict]:
    """
    Cria menu para navegação entre sistemas
    """
    all_links = create_navigation_links(user_roles)

    # Remove o sistema atual do menu
    cross_system_links = [
        link for link in all_links
        if link["system"] != current_system
    ]

    return cross_system_links