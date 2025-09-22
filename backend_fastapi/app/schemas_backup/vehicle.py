# backend_fastapi/app/schemas/vehicle.py
"""
Schemas de veículos
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VeiculoOut(BaseModel):
    id: int
    placa: str
    renavam: Optional[str] = None
    ano: Optional[int] = None
    modelo: Optional[str] = None
    marca: Optional[str] = None
    tipo: Optional[str] = None
    km_atual: int
    status: str
    ativo: bool
    
    class Config:
        from_attributes = True