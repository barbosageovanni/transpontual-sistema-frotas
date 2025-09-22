from flask import Blueprint, render_template, current_app, jsonify
import requests
from datetime import datetime, timedelta

bp = Blueprint("alerts", __name__)

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

def generate_sample_alerts():
    """Gera alertas de exemplo baseados na imagem"""
    now = datetime.now()
    alerts = [
        {
            "id": 1,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "ATA-4352/PR",
            "descricao": "Troca de Óleo",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "warning"
        },
        {
            "id": 2,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "ATA-4352/PR",
            "descricao": "Troca de Filtros",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "warning"
        },
        {
            "id": 3,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "MAR-L001/PR",
            "descricao": "Freios",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        },
        {
            "id": 4,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "XAV-0001/PR",
            "descricao": "Freio",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        },
        {
            "id": 5,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "XAV-0001/PR",
            "descricao": "Freio",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        },
        {
            "id": 6,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "XAV-0002/PR",
            "descricao": "Freio",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        },
        {
            "id": 7,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "XAV-0002/PR",
            "descricao": "Freio",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        },
        {
            "id": 8,
            "tipo": "Alerta de equipamento",
            "codigo_equipamento": "XAV-0000/PR",
            "descricao": "Freio até 01/02/2025",
            "data_hora": (now - timedelta(hours=2)).strftime("%d.%m %H:%M"),
            "nivel": "danger"
        }
    ]
    return alerts

@bp.route("/")
def alerts_list():
    """Lista de alertas do sistema"""
    try:
        # Por enquanto, usamos dados de exemplo
        # Futuramente isso pode vir da API
        alertas = generate_sample_alerts()

        # Separar alertas por categoria
        alertas_equipamentos = [a for a in alertas if a["tipo"] == "Alerta de equipamento"]

        return render_template("alerts/index.html",
                             alertas_equipamentos=alertas_equipamentos,
                             total_alertas=len(alertas))

    except Exception as e:
        current_app.logger.error(f"Erro ao carregar alertas: {str(e)}")
        return render_template("alerts/index.html",
                             alertas_equipamentos=[],
                             total_alertas=0,
                             error=str(e))

@bp.route("/api")
def alerts_api():
    """API endpoint para alertas (para uso AJAX)"""
    try:
        alertas = generate_sample_alerts()
        return jsonify({
            "alertas": alertas,
            "total": len(alertas)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500