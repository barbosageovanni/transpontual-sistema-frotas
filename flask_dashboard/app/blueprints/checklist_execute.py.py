# flask_dashboard/app/blueprints/checklist_execute.py
"""
Formulário de execução de checklist
"""
from flask import Blueprint, render_template_string, request, jsonify, redirect, url_for, flash, current_app
import requests
import json
from datetime import datetime

bp = Blueprint("checklist_execute", __name__)

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

# Template para novo checklist
NEW_CHECKLIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novo Checklist - Transpontual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        .step-header { border-bottom: 2px solid #007bff; padding-bottom: 1rem; margin-bottom: 2rem; }
        .form-step { display: none; }
        .form-step.active { display: block; }
        .search-result { cursor: pointer; padding: 0.5rem; border-bottom: 1px solid #eee; }
        .search-result:hover { background-color: #f8f9fa; }
        .search-results { max-height: 200px; overflow-y: auto; border: 1px solid #ddd; border-top: none; }
        .selected-item { background-color: #e3f2fd; border: 2px solid #2196f3; border-radius: 0.375rem; padding: 1rem; }
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
                <a class="nav-link" href="/checklist">Checklists</a>
                <a class="nav-link active" href="#">Novo Checklist</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header step-header">
                        <h4 class="mb-0">
                            <i class="bi bi-plus-circle me-2"></i>Novo Checklist
                        </h4>
                        
                        <!-- Progress Bar -->
                        <div class="progress mt-3" style="height: 5px;">
                            <div class="progress-bar" id="progressBar" style="width: 33%"></div>
                        </div>
                        
                        <!-- Steps Indicator -->
                        <div class="d-flex justify-content-between mt-3">
                            <small class="text-primary fw-bold" id="step1-indicator">1. Configuração</small>
                            <small class="text-muted" id="step2-indicator">2. Seleções</small>
                            <small class="text-muted" id="step3-indicator">3. Confirmação</small>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <form id="newChecklistForm">
                            <!-- Step 1: Configuração Básica -->
                            <div class="form-step active" id="step1">
                                <h5 class="mb-4">Configuração Básica</h5>
                                
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Tipo de Checklist *</label>
                                        <select name="tipo" class="form-select" required>
                                            <option value="">Selecione...</option>
                                            <option value="pre">Pré-viagem</option>
                                            <option value="pos">Pós-viagem</option>
                                            <option value="extra">Extraordinário</option>
                                        </select>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Modelo de Checklist *</label>
                                        <select name="modelo_id" class="form-select" required>
                                            <option value="">Carregando...</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Odômetro Inicial (KM) *</label>
                                        <input type="number" name="odometro_ini" class="form-control" required min="0" step="1">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Localização Atual</label>
                                        <div class="input-group">
                                            <input type="text" name="geo_inicio" class="form-control" placeholder="Detectando...">
                                            <button type="button" class="btn btn-outline-secondary" onclick="getLocation()">
                                                <i class="bi bi-geo-alt"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="d-flex justify-content-end">
                                    <button type="button" class="btn btn-primary" onclick="nextStep()">
                                        Próximo <i class="bi bi-arrow-right"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Step 2: Seleção de Veículo e Motorista -->
                            <div class="form-step" id="step2">
                                <h5 class="mb-4">Seleção de Veículo e Motorista</h5>
                                
                                <!-- Seleção de Veículo -->
                                <div class="mb-4">
                                    <label class="form-label">Veículo *</label>
                                    <div class="position-relative">
                                        <input type="text" id="veiculoSearch" class="form-control" 
                                               placeholder="Digite a placa ou modelo do veículo..." 
                                               autocomplete="off">
                                        <div id="veiculoResults" class="search-results" style="display: none;"></div>
                                    </div>
                                    <input type="hidden" name="veiculo_id" required>
                                    <div id="selectedVeiculo" class="selected-item mt-3" style="display: none;">
                                        <h6 class="mb-2">Veículo Selecionado:</h6>
                                        <div id="veiculoInfo"></div>
                                        <button type="button" class="btn btn-sm btn-outline-secondary mt-2" onclick="clearVeiculo()">
                                            <i class="bi bi-x"></i> Alterar
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Seleção de Motorista -->
                                <div class="mb-4">
                                    <label class="form-label">Motorista *</label>
                                    <div class="position-relative">
                                        <input type="text" id="motoristaSearch" class="form-control" 
                                               placeholder="Digite o nome ou CNH do motorista..." 
                                               autocomplete="off">
                                        <div id="motoristaResults" class="search-results" style="display: none;"></div>
                                    </div>
                                    <input type="hidden" name="motorista_id" required>
                                    <div id="selectedMotorista" class="selected-item mt-3" style="display: none;">
                                        <h6 class="mb-2">Motorista Selecionado:</h6>
                                        <div id="motoristaInfo"></div>
                                        <button type="button" class="btn btn-sm btn-outline-secondary mt-2" onclick="clearMotorista()">
                                            <i class="bi bi-x"></i> Alterar
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="d-flex justify-content-between">
                                    <button type="button" class="btn btn-outline-secondary" onclick="prevStep()">
                                        <i class="bi bi-arrow-left"></i> Anterior
                                    </button>
                                    <button type="button" class="btn btn-primary" onclick="nextStep()">
                                        Próximo <i class="bi bi-arrow-right"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Step 3: Confirmação -->
                            <div class="form-step" id="step3">
                                <h5 class="mb-4">Confirmação</h5>
                                
                                <div id="confirmationData">
                                    <!-- Dados serão preenchidos via JavaScript -->
                                </div>
                                
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle me-2"></i>
                                    Após criar o checklist, você será redirecionado para a tela de execução.
                                </div>
                                
                                <div class="d-flex justify-content-between">
                                    <button type="button" class="btn btn-outline-secondary" onclick="prevStep()">
                                        <i class="bi bi-arrow-left"></i> Anterior
                                    </button>
                                    <button type="submit" class="btn btn-success" id="submitBtn">
                                        <i class="bi bi-check-circle me-2"></i>Criar Checklist
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentStep = 1;
        let selectedVeiculo = null;
        let selectedMotorista = null;
        let searchTimeout = null;
        
        // Navegação entre steps
        function nextStep() {
            if (validateCurrentStep()) {
                currentStep++;
                updateStepDisplay();
                updateProgressBar();
                
                if (currentStep === 3) {
                    showConfirmation();
                }
            }
        }
        
        function prevStep() {
            currentStep--;
            updateStepDisplay();
            updateProgressBar();
        }
        
        function updateStepDisplay() {
            // Esconder todos os steps
            document.querySelectorAll('.form-step').forEach(step => {
                step.classList.remove('active');
            });
            
            // Mostrar step atual
            document.getElementById('step' + currentStep).classList.add('active');
            
            // Atualizar indicadores
            for (let i = 1; i <= 3; i++) {
                const indicator = document.getElementById('step' + i + '-indicator');
                if (i <= currentStep) {
                    indicator.className = 'text-primary fw-bold';
                } else {
                    indicator.className = 'text-muted';
                }
            }
        }
        
        function updateProgressBar() {
            const progress = (currentStep / 3) * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }
        
        function validateCurrentStep() {
            const currentStepEl = document.getElementById('step' + currentStep);
            const requiredFields = currentStepEl.querySelectorAll('[required]');
            
            for (let field of requiredFields) {
                if (!field.value.trim()) {
                    field.focus();
                    field.classList.add('is-invalid');
                    return false;
                }
                field.classList.remove('is-invalid');
            }
            
            // Validações específicas por step
            if (currentStep === 2) {
                if (!selectedVeiculo || !selectedMotorista) {
                    alert('Selecione um veículo e um motorista');
                    return false;
                }
            }
            
            return true;
        }
        
        // Busca de veículos
        function searchVeiculos(query) {
            if (query.length < 2) {
                document.getElementById('veiculoResults').style.display = 'none';
                return;
            }
            
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                fetch('/checklist/api/search/veiculos?q=' + encodeURIComponent(query))
                    .then(response => response.json())
                    .then(data => {
                        showVeiculoResults(data);
                    })
                    .catch(error => {
                        console.error('Erro na busca de veículos:', error);
                    });
            }, 300);
        }
        
        function showVeiculoResults(veiculos) {
            const resultsDiv = document.getElementById('veiculoResults');
            
            if (veiculos.length === 0) {
                resultsDiv.innerHTML = '<div class="search-result text-muted">Nenhum veículo encontrado</div>';
            } else {
                resultsDiv.innerHTML = veiculos.map(v => 
                    '<div class="search-result" onclick="selectVeiculo(' + JSON.stringify(v).replace(/"/g, '&quot;') + ')">' +
                    '<strong>' + v.placa + '</strong> - ' + (v.modelo || 'Sem modelo') +
                    '<br><small class="text-muted">Ano: ' + (v.ano || 'N/A') + ' | KM: ' + (v.km_atual || 0).toLocaleString() + '</small>' +
                    '</div>'
                ).join('');
            }
            
            resultsDiv.style.display = 'block';
        }
        
        function selectVeiculo(veiculo) {
            selectedVeiculo = veiculo;
            document.querySelector('[name="veiculo_id"]').value = veiculo.id;
            document.getElementById('veiculoSearch').value = veiculo.placa;
            document.getElementById('veiculoResults').style.display = 'none';
            
            // Mostrar veículo selecionado
            document.getElementById('veiculoInfo').innerHTML = 
                '<strong>' + veiculo.placa + '</strong> - ' + (veiculo.modelo || 'Sem modelo') +
                '<br><small class="text-muted">Ano: ' + (veiculo.ano || 'N/A') + ' | KM Atual: ' + (veiculo.km_atual || 0).toLocaleString() + '</small>';
            document.getElementById('selectedVeiculo').style.display = 'block';
            document.getElementById('veiculoSearch').style.display = 'none';
        }
        
        function clearVeiculo() {
            selectedVeiculo = null;
            document.querySelector('[name="veiculo_id"]').value = '';
            document.getElementById('veiculoSearch').value = '';
            document.getElementById('selectedVeiculo').style.display = 'none';
            document.getElementById('veiculoSearch').style.display = 'block';
            document.getElementById('veiculoSearch').focus();
        }
        
        // Busca de motoristas (similar aos veículos)
        function searchMotoristas(query) {
            if (query.length < 2) {
                document.getElementById('motoristaResults').style.display = 'none';
                return;
            }
            
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                fetch('/checklist/api/search/motoristas?q=' + encodeURIComponent(query))
                    .then(response => response.json())
                    .then(data => {
                        showMotoristaResults(data);
                    })
                    .catch(error => {
                        console.error('Erro na busca de motoristas:', error);
                    });
            }, 300);
        }
        
        function showMotoristaResults(motoristas) {
            const resultsDiv = document.getElementById('motoristaResults');
            
            if (motoristas.length === 0) {
                resultsDiv.innerHTML = '<div class="search-result text-muted">Nenhum motorista encontrado</div>';
            } else {
                resultsDiv.innerHTML = motoristas.map(m => 
                    '<div class="search-result" onclick="selectMotorista(' + JSON.stringify(m).replace(/"/g, '&quot;') + ')">' +
                    '<strong>' + m.nome + '</strong>' +
                    '<br><small class="text-muted">CNH: ' + (m.cnh || 'N/A') + ' | Categoria: ' + (m.categoria || 'N/A') + '</small>' +
                    '</div>'
                ).join('');
            }
            
            resultsDiv.style.display = 'block';
        }
        
        function selectMotorista(motorista) {
            selectedMotorista = motorista;
            document.querySelector('[name="motorista_id"]').value = motorista.id;
            document.getElementById('motoristaSearch').value = motorista.nome;
            document.getElementById('motoristaResults').style.display = 'none';
            
            // Mostrar motorista selecionado
            document.getElementById('motoristaInfo').innerHTML = 
                '<strong>' + motorista.nome + '</strong>' +
                '<br><small class="text-muted">CNH: ' + (motorista.cnh || 'N/A') + ' | Categoria: ' + (motorista.categoria || 'N/A') + '</small>';
            document.getElementById('selectedMotorista').style.display = 'block';
            document.getElementById('motoristaSearch').style.display = 'none';
        }
        
        function clearMotorista() {
            selectedMotorista = null;
            document.querySelector('[name="motorista_id"]').value = '';
            document.getElementById('motoristaSearch').value = '';
            document.getElementById('selectedMotorista').style.display = 'none';
            document.getElementById('motoristaSearch').style.display = 'block';
            document.getElementById('motoristaSearch').focus();
        }
        
        // Confirmação
        function showConfirmation() {
            const formData = new FormData(document.getElementById('newChecklistForm'));
            const tipo = formData.get('tipo');
            const modeloSelect = document.querySelector('[name="modelo_id"]');
            const modeloNome = modeloSelect.options[modeloSelect.selectedIndex].text;
            
            document.getElementById('confirmationData').innerHTML = 
                '<div class="row">' +
                '<div class="col-md-6">' +
                '<h6>Configuração:</h6>' +
                '<ul class="list-unstyled">' +
                '<li><strong>Tipo:</strong> ' + tipo.toUpperCase() + '</li>' +
                '<li><strong>Modelo:</strong> ' + modeloNome + '</li>' +
                '<li><strong>Odômetro:</strong> ' + formData.get('odometro_ini') + ' km</li>' +
                '</ul>' +
                '</div>' +
                '<div class="col-md-6">' +
                '<h6>Seleções:</h6>' +
                '<ul class="list-unstyled">' +
                '<li><strong>Veículo:</strong> ' + selectedVeiculo.placa + '</li>' +
                '<li><strong>Motorista:</strong> ' + selectedMotorista.nome + '</li>' +
                '</ul>' +
                '</div>' +
                '</div>';
        }
        
        // Geolocalização
        function getLocation() {
            if (navigator.geolocation) {
                document.querySelector('[name="geo_inicio"]').value = 'Detectando...';
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        document.querySelector('[name="geo_inicio"]').value = lat + ',' + lng;
                    },
                    function(error) {
                        document.querySelector('[name="geo_inicio"]').value = 'Erro ao detectar localização';
                        console.error('Erro de geolocalização:', error);
                    }
                );
            } else {
                alert('Geolocalização não suportada neste navegador');
            }
        }
        
        // Submit do formulário
        document.getElementById('newChecklistForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                tipo: formData.get('tipo'),
                modelo_id: parseInt(formData.get('modelo_id')),
                veiculo_id: parseInt(formData.get('veiculo_id')),
                motorista_id: parseInt(formData.get('motorista_id')),
                odometro_ini: parseInt(formData.get('odometro_ini')),
                geo_inicio: formData.get('geo_inicio') || null
            };
            
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Criando...';
            
            fetch('/checklist/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.id) {
                    alert('Checklist criado com sucesso!');
                    window.location.href = '/checklist/' + data.id + '/execute';
                } else {
                    throw new Error(data.error || 'Erro ao criar checklist');
                }
            })
            .catch(error => {
                alert('Erro: ' + error.message);
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('submitBtn').innerHTML = '<i class="bi bi-check-circle me-2"></i>Criar Checklist';
            });
        });
        
        // Event listeners
        document.getElementById('veiculoSearch').addEventListener('input', function() {
            searchVeiculos(this.value);
        });
        
        document.getElementById('motoristaSearch').addEventListener('input', function() {
            searchMotoristas(this.value);
        });
        
        // Esconder resultados ao clicar fora
        document.addEventListener('click', function(e) {
            if (!e.target.closest('#veiculoSearch') && !e.target.closest('#veiculoResults')) {
                document.getElementById('veiculoResults').style.display = 'none';
            }
            if (!e.target.closest('#motoristaSearch') && !e.target.closest('#motoristaResults')) {
                document.getElementById('motoristaResults').style.display = 'none';
            }
        });
        
        // Carregar modelos de checklist
        fetch('/checklist/api/modelos')
            .then(response => response.json())
            .then(modelos => {
                const select = document.querySelector('[name="modelo_id"]');
                select.innerHTML = '<option value="">Selecione um modelo...</option>';
                
                modelos.forEach(modelo => {
                    const option = document.createElement('option');
                    option.value = modelo.id;
                    option.textContent = modelo.nome + ' (' + modelo.tipo.toUpperCase() + ')';
                    select.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Erro ao carregar modelos:', error);
                document.querySelector('[name="modelo_id"]').innerHTML = '<option value="">Erro ao carregar modelos</option>';
            });
        
        // Detectar localização automaticamente ao carregar
        getLocation();
    </script>
</body>
</html>
"""

@bp.route("/new")
def new_checklist():
    """Formulário para novo checklist"""
    return render_template_string(NEW_CHECKLIST_TEMPLATE)

@bp.route("/api/start", methods=['POST'])
def api_start_checklist():
    """Proxy para iniciar checklist"""
    data = request.get_json()
    
    api_data = make_api_request('POST', '/checklist/start', json=data)
    
    if api_data:
        return jsonify(api_data)
    else:
        return jsonify({"error": "Erro ao criar checklist"}), 500

@bp.route("/api/modelos")
def api_list_modelos():
    """Proxy para listar modelos"""
    data = make_api_request('GET', '/checklist/modelos')
    return jsonify(data or [])