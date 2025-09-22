# flask_dashboard/app/blueprints/main.py
"""
Blueprint principal do dashboard
"""
from flask import Blueprint, render_template_string, request, jsonify, current_app, session
from app.utils import api_client as api
import requests

bp = Blueprint("main", __name__)


def _api_base():
    """Obtém API_BASE com possibilidade de override por sessão."""
    return session.get("API_BASE_OVERRIDE") or current_app.config.get("API_BASE", "http://localhost:8005")

# Template HTML moderno para o dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Transpontual</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        :root {
            --bs-primary: #0d47a1;
            --bs-success: #1b5e20;
            --bs-danger: #c62828;
            --bs-warning: #ef6c00;
        }

        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }

        .metric-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: none;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }

        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        .metric-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            margin-bottom: 15px;
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            color: #2d3436;
        }

        .metric-label {
            color: #636e72;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 10px;
        }

        .quick-actions {
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
        }

        .quick-action-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            border-radius: 10px;
            padding: 15px;
            text-decoration: none;
            display: block;
            transition: all 0.3s ease;
            margin-bottom: 10px;
        }

        .quick-action-btn:hover {
            background: rgba(255,255,255,0.3);
            color: white;
            border-color: rgba(255,255,255,0.5);
            transform: translateX(5px);
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }

        .status-online { background: #00b894; animation: pulse 2s infinite; }
        .status-offline { background: #e17055; }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .navbar {
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .card {
            border: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="bi bi-truck me-2"></i>Transpontual
            </a>
            <div class="d-flex align-items-center gap-3">
                <span class="status-indicator status-{{ 'online' if api_status == 'ok' else 'offline' }}"></span>
                <span class="text-light small">{{ api_status.upper() }}</span>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Dashboard Header -->
        <div class="dashboard-header">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="mb-2">
                        <i class="bi bi-speedometer2 me-2"></i>
                        Dashboard Operacional
                    </h1>
                    <p class="mb-0 opacity-75">
                        Sistema {{ 'Online' if api_status == 'ok' else 'Offline' }} - Última atualização: <span id="last-update">carregando...</span>
                    </p>
                </div>
                <div class="col-md-4 text-end">
                    <button class="btn btn-light btn-sm me-2" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Atualizar
                    </button>
                    <button class="btn btn-light btn-sm" onclick="testHealth()">
                        <i class="bi bi-plug me-1"></i>Testar API
                    </button>
                </div>
            </div>
        </div>

        <!-- KPIs Row -->
        <div class="row mb-4">
            <div class="col-xl-3 col-lg-6 col-md-6 mb-4">
                <div class="metric-card">
                    <div class="d-flex justify-content-between">
                        <div class="flex-grow-1">
                            <p class="metric-label">Total de Checklists</p>
                            <h2 class="metric-value" id="total-checklists">
                                {{ stats.total_checklists or 0 }}
                            </h2>
                        </div>
                        <div class="metric-icon" style="background: linear-gradient(135deg, #74b9ff, #0984e3);">
                            <i class="bi bi-clipboard-data"></i>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-lg-6 col-md-6 mb-4">
                <div class="metric-card">
                    <div class="d-flex justify-content-between">
                        <div class="flex-grow-1">
                            <p class="metric-label">Taxa de Aprovação</p>
                            <h2 class="metric-value" id="approval-rate">
                                {{ stats.taxa_aprovacao or 0 }}%
                            </h2>
                        </div>
                        <div class="metric-icon" style="background: linear-gradient(135deg, #00b894, #00a085);">
                            <i class="bi bi-check-circle"></i>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-lg-6 col-md-6 mb-4">
                <div class="metric-card">
                    <div class="d-flex justify-content-between">
                        <div class="flex-grow-1">
                            <p class="metric-label">Veículos Ativos</p>
                            <h2 class="metric-value" id="veiculos-ativos">
                                {{ stats.veiculos_ativos or 0 }}
                            </h2>
                        </div>
                        <div class="metric-icon" style="background: linear-gradient(135deg, #74b9ff, #0984e3);">
                            <i class="bi bi-truck"></i>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-xl-3 col-lg-6 col-md-6 mb-4">
                <div class="metric-card">
                    <div class="d-flex justify-content-between">
                        <div class="flex-grow-1">
                            <p class="metric-label">OS Abertas</p>
                            <h2 class="metric-value" id="os-abertas">
                                {{ stats.os_abertas or 0 }}
                            </h2>
                        </div>
                        <div class="metric-icon" style="background: linear-gradient(135deg, #fdcb6e, #f39c12);">
                            <i class="bi bi-tools"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Ações Rápidas -->
            <div class="col-xl-6 col-lg-6 mb-4">
                <div class="quick-actions">
                    <h5 class="mb-4">
                        <i class="bi bi-lightning me-2"></i>Ações Rápidas
                    </h5>

                    <button class="quick-action-btn w-100 border-0" onclick="openNewChecklist()">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-plus-circle me-3 fs-5"></i>
                            <div class="text-start">
                                <strong>Novo Checklist</strong>
                                <br><small>Iniciar novo checklist veicular</small>
                            </div>
                        </div>
                    </button>

                    <a href="/checklists" class="quick-action-btn">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-clock-history me-3 fs-5"></i>
                            <div class="text-start">
                                <strong>Ver Checklists</strong>
                                <br><small>Listar todos os checklists</small>
                            </div>
                        </div>
                    </a>

                    <a href="/modelos/pre" class="quick-action-btn">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-list-check me-3 fs-5"></i>
                            <div class="text-start">
                                <strong>Modelos de Checklist</strong>
                                <br><small>Gerenciar itens e modelos</small>
                            </div>
                        </div>
                    </a>
                </div>
            </div>

            <!-- Status e Informações -->
            <div class="col-xl-6 col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="bi bi-info-circle me-2"></i>Status do Sistema
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex align-items-center">
                                <div class="status-indicator status-{{ 'online' if api_status == 'ok' else 'offline' }}"></div>
                                <div>
                                    <strong>API Backend:</strong> {{ api_status.upper() }}
                                    <br><small class="text-muted">{{ api_base }}</small>
                                </div>
                            </div>
                        </div>

                        <div class="mb-3">
                            <div class="d-flex align-items-center">
                                <div class="status-indicator status-online"></div>
                                <div>
                                    <strong>Dashboard:</strong> ONLINE
                                    <br><small class="text-muted">Flask Dashboard v1.0</small>
                                </div>
                            </div>
                        </div>

                        <div class="d-flex gap-2 mt-3">
                            <a href="{{ api_docs_url }}" target="_blank" class="btn btn-outline-primary btn-sm">
                                <i class="bi bi-book me-1"></i>API Docs
                            </a>
                            <button class="btn btn-outline-secondary btn-sm" onclick="testApi()">
                                <i class="bi bi-wifi me-1"></i>Testar API
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Atualizar timestamp
        function updateLastUpdateTime() {
            const now = new Date();
            document.getElementById('last-update').textContent = now.toLocaleTimeString('pt-BR');
        }

        // Inicializar
        document.addEventListener('DOMContentLoaded', function() {
            updateLastUpdateTime();
            setInterval(updateLastUpdateTime, 1000);

            // Auto-refresh stats a cada 30 segundos
            setInterval(refreshStats, 30000);
            setTimeout(refreshStats, 1000);
        });

        // Refresh stats
        function refreshStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (!data.error) {
                        document.getElementById('total-checklists').textContent = data.total_checklists || 0;
                        document.getElementById('approval-rate').textContent = (data.taxa_aprovacao || 0) + '%';
                        document.getElementById('veiculos-ativos').textContent = data.veiculos_ativos || 0;
                        document.getElementById('os-abertas').textContent = data.os_abertas || 0;
                    }
                })
                .catch(error => console.log('Erro ao atualizar stats:', error));
        }

        function testApi() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    alert('API funcionando! Stats: ' + JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    alert('Erro na API: ' + error);
                });
        }

        function testHealth(){
            fetch('/ui/health')
              .then(r => r.json())
              .then(data => alert('Health: ' + JSON.stringify(data)))
              .catch(err => alert('Erro ao conectar: ' + err));
        }

        function openNewChecklist() {
            // carregar opções
            fetch('/ui/checklist/options')
              .then(r => r.json())
              .then(data => {
                const vSel = document.getElementById('veiculo_id');
                const mSel = document.getElementById('motorista_id');
                const modSel = document.getElementById('modelo_id');
                vSel.innerHTML = data.vehicles.map(v => `<option value="${v.id}">${v.placa} - ${v.modelo||''}</option>`).join('');
                mSel.innerHTML = data.drivers.map(u => `<option value="${u.id}">${u.nome}</option>`).join('');
                modSel.innerHTML = data.models.map(md => `<option value="${md.id}">${md.nome} (${md.tipo})</option>`).join('');
                const modal = new bootstrap.Modal(document.getElementById('novoChecklistModal'));
                modal.show();
              })
              .catch(err => alert('Erro ao carregar opções: ' + err));
        }

        function submitNovoChecklist() {
            const body = {
                veiculo_id: parseInt(document.getElementById('veiculo_id').value),
                motorista_id: parseInt(document.getElementById('motorista_id').value),
                modelo_id: parseInt(document.getElementById('modelo_id').value),
                tipo: document.getElementById('tipo').value,
                odometro_ini: document.getElementById('odometro_ini').value ? parseInt(document.getElementById('odometro_ini').value) : null
            };
            fetch('/ui/checklist/start', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
              .then(r => r.json())
              .then(data => {
                if (data.error) {
                    const el = document.getElementById('novoChecklistError');
                    el.classList.remove('d-none');
                    el.textContent = data.error;
                    return;
                }
                // sucesso -> abrir página do checklist
                bootstrap.Modal.getInstance(document.getElementById('novoChecklistModal')).hide();
                window.location.href = `/checklist/${data.id}`;
              })
              .catch(err => alert('Erro ao iniciar: ' + err));
        }
    </script>
    
    <!-- Modal Novo Checklist -->
    <div class="modal fade" id="novoChecklistModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Iniciar Novo Checklist</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form id="formNovoChecklist">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label">Veículo</label>
                  <select class="form-select" id="veiculo_id" required></select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Motorista</label>
                  <select class="form-select" id="motorista_id" required></select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Modelo</label>
                  <select class="form-select" id="modelo_id" required></select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Tipo</label>
                  <select class="form-select" id="tipo" required>
                    <option value="pre">Pré-viagem</option>
                    <option value="pos">Pós-viagem</option>
                    <option value="extra">Extra</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Odômetro Inicial</label>
                  <input type="number" class="form-control" id="odometro_ini" min="0" placeholder="Opcional">
                </div>
              </div>
            </form>
            <div class="alert alert-danger d-none mt-3" id="novoChecklistError"></div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="button" class="btn btn-primary" onclick="submitNovoChecklist()">Iniciar</button>
          </div>
        </div>
      </div>
    </div>
    <script>
        function testApi() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    alert('API funcionando! Stats: ' + JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    alert('Erro na API: ' + error);
                });
        }
        function testHealth(){
            fetch('/ui/health')
              .then(r => r.json())
              .then(data => alert('Health: ' + JSON.stringify(data)))
              .catch(err => alert('Erro ao conectar: ' + err));
        }
        // API_BASE selector
        function initApiBaseUI(){
            const cur = '{{ api_base }}';
            const sel = document.getElementById('apiBaseSelect');
            const inp = document.getElementById('apiBaseCustom');
            if(!sel || !inp) return;
            const known = [ 'http://localhost:8005', 'http://backend:8005', 'http://host.docker.internal:8005' ];
            if(known.includes(cur)){
                sel.value = cur;
                inp.classList.add('d-none');
            } else {
                sel.value = '__custom__';
                inp.classList.remove('d-none');
                inp.value = cur || '';
            }
            sel.addEventListener('change', ()=>{
                if(sel.value === '__custom__'){
                    inp.classList.remove('d-none');
                    inp.focus();
                } else {
                    inp.classList.add('d-none');
                }
            });
        }
        function applyApiBase(){
            const sel = document.getElementById('apiBaseSelect');
            const inp = document.getElementById('apiBaseCustom');
            let val = sel.value === '__custom__' ? (inp.value||'') : sel.value;
            if(!val){ alert('Informe uma URL'); return; }
            fetch('/ui/api_base', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({api_base: val})})
              .then(()=> location.reload())
              .catch(err => alert('Erro ao definir API_BASE: ' + err));
        }
        function clearApiBase(){
            fetch('/ui/api_base', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})})
              .then(()=> location.reload())
              .catch(err => alert('Erro ao limpar override: ' + err));
        }
        initApiBaseUI();
        function setApiBase(){
            var cur = '{{ api_base }}';
            var val = prompt('Defina API_BASE para o Dashboard', cur||'http://localhost:8005');
            if(!val) return;
            fetch('/ui/api_base', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({api_base: val})})
              .then(()=> location.reload())
              .catch(err => alert('Erro ao definir API_BASE: ' + err));
        }
        
        function openNewChecklist() {
            // carregar opções
            fetch('/ui/checklist/options')
              .then(r => r.json())
              .then(data => {
                const vSel = document.getElementById('veiculo_id');
                const mSel = document.getElementById('motorista_id');
                const modSel = document.getElementById('modelo_id');
                vSel.innerHTML = data.vehicles.map(v => `<option value="${v.id}">${v.placa} - ${v.modelo||''}</option>`).join('');
                mSel.innerHTML = data.drivers.map(u => `<option value="${u.id}">${u.nome}</option>`).join('');
                modSel.innerHTML = data.models.map(md => `<option value="${md.id}">${md.nome} (${md.tipo})</option>`).join('');
                const modal = new bootstrap.Modal(document.getElementById('novoChecklistModal'));
                modal.show();
              })
              .catch(err => alert('Erro ao carregar opções: ' + err));
        }

        function submitNovoChecklist() {
            const body = {
                veiculo_id: parseInt(document.getElementById('veiculo_id').value),
                motorista_id: parseInt(document.getElementById('motorista_id').value),
                modelo_id: parseInt(document.getElementById('modelo_id').value),
                tipo: document.getElementById('tipo').value,
                odometro_ini: document.getElementById('odometro_ini').value ? parseInt(document.getElementById('odometro_ini').value) : null
            };
            fetch('/ui/checklist/start', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
              .then(r => r.json())
              .then(data => {
                if (data.error) {
                    const el = document.getElementById('novoChecklistError');
                    el.classList.remove('d-none');
                    el.textContent = data.error;
                    return;
                }
                // sucesso -> abrir página do checklist
                bootstrap.Modal.getInstance(document.getElementById('novoChecklistModal')).hide();
                window.location.href = `/checklist/${data.id}`;
              })
              .catch(err => alert('Erro ao iniciar: ' + err));
        }
        
        // Auto-refresh stats
        function refreshStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (!data.error) {
                        document.getElementById('total-checklists').textContent = data.total_checklists || 0;
                        document.getElementById('taxa-aprovacao').textContent = (data.taxa_aprovacao || 0) + '%';
                        document.getElementById('veiculos').textContent = data.veiculos_ativos || 0;
                        document.getElementById('os-abertas').textContent = data.os_abertas || 0;
                    }
                })
                .catch(error => console.log('Erro ao atualizar stats:', error));
        }
        
        // Refresh a cada 30 segundos
        setInterval(refreshStats, 30000);
        
        // Refresh na carga
        setTimeout(refreshStats, 1000);
        // Init theme switch for navbar
        (function(){
          const sw=document.getElementById('themeSwitch');
          if(sw){ sw.checked=document.documentElement.classList.contains('dark'); sw.addEventListener('change', ()=>{ const el=document.documentElement; const v=el.classList.toggle('dark'); try{localStorage.setItem('theme', v?'dark':'light');}catch(e){}; }); }
        })();
    </script>
