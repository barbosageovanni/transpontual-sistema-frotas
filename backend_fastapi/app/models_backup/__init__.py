# backend_fastapi/app/models/__init__.py
"""
Modelos SQLAlchemy
"""
from .base import Base
from .user import Usuario
from .vehicle import Veiculo
from .checklist import ChecklistModelo, ChecklistItem, Checklist, ChecklistResposta
from .maintenance import Defeito, OrdemServico

__all__ = [
    "Base",
    "Usuario", 
    "Veiculo",
    "ChecklistModelo",
    "ChecklistItem", 
    "Checklist",
    "ChecklistResposta",
    "Defeito",
    "OrdemServico"
]
