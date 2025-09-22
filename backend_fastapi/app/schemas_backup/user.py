# backend_fastapi/app/schemas/user.py
"""
Schemas de usuários
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    papel: str
    ativo: bool
    criado_em: datetime
    
    class Config:
        from_attributes = True

class MotoristaOut(BaseModel):
    id: int
    nome: str
    cnh: Optional[str] = None
    categoria: Optional[str] = None
    validade_cnh: Optional[date] = None
    telefone: Optional[str] = None
    ativo: bool
    
    class Config:
        from_attributes = True