</body>
</html>
"""

@bp.route("/")
def dashboard():
    """Dashboard principal"""
    try:
        # Testar conexão com API
        api_base = _api_base()
        try:
            response = requests.get(f"{api_base}/api/v1/health", timeout=5)
            if response.status_code != 200:
                # Fallback para /health simples
                response = requests.get(f"{api_base}/health", timeout=5)
            api_status = "ok" if response.status_code == 200 else "error"
        except:
            # Último fallback: tentar /health
            try:
                response = requests.get(f"{api_base}/health", timeout=5)
                api_status = "ok" if response.status_code == 200 else "error"
            except:
                api_status = "error"
        
        # Consumir API real (quando disponível) – fallback para simulados
        stats = {"total_checklists": 0, "taxa_aprovacao": 0, "veiculos_ativos": 0, "os_abertas": 0}
        try:
            sresp = requests.get(f"{api_base}/api/v1/checklist/stats/summary", timeout=5)
            if sresp.status_code != 200:
                sresp = requests.get(f"{api_base}/kpis/summary", timeout=5)
            s = sresp.json()
            stats["total_checklists"] = s.get("total_checklists", s.get("total", 0))
            stats["taxa_aprovacao"] = round(s.get("taxa_aprovacao", 0), 1)
        except Exception:
            pass
        
        context = {
            "api_status": api_status,
            "stats": stats,
            "api_docs_url": f"{api_base}/docs",
            "api_base": api_base,
        }
        
        return render_template_string(DASHBOARD_TEMPLATE, **context)
        
    except Exception as e:
        return f"""
        <div class="alert alert-danger">
            <strong>Erro:</strong> {str(e)}
        </div>
        <a href="/" class="btn btn-primary">Tentar Novamente</a>
        """

@bp.route("/api/stats")
def api_stats():
    """API para estatísticas do dashboard"""
    try:
        # Proxy simples para a API quando possível
        api_base = _api_base()
        try:
            s = requests.get(f"{api_base}/api/v1/checklist/stats/summary", timeout=5).json()
        except Exception:
            s = {"total_checklists": 0, "taxa_aprovacao": 0}
        return jsonify(s)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/ui/health")
def ui_health():
    """Proxy simples do health da API alvo."""
    try:
        api_base = _api_base()
        r = requests.get(f"{api_base}/api/v1/health", timeout=5)
        if r.status_code != 200:
            r = requests.get(f"{api_base}/health", timeout=5)
        return jsonify(r.json() if r.content else {"status": r.status_code}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@bp.route("/ui/api_base", methods=["POST"])
def ui_set_api_base():
    """Define ou limpa override de API_BASE na sessão do Dashboard."""
    data = request.get_json(silent=True) or {}
    val = data.get("api_base")
    if not val:
        session.pop("API_BASE_OVERRIDE", None)
        return jsonify({"ok": True, "cleared": True})
    val = str(val).strip()
    if not (val.startswith("http://") or val.startswith("https://")):
        return jsonify({"error": "URL inválida. Use http(s)://..."}), 400
    session["API_BASE_OVERRIDE"] = val
    return jsonify({"ok": True, "api_base": val})


# ======================== Lista de checklists recentes ========================
RECENT_LIST_TEMPLATE = """
<!doctype html>
<html lang=pt-BR>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>Checklists Recentes</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css">
  <script>(function(){try{const t=localStorage.getItem('theme')||'light'; if(t==='dark') document.documentElement.classList.add('dark');}catch(e){}})();</script>
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>Checklists Recentes</h3>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-secondary" id="themeToggle">Tema</button>
        <a href="/" class="btn btn-outline-secondary">← Dashboard</a>
      </div>
    </div>
    <form method="get" class="row g-2 mb-3">
      <div class="col-12 col-md-3"><input class="form-control" placeholder="Placa" name="placa" value="{{ placa or '' }}"></div>
      <div class="col-12 col-md-3"><input class="form-control" placeholder="Motorista" name="motorista_nome" value="{{ motorista_nome or '' }}"></div>
      <div class="col-6 col-md-2"><input class="form-control" type="date" name="data_inicio" value="{{ data_inicio or '' }}"></div>
      <div class="col-6 col-md-2"><input class="form-control" type="date" name="data_fim" value="{{ data_fim or '' }}"></div>
      <div class="col-6 col-md-1">
        <select name="per_page" class="form-select">
          {% for n in [10,20,50,100] %}
          <option value="{{n}}" {% if per_page==n %}selected{% endif %}>{{n}}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-6 col-md-1"><button class="btn btn-primary w-100">Filtrar</button></div>
    </form>
    <div class="card">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0">
            <thead><tr><th>ID</th><th>Data</th><th>Veículo</th><th>Motorista</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {% for c in items %}
              <tr>
                <td>#{{ c.id }}</td>
                <td>{{ c.dt_inicio or '-' }}</td>
                <td>{{ c.veiculo_placa or '-' }} {{ c.veiculo_modelo or '' }}</td>
                <td>{{ c.motorista_nome or '-' }}</td>
                <td>
                  <span class="badge badge-status status-{{ c.status }}">{{ c.status }}</span>
                </td>
                <td class="text-end"><a class="btn btn-sm btn-primary" href="/checklist/{{ c.id }}">Abrir</a></td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
      <div class="card-footer d-flex justify-content-between">
        <div class="text-muted small">Total: {{ total }}</div>
        <div class="btn-group">
          <a class="btn btn-sm btn-outline-secondary {% if page<=1 %}disabled{% endif %}" href="?page={{ page-1 if page>1 else 1 }}&per_page={{ per_page }}&placa={{ placa or '' }}&motorista_nome={{ motorista_nome or '' }}&data_inicio={{ data_inicio or '' }}&data_fim={{ data_fim or '' }}">Anterior</a>
          <span class="btn btn-sm btn-outline-secondary disabled">Página {{ page }} / {{ pages }}</span>
          <a class="btn btn-sm btn-outline-secondary {% if page>=pages %}disabled{% endif %}" href="?page={{ page+1 if page<pages else pages }}&per_page={{ per_page }}&placa={{ placa or '' }}&motorista_nome={{ motorista_nome or '' }}&data_inicio={{ data_inicio or '' }}&data_fim={{ data_fim or '' }}">Próxima</a>
        </div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    (function(){
      function updateToggleIcon(){
        const btn=document.getElementById('themeToggle');
        if(!btn) return;
        const dark=document.documentElement.classList.contains('dark');
        btn.innerHTML = dark ? '<i class="bi bi-sun me-1"></i>Claro' : '<i class="bi bi-moon-stars me-1"></i>Escuro';
        btn.onclick = function(){ const el=document.documentElement; const d=el.classList.toggle('dark'); try{localStorage.setItem('theme', d?'dark':'light');}catch(e){}; updateToggleIcon(); }
      }
      updateToggleIcon();
    })();
  </script>
  </body>
  </html>
