# backend_fastapi/app/models/user.py
"""
Modelos relacionados a usuários
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Usuario(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, nullable=False)  # gestor|mecanico|motorista
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    motorista = relationship("Motorista", back_populates="usuario", uselist=False)

class Motorista(Base):
    """Modelo para motoristas"""
    __tablename__ = "motoristas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnh = Column(String)
    categoria = Column(String)
    validade_cnh = Column(Date)
    telefone = Column(String)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="motorista")
    checklists = relationship("Checklist", back_populates="motorista")