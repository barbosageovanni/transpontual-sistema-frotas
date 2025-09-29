"""
JWT Handler unificado para sistemas Transpontual
Gerencia criação, verificação e validação de tokens JWT padronizados
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

from .schemas import (
    UserInfo,
    TokenPayload,
    PermissionClaim,
    SystemRole,
    AccessRestrictions,
    SecurityAuditLog
)

logger = logging.getLogger(__name__)


@dataclass
class JWTConfig:
    """Configuração do JWT"""
    secret: str = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))  # 24h default
    refresh_token_expire_days: int = 7
    issuer: str = "transpontual"
    audience: str = "transpontual"


class TranspontualJWTHandler:
    """Handler principal para JWT da Transpontual"""

    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()

    def create_access_token(
        self,
        user: UserInfo,
        roles: List[SystemRole],
        permissoes: PermissionClaim,
        restricoes: Optional[AccessRestrictions] = None,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None,
        sessao_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria token JWT padronizado
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)

        # Criar payload padronizado
        payload = TokenPayload(
            sub=str(user.id),  # JWT sub deve ser string
            user_info=user,    # Armazenar info completa em campo customizado
            exp=expire,
            iat=datetime.utcnow(),
            iss=self.config.issuer,
            aud=self.config.audience,
            roles=roles,
            permissoes=permissoes,
            restricoes=restricoes,
            sessao_id=sessao_id,
            ip_origem=ip_origem,
            user_agent=user_agent
        )

        try:
            # Converter para dict para JWT
            payload_dict = self._payload_to_dict(payload)

            encoded_jwt = jwt.encode(
                payload_dict,
                self.config.secret,
                algorithm=self.config.algorithm
            )

            # Log de criação de token
            self._log_security_event(
                "TOKEN_CREATED",
                user_id=str(user.id),
                email=user.email,
                sistema=user.sistema_origem,
                ip_address=ip_origem,
                user_agent=user_agent,
                sucesso=True,
                detalhes={"expires": expire.isoformat(), "roles": [r.value for r in roles]}
            )

            return encoded_jwt

        except Exception as e:
            logger.error(f"Erro ao criar token: {e}")

            self._log_security_event(
                "TOKEN_CREATION_FAILED",
                email=user.email if user else None,
                sistema=user.sistema_origem if user else "unknown",
                ip_address=ip_origem,
                sucesso=False,
                detalhes={"error": str(e)}
            )

            raise

    def verify_token(self, token: str, validate_restrictions: bool = True) -> Optional[TokenPayload]:
        """
        Verifica e decodifica token JWT
        """
        try:
            # Decodificar token
            payload_dict = jwt.decode(
                token,
                self.config.secret,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer
            )

            # Converter dict para TokenPayload
            payload = self._dict_to_payload(payload_dict)

            # Validar restrições se solicitado
            if validate_restrictions and payload.restricoes:
                if not self._validate_access_restrictions(payload.restricoes):
                    self._log_security_event(
                        "ACCESS_DENIED_RESTRICTIONS",
                        user_id=str(payload.sub.id),
                        email=payload.sub.email,
                        sistema=payload.sub.sistema_origem,
                        sucesso=False,
                        detalhes={"restricoes": payload.restricoes.dict() if payload.restricoes else None}
                    )
                    return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidAudienceError:
            logger.warning("Audience inválida no token")
            return None
        except jwt.InvalidIssuerError:
            logger.warning("Issuer inválido no token")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao verificar token: {e}")
            return None

    def create_user_payload(
        self,
        user_id: Union[int, str],
        email: str,
        nome: str,
        sistema_origem: str,
        roles: List[str],
        papel: Optional[str] = None,
        username: Optional[str] = None,
        ativo: bool = True,
        permissoes_custom: Optional[Dict] = None,
        restricoes: Optional[Dict] = None
    ) -> tuple[UserInfo, List[SystemRole], PermissionClaim, Optional[AccessRestrictions]]:
        """
        Cria payload de usuário padronizado a partir de dados básicos
        """
        # Criar UserInfo
        user_info = UserInfo(
            id=user_id,
            email=email,
            username=username or email.split('@')[0],
            nome=nome,
            papel=papel,
            ativo=ativo,
            sistema_origem=sistema_origem
        )

        # Converter roles para SystemRole
        system_roles = []
        for role in roles:
            try:
                if ':' not in role:
                    # Adicionar prefixo do sistema se não tiver
                    role = f"{sistema_origem}:{role}"
                system_roles.append(SystemRole(role))
            except ValueError:
                # Role customizada não mapeada
                logger.warning(f"Role não mapeada: {role}")

        # Criar permissões
        if permissoes_custom:
            permissoes = PermissionClaim(**permissoes_custom)
        else:
            # Permissões padrão baseadas no sistema de origem
            permissoes_dict = {}
            if sistema_origem == "frotas":
                permissoes_dict["frotas"] = {"menus": self._get_default_menus_frotas(roles)}
            elif sistema_origem == "baker":
                permissoes_dict["baker"] = {"menus": self._get_default_menus_baker(roles)}
            elif sistema_origem == "financeiro":
                permissoes_dict["financeiro"] = {"menus": self._get_default_menus_financeiro(roles)}

            permissoes = PermissionClaim(**permissoes_dict)

        # Criar restrições se fornecidas
        access_restrictions = None
        if restricoes:
            access_restrictions = AccessRestrictions(**restricoes)

        return user_info, system_roles, permissoes, access_restrictions

    def extract_user_from_payload(self, payload: TokenPayload) -> Dict[str, Any]:
        """
        Extrai informações do usuário do payload para uso nos sistemas
        """
        return {
            "id": payload.sub.id,
            "email": payload.sub.email,
            "username": payload.sub.username,
            "nome": payload.sub.nome,
            "papel": payload.sub.papel,
            "ativo": payload.sub.ativo,
            "sistema_origem": payload.sub.sistema_origem,
            "roles": [role.value for role in payload.roles],
            "permissoes": payload.permissoes.dict(),
            "restricoes": payload.restricoes.dict() if payload.restricoes else None,
            "exp": payload.exp,
            "iat": payload.iat
        }

    def _payload_to_dict(self, payload: TokenPayload) -> Dict[str, Any]:
        """Converte TokenPayload para dict para JWT"""
        payload_dict = {
            "sub": payload.sub,
            "user_info": payload.user_info.dict(),
            "exp": payload.exp,
            "iat": payload.iat,
            "iss": payload.iss,
            "aud": payload.aud,
            "roles": [role.value for role in payload.roles],
            "permissoes": payload.permissoes.dict(),
            "restricoes": payload.restricoes.dict() if payload.restricoes else None,
            "sessao_id": payload.sessao_id,
            "ip_origem": payload.ip_origem,
            "user_agent": payload.user_agent
        }
        return payload_dict

    def _dict_to_payload(self, payload_dict: Dict[str, Any]) -> TokenPayload:
        """Converte dict do JWT para TokenPayload"""
        # Converter user_info de volta para UserInfo
        user_info = UserInfo(**payload_dict["user_info"])

        # Converter roles de volta para SystemRole
        roles = [SystemRole(role) for role in payload_dict.get("roles", [])]

        # Converter permissões
        permissoes = PermissionClaim(**(payload_dict.get("permissoes") or {}))

        # Converter restrições
        restricoes = None
        if payload_dict.get("restricoes"):
            restricoes = AccessRestrictions(**payload_dict["restricoes"])

        return TokenPayload(
            sub=payload_dict["sub"],
            user_info=user_info,
            exp=datetime.fromtimestamp(payload_dict["exp"]),
            iat=datetime.fromtimestamp(payload_dict["iat"]),
            iss=payload_dict.get("iss", "transpontual"),
            aud=payload_dict.get("aud", "transpontual"),
            roles=roles,
            permissoes=permissoes,
            restricoes=restricoes,
            sessao_id=payload_dict.get("sessao_id"),
            ip_origem=payload_dict.get("ip_origem"),
            user_agent=payload_dict.get("user_agent")
        )

    def _validate_access_restrictions(self, restricoes: AccessRestrictions) -> bool:
        """Valida restrições de acesso"""
        if restricoes.bloqueado:
            logger.warning(f"Usuário bloqueado: {restricoes.motivo_bloqueio}")
            return False

        # Validar horário se definido
        if restricoes.horario_inicio and restricoes.horario_fim:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            if not (restricoes.horario_inicio <= current_time <= restricoes.horario_fim):
                logger.warning(f"Acesso fora do horário permitido: {current_time}")
                return False

        # Validar dias da semana se definido
        if restricoes.dias_semana:
            today = datetime.now().weekday()
            if today not in restricoes.dias_semana:
                logger.warning(f"Acesso negado para dia da semana: {today}")
                return False

        return True

    def _get_default_menus_frotas(self, roles: List[str]) -> List[str]:
        """Retorna menus padrão do sistema de frotas baseado em roles"""
        base_menus = ["dashboard"]

        if "admin" in roles or "gestor" in roles:
            return base_menus + ["veiculos", "motoristas", "checklist", "relatorios", "usuarios"]
        elif "operador" in roles:
            return base_menus + ["veiculos", "motoristas", "checklist"]
        else:
            return base_menus + ["checklist"]

    def _get_default_menus_baker(self, roles: List[str]) -> List[str]:
        """Retorna menus padrão do dashboard baker baseado em roles"""
        base_menus = ["dashboard"]

        if "admin" in roles:
            return base_menus + ["financeiro", "relatorios", "usuarios", "configuracoes"]
        elif "financeiro" in roles:
            return base_menus + ["financeiro", "relatorios"]
        else:
            return base_menus

    def _get_default_menus_financeiro(self, roles: List[str]) -> List[str]:
        """Retorna menus padrão do sistema financeiro baseado em roles"""
        base_menus = ["dashboard"]

        if "admin" in roles or "gestor" in roles:
            return base_menus + ["contas", "receitas", "despesas", "relatorios", "usuarios"]
        elif "operador" in roles:
            return base_menus + ["contas", "receitas", "despesas"]
        else:
            return base_menus

    def _log_security_event(
        self,
        evento: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        sistema: str = "unknown",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        sucesso: bool = True,
        detalhes: Optional[Dict] = None
    ):
        """Log de eventos de segurança"""
        log_entry = SecurityAuditLog(
            evento=evento,
            usuario_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            sistema=sistema,
            timestamp=datetime.utcnow(),
            detalhes=detalhes,
            sucesso=sucesso
        )

        logger.info(f"SECURITY_EVENT: {log_entry.dict()}")


# Instância global padrão
default_jwt_handler = TranspontualJWTHandler()

# Funções de conveniência
def create_access_token(
    user: UserInfo,
    roles: List[SystemRole],
    permissoes: PermissionClaim,
    restricoes: Optional[AccessRestrictions] = None,
    **kwargs
) -> str:
    """Função de conveniência para criar token"""
    return default_jwt_handler.create_access_token(
        user, roles, permissoes, restricoes, **kwargs
    )

def verify_token(token: str, validate_restrictions: bool = True) -> Optional[TokenPayload]:
    """Função de conveniência para verificar token"""
    return default_jwt_handler.verify_token(token, validate_restrictions)

def create_user_payload(*args, **kwargs):
    """Função de conveniência para criar payload de usuário"""
    return default_jwt_handler.create_user_payload(*args, **kwargs)

def extract_user_from_payload(payload: TokenPayload) -> Dict[str, Any]:
    """Função de conveniência para extrair usuário do payload"""
    return default_jwt_handler.extract_user_from_payload(payload)