
# flask_dashboard/run.py
"""
Entry point do Flask Dashboard
"""
import os
# Importar diretamente do dashboard principal (sem confusão)
from app.dashboard import create_app

app = create_app()

if __name__ == "__main__":
    # Railway usa a variável PORT, fallback para DASHBOARD_PORT ou 8050
    port = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT", "8050")))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )