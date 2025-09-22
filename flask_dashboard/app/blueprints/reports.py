# flask_dashboard/app/blueprints/reports.py
"""
Blueprint para relatórios
"""
from flask import Blueprint, render_template, request, make_response, current_app
import csv
from io import StringIO
import requests
from datetime import datetime, timedelta

bp = Blueprint("reports", __name__)

def make_api_request(method, path, **kwargs):
    """Helper para fazer requisições à API"""
    try:
        base = current_app.config.get("API_BASE", "http://localhost:8005")
        url = f"{base}{path}"
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
    """Página de relatórios"""
    return render_template("reports/index.html")

@bp.route("/performance")
def performance():
    """Relatório de performance"""
    # Dados simulados
    data = [
        {"motorista": "João Silva", "checklists": 25, "taxa_aprovacao": 92.0},
        {"motorista": "Maria Santos", "checklists": 30, "taxa_aprovacao": 87.5},
        {"motorista": "Carlos Lima", "checklists": 20, "taxa_aprovacao": 95.0}
    ]
    
    return render_template("reports/performance.html", data=data)

@bp.route("/abastecimentos")
def abastecimentos():
    """Relatório de abastecimentos"""
    # Parâmetros de filtro
    veiculo_id = request.args.get('veiculo_id', type=int)
    motorista_id = request.args.get('motorista_id', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    # Se não há filtro de data, usar últimos 30 dias
    if not data_inicio and not data_fim:
        data_fim = datetime.now().strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Montar parâmetros da API
    params = {}
    if veiculo_id:
        params['veiculo_id'] = veiculo_id
    if motorista_id:
        params['motorista_id'] = motorista_id
    if data_inicio:
        params['data_inicio'] = data_inicio
    if data_fim:
        params['data_fim'] = data_fim

    # Buscar dados da API
    abastecimentos = make_api_request('GET', '/api/v1/abastecimentos', params=params) or []

    # Buscar dados para filtros
    veiculos = make_api_request('GET', '/api/v1/vehicles') or []
    motoristas = make_api_request('GET', '/api/v1/drivers') or []

    # Calcular estatísticas
    total_abastecimentos = len(abastecimentos)
    total_litros = sum(float(a.get('litros', 0)) for a in abastecimentos)
    total_valor = sum(float(a.get('valor_total', 0)) for a in abastecimentos)
    media_preco_litro = total_valor / total_litros if total_litros > 0 else 0

    # Agrupar por veículo
    por_veiculo = {}
    for abastecimento in abastecimentos:
        veiculo = abastecimento.get('veiculo', {})
        placa = veiculo.get('placa', 'N/A')

        if placa not in por_veiculo:
            por_veiculo[placa] = {
                'veiculo': veiculo,
                'total_litros': 0,
                'total_valor': 0,
                'total_abastecimentos': 0
            }

        por_veiculo[placa]['total_litros'] += float(abastecimento.get('litros', 0))
        por_veiculo[placa]['total_valor'] += float(abastecimento.get('valor_total', 0))
        por_veiculo[placa]['total_abastecimentos'] += 1

    # Agrupar por mês
    por_mes = {}
    for abastecimento in abastecimentos:
        data_str = abastecimento.get('data_abastecimento', '')
        if data_str:
            try:
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                mes_key = data.strftime('%Y-%m')

                if mes_key not in por_mes:
                    por_mes[mes_key] = {
                        'mes': data.strftime('%B %Y'),
                        'total_litros': 0,
                        'total_valor': 0,
                        'total_abastecimentos': 0
                    }

                por_mes[mes_key]['total_litros'] += float(abastecimento.get('litros', 0))
                por_mes[mes_key]['total_valor'] += float(abastecimento.get('valor_total', 0))
                por_mes[mes_key]['total_abastecimentos'] += 1
            except:
                pass

    estatisticas = {
        'total_abastecimentos': total_abastecimentos,
        'total_litros': total_litros,
        'total_valor': total_valor,
        'media_preco_litro': media_preco_litro,
        'por_veiculo': list(por_veiculo.values()),
        'por_mes': list(por_mes.values())
    }

    return render_template('reports/abastecimentos.html',
                         abastecimentos=abastecimentos,
                         veiculos=veiculos,
                         motoristas=motoristas,
                         estatisticas=estatisticas,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@bp.route("/abastecimentos/export/csv")
def export_abastecimentos_csv():
    """Exportar relatório de abastecimentos para CSV"""
    # Parâmetros de filtro (mesmo que o relatório)
    veiculo_id = request.args.get('veiculo_id', type=int)
    motorista_id = request.args.get('motorista_id', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    # Montar parâmetros da API
    params = {}
    if veiculo_id:
        params['veiculo_id'] = veiculo_id
    if motorista_id:
        params['motorista_id'] = motorista_id
    if data_inicio:
        params['data_inicio'] = data_inicio
    if data_fim:
        params['data_fim'] = data_fim

    abastecimentos = make_api_request('GET', '/api/v1/abastecimentos', params=params) or []

    output = StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "Data", "Veículo", "Placa", "Motorista", "Posto",
        "Odômetro", "Litros", "Valor/Litro", "Valor Total",
        "Tipo Combustível", "Observações"
    ])

    # Dados
    for abastecimento in abastecimentos:
        veiculo = abastecimento.get('veiculo', {})
        motorista = abastecimento.get('motorista', {})

        data_formatted = ""
        if abastecimento.get('data_abastecimento'):
            try:
                data = datetime.fromisoformat(abastecimento['data_abastecimento'].replace('Z', '+00:00'))
                data_formatted = data.strftime('%d/%m/%Y %H:%M')
            except:
                data_formatted = abastecimento.get('data_abastecimento', '')

        writer.writerow([
            data_formatted,
            f"{veiculo.get('marca', '')} {veiculo.get('modelo', '')}".strip(),
            veiculo.get('placa', ''),
            motorista.get('nome', ''),
            abastecimento.get('posto', ''),
            abastecimento.get('odometro', ''),
            abastecimento.get('litros', ''),
            abastecimento.get('valor_litro', ''),
            abastecimento.get('valor_total', ''),
            abastecimento.get('tipo_combustivel', ''),
            abastecimento.get('observacoes', '')
        ])

    filename = f"relatorio_abastecimentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"

    return response

@bp.route("/export/csv")
def export_csv():
    """Exportar dados para CSV"""
    output = StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow(["Motorista", "Checklists", "Taxa Aprovação"])

    # Dados simulados
    writer.writerow(["João Silva", "25", "92.0"])
    writer.writerow(["Maria Santos", "30", "87.5"])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=performance.csv"
    response.headers["Content-type"] = "text/csv"

    return response

