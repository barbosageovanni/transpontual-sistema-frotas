# flask_dashboard/app/blueprints/checklist.py
"""
Blueprint para checklist
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..utils.api_client import APIClient

bp = Blueprint("checklist", __name__)

@bp.route("/")
def index():
    """Lista de checklists"""
    try:
        api = APIClient()
        
        # Em produção: buscar da API
        checklists = [
            {
                "id": 1,
                "veiculo_placa": "ABC1234",
                "motorista_nome": "João Silva", 
                "tipo": "pre",
                "status": "aprovado",
                "dt_inicio": "2024-01-15 08:30"
            },
            {
                "id": 2,
                "veiculo_placa": "DEF5678",
                "motorista_nome": "Maria Santos",
                "tipo": "pre", 
                "status": "reprovado",
                "dt_inicio": "2024-01-15 09:15"
            }
        ]
        
        return render_template("checklist/index.html", checklists=checklists)
        
    except Exception as e:
        flash(f"Erro ao carregar checklists: {e}", "danger")
        return render_template("checklist/index.html", checklists=[])

@bp.route("/models")
def models():
    """Modelos de checklist"""
    try:
        api = APIClient()
        
        # Em produção: buscar da API
        models = [
            {"id": 1, "nome": "Carreta - Pré-viagem", "tipo": "pre", "ativo": True},
            {"id": 2, "nome": "Cavalo - Pré-viagem", "tipo": "pre", "ativo": True},
            {"id": 3, "nome": "Leve - Pré-viagem", "tipo": "pre", "ativo": True}
        ]
        
        return render_template("checklist/models.html", models=models)
        
    except Exception as e:
        flash(f"Erro ao carregar modelos: {e}", "danger")
        return render_template("checklist/models.html", models=[])

@bp.route("/start", methods=["GET", "POST"])
def start():
    """Iniciar novo checklist"""
    if request.method == "POST":
        try:
            api = APIClient()
            
            payload = {
                "veiculo_id": int(request.form["veiculo_id"]),
                "motorista_id": int(request.form["motorista_id"]),
                "modelo_id": int(request.form["modelo_id"]),
                "tipo": request.form.get("tipo", "pre"),
                "odometro_ini": int(request.form.get("odometro_ini", "0")),
                "geo_inicio": request.form.get("geo_inicio") or None
            }
            
            # Em produção: fazer POST na API
            # result = api.post("/checklist/start", payload)
            
            flash("Checklist iniciado com sucesso!", "success")
            return redirect(url_for("checklist.index"))
            
        except Exception as e:
            flash(f"Erro ao iniciar checklist: {e}", "danger")
    
    # GET - mostrar formulário
    models = [
        {"id": 1, "nome": "Carreta - Pré-viagem", "tipo": "pre"},
        {"id": 2, "nome": "Cavalo - Pré-viagem", "tipo": "pre"}
    ]
    
    return render_template("checklist/start.html", models=models)