"""


@bp.route("/checklists")
def checklists():
    api_base = current_app.config.get("API_BASE", "http://localhost:8005")
    try:
        page = int(request.args.get('page', '1'))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get('per_page', '20'))
    except Exception:
        per_page = 20
    placa = request.args.get('placa')
    motorista_nome = request.args.get('motorista_nome')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    params = {
        "page": page,
        "per_page": per_page,
        "order_by": "dt_inicio",
        "order_dir": "desc",
    }
    if placa: params["placa"] = placa
    if motorista_nome: params["motorista_nome"] = motorista_nome
    if data_inicio: params["data_inicio"] = data_inicio
    if data_fim: params["data_fim"] = data_fim
    try:
        r = requests.get(f"{api_base}/api/v1/checklist", params=params, timeout=5).json()
        items = r.get("items", []) if isinstance(r, dict) else []
        total = r.get("total", 0) if isinstance(r, dict) else len(items)
        pages = r.get("pages", 1) if isinstance(r, dict) else 1
    except Exception:
        items, total, pages = [], 0, 1
    return render_template_string(RECENT_LIST_TEMPLATE, items=items, total=total, pages=pages, page=page, per_page=per_page, placa=placa, motorista_nome=motorista_nome, data_inicio=data_inicio, data_fim=data_fim)


@bp.route("/ui/checklist/options")
def ui_checklist_options():
    """Retorna listas para o modal: models, vehicles, drivers."""
    client = api.APIClient()
    models_list = client.get("/api/v1/checklist/modelos") or []
    vehicles = client.get("/api/v1/vehicles") or []
    drivers = client.get("/api/v1/drivers") or []
    # normalizar
    return jsonify({
        "models": models_list if isinstance(models_list, list) else [],
        "vehicles": vehicles if isinstance(vehicles, list) else [],
        "drivers": drivers if isinstance(drivers, list) else [],
    })


@bp.route("/ui/checklist/start", methods=["POST"])
def ui_checklist_start():
    body = request.get_json() or {}
    required = ["veiculo_id", "motorista_id", "modelo_id", "tipo"]
    missing = [k for k in required if k not in body]
    if missing:
        return jsonify({"error": f"Campos obrigatórios: {', '.join(missing)}"}), 400
    client = api.APIClient()
    resp = client.post("/api/v1/checklist/start", data=body)
    if isinstance(resp, dict) and resp.get("error"):
        return jsonify({"error": resp.get("error")}), 502
    return jsonify(resp)


# ======================== Páginas e APIs de apoio ========================

# Página de lista de modelos pré-viagem
MODELOS_PRE_TEMPLATE = """
<!doctype html>
<html lang=pt-BR>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>Modelos (Pré-viagem)</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css">
  <script>(function(){try{const t=localStorage.getItem('theme')||'light'; if(t==='dark') document.documentElement.classList.add('dark');}catch(e){} })();</script>
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>Modelos de Checklist (Pré-viagem)</h3>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-secondary" id="themeToggle">Tema</button>
        <a href="/" class="btn btn-outline-secondary">← Voltar</a>
      </div>
    </div>
    {% if models %}
      <div class="list-group">
        {% for m in models %}
          <a class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" href="/modelos/{{m.id}}">
            <div>
              <div class="fw-bold">{{ m.nome }}</div>
              <div class="text-muted small">Tipo: {{ m.tipo }} • Criado em: {{ m.criado_em }}</div>
            </div>
            <i class="bi bi-chevron-right"></i>
          </a>
        {% endfor %}
      </div>
    {% else %}
      <div class="alert alert-info">Nenhum modelo encontrado.</div>
    {% endif %}
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    (function(){
      function updateToggleIcon(){
        const btn=document.getElementById('themeToggle');
        if(!btn) return;
        const dark=document.documentElement.classList.contains('dark');
        btn.innerHTML = dark ? '<i class="bi bi-sun me-1"></i>Claro' : '<i class="bi bi-moon-stars me-1"></i>Escuro';
        btn.onclick = function(){ const el=document.documentElement; const d=el.classList.toggle('dark'); try{localStorage.setItem('theme', d?'dark':'light');}catch(e){}; updateToggleIcon(); }
      }
      updateToggleIcon();
    })();
  </script>
  <script>
    (function(){
      function updateToggleIcon(){
        const btn=document.getElementById('themeToggle');
        if(!btn) return;
        const dark=document.documentElement.classList.contains('dark');
        btn.innerHTML = dark ? '<i class="bi bi-sun me-1"></i>Claro' : '<i class="bi bi-moon-stars me-1"></i>Escuro';
        btn.onclick = function(){ const el=document.documentElement; const d=el.classList.toggle('dark'); try{localStorage.setItem('theme', d?'dark':'light');}catch(e){}; updateToggleIcon(); }
      }
      updateToggleIcon();
    })();
  </script>
