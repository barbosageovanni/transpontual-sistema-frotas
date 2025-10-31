# flask_dashboard/app/routes.py
from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash, jsonify
import requests
from datetime import datetime

bp = Blueprint("routes", __name__)

def api_url(path: str) -> str:
    base = current_app.config.get("API_BASE", "http://localhost:8005")
    return f"{base}{path}"

def make_api_request(method, path, **kwargs):
    """Helper para fazer requisições à API"""
    try:
        url = api_url(path)
        response = requests.request(method, url, timeout=30, **kwargs)
        if response.status_code >= 400:
            current_app.logger.error(f"API Error {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as e:
        current_app.logger.error(f"API Request failed: {str(e)}")
        return None

@bp.route("/")
def index():
    """Dashboard principal com KPIs"""
    try:
        # Buscar dados de saúde da API
        health = make_api_request('GET', '/health')
        if not health:
            health = {"status": "erro", "message": "API indisponível"}
        
        # Buscar KPIs de checklist dos últimos 30 dias
        kpis = make_api_request('GET', '/checklist/kpis?days=30')
        if not kpis:
            kpis = {
                "estatisticas_gerais": {
                    "total_checklists": 0,
                    "aprovados": 0,
                    "reprovados": 0,
                    "taxa_aprovacao": 0
                }
            }
        
        return render_template("dashboard.html", 
                             health=health, 
                             kpis=kpis)
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard: {str(e)}")
        return render_template("dashboard.html", 
                             health={"status": "erro"}, 
                             kpis={}, 
                             error=str(e))

@bp.route("/models")
def models():
    """Lista de modelos de checklist"""
    try:
        modelos = make_api_request('GET', '/checklist/modelos')
        if not modelos:
            modelos = []
            flash("Erro ao carregar modelos da API", "warning")
        
        return render_template("models.html", modelos=modelos)
        
    except Exception as e:
        flash(f"Erro interno: {str(e)}", "danger")
        return render_template("models.html", modelos=[])

@bp.route("/start", methods=["GET", "POST"])
def start():
    """Iniciar novo checklist (redireciona para nova interface)"""
    return redirect(url_for('checklist.new_checklist'))

# ==============================
# GESTÃO DE MOTORISTAS
# ==============================

@bp.route("/drivers")
def drivers_list():
    """Listar motoristas"""
    try:
        motoristas = make_api_request('GET', '/drivers')
        if not motoristas:
            motoristas = []
            flash("Erro ao carregar motoristas da API", "warning")
        
        return render_template("drivers/list.html", motoristas=motoristas)
        
    except Exception as e:
        flash(f"Erro interno: {str(e)}", "danger")
        return render_template("drivers/list.html", motoristas=[])

@bp.route("/drivers/new", methods=["GET", "POST"])
def driver_new():
    """Cadastrar novo motorista"""
    if request.method == "POST":
        try:
            # Handle JSON (AJAX) requests
            if request.is_json:
                json_data = request.get_json()
                current_app.logger.info(f"Received driver data: {json_data}")

                if not json_data or not json_data.get('nome'):
                    return jsonify({'message': 'Nome é obrigatório'}), 400

                # Prepare data for API
                driver_data = {
                    'nome': json_data['nome'],
                    'email': json_data.get('email', ''),
                    'senha': json_data.get('senha', ''),
                    'cnh': json_data.get('cnh', ''),
                    'categoria': json_data.get('categoria'),
                    'validade_cnh': json_data.get('validade_cnh'),
                    'ativo': json_data.get('ativo', True),
                    'observacoes': json_data.get('observacoes', '')
                }

                # Remove empty values
                driver_data = {k: v for k, v in driver_data.items() if v not in ['', None]}

                current_app.logger.info(f"Sending to API: {driver_data}")
                response = make_api_request('POST', '/drivers', json=driver_data)
                current_app.logger.info(f"API response: {response}")

                if response:
                    return jsonify({'message': 'Motorista cadastrado com sucesso!', 'motorista': response})
                else:
                    return jsonify({'message': 'Erro ao cadastrar motorista na API'}), 500
            
            # Handle form submissions
            else:
                driver_data = {
                    'nome': request.form['nome'],
                    'email': request.form.get('email', ''),
                    'senha': request.form.get('senha', ''),
                    'cnh': request.form.get('cnh', ''),
                    'categoria': request.form.get('categoria'),
                    'validade_cnh': request.form.get('validade_cnh'),
                    'ativo': request.form.get('ativo', 'true') == 'true',
                    'observacoes': request.form.get('observacoes', '')
                }

                # Remove empty values
                driver_data = {k: v for k, v in driver_data.items() if v not in ['', None]}

                response = make_api_request('POST', '/drivers', json=driver_data)
                if response:
                    flash('Motorista cadastrado com sucesso!', 'success')
                    return redirect(url_for('main.drivers_list'))
                else:
                    flash('Erro ao cadastrar motorista', 'danger')

        except Exception as e:
            current_app.logger.error(f"Error in driver_new: {str(e)}")
            if request.is_json:
                return jsonify({'message': f'Erro interno: {str(e)}'}), 500
            else:
                flash(f'Erro interno: {str(e)}', 'danger')

    return render_template('drivers/form.html', motorista=None)

@bp.route("/drivers/<int:driver_id>", methods=["PUT"])
def drivers_update(driver_id):
    """Atualizar motorista via AJAX"""
    try:
        if not request.is_json:
            return jsonify({'message': 'Content-Type deve ser application/json'}), 400

        json_data = request.get_json()
        current_app.logger.info(f"Updating driver {driver_id}: {json_data}")

        driver_data = {
            'nome': json_data.get('nome'),
            'cnh': json_data.get('cnh'),
            'categoria': json_data.get('categoria'),
            'validade_cnh': json_data.get('validade_cnh'),
            'email': json_data.get('email'),
            'ativo': json_data.get('ativo', True),
            'observacoes': json_data.get('observacoes', '')
        }

        # Remove empty values
        driver_data = {k: v for k, v in driver_data.items() if v not in ['', None]}

        response = make_api_request('PUT', f'/drivers/{driver_id}', json=driver_data)
        
        if response:
            return jsonify({'message': 'Motorista atualizado com sucesso!', 'motorista': response})
        else:
            return jsonify({'message': 'Erro ao atualizar motorista na API'}), 500

    except Exception as e:
        current_app.logger.error(f"Error updating driver {driver_id}: {str(e)}")
        return jsonify({'message': f'Erro interno: {str(e)}'}), 500

@bp.route("/drivers/<int:driver_id>/edit")
def driver_edit(driver_id):
    """Formulário para editar motorista"""
    try:
        motorista = make_api_request('GET', f'/drivers/{driver_id}')
        if not motorista:
            flash('Motorista não encontrado', 'warning')
            return redirect(url_for('main.drivers_list'))
        
        return render_template('drivers/form.html', motorista=motorista)
        
    except Exception as e:
        flash(f'Erro ao carregar motorista: {str(e)}', 'danger')
        return redirect(url_for('main.drivers_list'))

# ==============================
# GESTÃO DE FORNECEDORES
# ==============================

@bp.route("/fornecedores")
def fornecedores_list():
    """Listar fornecedores"""
    try:
        fornecedores = make_api_request('GET', '/fornecedores')
        if not fornecedores:
            fornecedores = []
            flash("Erro ao carregar fornecedores da API", "warning")

        return render_template("fornecedores/list.html", fornecedores=fornecedores)

    except Exception as e:
        flash(f"Erro interno: {str(e)}", "danger")
        return render_template("fornecedores/list.html", fornecedores=[])

@bp.route("/fornecedores/new", methods=["GET", "POST"])
def fornecedor_new():
    """Cadastrar novo fornecedor"""
    if request.method == "POST":
        try:
            # Handle JSON (AJAX) requests
            if request.is_json:
                json_data = request.get_json()
                current_app.logger.info(f"Received fornecedor data: {json_data}")

                if not json_data or not json_data.get('nome'):
                    return jsonify({'message': 'Nome é obrigatório'}), 400

                # Prepare data for API
                fornecedor_data = {
                    'nome': json_data['nome'],
                    'tipo': json_data.get('tipo', 'posto'),
                    'cnpj': json_data.get('cnpj', ''),
                    'inscricao_estadual': json_data.get('inscricao_estadual', ''),
                    'telefone': json_data.get('telefone', ''),
                    'email': json_data.get('email', ''),
                    'cep': json_data.get('cep', ''),
                    'endereco': json_data.get('endereco', ''),
                    'numero': json_data.get('numero', ''),
                    'complemento': json_data.get('complemento', ''),
                    'bairro': json_data.get('bairro', ''),
                    'cidade': json_data.get('cidade', ''),
                    'estado': json_data.get('estado', ''),
                    'banco': json_data.get('banco', ''),
                    'agencia': json_data.get('agencia', ''),
                    'conta': json_data.get('conta', ''),
                    'contato_nome': json_data.get('contato_nome', ''),
                    'contato_telefone': json_data.get('contato_telefone', ''),
                    'observacoes': json_data.get('observacoes', ''),
                    'ativo': json_data.get('ativo', True)
                }

                # Remove empty values
                fornecedor_data = {k: v for k, v in fornecedor_data.items() if v not in ['', None]}

                current_app.logger.info(f"Sending to API: {fornecedor_data}")
                response = make_api_request('POST', '/fornecedores', json=fornecedor_data)
                current_app.logger.info(f"API response: {response}")

                if response:
                    return jsonify({'message': 'Fornecedor cadastrado com sucesso!', 'fornecedor': response})
                else:
                    return jsonify({'message': 'Erro ao cadastrar fornecedor na API'}), 500

            # Handle form submissions
            else:
                fornecedor_data = {
                    'nome': request.form['nome'],
                    'tipo': request.form.get('tipo', 'posto'),
                    'cnpj': request.form.get('cnpj', ''),
                    'inscricao_estadual': request.form.get('inscricao_estadual', ''),
                    'telefone': request.form.get('telefone', ''),
                    'email': request.form.get('email', ''),
                    'cep': request.form.get('cep', ''),
                    'endereco': request.form.get('endereco', ''),
                    'numero': request.form.get('numero', ''),
                    'complemento': request.form.get('complemento', ''),
                    'bairro': request.form.get('bairro', ''),
                    'cidade': request.form.get('cidade', ''),
                    'estado': request.form.get('estado', ''),
                    'banco': request.form.get('banco', ''),
                    'agencia': request.form.get('agencia', ''),
                    'conta': request.form.get('conta', ''),
                    'contato_nome': request.form.get('contato_nome', ''),
                    'contato_telefone': request.form.get('contato_telefone', ''),
                    'observacoes': request.form.get('observacoes', ''),
                    'ativo': request.form.get('ativo', 'true') == 'true'
                }

                # Remove empty values
                fornecedor_data = {k: v for k, v in fornecedor_data.items() if v not in ['', None]}

                response = make_api_request('POST', '/fornecedores', json=fornecedor_data)
                if response:
                    flash('Fornecedor cadastrado com sucesso!', 'success')
                    return redirect(url_for('routes.fornecedores_list'))
                else:
                    flash('Erro ao cadastrar fornecedor', 'danger')

        except Exception as e:
            current_app.logger.error(f"Error in fornecedor_new: {str(e)}")
            if request.is_json:
                return jsonify({'message': f'Erro interno: {str(e)}'}), 500
            else:
                flash(f'Erro interno: {str(e)}', 'danger')

    return render_template('fornecedores/form.html', fornecedor=None)

@bp.route("/fornecedores/<int:fornecedor_id>", methods=["PUT"])
def fornecedor_update(fornecedor_id):
    """Atualizar fornecedor via AJAX"""
    try:
        if not request.is_json:
            return jsonify({'message': 'Content-Type deve ser application/json'}), 400

        json_data = request.get_json()
        current_app.logger.info(f"Updating fornecedor {fornecedor_id}: {json_data}")

        fornecedor_data = {
            'nome': json_data.get('nome'),
            'tipo': json_data.get('tipo'),
            'cnpj': json_data.get('cnpj'),
            'inscricao_estadual': json_data.get('inscricao_estadual'),
            'telefone': json_data.get('telefone'),
            'email': json_data.get('email'),
            'cep': json_data.get('cep'),
            'endereco': json_data.get('endereco'),
            'numero': json_data.get('numero'),
            'complemento': json_data.get('complemento'),
            'bairro': json_data.get('bairro'),
            'cidade': json_data.get('cidade'),
            'estado': json_data.get('estado'),
            'banco': json_data.get('banco'),
            'agencia': json_data.get('agencia'),
            'conta': json_data.get('conta'),
            'contato_nome': json_data.get('contato_nome'),
            'contato_telefone': json_data.get('contato_telefone'),
            'observacoes': json_data.get('observacoes'),
            'ativo': json_data.get('ativo', True)
        }

        # Remove empty values
        fornecedor_data = {k: v for k, v in fornecedor_data.items() if v not in ['', None]}

        response = make_api_request('PUT', f'/fornecedores/{fornecedor_id}', json=fornecedor_data)

        if response:
            return jsonify({'message': 'Fornecedor atualizado com sucesso!', 'fornecedor': response})
        else:
            return jsonify({'message': 'Erro ao atualizar fornecedor na API'}), 500

    except Exception as e:
        current_app.logger.error(f"Error updating fornecedor {fornecedor_id}: {str(e)}")
        return jsonify({'message': f'Erro interno: {str(e)}'}), 500

@bp.route("/fornecedores/<int:fornecedor_id>/edit")
def fornecedor_edit(fornecedor_id):
    """Formulário para editar fornecedor"""
    try:
        fornecedor = make_api_request('GET', f'/fornecedores/{fornecedor_id}')
        if not fornecedor:
            flash('Fornecedor não encontrado', 'warning')
            return redirect(url_for('routes.fornecedores_list'))

        return render_template('fornecedores/form.html', fornecedor=fornecedor)

    except Exception as e:
        flash(f'Erro ao carregar fornecedor: {str(e)}', 'danger')
        return redirect(url_for('routes.fornecedores_list'))

# ==============================
# API ENDPOINTS
# ==============================

@bp.route("/api/health")
def api_health():
    """Proxy para health check da API"""
    health = make_api_request('GET', '/health')
    return jsonify(health or {"status": "error"})

@bp.route("/api/kpis")
def api_kpis():
    """Proxy para KPIs da API"""
    days = request.args.get('days', 30, type=int)
    kpis = make_api_request('GET', f'/checklist/kpis?days={days}')
    return jsonify(kpis or {})

# ==============================
# REDIRECIONAMENTOS
# ==============================

@bp.route("/billing")
def billing_redirect():
    """Redireciona para o sistema de faturamento dashboard_baker"""
    return redirect("http://localhost:5000/")

@bp.route("/financial")
def financial_redirect():
    """Redireciona para o sistema de faturamento dashboard_baker"""
    return redirect("http://localhost:5000/")