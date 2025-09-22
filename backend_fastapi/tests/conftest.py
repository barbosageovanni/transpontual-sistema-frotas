# backend_fastapi/tests/conftest.py
"""
Configuração dos testes
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Garantir que o pacote 'app' seja importável ao rodar a partir da raiz do repo
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import Base, get_db
from app.main import app
from app.models import Usuario, Motorista, Veiculo, ChecklistModelo, ChecklistItem

# Banco de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Engine do banco de testes"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Sessão do banco para cada teste"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Cliente de teste do FastAPI"""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db_session):
    """Usuário administrador para testes"""
    user = Usuario(
        nome="Admin Test",
        email="admin@test.com",
        senha_hash="admin123",  # Em produção seria hash
        papel="gestor",
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def motorista_user(db_session):
    """Usuário motorista para testes"""
    user = Usuario(
        nome="Motorista Test",
        email="motorista@test.com", 
        senha_hash="motorista123",
        papel="motorista",
        ativo=True
    )
    db_session.add(user)
    db_session.flush()
    
    motorista = Motorista(
        nome=user.nome,
        cnh="12345678900",
        categoria="E",
        usuario_id=user.id,
        ativo=True
    )
    db_session.add(motorista)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def veiculo_test(db_session):
    """Veículo para testes"""
    veiculo = Veiculo(
        placa="TEST123",
        modelo="Teste Model",
        marca="Teste",
        tipo="cavalo",
        km_atual=100000,
        ativo=True
    )
    db_session.add(veiculo)
    db_session.commit()
    db_session.refresh(veiculo)
    return veiculo

@pytest.fixture
def checklist_modelo(db_session):
    """Modelo de checklist para testes"""
    modelo = ChecklistModelo(
        nome="Teste - Pré-viagem",
        tipo="pre",
        ativo=True
    )
    db_session.add(modelo)
    db_session.flush()
    
    # Adicionar alguns itens
    itens = [
        ChecklistItem(
            modelo_id=modelo.id,
            ordem=1,
            descricao="Freios",
            categoria="freios",
            tipo_resposta="ok",
            severidade="alta",
            bloqueia_viagem=True
        ),
        ChecklistItem(
            modelo_id=modelo.id,
            ordem=2,
            descricao="Pneus",
            categoria="pneus", 
            tipo_resposta="ok",
            severidade="alta",
            bloqueia_viagem=True
        )
    ]
    
    for item in itens:
        db_session.add(item)
    
    db_session.commit()
    db_session.refresh(modelo)
    return modelo
