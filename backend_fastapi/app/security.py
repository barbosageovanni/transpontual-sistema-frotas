import os, jwt
from datetime import datetime, timedelta, time
from passlib.context import CryptContext
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "120"))

def create_access_token(subject: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode = {"exp": expire, **subject}
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica bcrypt; em DEV aceita hash em texto puro (sem prefixo '$2')."""  # plain fallback
    try:
        if hashed.startswith("$2"):
            return pwd_context.verify(plain, hashed)
        # Fallback DEV: comparar texto puro (útil para seeds iniciais)
        return plain == hashed
    except Exception:
        return False

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

# Perfis de acesso predefinidos
PERFIS_PADRAO = {
    "admin": {
        "nome": "Administrador",
        "descricao": "Acesso total ao sistema",
        "permissoes": {
            "usuarios": ["visualizar", "criar", "editar", "excluir"],
            "veiculos": ["visualizar", "criar", "editar", "excluir"],
            "motoristas": ["visualizar", "criar", "editar", "excluir"],
            "checklists": ["visualizar", "criar", "editar", "excluir"],
            "abastecimentos": ["visualizar", "criar", "editar", "excluir"],
            "ordens_servico": ["visualizar", "criar", "editar", "excluir"],
            "financeiro": ["visualizar", "criar", "editar", "excluir"],
            "fiscal": ["visualizar", "criar", "editar", "excluir"],
            "relatorios": ["visualizar", "criar", "editar", "excluir"]
        }
    },
    "gestor": {
        "nome": "Gestor de Frota",
        "descricao": "Acesso à gestão de frota e relatórios",
        "permissoes": {
            "veiculos": ["visualizar", "criar", "editar"],
            "motoristas": ["visualizar", "criar", "editar"],
            "checklists": ["visualizar", "criar", "editar"],
            "abastecimentos": ["visualizar", "criar", "editar"],
            "ordens_servico": ["visualizar", "criar", "editar"],
            "relatorios": ["visualizar", "criar"]
        }
    },
    "fiscal": {
        "nome": "Responsável Fiscal",
        "descricao": "Acesso apenas aos documentos fiscais",
        "permissoes": {
            "fiscal": ["visualizar", "criar", "editar"],
            "veiculos": ["visualizar"],
            "relatorios": ["visualizar"]
        }
    },
    "financeiro": {
        "nome": "Responsável Financeiro",
        "descricao": "Acesso aos controles financeiros",
        "permissoes": {
            "financeiro": ["visualizar", "criar", "editar"],
            "abastecimentos": ["visualizar"],
            "ordens_servico": ["visualizar"],
            "relatorios": ["visualizar", "criar"]
        }
    },
    "operacional": {
        "nome": "Operacional",
        "descricao": "Acesso aos checklists e operações básicas",
        "permissoes": {
            "checklists": ["visualizar", "criar", "editar"],
            "veiculos": ["visualizar"],
            "motoristas": ["visualizar"]
        }
    },
    "estagiario": {
        "nome": "Estagiário",
        "descricao": "Acesso limitado e com restrições de horário",
        "permissoes": {
            "veiculos": ["visualizar"],
            "checklists": ["visualizar"],
            "relatorios": ["visualizar"]
        }
    }
}

def verificar_acesso_horario(usuario) -> bool:
    """Verifica se o usuário pode acessar no horário atual"""
    if not usuario.horario_inicio or not usuario.horario_fim:
        return True  # Sem restrição de horário

    agora = datetime.now().time()
    return usuario.horario_inicio <= agora <= usuario.horario_fim

def verificar_acesso_dia_semana(usuario) -> bool:
    """Verifica se o usuário pode acessar no dia da semana atual"""
    if not usuario.dias_semana:
        return True  # Sem restrição de dias

    hoje = datetime.now().weekday() + 1  # 1=segunda, 7=domingo
    dias_permitidos = [int(d.strip()) for d in usuario.dias_semana.split(',') if d.strip().isdigit()]
    return hoje in dias_permitidos

def verificar_acesso_ip(usuario, ip_cliente: str) -> bool:
    """Verifica se o IP do cliente está na lista de IPs permitidos"""
    if not usuario.ips_permitidos:
        return True  # Sem restrição de IP

    ips_permitidos = [ip.strip() for ip in usuario.ips_permitidos.split(',')]
    return ip_cliente in ips_permitidos

def verificar_data_validade(usuario) -> bool:
    """Verifica se o acesso do usuário ainda é válido"""
    if not usuario.data_validade:
        return True  # Sem restrição de data

    return datetime.now().date() <= usuario.data_validade

def verificar_usuario_bloqueado(usuario) -> bool:
    """Verifica se o usuário está bloqueado temporariamente"""
    if not usuario.bloqueado_ate:
        return False  # Não está bloqueado

    return datetime.now() < usuario.bloqueado_ate

def pode_acessar_sistema(usuario, ip_cliente: str) -> tuple[bool, str]:
    """
    Verifica todas as condições de acesso do usuário
    Retorna (pode_acessar, motivo_negacao)
    """
    if not usuario.ativo:
        return False, "Usuário inativo"

    if verificar_usuario_bloqueado(usuario):
        return False, "Usuário bloqueado temporariamente"

    if not verificar_data_validade(usuario):
        return False, "Acesso expirado"

    if not verificar_acesso_horario(usuario):
        return False, "Fora do horário permitido"

    if not verificar_acesso_dia_semana(usuario):
        return False, "Dia da semana não permitido"

    if not verificar_acesso_ip(usuario, ip_cliente):
        return False, "IP não autorizado"

    return True, ""

def verificar_permissao_modulo(usuario, modulo: str, acao: str, db: Session) -> bool:
    """
    Verifica se o usuário tem permissão para uma ação específica em um módulo
    """
    from app.models import UsuarioPermissao

    # Verificar permissões específicas do usuário
    permissao = db.query(UsuarioPermissao).filter(
        UsuarioPermissao.usuario_id == usuario.id,
        UsuarioPermissao.modulo == modulo,
        UsuarioPermissao.acao == acao
    ).first()

    if permissao:
        return permissao.permitido

    # Verificar permissões dos perfis do usuário
    for perfil in usuario.perfis:
        if perfil.ativo and perfil.permissoes:
            modulo_perms = perfil.permissoes.get(modulo, [])
            if acao in modulo_perms:
                return True

    # Verificar papel tradicional (compatibilidade)
    if usuario.papel in PERFIS_PADRAO:
        modulo_perms = PERFIS_PADRAO[usuario.papel]["permissoes"].get(modulo, [])
        return acao in modulo_perms

    return False

def registrar_tentativa_login(usuario, sucesso: bool, ip_cliente: str, motivo: str = "", db: Session = None):
    """Registra tentativa de login para auditoria"""
    if not db:
        return

    from app.models import LogAcesso

    log = LogAcesso(
        usuario_id=usuario.id if usuario else None,
        ip_acesso=ip_cliente,
        url_acessada="/login",
        metodo_http="POST",
        sucesso=sucesso,
        motivo_falha=motivo if not sucesso else None
    )

    db.add(log)

    # Atualizar tentativas de login falhadas
    if usuario and not sucesso:
        usuario.tentativas_login += 1
        # Bloquear após 5 tentativas por 30 minutos
        if usuario.tentativas_login >= 5:
            usuario.bloqueado_ate = datetime.now() + timedelta(minutes=30)
    elif usuario and sucesso:
        usuario.tentativas_login = 0
        usuario.ultimo_acesso = datetime.now()
        usuario.ultimo_ip = ip_cliente

    db.commit()

def criar_perfis_padrao(db: Session):
    """Cria os perfis de acesso padrão no banco de dados"""
    from app.models import PerfilAcesso

    for codigo, dados in PERFIS_PADRAO.items():
        perfil_existente = db.query(PerfilAcesso).filter(PerfilAcesso.nome == dados["nome"]).first()
        if not perfil_existente:
            perfil = PerfilAcesso(
                nome=dados["nome"],
                descricao=dados["descricao"],
                permissoes=dados["permissoes"]
            )
            db.add(perfil)

    db.commit()