</body>
</html>
"""


@bp.route("/modelos/pre")
def modelos_pre():
    client = api.APIClient()
    resp = client.get("/api/v1/checklist/modelos")
    models_list = []
    if isinstance(resp, list):
        models_list = [m for m in resp if isinstance(m, dict) and m.get("tipo") == "pre" and m.get("ativo")]
    elif isinstance(resp, dict) and resp.get("error"):
        # Mantém a página funcional mesmo com erro na API
        print(f"Erro ao listar modelos: {resp.get('error')}")
    return render_template_string(MODELOS_PRE_TEMPLATE, models=models_list)


# Página de itens do modelo + cadastro de novo item
MODELO_ITENS_TEMPLATE = """
<!doctype html>
<html lang=pt-BR>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>Itens do Modelo</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css">
  <script>(function(){try{const t=localStorage.getItem('theme')||'light'; if(t==='dark') document.documentElement.classList.add('dark');}catch(e){} })();</script>
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>{{ model.nome }} ({{ model.tipo }})</h3>
      <div>
        <button class="btn btn-outline-secondary me-2" id="themeToggle">Tema</button>
        <a href="/modelos/pre" class="btn btn-outline-secondary">← Modelos</a>
        <a href="/" class="btn btn-outline-secondary ms-2">Dashboard</a>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-lg-7">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span>Itens</span>
            <div class="d-flex align-items-center gap-2">
              <form method="get" class="d-flex align-items-center gap-2">
                <input type="hidden" name="page" value="{{ page }}"/>
                <label class="text-muted small">por página</label>
                <select class="form-select form-select-sm" name="per_page" onchange="this.form.submit()">
                  {% for opt in [10,20,50,100,200] %}
                    <option value="{{opt}}" {% if per_page == opt %}selected{% endif %}>{{opt}}</option>
                  {% endfor %}
                </select>
              </form>
              <button class="btn btn-sm btn-outline-primary" onclick="salvarOrdem()">Salvar ordem</button>
            </div>
          </div>
          <div class="card-body p-0">
            <table class="table table-striped mb-0" id="itensTable">
              <thead><tr><th style="width:40px"></th><th>#</th><th>Descrição</th><th>Severidade</th><th>Foto?</th><th>Bloqueia?</th></tr></thead>
              <tbody>
                {% for i in itens %}
                  <tr draggable="true" data-item-id="{{ i.id }}" class="draggable-row">
                    <td class="text-muted"><i class="bi bi-grip-vertical"></i></td>
                    <td class="ordem">{{ i.ordem }}</td>
                    <td>{{ i.descricao }}</td>
                    <td><span class="badge sev-{{ i.severidade }}">{{ i.severidade }}</span></td>
                    <td>{{ 'Sim' if i.exige_foto else 'Não' }}</td>
                    <td>{{ 'Sim' if i.bloqueia_viagem else 'Não' }}</td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          <div class="card-footer d-flex justify-content-between">
            <div>
              <span class="text-muted small">Total: {{ total }}</span>
            </div>
            <div class="btn-group">
              <a class="btn btn-sm btn-outline-secondary {% if page<=1 %}disabled{% endif %}" href="?page={{ page-1 if page>1 else 1 }}&per_page={{ per_page }}">Anterior</a>
              <span class="btn btn-sm btn-outline-secondary disabled">Página {{ page }} / {{ pages }}</span>
              <a class="btn btn-sm btn-outline-secondary {% if page>=pages %}disabled{% endif %}" href="?page={{ page+1 if page<pages else pages }}&per_page={{ per_page }}">Próxima</a>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-5">
        <div class="card">
          <div class="card-header">Cadastrar Novo Item</div>
          <div class="card-body">
            <form id="formNovoItem">
              <div class="row g-3">
                <div class="col-4">
                  <label class="form-label">Ordem</label>
                  <input type="number" min="1" class="form-control" id="ordem" required>
                </div>
                <div class="col-8">
                  <label class="form-label">Severidade</label>
                  <select class="form-select" id="severidade">
                    <option value="baixa">Baixa</option>
                    <option value="media" selected>Média</option>
                    <option value="alta">Alta</option>
                  </select>
                </div>
                <div class="col-12">
                  <label class="form-label">Descrição do item</label>
                  <textarea class="form-control" id="descricao" rows="2" required></textarea>
                </div>
                <div class="col-6">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="exige_foto">
                    <label class="form-check-label" for="exige_foto">Exige Foto</label>
                  </div>
                </div>
                <div class="col-6">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="bloqueia_viagem">
                    <label class="form-check-label" for="bloqueia_viagem">Bloqueia Viagem</label>
                  </div>
                </div>
              </div>
            </form>
            <div class="alert alert-danger d-none mt-3" id="novoItemError"></div>
          </div>
          <div class="card-footer text-end">
            <button class="btn btn-primary" onclick="submitNovoItem()">Cadastrar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    // Drag & Drop simples nas linhas da tabela
    const tableBody = document.querySelector('#itensTable tbody');
    let dragSrcRow = null;
    tableBody?.addEventListener('dragstart', (e) => {
      const tr = e.target.closest('tr');
      if (!tr) return;
      dragSrcRow = tr;
      e.dataTransfer.effectAllowed = 'move';
      tr.classList.add('table-warning');
    });
    tableBody?.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const tr = e.target.closest('tr');
      if (!tr || tr === dragSrcRow) return;
      const rect = tr.getBoundingClientRect();
      const next = (e.clientY - rect.top)/(rect.height) > 0.5;
      tableBody.insertBefore(dragSrcRow, next ? tr.nextSibling : tr);
    });
    tableBody?.addEventListener('dragend', (e) => {
      const trs = tableBody.querySelectorAll('tr');
      trs.forEach((row, idx) => {
        row.classList.remove('table-warning');
        row.querySelector('.ordem').textContent = (idx + 1 + ({{page}}-1)*{{per_page}});
      });
    });

    function salvarOrdem() {
      const ids = Array.from(document.querySelectorAll('#itensTable tbody tr')).map(tr => parseInt(tr.dataset.itemId));
      fetch('/ui/modelos/{{ model.id }}/itens/reorder', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ item_ids: ids, page: {{page}}, per_page: {{per_page}} })})
        .then(r => r.json())
        .then(data => {
          if (data.error) { alert('Erro ao salvar ordem: ' + data.error); return; }
          alert('Ordem salva com sucesso!');
        })
        .catch(err => alert('Erro: ' + err));
    }
    function submitNovoItem() {
      const body = {
        modelo_id: {{ model.id }},
        ordem: parseInt(document.getElementById('ordem').value),
        descricao: document.getElementById('descricao').value,
        tipo_resposta: 'ok',
        severidade: document.getElementById('severidade').value,
        exige_foto: document.getElementById('exige_foto').checked,
        bloqueia_viagem: document.getElementById('bloqueia_viagem').checked
      };
      fetch('/ui/modelos/{{ model.id }}/itens', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
        .then(r => r.json())
        .then(data => {
          if (data.error) {
            const el = document.getElementById('novoItemError');
            el.classList.remove('d-none');
            el.textContent = data.error;
            return;
          }
          location.reload();
        })
        .catch(err => alert('Erro ao cadastrar item: ' + err));
    }
  </script>
</body>
</html>
"""


@bp.route("/modelos/<int:modelo_id>")
def modelo_itens(modelo_id: int):
    client = api.APIClient()
    # Buscar um modelo específico da lista
    models_list = client.get("/api/v1/checklist/modelos") or []
    model = next((m for m in models_list if m.get("id") == modelo_id), None)
    if not model:
        return "Modelo não encontrado", 404
    itens = client.get(f"/api/v1/checklist/modelos/{modelo_id}/itens") or []
    # Paginação simples via query string
    try:
        page = int(request.args.get('page', '1'))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get('per_page', '50'))
    except Exception:
        per_page = 50
    page = max(1, page)
    per_page = min(200, max(1, per_page))
    total = len(itens)
    start = (page - 1) * per_page
    end = start + per_page
    itens_page = itens[start:end]
    pages = (total + per_page - 1) // per_page if per_page else 1
    return render_template_string(MODELO_ITENS_TEMPLATE, model=model, itens=itens_page, page=page, per_page=per_page, total=total, pages=pages)


@bp.route("/ui/modelos/<int:modelo_id>/itens", methods=["POST"])
def ui_modelo_add_item(modelo_id: int):
    body = request.get_json() or {}
    client = api.APIClient()
    resp = client.post(f"/api/v1/checklist/modelos/{modelo_id}/itens", data=body)
    if isinstance(resp, dict) and resp.get("error"):
        return jsonify({"error": resp.get("error")}), 502
    return jsonify(resp)


@bp.route("/ui/modelos/<int:modelo_id>/itens/reorder", methods=["POST"])
def ui_modelo_reorder_itens(modelo_id: int):
    data = request.get_json() or {}
    item_ids = data.get('item_ids') or []
    page = int(data.get('page') or 1)
    per_page = int(data.get('per_page') or len(item_ids) or 50)
    if not item_ids:
        return jsonify({"error": "Lista de itens vazia"}), 400
    start_ord = (page - 1) * per_page + 1
    client = api.APIClient()
    # Atualiza ordens dos itens desta página
    ordem = start_ord
    for iid in item_ids:
        resp = client.post(f"/api/v1/checklist/itens/{iid}", data={"ordem": ordem})
        # Se API não aceitar POST para update, usa PUT
        if isinstance(resp, dict) and resp.get("error"):
            # Tenta PUT
            try:
                import requests
                base = current_app.config.get("API_BASE", "http://localhost:8005")
                import json as _json
                requests.put(f"{base}/api/v1/checklist/itens/{iid}", json={"ordem": ordem}, timeout=10)
            except Exception:
                pass
        ordem += 1
    return jsonify({"ok": True})


# Página de execução do checklist (aprovação rápida por item)
CHECKLIST_DETAIL_TEMPLATE = """
<!doctype html>
<html lang=pt-BR>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>Checklist {{ chk.id }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/styles.css">
  <script>(function(){try{const t=localStorage.getItem('theme')||'light'; if(t==='dark') document.documentElement.classList.add('dark');}catch(e){} })();</script>
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h3>Checklist #{{ chk.id }} • {{ chk.tipo }} • Status: <span class="badge badge-status status-{{ chk.status }}">{{ chk.status }}</span></h3>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-secondary" id="themeToggle">Tema</button>
        <a href="/" class="btn btn-outline-secondary">← Dashboard</a>
      </div>
    </div>
    <div class="row g-4">
      <div class="col-lg-8">
        {% for i in chk.itens %}
        <div class="card mb-3">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <div>
                <span class="badge bg-light text-dark me-2">#{{ i.ordem }}</span>
                <strong>{{ i.descricao }}</strong>
                <span class="badge sev-{{ i.severidade }} ms-2">{{ i.severidade }}</span>
              </div>
            </div>
            <div class="btn-group" role="group" aria-label="Resposta">
              <input type="radio" class="btn-check" name="resp_{{ i.id }}" id="ok_{{ i.id }}" autocomplete="off" checked>
              <label class="btn btn-outline-success" for="ok_{{ i.id }}">OK</label>
              <input type="radio" class="btn-check" name="resp_{{ i.id }}" id="nao_{{ i.id }}" autocomplete="off">
              <label class="btn btn-outline-danger" for="nao_{{ i.id }}">NÃO OK</label>
              <input type="radio" class="btn-check" name="resp_{{ i.id }}" id="na_{{ i.id }}" autocomplete="off">
              <label class="btn btn-outline-secondary" for="na_{{ i.id }}">N/A</label>
            </div>
            <div class="mt-3 d-none" id="obs_wrap_{{ i.id }}">
              <label class="form-label">Descreva o problema identificado</label>
              <textarea class="form-control" id="obs_{{ i.id }}" rows="2" placeholder="Detalhe a inconformidade"></textarea>
            </div>
            <div class="text-end mt-3">
              <button class="btn btn-primary" onclick="salvarItem({{ i.id }})">Salvar item</button>
            </div>
          </div>
        </div>
        <script>
          document.getElementById('nao_{{ i.id }}').addEventListener('change', (e) => {
            document.getElementById('obs_wrap_{{ i.id }}').classList.remove('d-none');
          });
          document.getElementById('ok_{{ i.id }}').addEventListener('change', (e) => {
            document.getElementById('obs_wrap_{{ i.id }}').classList.add('d-none');
          });
          document.getElementById('na_{{ i.id }}').addEventListener('change', (e) => {
            document.getElementById('obs_wrap_{{ i.id }}').classList.add('d-none');
          });
        </script>
        {% endfor %}
      </div>
      <div class="col-lg-4">
        <div class="card">
          <div class="card-header">Finalização</div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Odômetro Final</label>
              <input type="number" class="form-control" id="odometro_fim" min="0" placeholder="Opcional">
            </div>
            <button class="btn btn-success w-100" onclick="finalizarChecklist()">Finalizar Checklist</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    function valorSelecionado(itemId) {
      if (document.getElementById('ok_'+itemId).checked) return 'ok';
      if (document.getElementById('nao_'+itemId).checked) return 'nao_ok';
      return 'na';
    }
    function salvarItem(itemId) {
      const body = { checklist_id: {{ chk.id }}, respostas: [{ item_id: itemId, valor: valorSelecionado(itemId), observacao: (document.getElementById('obs_'+itemId)?.value || null) }] };
      fetch('/ui/checklist/answer', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
        .then(r => r.json())
        .then(data => {
          if (data.error) { alert('Erro: ' + data.error); return; }
          alert('Resposta salva!');
        })
        .catch(err => alert('Erro ao salvar: ' + err));
    }
    function finalizarChecklist() {
      const body = { checklist_id: {{ chk.id }}, odometro_fim: document.getElementById('odometro_fim').value ? parseInt(document.getElementById('odometro_fim').value) : null };
      fetch('/ui/checklist/finish', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
        .then(r => r.json())
        .then(data => {
          if (data.error) { alert('Erro: ' + data.error); return; }
          alert('Checklist finalizado! Status: '+ data.status);
          window.location.href = '/';
        })
        .catch(err => alert('Erro ao finalizar: ' + err));
    }
  </script>
</body>
</html>
"""


@bp.route("/checklist/<int:checklist_id>")
def checklist_detail(checklist_id: int):
    client = api.APIClient()
    chk = client.get(f"/api/v1/checklist/{checklist_id}")
    if not chk or isinstance(chk, dict) and chk.get('error'):
        return "Checklist não encontrado", 404
    return render_template_string(CHECKLIST_DETAIL_TEMPLATE, chk=chk)


@bp.route("/ui/checklist/answer", methods=["POST"])
def ui_checklist_answer():
    body = request.get_json() or {}
    # Process multiple responses
    import requests
    try:
        checklist_id = body.get('checklist_id')
        respostas = body.get('respostas', [])

        results = []
        for resposta in respostas:
            data = {
                "checklist_id": checklist_id,
                "item_id": resposta.get('item_id'),
                "valor": resposta.get('valor'),
                "observacao": resposta.get('observacao', '')
            }
            resp = requests.post("http://localhost:8005/checklist/answer", json=data, timeout=10)
            if resp.status_code == 200:
                results.append(resp.json())
            else:
                print(f"Error saving response for item {resposta.get('item_id')}: {resp.status_code}")

        return jsonify({"success": True, "saved": len(results), "message": f"{len(results)} respostas salvas"})
    except Exception as e:
        print(f"Error processing answers: {e}")
        return jsonify({"error": str(e)}), 502


@bp.route("/ui/checklist/finish", methods=["POST"])
def ui_checklist_finish():
    body = request.get_json() or {}
    checklist_id = body.get('checklist_id')

    if not checklist_id:
        return jsonify({"error": "checklist_id is required"}), 400

    # Call the API directly to finish the checklist
    try:
        import requests
        api_base = _api_base()

        # Remove checklist_id from body since it goes in the URL
        api_body = {k: v for k, v in body.items() if k != 'checklist_id'}

        response = requests.post(f"{api_base}/api/v1/checklist/{checklist_id}/finish",
                               json=api_body,
                               timeout=20)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"API returned {response.status_code}: {response.text}"}), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500
