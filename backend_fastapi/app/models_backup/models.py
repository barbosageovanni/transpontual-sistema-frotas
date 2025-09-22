# backend_fastapi/app/models.py
"""
SQLAlchemy Models - Sistema Transpontual
Modelos de dados para o sistema de checklist veicular
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    BigInteger, Text, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from app.core.database import Base

# ==============================
# MÓDULO 1: CHECKLIST VEICULAR
# ==============================

class Usuario(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = "usuarios"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    papel: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    motorista = relationship("Motorista", back_populates="usuario", uselist=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "papel IN ('gestor','mecanico','motorista','admin')",
            name="chk_usuarios_papel"
        ),
        Index("idx_usuarios_email", "email"),
        Index("idx_usuarios_papel", "papel"),
    )

class Veiculo(Base):
    """Modelo para veículos da frota"""
    __tablename__ = "veiculos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    renavam: Mapped[Optional[str]] = mapped_column(String(11))
    ano: Mapped[Optional[int]] = mapped_column(Integer)
    modelo: Mapped[Optional[str]] = mapped_column(String(100))
    km_atual: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    checklists = relationship("Checklist", back_populates="veiculo")
    defeitos = relationship("Defeito", back_populates="veiculo")
    ordens_servico = relationship("OrdemServico", back_populates="veiculo")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("km_atual >= 0", name="chk_veiculos_km"),
        Index("idx_veiculos_placa", "placa"),
        Index("idx_veiculos_ativo", "ativo"),
    )

class Motorista(Base):
    """Modelo para motoristas e condutores"""
    __tablename__ = "motoristas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cnh: Mapped[Optional[str]] = mapped_column(String(11))
    categoria: Mapped[Optional[str]] = mapped_column(String(5))
    validade_cnh: Mapped[Optional[datetime]] = mapped_column(DateTime)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="motorista")
    checklists = relationship("Checklist", back_populates="motorista")
    
    # Constraints
    __table_args__ = (
        Index("idx_motoristas_cnh", "cnh"),
        Index("idx_motoristas_usuario", "usuario_id"),
        Index("idx_motoristas_ativo", "ativo"),
    )

class ChecklistModelo(Base):
    """Modelo para templates/modelos de checklist"""
    __tablename__ = "checklist_modelos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    versao: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    itens = relationship("ChecklistItem", back_populates="modelo", cascade="all, delete-orphan")
    checklists = relationship("Checklist", back_populates="modelo")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('pre','pos','extra')", name="chk_modelos_tipo"),
        Index("idx_checklist_modelos_tipo", "tipo"),
        Index("idx_checklist_modelos_ativo", "ativo"),
    )

class ChecklistItem(Base):
    """Modelo para itens individuais do checklist"""
    __tablename__ = "checklist_itens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[int] = mapped_column(ForeignKey("checklist_modelos.id", ondelete="CASCADE"), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_resposta: Mapped[str] = mapped_column(String(20), nullable=False)
    severidade: Mapped[str] = mapped_column(String(20), nullable=False)
    exige_foto: Mapped[bool] = mapped_column(Boolean, default=False)
    bloqueia_viagem: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    modelo = relationship("ChecklistModelo", back_populates="itens")
    respostas = relationship("ChecklistResposta", back_populates="item")
    defeitos = relationship("Defeito", back_populates="item")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("tipo_resposta IN ('ok','na','obs','foto')", name="chk_itens_tipo_resposta"),
        CheckConstraint("severidade IN ('baixa','media','alta')", name="chk_itens_severidade"),
        Index("idx_checklist_itens_modelo", "modelo_id"),
        Index("idx_checklist_itens_ordem", "modelo_id", "ordem"),
    )

class Checklist(Base):
    """Modelo principal para checklists executados"""
    __tablename__ = "checklists"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False)
    motorista_id: Mapped[int] = mapped_column(ForeignKey("motoristas.id"), nullable=False)
    modelo_id: Mapped[int] = mapped_column(ForeignKey("checklist_modelos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    odometro_ini: Mapped[Optional[int]] = mapped_column(BigInteger)
    odometro_fim: Mapped[Optional[int]] = mapped_column(BigInteger)
    geo_inicio: Mapped[Optional[str]] = mapped_column(Text)
    geo_fim: Mapped[Optional[str]] = mapped_column(Text)
    dt_inicio: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    dt_fim: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="pendente", nullable=False)
    assinatura_motorista: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relacionamentos
    veiculo = relationship("Veiculo", back_populates="checklists")
    motorista = relationship("Motorista", back_populates="checklists")
    modelo = relationship("ChecklistModelo", back_populates="checklists")
    respostas = relationship("ChecklistResposta", back_populates="checklist", cascade="all, delete-orphan")
    defeitos = relationship("Defeito", back_populates="checklist")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('pre','pos','extra')", name="chk_checklists_tipo"),
        CheckConstraint("status IN ('pendente','aprovado','reprovado')", name="chk_checklists_status"),
        Index("idx_checklists_veiculo", "veiculo_id"),
        Index("idx_checklists_motorista", "motorista_id"),
        Index("idx_checklists_status", "status"),
        Index("idx_checklists_data_inicio", "dt_inicio"),
    )

class ChecklistResposta(Base):
    """Modelo para respostas individuais dos itens"""
    __tablename__ = "checklist_respostas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("checklist_itens.id"), nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text)
    foto_url: Mapped[Optional[str]] = mapped_column(Text)
    geo: Mapped[Optional[str]] = mapped_column(Text)
    dt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    checklist = relationship("Checklist", back_populates="respostas")
    item = relationship("ChecklistItem", back_populates="respostas")
    
    # Constraints
    __table_args__ = (
        Index("idx_checklist_respostas_checklist", "checklist_id"),
        Index("idx_checklist_respostas_item", "item_id"),
    )

class Defeito(Base):
    """Modelo para defeitos identificados nos checklists"""
    __tablename__ = "defeitos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("checklist_itens.id"), nullable=False)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False)
    severidade: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="aberto", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    checklist = relationship("Checklist", back_populates="defeitos")
    item = relationship("ChecklistItem", back_populates="defeitos")
    veiculo = relationship("Veiculo", back_populates="defeitos")
    ordens_servico = relationship("OrdemServico", back_populates="defeito")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("severidade IN ('baixa','media','alta')", name="chk_defeitos_severidade"),
        CheckConstraint("status IN ('aberto','em_andamento','resolvido')", name="chk_defeitos_status"),
        Index("idx_defeitos_checklist", "checklist_id"),
        Index("idx_defeitos_veiculo", "veiculo_id"),
        Index("idx_defeitos_status", "status"),
    )

class OrdemServico(Base):
    """Modelo para ordens de serviço de manutenção"""
    __tablename__ = "ordens_servico"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False)
    defeito_id: Mapped[Optional[int]] = mapped_column(ForeignKey("defeitos.id"))
    abertura_dt: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    encerramento_dt: Mapped[Optional[datetime]] = mapped_column(DateTime)
    custo_peca: Mapped[float] = mapped_column(String, default=0)
    custo_mo: Mapped[float] = mapped_column(String, default=0)
    centro_custo: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="aberta", nullable=False)
    
    # Relacionamentos
    veiculo = relationship("Veiculo", back_populates="ordens_servico")
    defeito = relationship("Defeito", back_populates="ordens_servico")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('aberta','em_execucao','fechada')", name="chk_os_status"),
        Index("idx_os_veiculo", "veiculo_id"),
        Index("idx_os_defeito", "defeito_id"),
        Index("idx_os_status", "status"),
    )