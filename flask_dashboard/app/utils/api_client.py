# flask_dashboard/app/utils/api_client.py
"""
Cliente simples para comunicação com a API
"""
import requests
from flask import current_app, session

class APIClient:
    """Cliente para fazer requests para a API FastAPI"""
    
    def __init__(self):
        self.base_url = session.get("API_BASE_OVERRIDE") or current_app.config.get("API_BASE", "http://localhost:8005")
        self.timeout = 10
        self._token = None

    def _ensure_token(self):
        """Obtém JWT e guarda em cache."""
        if self._token:
            return
        email = current_app.config.get("API_LOGIN_EMAIL")
        password = current_app.config.get("API_LOGIN_PASSWORD")
        if not email or not password:
            return
        try:
            url = f"{self.base_url}/api/v1/auth/login"
            resp = requests.post(url, json={"email": email, "senha": password}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            self._token = data.get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao autenticar no backend: {e}")
            self._token = None

    def _headers(self):
        self._ensure_token()
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    def get(self, endpoint, params=None):
        """GET request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na API GET {endpoint}: {e}")
            return {"error": str(e)}
    
    def post(self, endpoint, data=None):
        """POST request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, headers=self._headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na API POST {endpoint}: {e}")
            return {"error": str(e)}
