"""
Decorators avançados para autenticação e autorização
"""
import functools
import requests
from flask import session, redirect, url_for, request, abort, flash, current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_current_user():
    """Obtém informações do usuário atual via API"""
    if 'access_token' not in session:
        return None

    try:
        response = requests.get(
            f"{current_app.config.get('API_BASE_URL', 'http://localhost:8051')}/api/v1/users/me",
            headers={'Authorization': f"Bearer {session['access_token']}"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Erro ao obter usuário atual: {e}")

    return None

def get_client_ip():
    """Obtém o IP real do cliente considerando proxies"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    else:
        return request.remote_addr

def advanced_login_required(f):
    """
    Decorator avançado para login com verificações de segurança
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se tem token
        if 'access_token' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))

        # Obter dados do usuário
        user = get_current_user()
        if not user:
            session.clear()
            flash('Sessão expirada. Faça login novamente.', 'warning')
            return redirect(url_for('login'))

        # Verificar se usuário está ativo
        if not user.get('ativo'):
            session.clear()
            flash('Sua conta está inativa. Contate o administrador.', 'error')
            return redirect(url_for('login'))

        # Verificar se usuário está bloqueado
        if user.get('bloqueado_ate'):
            try:
                bloqueado_ate = datetime.fromisoformat(user['bloqueado_ate'].replace('Z', '+00:00'))
                if datetime.now() < bloqueado_ate:
                    session.clear()
                    flash('Sua conta está temporariamente bloqueada.', 'error')
                    return redirect(url_for('login'))
            except Exception:
                pass

        # Verificar data de validade
        if user.get('data_validade'):
            try:
                data_validade = datetime.fromisoformat(user['data_validade']).date()
                if datetime.now().date() > data_validade:
                    session.clear()
                    flash('Seu acesso expirou. Contate o administrador.', 'error')
                    return redirect(url_for('login'))
            except Exception:
                pass

        # Verificar horário de acesso
        if user.get('horario_inicio') and user.get('horario_fim'):
            try:
                agora = datetime.now().time()
                inicio = datetime.strptime(user['horario_inicio'], '%H:%M:%S').time()
                fim = datetime.strptime(user['horario_fim'], '%H:%M:%S').time()

                if not (inicio <= agora <= fim):
                    flash('Acesso fora do horário permitido.', 'error')
                    return redirect(url_for('access_denied'))
            except Exception:
                pass

        # Verificar dias da semana
        if user.get('dias_semana'):
            try:
                hoje = datetime.now().weekday() + 1  # 1=segunda, 7=domingo
                dias_permitidos = [int(d.strip()) for d in user['dias_semana'].split(',') if d.strip().isdigit()]

                if hoje not in dias_permitidos:
                    flash('Acesso não permitido no dia da semana atual.', 'error')
                    return redirect(url_for('access_denied'))
            except Exception:
                pass

        # Verificar IP permitido
        if user.get('ips_permitidos'):
            try:
                ip_cliente = get_client_ip()
                ips_permitidos = [ip.strip() for ip in user['ips_permitidos'].split(',')]

                if ip_cliente not in ips_permitidos:
                    logger.warning(f"Tentativa de acesso de IP não autorizado: {ip_cliente} para usuário {user.get('email')}")
                    flash('Acesso negado: IP não autorizado.', 'error')
                    return redirect(url_for('access_denied'))
            except Exception:
                pass

        # Registrar atividade
        try:
            requests.post(
                f"{current_app.config.get('API_BASE_URL', 'http://localhost:8051')}/api/v1/users/activity",
                headers={'Authorization': f"Bearer {session['access_token']}"},
                json={
                    'url': request.url,
                    'method': request.method,
                    'ip': get_client_ip(),
                    'user_agent': request.headers.get('User-Agent', '')
                },
                timeout=2
            )
        except Exception:
            pass  # Não falhar se não conseguir registrar atividade

        return f(*args, **kwargs)

    return decorated_function

