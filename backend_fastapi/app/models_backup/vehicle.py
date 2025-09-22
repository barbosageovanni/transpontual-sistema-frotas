# backend_fastapi/app/models/vehicle.py
"""
Modelos relacionados a veículos
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Veiculo(Base):
    """Modelo para veículos"""
    __tablename__ = "veiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True, nullable=False)
    renavam = Column(String)
    ano = Column(Integer)
    modelo = Column(String)
    marca = Column(String)
    tipo = Column(String)  # carreta|cavalo|leve|utilitario
    km_atual = Column(BigInteger, default=0)
    status = Column(String, default="ativo")  # ativo|manutencao|inativo
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    checklists = relationship("Checklist", back_populates="veiculo")
    defeitos = relationship("Defeito", back_populates="veiculo")
    ordens_servico = relationship("OrdemServico", back_populates="veiculo")

class Viagem(Base):
    """Modelo para viagens"""
    __tablename__ = "viagens"
    
    id = Column(Integer, primary_key=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=False)
    origem = Column(String)
    destino = Column(String)
    data_partida = Column(DateTime)
    data_chegada_prevista = Column(DateTime)
    data_chegada_real = Column(DateTime)
    km_inicial = Column(BigInteger)
    km_final = Column(BigInteger)
    status = Column(String, default="planejada")  # planejada|em_andamento|finalizada|cancelada
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    veiculo = relationship("Veiculo")
    motorista = relationship("Motorista")
    checklists = relationship("Checklist", back_populates="viagem")