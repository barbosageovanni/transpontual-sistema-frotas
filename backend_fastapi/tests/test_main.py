# backend_fastapi/tests/test_main.py
"""
Testes da aplicação principal
"""
import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client):
    """Teste do endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Transpontual" in data["message"]

def test_health_endpoint(client):
    """Teste do health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_docs_endpoint(client):
    """Teste da documentação da API"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_endpoint(client):
    """Teste do schema OpenAPI"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data