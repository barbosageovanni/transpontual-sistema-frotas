# flask_dashboard/app/blueprints/checklist.py
"""
Blueprint para gestão de checklists - Conectado com API real
"""
from flask import Blueprint, render_template_string, request, jsonify, redirect, url_for, flash, current_app
import requests
from datetime import datetime, timedelta
import json
from urllib.parse import urlencode

bp = Blueprint("checklist", __name__)

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

# Template de edição de checklist
EDIT_CHECKLIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Checklist #{{ checklist.id }} - Transpontual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        .edit-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section-title {
            color: #495057;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .readonly-field {
            background-color: #f8f9fa;
            border-color: #e9ecef;
        }
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 500;
        }
        .save-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1050;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: 500;
            display: none;
        }
        .save-indicator.saving { background: #17a2b8; color: white; }
        .save-indicator.saved { background: #28a745; color: white; }
        .save-indicator.error { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <!-- Save Indicator -->
        <div id="saveIndicator" class="save-indicator">
            <i class="bi bi-check-circle me-2"></i>
            <span id="saveText">Salvando...</span>
        </div>

        <!-- Header -->
        <div class="edit-header">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <div class="d-flex align-items-center">
                        <a href="/checklists" class="btn btn-outline-light btn-sm me-3">
                            <i class="bi bi-arrow-left me-1"></i>Voltar
                        </a>
                        <div>
                            <h2 class="mb-1">
                                <i class="bi bi-pencil-square me-2"></i>
                                Editar Checklist #{{ checklist.id }}
                            </h2>
                            <p class="mb-0 opacity-75">
                                Modifique os dados básicos do checklist
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 text-end">
                    <span class="status-badge bg-{{ 'warning' if checklist.status == 'em_andamento' else 'success' if checklist.status == 'aprovado' else 'danger' }}">
                        {{ checklist.status.replace('_', ' ').title() }}
                    </span>
                </div>
            </div>
        </div>

        <form id="editForm">
            <!-- Informações Básicas -->
            <div class="form-section">
                <h5 class="section-title">
                    <i class="bi bi-info-circle me-2"></i>Informações Básicas
                </h5>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">ID do Checklist</label>
                        <input type="text" class="form-control readonly-field" value="{{ checklist.id }}" readonly>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Tipo de Checklist</label>
                        <select name="tipo" class="form-select" {{ 'disabled' if checklist.status != 'em_andamento' else '' }}>
                            <option value="pre" {{ 'selected' if checklist.tipo == 'pre' else '' }}>Pré-viagem</option>
                            <option value="pos" {{ 'selected' if checklist.tipo == 'pos' else '' }}>Pós-viagem</option>
                            <option value="extra" {{ 'selected' if checklist.tipo == 'extra' else '' }}>Extraordinário</option>
                        </select>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-md-6">
                        <label class="form-label">Modelo de Checklist</label>
                        <select name="modelo_id" class="form-select" {{ 'disabled' if checklist.status != 'em_andamento' else '' }}>
                            {% for modelo in modelos %}
                            <option value="{{ modelo.id }}" {{ 'selected' if modelo.id == checklist.modelo_id else '' }}>
                                {{ modelo.nome }} ({{ modelo.tipo.upper() }})
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Status</label>
                        <input type="text" class="form-control readonly-field"
                               value="{{ checklist.status.replace('_', ' ').title() }}" readonly>
                    </div>
                </div>
            </div>

            <!-- Veículo e Motorista -->
            <div class="form-section">
                <h5 class="section-title">
                    <i class="bi bi-truck me-2"></i>Veículo e Motorista
                </h5>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Veículo</label>
                        <select name="veiculo_id" class="form-select">
                            {% for veiculo in veiculos %}
                            <option value="{{ veiculo.id }}" {{ 'selected' if veiculo.id == checklist.veiculo_id else '' }}>
                                {{ veiculo.placa }} - {{ veiculo.modelo }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Motorista</label>
                        <select name="motorista_id" class="form-select">
                            {% for motorista in motoristas %}
                            <option value="{{ motorista.id }}" {{ 'selected' if motorista.id == checklist.motorista_id else '' }}>
                                {{ motorista.nome }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
            </div>

            <!-- Odômetros -->
            <div class="form-section">
                <h5 class="section-title">
                    <i class="bi bi-speedometer2 me-2"></i>Odômetros
                </h5>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Odômetro Inicial (KM)</label>
                        <input type="number" name="odometro_ini" class="form-control"
                               value="{{ checklist.odometro_ini }}" min="0" step="1">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Odômetro Final (KM)</label>
                        <input type="number" name="odometro_fim" class="form-control"
                               value="{{ checklist.odometro_fim or '' }}" min="0" step="1"
                               {{ 'readonly' if checklist.status == 'em_andamento' else '' }}>
                    </div>
                </div>
            </div>

            <!-- Datas -->
            <div class="form-section">
                <h5 class="section-title">
                    <i class="bi bi-calendar me-2"></i>Datas e Horários
                </h5>

                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Data/Hora de Início</label>
                        <input type="text" class="form-control readonly-field"
                               value="{{ checklist.dt_inicio }}" readonly>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Data/Hora de Fim</label>
                        <input type="text" class="form-control readonly-field"
                               value="{{ checklist.dt_fim or 'Em andamento' }}" readonly>
                    </div>
                </div>
            </div>

            <!-- Botões de Ação -->
            <div class="form-section">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <a href="/checklists/{{ checklist.id }}" class="btn btn-outline-secondary">
                            <i class="bi bi-eye me-1"></i>Visualizar
                        </a>
                        {% if checklist.status == 'em_andamento' %}
                        <a href="/checklists/{{ checklist.id }}/execute" class="btn btn-outline-primary">
                            <i class="bi bi-play me-1"></i>Continuar Execução
                        </a>
                        {% endif %}
                    </div>

                    <div>
                        <button type="button" class="btn btn-outline-secondary me-2" onclick="resetForm()">
                            <i class="bi bi-arrow-clockwise me-1"></i>Resetar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-save me-1"></i>Salvar Alterações
                        </button>
                    </div>
                </div>
            </div>
        </form>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let originalData = {};
        let hasChanges = false;

        document.addEventListener('DOMContentLoaded', function() {
            // Salvar dados originais
            saveOriginalData();

            // Monitorar mudanças
            const form = document.getElementById('editForm');
            form.addEventListener('change', detectChanges);
            form.addEventListener('input', detectChanges);

            // Submit handler
            form.addEventListener('submit', handleSubmit);

            // Warning ao sair
            window.addEventListener('beforeunload', function(e) {
                if (hasChanges) {
                    e.preventDefault();
                    e.returnValue = '';
                }
            });
        });

        function saveOriginalData() {
            const form = document.getElementById('editForm');
            const formData = new FormData(form);

            originalData = {};
            for (let [key, value] of formData.entries()) {
                originalData[key] = value;
            }
        }

        function detectChanges() {
            const form = document.getElementById('editForm');
            const formData = new FormData(form);

            hasChanges = false;
            for (let [key, value] of formData.entries()) {
                if (originalData[key] !== value) {
                    hasChanges = true;
                    break;
                }
            }

            // Atualizar visual do botão salvar
            const saveBtn = form.querySelector('button[type="submit"]');
            if (hasChanges) {
                saveBtn.classList.remove('btn-primary');
                saveBtn.classList.add('btn-warning');
                saveBtn.innerHTML = '<i class="bi bi-exclamation-triangle me-1"></i>Salvar Alterações';
            } else {
                saveBtn.classList.remove('btn-warning');
                saveBtn.classList.add('btn-primary');
                saveBtn.innerHTML = '<i class="bi bi-save me-1"></i>Salvar Alterações';
            }
        }

        function resetForm() {
            if (hasChanges && !confirm('Descartar todas as alterações?')) {
                return;
            }

            location.reload();
        }

        async function handleSubmit(e) {
            e.preventDefault();

            if (!hasChanges) {
                showSaveIndicator('saved', 'Nenhuma alteração para salvar');
                return;
            }

            const form = e.target;
            const formData = new FormData(form);
            const data = {};

            for (let [key, value] of formData.entries()) {
                // Converter números
                if (['veiculo_id', 'motorista_id', 'modelo_id', 'odometro_ini', 'odometro_fim'].includes(key)) {
                    data[key] = value ? parseInt(value) : null;
                } else {
                    data[key] = value;
                }
            }

            showSaveIndicator('saving', 'Salvando alterações...');

            try {
                const response = await fetch('/checklists/{{ checklist.id }}/edit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    showSaveIndicator('saved', 'Alterações salvas com sucesso!');
                    hasChanges = false;
                    saveOriginalData();
                    detectChanges();
                } else {
                    throw new Error(result.error || 'Erro ao salvar');
                }

            } catch (error) {
                console.error('Erro ao salvar:', error);
                showSaveIndicator('error', 'Erro ao salvar: ' + error.message);
            }
        }

        function showSaveIndicator(type, message) {
            const indicator = document.getElementById('saveIndicator');
            const text = document.getElementById('saveText');

            indicator.className = `save-indicator ${type}`;
            text.textContent = message;
            indicator.style.display = 'block';

            if (type !== 'saving') {
                setTimeout(() => {
                    indicator.style.display = 'none';
                }, 3000);
            }
        }
    </script>
</body>
</html>
"""

# Template atualizado para lista de checklists
CHECKLIST_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checklists - Transpontual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        .status-badge { font-size: 0.75rem; }
        .table-responsive { max-height: 600px; overflow-y: auto; }
        .filters-card { margin-bottom: 1rem; }
        .action-buttons { white-space: nowrap; }
        .kpi-card { background: linear-gradient(45deg, #007bff, #0056b3); color: white; }
        .kpi-card.success { background: linear-gradient(45deg, #28a745, #1e7e34); }
        .kpi-card.danger { background: linear-gradient(45deg, #dc3545, #bd2130); }
        .kpi-card.warning { background: linear-gradient(45deg, #ffc107, #e0a800); color: #000; }
        .loading { text-align: center; padding: 3rem; }
        .error-alert { margin: 1rem 0; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="bi bi-truck me-2"></i>Transpontual
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link active" href="/checklist">Checklists</a>
                <a class="nav-link" href="/checklist/models">Modelos</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <!-- Alerts de erro -->
        {% if error %}
        <div class="alert alert-danger error-alert">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
        </div>
        {% endif %}
        
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-md-8">
                <h1 class="h3 mb-0">Gestão de Checklists</h1>
                <p class="text-muted">Visualize e gerencie todos os checklists</p>
            </div>
            <div class="col-md-4 text-end">
                <a href="/checklist/new" class="btn btn-primary">
                    <i class="bi bi-plus-circle me-2"></i>Novo Checklist
                </a>
            </div>
        </div>
        
        <!-- Filtros -->
        <div class="card filters-card">
            <div class="card-header">
                <h6 class="card-title mb-0">
                    <i class="bi bi-funnel me-2"></i>Filtros
                    <button class="btn btn-sm btn-outline-secondary float-end" onclick="clearFilters()">
                        <i class="bi bi-x-circle me-1"></i>Limpar
                    </button>
                </h6>
            </div>
            <div class="card-body">
                <form method="GET" class="row g-3" id="filtersForm">
                    <div class="col-md-2">
                        <label class="form-label">Status</label>
                        <select name="status" class="form-select">
                            <option value="">Todos</option>
                            <option value="pendente" {{ 'selected' if filters.status == 'pendente' else '' }}>Pendente</option>
                            <option value="aprovado" {{ 'selected' if filters.status == 'aprovado' else '' }}>Aprovado</option>
                            <option value="reprovado" {{ 'selected' if filters.status == 'reprovado' else '' }}>Reprovado</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Tipo</label>
                        <select name="tipo" class="form-select">
                            <option value="">Todos</option>
                            <option value="pre" {{ 'selected' if filters.tipo == 'pre' else '' }}>Pré-viagem</option>
                            <option value="pos" {{ 'selected' if filters.tipo == 'pos' else '' }}>Pós-viagem</option>
                            <option value="extra" {{ 'selected' if filters.tipo == 'extra' else '' }}>Extraordinário</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Veículo</label>
                        <input type="text" name="veiculo_search" class="form-control" placeholder="Placa..." 
                               value="{{ request.args.get('veiculo_search', '') }}" 
                               onkeyup="searchVeiculos(this.value)">
                        <div id="veiculo-suggestions" class="dropdown-menu"></div>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Data Início</label>
                        <input type="date" name="data_inicio" class="form-control" 
                               value="{{ filters.data_inicio or '' }}">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Data Fim</label>
                        <input type="date" name="data_fim" class="form-control" 
                               value="{{ filters.data_fim or '' }}">
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button type="submit" class="btn btn-secondary me-2">
                            <i class="bi bi-search"></i> Filtrar
                        </button>
                        <button type="button" class="btn btn-outline-info" onclick="refreshData()">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- KPIs -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card kpi-card text-center">
                    <div class="card-body py-3">
                        <h4 class="mb-0">{{ stats.total or 0 }}</h4>
                        <small>Total de Checklists</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card kpi-card success text-center">
                    <div class="card-body py-3">
                        <h4 class="mb-0">{{ stats.aprovados or 0 }}</h4>
                        <small>Aprovados ({{ "%.1f"|format((stats.aprovados or 0) * 100 / (stats.total or 1)) }}%)</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card kpi-card danger text-center">
                    <div class="card-body py-3">
                        <h4 class="mb-0">{{ stats.reprovados or 0 }}</h4>
                        <small>Reprovados</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card kpi-card warning text-center">
                    <div class="card-body py-3">
                        <h4 class="mb-0">{{ stats.pendentes or 0 }}</h4>
                        <small>Pendentes</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tabela de Checklists -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="card-title mb-0">
                    Lista de Checklists
                    {% if pagination %}
                    <span class="badge bg-secondary ms-2">{{ pagination.total }}</span>
                    {% endif %}
                </h6>
                <div>
                    <button class="btn btn-outline-success btn-sm me-2" onclick="exportData('csv')">
                        <i class="bi bi-download me-1"></i>CSV
                    </button>
                    <button class="btn btn-outline-danger btn-sm" onclick="exportData('excel')">
                        <i class="bi bi-file-excel me-1"></i>Excel
                    </button>
                </div>
            </div>
            <div class="card-body p-0">
                {% if not checklists %}
                <div class="text-center py-5">
                    <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
                    <p class="text-muted mt-3 mb-0">Nenhum checklist encontrado</p>
                    {% if not request.args %}
                    <a href="/checklist/new" class="btn btn-primary mt-3">Criar primeiro checklist</a>
                    {% else %}
                    <button class="btn btn-outline-secondary mt-3" onclick="clearFilters()">Limpar filtros</button>
                    {% endif %}
                </div>
                {% else %}
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light sticky-top">
                            <tr>
                                <th>
                                    <a href="?{{ update_query_string('order_by', 'id') }}" class="text-decoration-none">
                                        ID <i class="bi bi-arrow-up-down"></i>
                                    </a>
                                </th>
                                <th>Veículo</th>
                                <th>Motorista</th>
                                <th>Tipo</th>
                                <th>
                                    <a href="?{{ update_query_string('order_by', 'dt_inicio') }}" class="text-decoration-none">
                                        Data/Hora <i class="bi bi-arrow-up-down"></i>
                                    </a>
                                </th>
                                <th>Status</th>
                                <th>Duração</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for checklist in checklists %}
                            <tr>
                                <td>
                                    <strong>#{{ checklist.id }}</strong>
                                </td>
                                <td>
                                    <div>
                                        <strong>{{ checklist.veiculo_placa or ('ID ' + checklist.veiculo_id|string) }}</strong>
                                        {% if checklist.veiculo_modelo %}
                                            <br><small class="text-muted">{{ checklist.veiculo_modelo }}</small>
                                        {% endif %}
                                        {% if checklist.odometro_ini %}
                                            <br><small class="text-muted">{{ "{:,}".format(checklist.odometro_ini).replace(',', '.') }} km</small>
                                        {% endif %}
                                    </div>
                                </td>
                                <td>{{ checklist.motorista_nome or ('ID ' + checklist.motorista_id|string) }}</td>
                                <td>
                                    <span class="badge bg-{{ 'primary' if checklist.tipo == 'pre' else 'info' if checklist.tipo == 'pos' else 'warning' }}">
                                        {{ checklist.tipo.upper() }}
                                    </span>
                                </td>
                                <td>
                                    <div>
                                        {% if checklist.dt_inicio %}
                                            {{ checklist.dt_inicio[:16].replace('T', ' ') }}
                                        {% else %}
                                            <span class="text-muted">-</span>
                                        {% endif %}
                                        {% if checklist.dt_fim %}
                                            <br><small class="text-success">
                                                <i class="bi bi-check-circle me-1"></i>Finalizado
                                            </small>
                                        {% endif %}
                                    </div>
                                </td>
                                <td>
                                    {% if checklist.status == 'aprovado' %}
                                        <span class="badge bg-success status-badge">
                                            <i class="bi bi-check-circle me-1"></i>Aprovado
                                        </span>
                                    {% elif checklist.status == 'reprovado' %}
                                        <span class="badge bg-danger status-badge">
                                            <i class="bi bi-x-circle me-1"></i>Reprovado
                                        </span>
                                    {% else %}
                                        <span class="badge bg-warning status-badge">
                                            <i class="bi bi-clock me-1"></i>Pendente
                                        </span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if checklist.duracao_minutos %}
                                        <span class="badge bg-light text-dark">{{ checklist.duracao_minutos }} min</span>
                                    {% else %}
                                        <small class="text-muted">Em andamento...</small>
                                    {% endif %}
                                </td>
                                <td class="action-buttons">
                                    <div class="btn-group btn-group-sm">
                                        <a href="/checklist/{{ checklist.id }}" class="btn btn-outline-primary" title="Ver detalhes">
                                            <i class="bi bi-eye"></i>
                                        </a>
                                        {% if checklist.status == 'pendente' %}
                                            <a href="/checklist/{{ checklist.id }}/execute" class="btn btn-outline-success" title="Executar">
                                                <i class="bi bi-play"></i>
                                            </a>
                                        {% endif %}
                                        <button class="btn btn-outline-info" onclick="downloadReport({{ checklist.id }})" title="Relatório">
                                            <i class="bi bi-download"></i>
                                        </button>
                                        {% if checklist.status == 'pendente' %}
                                            <button class="btn btn-outline-danger" onclick="cancelChecklist({{ checklist.id }})" title="Cancelar">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        {% endif %}
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
            </div>
            
            <!-- Paginação -->
            {% if pagination and pagination.total_pages > 1 %}
            <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <small class="text-muted">
                            Página {{ pagination.page }} de {{ pagination.total_pages }} 
                            ({{ pagination.total }} resultados)
                        </small>
                    </div>
                    <nav>
                        <ul class="pagination pagination-sm mb-0">
                            <li class="page-item {{ 'disabled' if not pagination.has_prev else '' }}">
                                <a class="page-link" href="?{{ update_query_string('page', pagination.prev_num) }}">Anterior</a>
                            </li>
                            
                            {% for page_num in range(1, pagination.total_pages + 1) %}
                                {% if page_num == pagination.page or 
                                      page_num == 1 or 
                                      page_num == pagination.total_pages or
                                      (page_num >= pagination.page - 2 and page_num <= pagination.page + 2) %}
                                    <li class="page-item {{ 'active' if page_num == pagination.page else '' }}">
                                        <a class="page-link" href="?{{ update_query_string('page', page_num) }}">{{ page_num }}</a>
                                    </li>
                                {% elif page_num == pagination.page - 3 or page_num == pagination.page + 3 %}
                                    <li class="page-item disabled">
                                        <span class="page-link">...</span>
                                    </li>
                                {% endif %}
                            {% endfor %}
                            
                            <li class="page-item {{ 'disabled' if not pagination.has_next else '' }}">
                                <a class="page-link" href="?{{ update_query_string('page', pagination.next_num) }}">Próxima</a>
                            </li>
                        </ul>
                    </nav>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Utilitários
        function clearFilters() {
            window.location.href = '/checklist';
        }
        
        function refreshData() {
            window.location.reload();
        }
        
        function updateQueryString(key, value) {
            const params = new URLSearchParams(window.location.search);
            if (value) {
                params.set(key, value);
            } else {
                params.delete(key);
            }
            return params.toString();
        }
        
        // Busca de veículos
        let veiculoSearchTimeout;
        function searchVeiculos(query) {
            clearTimeout(veiculoSearchTimeout);
            veiculoSearchTimeout = setTimeout(() => {
                if (query.length >= 2) {
                    fetch(`/checklist/api/search/veiculos?q=${encodeURIComponent(query)}`)
                        .then(response => response.json())
                        .then(data => {
                            // Implementar dropdown de sugestões
                            console.log('Veículos encontrados:', data);
                        })
                        .catch(error => console.error('Erro na busca:', error));
                }
            }, 300);
        }
        
        // Exportações
        function exportData(format) {
            const params = new URLSearchParams(window.location.search);
            params.set('export', format);
            window.open('/checklist/export?' + params.toString(), '_blank');
        }
        
        // Download de relatório
        function downloadReport(checklistId) {
            window.open('/checklist/' + checklistId + '/report', '_blank');
        }
        
        // Cancelar checklist
        function cancelChecklist(checklistId) {
            if (confirm('Tem certeza que deseja cancelar este checklist?')) {
                fetch('/checklist/api/cancel/' + checklistId, { method: 'DELETE' })
                    .then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Erro ao cancelar checklist');
                        }
                    })
                    .catch(error => {
                        alert('Erro: ' + error.message);
                    });
            }
        }
        
        // Auto-refresh opcional (desativado por padrão)
        // setInterval(refreshData, 300000); // 5 minutos
    </script>
</body>
</html>
"""

@bp.route("/")
def list_checklists():
    """Lista de checklists com filtros - conectando com API real"""
    try:
        # Parâmetros de filtro
        params = {
            'page': int(request.args.get('page', 1)),
            'per_page': 20,
            'status': request.args.get('status', ''),
            'tipo': request.args.get('tipo', ''),
            'data_inicio': request.args.get('data_inicio', ''),
            'data_fim': request.args.get('data_fim', ''),
            'order_by': request.args.get('order_by', 'dt_inicio'),
            'order_dir': request.args.get('order_dir', 'desc')
        }
        
        # Remover parâmetros vazios
        params = {k: v for k, v in params.items() if v}
        
        # Buscar dados da API
        data = make_api_request('GET', '/checklist', params=params)
        
        if not data:
            flash("Erro ao carregar dados da API", "danger")
            return render_template_string(CHECKLIST_LIST_TEMPLATE, 
                                        error="Erro ao conectar com a API",
                                        checklists=[], 
                                        stats={}, 
                                        pagination={},
                                        filters={},
                                        request=request)
        
        # Helper para URLs de paginação
        def update_query_string(key, value):
            from urllib.parse import urlencode
            query_dict = dict(request.args)
            if value:
                query_dict[key] = value
            elif key in query_dict:
                del query_dict[key]
            return urlencode(query_dict)
        
        context = {
            'checklists': data.get('checklists', []),
            'stats': data.get('stats', {}),
            'pagination': data.get('pagination', {}),
            'filters': data.get('filters', {}),
            'request': request,
            'update_query_string': update_query_string
        }
        
        return render_template_string(CHECKLIST_LIST_TEMPLATE, **context)
        
    except Exception as e:
        current_app.logger.error(f"Erro na lista de checklists: {str(e)}")
        flash(f"Erro interno: {str(e)}", "danger")
        return render_template_string(CHECKLIST_LIST_TEMPLATE, 
                                    error=str(e),
                                    checklists=[], 
                                    stats={}, 
                                    pagination={},
                                    filters={},
                                    request=request)

@bp.route("/api/search/veiculos")
def api_search_veiculos():
    """Proxy para busca de veículos"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    data = make_api_request('GET', f'/checklist/search/veiculos?q={query}')
    return jsonify(data or [])

@bp.route("/api/search/motoristas")
def api_search_motoristas():
    """Proxy para busca de motoristas"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    data = make_api_request('GET', f'/checklist/search/motoristas?q={query}')
    return jsonify(data or [])

@bp.route("/api/cancel/<int:checklist_id>", methods=['DELETE'])
def api_cancel_checklist(checklist_id):
    """Proxy para cancelar checklist"""
    data = make_api_request('DELETE', f'/checklist/{checklist_id}')
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "Erro ao cancelar checklist"}), 500

@bp.route("/export")
def export_checklists():
    """Exportar checklists em CSV ou Excel"""
    export_format = request.args.get('export', 'csv')
    
    # Buscar dados com os mesmos filtros
    params = dict(request.args)
    params.pop('export', None)
    params['per_page'] = 1000  # Buscar mais dados para export
    
    data = make_api_request('GET', '/checklist', params=params)
    
    if not data:
        flash("Erro ao exportar dados", "danger")
        return redirect(url_for('checklist.list_checklists'))
    
    checklists = data.get('checklists', [])
    
    if export_format == 'csv':
        return export_to_csv(checklists)
    elif export_format == 'excel':
        return export_to_excel(checklists)
    else:
        flash("Formato de exportação inválido", "warning")
        return redirect(url_for('checklist.list_checklists'))

def export_to_csv(checklists):
    """Exportar para CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Veículo', 'Placa', 'Motorista', 'Tipo', 'Status',
        'Data Início', 'Data Fim', 'Duração (min)', 'Odômetro Inicial',
        'Odômetro Final', 'Localização Início'
    ])
    
    # Dados
    for c in checklists:
        writer.writerow([
            c.get('id'),
            c.get('veiculo_modelo', ''),
            c.get('veiculo_placa', ''),
            c.get('motorista_nome', ''),
            c.get('tipo', '').upper(),
            c.get('status', '').upper(),
            c.get('dt_inicio', ''),
            c.get('dt_fim', ''),
            c.get('duracao_minutos', ''),
            c.get('odometro_ini', ''),
            c.get('odometro_fim', ''),
            c.get('geo_inicio', '')
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=checklists_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        }
    )

def export_to_excel(checklists):
    """Exportar para Excel (simulado como CSV por simplicidade)"""
    # Em produção, usar openpyxl ou xlsxwriter
    return export_to_csv(checklists)

@bp.route("/new")
def new_checklist():
    """Formulário para novo checklist"""
    return "<h1>Novo Checklist</h1><p>Formulário em desenvolvimento...</p>"

@bp.route("/<int:checklist_id>")
def checklist_detail(checklist_id):
    """Detalhes do checklist"""
    data = make_api_request('GET', f'/checklist/{checklist_id}')
    
    if not data:
        flash("Checklist não encontrado", "warning")
        return redirect(url_for('checklist.list_checklists'))
    
    return f"<h1>Checklist #{checklist_id}</h1><pre>{json.dumps(data, indent=2)}</pre>"

@bp.route("/<int:checklist_id>/execute")
def execute_checklist(checklist_id):
    """Executar checklist"""
    return f"<h1>Executar Checklist #{checklist_id}</h1><p>Interface em desenvolvimento...</p>"

@bp.route("/<int:checklist_id>/report")
def checklist_report(checklist_id):
    """Relatório do checklist"""
    return f"<h1>Relatório Checklist #{checklist_id}</h1><p>Relatório em desenvolvimento...</p>"

@bp.route("/<int:checklist_id>/finish", methods=['POST'])
def finish_checklist(checklist_id):
    """Finalizar checklist"""
    try:
        # Get request data
        data = request.get_json() or {}

        # Call API to finish checklist
        api_data = make_api_request('POST', f'/api/v1/checklist/{checklist_id}/finish', json={
            'odometro_fim': data.get('odometro_fim')
        })

        if api_data:
            return jsonify({"message": "Checklist finalizado com sucesso", "data": api_data})
        else:
            return jsonify({"error": "Erro ao finalizar checklist"}), 500

    except Exception as e:
        current_app.logger.error(f"Erro ao finalizar checklist {checklist_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/<int:checklist_id>/edit")
def edit_checklist(checklist_id):
    """Página de edição de checklist"""
    try:
        # Buscar dados do checklist
        checklist_data = make_api_request('GET', f'/checklist/{checklist_id}')

        if not checklist_data:
            flash("Checklist não encontrado", "error")
            return redirect(url_for('checklist.list_checklists'))

        # Buscar veículos e motoristas para seleção
        veiculos = make_api_request('GET', '/veiculo') or []
        motoristas = make_api_request('GET', '/motorista') or []
        modelos = make_api_request('GET', '/checklist/modelos') or []

        return render_template_string(EDIT_CHECKLIST_TEMPLATE,
                                    checklist=checklist_data,
                                    veiculos=veiculos,
                                    motoristas=motoristas,
                                    modelos=modelos)

    except Exception as e:
        current_app.logger.error(f"Erro ao carregar checklist para edição {checklist_id}: {str(e)}")
        flash("Erro ao carregar checklist", "error")
        return redirect(url_for('checklist.list_checklists'))

@bp.route("/<int:checklist_id>/edit", methods=['POST'])
def update_checklist(checklist_id):
    """Atualizar dados do checklist"""
    try:
        data = request.get_json()

        # Validações básicas
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        # Fazer chamada para API de atualização
        api_data = make_api_request('PATCH', f'/checklist/{checklist_id}', json=data)

        if api_data:
            return jsonify({"message": "Checklist atualizado com sucesso", "data": api_data})
        else:
            return jsonify({"error": "Erro ao atualizar checklist"}), 500

    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar checklist {checklist_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/<int:checklist_id>", methods=['DELETE'])
def delete_checklist(checklist_id):
    """Excluir checklist"""
    try:
        # Call API to delete checklist
        api_data = make_api_request('DELETE', f'/checklist/{checklist_id}')

        if api_data:
            return jsonify({"message": "Checklist excluído com sucesso", "data": api_data})
        else:
            return jsonify({"error": "Erro ao excluir checklist"}), 500

    except Exception as e:
        current_app.logger.error(f"Erro ao excluir checklist {checklist_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/models")
def list_models():
    """Lista de modelos de checklist"""
    data = make_api_request('GET', '/checklist/modelos')
    
    if not data:
        flash("Erro ao carregar modelos", "danger")
        return "<h1>Erro ao carregar modelos</h1>"
    
    models_html = "<h1>Modelos de Checklist</h1>"
    models_html += "<table class='table'><tr><th>ID</th><th>Nome</th><th>Tipo</th><th>Ativo</th></tr>"
    
    for model in data:
        models_html += f"<tr><td>{model['id']}</td><td>{model['nome']}</td><td>{model['tipo']}</td><td>{model['ativo']}</td></tr>"
    
    models_html += "</table>"
    return models_html