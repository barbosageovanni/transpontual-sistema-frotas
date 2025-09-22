# flask_dashboard/app/blueprints/checklist_detail.py
"""
Página de detalhes do checklist
"""
from flask import Blueprint, render_template_string, request, current_app, redirect, url_for, flash
import requests
from datetime import datetime

bp = Blueprint("checklist_detail", __name__)

def api_url(path: str) -> str:
    """Helper para URL da API"""
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

# Template para detalhes do checklist
CHECKLIST_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checklist #{{ checklist.id }} - Transpontual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        .checklist-header { 
            background: linear-gradient(135deg, #007bff, #0056b3); 
            color: white; 
            padding: 2rem 0; 
        }
        .status-badge { font-size: 1rem; padding: 0.5rem 1rem; }
        .item-row { border-left: 4px solid #dee2e6; margin-bottom: 0.5rem; padding: 1rem; }
        .item-row.ok { border-left-color: #28a745; background-color: #f8fffa; }
        .item-row.nao_ok { border-left-color: #dc3545; background-color: #fff5f5; }
        .item-row.na { border-left-color: #6c757d; background-color: #f8f9fa; }
        .severity-badge { font-size: 0.75rem; }
        .timeline-item { 
            border-left: 2px solid #dee2e6; 
            padding-left: 1rem; 
            margin-left: 1rem; 
            padding-bottom: 1rem; 
        }
        .timeline-item:last-child { border-left-color: transparent; }
        .timeline-icon { 
            background: white; 
            border: 2px solid #dee2e6; 
            border-radius: 50%; 
            width: 2rem; 
            height: 2rem; 
            margin-left: -1.5rem; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .info-card { border-radius: 15px; }
        .signature-display { 
            background: #f8f9fa; 
            border: 2px dashed #dee2e6; 
            border-radius: 10px; 
            padding: 2rem; 
            text-align: center; 
        }
        @media print {
            .no-print { display: none !important; }
            .checklist-header { background: #007bff !important; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="checklist-header no-print">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="h3 mb-1">
                        <i class="bi bi-clipboard-check me-2"></i>
                        Checklist #{{ checklist.id }}
                    </h1>
                    <p class="mb-0 opacity-75">
                        Detalhes completos e histórico de execução
                    </p>
                </div>
                <div class="col-md-4 text-end">
                    <div class="btn-group">
                        <a href="/checklist" class="btn btn-light btn-sm">
                            <i class="bi bi-arrow-left"></i> Voltar
                        </a>
                        <button class="btn btn-outline-light btn-sm" onclick="window.print()">
                            <i class="bi bi-printer"></i> Imprimir
                        </button>
                        <button class="btn btn-outline-light btn-sm" onclick="exportPDF()">
                            <i class="bi bi-file-pdf"></i> PDF
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container mt-4">
        <!-- Informações Gerais -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="card info-card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-info-circle me-2"></i>Informações do Checklist
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <table class="table table-borderless table-sm">
                                    <tr>
                                        <td><strong>ID:</strong></td>
                                        <td>#{{ checklist.id }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Tipo:</strong></td>
                                        <td>
                                            <span class="badge bg-{{ 'primary' if checklist.tipo == 'pre' else 'info' if checklist.tipo == 'pos' else 'warning' }}">
                                                {{ checklist.tipo.upper() }}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td><strong>Status:</strong></td>
                                        <td>
                                            {% if checklist.status == 'aprovado' %}
                                                <span class="badge bg-success status-badge">
                                                    <i class="bi bi-check-circle me-1"></i>APROVADO
                                                </span>
                                            {% elif checklist.status == 'reprovado' %}
                                                <span class="badge bg-danger status-badge">
                                                    <i class="bi bi-x-circle me-1"></i>REPROVADO
                                                </span>
                                            {% else %}
                                                <span class="badge bg-warning status-badge">
                                                    <i class="bi bi-clock me-1"></i>PENDENTE
                                                </span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td><strong>Veículo:</strong></td>
                                        <td>{{ veiculo_info.placa or ('ID ' + checklist.veiculo_id|string) }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Motorista:</strong></td>
                                        <td>{{ motorista_info.nome or ('ID ' + checklist.motorista_id|string) }}</td>
                                    </tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <table class="table table-borderless table-sm">
                                    <tr>
                                        <td><strong>Iniciado em:</strong></td>
                                        <td>{{ checklist.dt_inicio[:16].replace('T', ' ') if checklist.dt_inicio else '-' }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Finalizado em:</strong></td>
                                        <td>{{ checklist.dt_fim[:16].replace('T', ' ') if checklist.dt_fim else 'Em andamento' }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Duração:</strong></td>
                                        <td>
                                            {% if duracao_minutos %}
                                                {{ duracao_minutos }} minutos
                                            {% else %}
                                                <span class="text-muted">Em andamento</span>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td><strong>Odômetro Inicial:</strong></td>
                                        <td>{{ "{:,}".format(checklist.odometro_ini).replace(',', '.') if checklist.odometro_ini else '-' }} km</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Odômetro Final:</strong></td>
                                        <td>{{ "{:,}".format(checklist.odometro_fim).replace(',', '.') if checklist.odometro_fim else '-' }} km</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Resumo de Respostas -->
            <div class="col-lg-4">
                <div class="card info-card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="bi bi-pie-chart me-2"></i>Resumo de Respostas
                        </h6>
                    </div>
                    <div class="card-body text-center">
                        <div class="row">
                            <div class="col-4">
                                <div class="text-success fs-3 fw-bold">{{ resumo.ok_count }}</div>
                                <small class="text-muted">OK</small>
                            </div>
                            <div class="col-4">
                                <div class="text-danger fs-3 fw-bold">{{ resumo.nao_ok_count }}</div>
                                <small class="text-muted">NÃO OK</small>
                            </div>
                            <div class="col-4">
                                <div class="text-secondary fs-3 fw-bold">{{ resumo.na_count }}</div>
                                <small class="text-muted">N/A</small>
                            </div>
                        </div>
                        {% if resumo.bloqueios_count > 0 %}
                        <div class="alert alert-danger mt-3 mb-0">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            <strong>{{ resumo.bloqueios_count }}</strong> item(ns) crítico(s) reprovado(s)
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Respostas dos Itens -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-list-check me-2"></i>Respostas dos Itens
                        </h5>
                    </div>
                    <div class="card-body">
                        {% for item in itens_with_responses %}
                        <div class="item-row {{ item.resposta.valor if item.resposta else 'unanswered' }}">
                            <div class="row align-items-center">
                                <div class="col-md-1 text-center">
                                    <span class="badge bg-primary rounded-pill">{{ item.ordem }}</span>
                                </div>
                                <div class="col-md-6">
                                    <h6 class="mb-1">{{ item.descricao }}</h6>
                                    <div>
                                        <span class="badge severity-badge bg-{{ 'danger' if item.severidade == 'alta' else 'warning' if item.severidade == 'media' else 'secondary' }}">
                                            {{ item.severidade.upper() }}
                                        </span>
                                        {% if item.bloqueia_viagem %}
                                        <span class="badge severity-badge bg-danger ms-1">
                                            <i class="bi bi-exclamation-triangle-fill"></i> CRÍTICO
                                        </span>
                                        {% endif %}
                                        {% if item.exige_foto %}
                                        <span class="badge severity-badge bg-info ms-1">
                                            <i class="bi bi-camera"></i> FOTO
                                        </span>
                                        {% endif %}
                                    </div>
                                </div>
                                <div class="col-md-2 text-center">
                                    {% if item.resposta %}
                                        {% if item.resposta.valor == 'ok' %}
                                            <span class="badge bg-success fs-6">
                                                <i class="bi bi-check-circle me-1"></i>OK
                                            </span>
                                        {% elif item.resposta.valor == 'nao_ok' %}
                                            <span class="badge bg-danger fs-6">
                                                <i class="bi bi-x-circle me-1"></i>NÃO OK
                                            </span>
                                        {% else %}
                                            <span class="badge bg-secondary fs-6">
                                                <i class="bi bi-dash-circle me-1"></i>N/A
                                            </span>
                                        {% endif %}
                                    {% else %}
                                        <span class="badge bg-light text-dark fs-6">
                                            <i class="bi bi-clock me-1"></i>PENDENTE
                                        </span>
                                    {% endif %}
                                </div>
                                <div class="col-md-3">
                                    {% if item.resposta and item.resposta.observacao %}
                                    <small class="text-muted">
                                        <i class="bi bi-chat-dots me-1"></i>
                                        {{ item.resposta.observacao }}
                                    </small>
                                    {% endif %}
                                    {% if item.resposta and item.resposta.dt %}
                                    <br><small class="text-muted">
                                        <i class="bi bi-clock me-1"></i>
                                        {{ item.resposta.dt[:16].replace('T', ' ') }}
                                    </small>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Assinatura e Localização -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="bi bi-geo-alt me-2"></i>Localizações
                        </h6>
                    </div>
                    <div class="card-body">
                        <table class="table table-borderless table-sm">
                            <tr>
                                <td><strong>Início:</strong></td>
                                <td>{{ checklist.geo_inicio or 'Não informado' }}</td>
                            </tr>
                            <tr>
                                <td><strong>Fim:</strong></td>
                                <td>{{ checklist.geo_fim or 'Não informado' }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="bi bi-pencil-square me-2"></i>Assinatura Digital
                        </h6>
                    </div>
                    <div class="card-body">
                        {% if checklist.assinatura_motorista %}
                        <div class="signature-display">
                            <i class="bi bi-check-circle-fill text-success fs-2"></i>
                            <p class="mt-2 mb-0">{{ checklist.assinatura_motorista }}</p>
                        </div>
                        {% else %}
                        <div class="signature-display text-muted">
                            <i class="bi bi-x-circle fs-2"></i>
                            <p class="mt-2 mb-0">Não assinado</p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Timeline de Atividade -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-clock-history me-2"></i>Timeline de Atividade
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="timeline">
                            <div class="timeline-item">
                                <div class="timeline-icon bg-primary text-white">
                                    <i class="bi bi-play-fill"></i>
                                </div>
                                <div class="ms-3">
                                    <h6 class="mb-1">Checklist Iniciado</h6>
                                    <p class="text-muted mb-1">{{ checklist.dt_inicio[:16].replace('T', ' ') if checklist.dt_inicio else '-' }}</p>
                                    <small class="text-muted">Checklist criado e iniciado pelo motorista</small>
                                </div>
                            </div>

                            {% if resumo.nao_ok_count > 0 %}
                            <div class="timeline-item">
                                <div class="timeline-icon bg-warning text-white">
                                    <i class="bi bi-exclamation-triangle-fill"></i>
                                </div>
                                <div class="ms-3">
                                    <h6 class="mb-1">Problemas Identificados</h6>
                                    <p class="text-muted mb-1">Durante a execução</p>
                                    <small class="text-muted">{{ resumo.nao_ok_count }} item(ns) reprovado(s)</small>
                                </div>
                            </div>
                            {% endif %}

                            {% if checklist.dt_fim %}
                            <div class="timeline-item">
                                <div class="timeline-icon bg-{{ 'success' if checklist.status == 'aprovado' else 'danger' }} text-white">
                                    <i class="bi bi-{{ 'check-circle-fill' if checklist.status == 'aprovado' else 'x-circle-fill' }}"></i>
                                </div>
                                <div class="ms-3">
                                    <h6 class="mb-1">Checklist {{ 'Aprovado' if checklist.status == 'aprovado' else 'Reprovado' }}</h6>
                                    <p class="text-muted mb-1">{{ checklist.dt_fim[:16].replace('T', ' ') }}</p>
                                    <small class="text-muted">
                                        {% if checklist.status == 'aprovado' %}
                                            Checklist finalizado com sucesso. Veículo liberado para viagem.
                                        {% else %}
                                            Checklist reprovado. Veículo bloqueado para viagem.
                                        {% endif %}
                                    </small>
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Ações (apenas se pendente) -->
        {% if checklist.status == 'pendente' %}
        <div class="row no-print">
            <div class="col-12">
                <div class="card border-warning">
                    <div class="card-header bg-warning text-dark">
                        <h6 class="mb-0">
                            <i class="bi bi-exclamation-triangle me-2"></i>Ações Disponíveis
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex gap-2">
                            <a href="/checklist/{{ checklist.id }}/execute" class="btn btn-success">
                                <i class="bi bi-play me-2"></i>Continuar Execução
                            </a>
                            <button class="btn btn-outline-danger" onclick="cancelChecklist()">
                                <i class="bi bi-trash me-2"></i>Cancelar Checklist
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function exportPDF() {
            window.open('/checklist/{{ checklist.id }}/report', '_blank');
        }

        function cancelChecklist() {
            if (confirm('Tem certeza que deseja cancelar este checklist?')) {
                fetch('/checklist/api/cancel/{{ checklist.id }}', { method: 'DELETE' })
                    .then(response => {
                        if (response.ok) {
                            alert('Checklist cancelado com sucesso');
                            window.location.href = '/checklist';
                        } else {
                            alert('Erro ao cancelar checklist');
                        }
                    })
                    .catch(error => {
                        alert('Erro: ' + error.message);
                    });
            }
        }
    </script>
</body>
</html>
"""

@bp.route("/<int:checklist_id>")
def checklist_detail(checklist_id):
    """Detalhes do checklist"""
    try:
        # Buscar dados do checklist
        checklist_data = make_api_request('GET', f'/checklist/{checklist_id}')
        
        if not checklist_data:
            flash("Checklist não encontrado", "warning")
            return redirect(url_for('checklist.list_checklists'))
        
        # Calcular duração se finalizado
        duracao_minutos = None
        if checklist_data.get('dt_inicio') and checklist_data.get('dt_fim'):
            from datetime import datetime
            dt_inicio = datetime.fromisoformat(checklist_data['dt_inicio'].replace('Z', '+00:00'))
            dt_fim = datetime.fromisoformat(checklist_data['dt_fim'].replace('Z', '+00:00'))
            duracao_minutos = int((dt_fim - dt_inicio).total_seconds() / 60)
        
        # Mapear respostas por item_id
        respostas_map = {r['item_id']: r for r in checklist_data.get('respostas', [])}
        
        # Combinar itens com respostas
        itens_with_responses = []
        for item in checklist_data.get('itens', []):
            item['resposta'] = respostas_map.get(item['id'])
            itens_with_responses.append(item)
        
        # Calcular resumo
        respostas = checklist_data.get('respostas', [])
        resumo = {
            'ok_count': len([r for r in respostas if r['valor'] == 'ok']),
            'nao_ok_count': len([r for r in respostas if r['valor'] == 'nao_ok']),
            'na_count': len([r for r in respostas if r['valor'] == 'na']),
            'bloqueios_count': len([r for r in respostas if r['valor'] == 'nao_ok' and any(
                item['id'] == r['item_id'] and item.get('bloqueia_viagem') 
                for item in checklist_data.get('itens', [])
            )])
        }
        
        # Informações adicionais (simuladas por enquanto)
        veiculo_info = {'placa': f"Veículo {checklist_data['veiculo_id']}"}
        motorista_info = {'nome': f"Motorista {checklist_data['motorista_id']}"}
        
        context = {
            'checklist': checklist_data,
            'itens_with_responses': itens_with_responses,
            'duracao_minutos': duracao_minutos,
            'resumo': resumo,
            'veiculo_info': veiculo_info,
            'motorista_info': motorista_info
        }
        
        return render_template_string(CHECKLIST_DETAIL_TEMPLATE, **context)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar detalhes do checklist: {str(e)}")
        flash(f"Erro interno: {str(e)}", "danger")
        return redirect(url_for('checklist.list_checklists'))

@bp.route("/<int:checklist_id>/report")
def checklist_report(checklist_id):
    """Relatório do checklist em PDF"""
    # Por enquanto, redireciona para a versão para impressão
    return redirect(url_for('checklist_detail.checklist_detail', checklist_id=checklist_id) + '?print=1')