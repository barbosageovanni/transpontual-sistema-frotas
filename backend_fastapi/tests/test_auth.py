# backend_fastapi/tests/test_auth.py
"""
Testes de autenticação
"""
import pytest

def test_login_success(client, admin_user):
    """Teste de login com sucesso"""
    response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin_user.email

def test_login_invalid_credentials(client, admin_user):
    """Teste de login com credenciais inválidas"""
    response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "senha_errada"
    })
    assert response.status_code == 401

def test_login_user_not_found(client):
    """Teste de login com usuário inexistente"""
    response = client.post("/api/v1/auth/login", json={
        "email": "inexistente@test.com",
        "senha": "qualquer"
    })
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    """Teste de endpoint protegido sem token"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token(client, admin_user):
    """Teste de endpoint protegido com token válido"""
    # Fazer login
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "admin123"
    })
    token = login_response.json()["access_token"]
    
    # Usar token
    response = client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_user.email


# backend_fastapi/tests/test_checklist.py
"""
Testes do módulo de checklist
"""
import pytest

def test_list_checklist_models(client, admin_user, checklist_modelo):
    """Teste de listagem de modelos de checklist"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "admin123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Listar modelos
    response = client.get("/api/v1/checklist/modelos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nome"] == checklist_modelo.nome

def test_get_model_items(client, admin_user, checklist_modelo):
    """Teste de obtenção de itens de modelo"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "admin123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obter itens
    response = client.get(f"/api/v1/checklist/modelos/{checklist_modelo.id}/itens", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # 2 itens criados no fixture
    assert data[0]["descricao"] == "Freios"

def test_start_checklist(client, motorista_user, veiculo_test, checklist_modelo):
    """Teste de início de checklist"""
    # Login como motorista
    login_response = client.post("/api/v1/auth/login", json={
        "email": motorista_user.email,
        "senha": "motorista123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Iniciar checklist
    payload = {
        "veiculo_id": veiculo_test.id,
        "motorista_id": 1,  # Primeiro motorista
        "modelo_id": checklist_modelo.id,
        "tipo": "pre",
        "odometro_ini": 100000
    }
    
    response = client.post("/api/v1/checklist/start", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "em_andamento"
    assert data["veiculo_id"] == veiculo_test.id

def test_checklist_stats(client, admin_user):
    """Teste de estatísticas de checklist"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "senha": "admin123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Obter estatísticas
    response = client.get("/api/v1/checklist/stats/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_checklists" in data
    assert "taxa_aprovacao" in data
