# flask_dashboard/app/blueprints/maintenance.py
"""
Blueprint para manutenção
"""
from flask import Blueprint, render_template
from ..utils.api_client import APIClient

bp = Blueprint("maintenance", __name__)

@bp.route("/")
def index():
    """Dashboard de manutenção"""
    try:
        # Dados simulados
        context = {
            "os_abertas": 12,
            "os_em_andamento": 5,
            "os_fechadas_mes": 28,
            "custo_mes": 15750.00,
            "title": "Manutenção"
        }
        
        return render_template("maintenance/index.html", **context)
        
    except Exception as e:
        return render_template("error.html", error=str(e))

@bp.route("/service-orders")
def service_orders():
    """Lista de ordens de serviço"""
    orders = [
        {
            "id": 1,
            "veiculo_placa": "ABC1234",
            "descricao": "Troca de pastilha de freio",
            "status": "aberta",
            "custo_estimado": 450.00,
            "abertura": "2024-01-15"
        }
    ]
    
    return render_template("maintenance/service_orders.html", orders=orders)