def permission_required(modulo, acao):
    """
    Decorator para verificar permissões específicas de módulo/ação

    Args:
        modulo (str): Nome do módulo (ex: 'veiculos', 'financeiro')
        acao (str): Ação requerida (ex: 'visualizar', 'criar', 'editar', 'excluir')
    """
    def decorator(f):
        @functools.wraps(f)
        @advanced_login_required
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                abort(401)

            # Verificar permissão via API
            try:
                response = requests.get(
                    f"{current_app.config.get('API_BASE_URL', 'http://localhost:8051')}/api/v1/users/permissions/{modulo}/{acao}",
                    headers={'Authorization': f"Bearer {session['access_token']}"},
                    timeout=5
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('permitido'):
                        return f(*args, **kwargs)

                # Permissão negada
                logger.warning(f"Acesso negado para usuário {user.get('email')} no módulo {modulo}, ação {acao}")
                flash(f'Você não tem permissão para {acao} em {modulo}.', 'error')
                return redirect(url_for('access_denied'))

            except Exception as e:
                logger.error(f"Erro ao verificar permissão: {e}")
                # Em caso de erro, negar acesso por segurança
                flash('Erro ao verificar permissões. Tente novamente.', 'error')
                return redirect(url_for('dashboard'))

        return decorated_function
    return decorator

def role_required_advanced(roles):
    """
    Decorator avançado para verificar papéis com fallback para o sistema antigo

    Args:
        roles (list): Lista de papéis permitidos
    """
    def decorator(f):
        @functools.wraps(f)
        @advanced_login_required
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                abort(401)

            user_role = user.get('papel')
            if user_role in roles:
                return f(*args, **kwargs)

            # Verificar se é admin (sempre tem acesso)
            if user_role == 'admin':
                return f(*args, **kwargs)

            logger.warning(f"Acesso negado para usuário {user.get('email')} com papel {user_role}, papéis necessários: {roles}")
            flash(f'Acesso negado. Papel necessário: {", ".join(roles)}', 'error')
            return redirect(url_for('access_denied'))

        return decorated_function
    return decorator

def admin_required(f):
    """Decorator que exige papel de administrador"""
    return role_required_advanced(['admin'])(f)

def log_user_action(acao, detalhes=None):
    """
    Decorator para logar ações importantes do usuário

    Args:
        acao (str): Descrição da ação
        detalhes (dict): Detalhes adicionais da ação
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            # Executar a função primeiro
            result = f(*args, **kwargs)

            # Registrar ação
            try:
                log_data = {
                    'acao': acao,
                    'url': request.url,
                    'method': request.method,
                    'ip': get_client_ip(),
                    'user_agent': request.headers.get('User-Agent', ''),
                    'detalhes': detalhes or {}
                }

                requests.post(
                    f"{current_app.config.get('API_BASE_URL', 'http://localhost:8051')}/api/v1/users/log-action",
                    headers={'Authorization': f"Bearer {session['access_token']}"},
                    json=log_data,
                    timeout=2
                )
            except Exception as e:
                logger.error(f"Erro ao registrar ação: {e}")

            return result

        return decorated_function
    return decorator

def session_required(f):
    """
    Decorator para verificar se a sessão é válida e não duplicada
    """
    @functools.wraps(f)
    @advanced_login_required
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            abort(401)

        # Verificar limite de sessões
        try:
            response = requests.get(
                f"{current_app.config.get('API_BASE_URL', 'http://localhost:8051')}/api/v1/users/session-check",
                headers={'Authorization': f"Bearer {session['access_token']}"},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get('valida'):
                    session.clear()
                    flash('Sua sessão foi invalidada. Faça login novamente.', 'warning')
                    return redirect(url_for('login'))

        except Exception as e:
            logger.error(f"Erro ao verificar sessão: {e}")

        return f(*args, **kwargs)

    return decorated_function