from fastapi.testclient import TestClient


def login_and_get_token(client: TestClient, email: str, senha: str) -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_gestor_can_crud_modelo_and_itens(client: TestClient, admin_user):
    token = login_and_get_token(client, admin_user.email, "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create model
    payload_model = {"nome": "Modelo Teste", "tipo": "pre", "ativo": True}
    r = client.post("/api/v1/checklist/modelos", json=payload_model, headers=headers)
    assert r.status_code == 201
    modelo = r.json()
    assert modelo["nome"] == "Modelo Teste"
    modelo_id = modelo["id"]

    # Create item
    payload_item = {
        "modelo_id": modelo_id,
        "ordem": 1,
        "descricao": "Freios",
        "tipo_resposta": "ok",
        "severidade": "alta",
        "exige_foto": False,
        "bloqueia_viagem": True,
    }
    r = client.post(f"/api/v1/checklist/modelos/{modelo_id}/itens", json=payload_item, headers=headers)
    assert r.status_code == 201
    item = r.json()
    assert item["descricao"] == "Freios"
    item_id = item["id"]

    # List items
    r = client.get(f"/api/v1/checklist/modelos/{modelo_id}/itens", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert any(i["id"] == item_id for i in items)

    # Update model
    r = client.put(f"/api/v1/checklist/modelos/{modelo_id}", json={"nome": "Modelo Atualizado"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["nome"] == "Modelo Atualizado"

    # Update item
    r = client.put(f"/api/v1/checklist/itens/{item_id}", json={"descricao": "Freios (Atualizado)"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["descricao"] == "Freios (Atualizado)"

    # Delete item
    r = client.delete(f"/api/v1/checklist/itens/{item_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Soft-delete model
    r = client.delete(f"/api/v1/checklist/modelos/{modelo_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Model should not appear in list (ativo=False)
    r = client.get("/api/v1/checklist/modelos", headers=headers)
    assert r.status_code == 200
    assert all(m["id"] != modelo_id for m in r.json())


def test_motorista_forbidden_crud(client: TestClient, motorista_user):
    token = login_and_get_token(client, motorista_user.email, "motorista123")
    headers = {"Authorization": f"Bearer {token}"}

    # Try create model (should be forbidden)
    r = client.post(
        "/api/v1/checklist/modelos",
        json={"nome": "Modelo Motorista", "tipo": "pre", "ativo": True},
        headers=headers,
    )
    assert r.status_code == 403

