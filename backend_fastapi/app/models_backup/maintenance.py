# backend_fastapi/app/models/maintenance.py
"""
Modelos relacionados a manutenção
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Defeito(Base):
    """Defeito identificado em checklist"""
    __tablename__ = "defeitos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)  # Código único
    
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("checklist_itens.id"), nullable=False)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    
    categoria = Column(String)  # freios|pneus|motor|etc
    severidade = Column(String, nullable=False)  # baixa|media|alta|critica
    descricao = Column(Text, nullable=False)
    observacao = Column(Text)
    foto_urls = Column(Text)  # URLs das fotos, separadas por vírgula
    
    status = Column(String, default="identificado")  # identificado|aberto|em_andamento|resolvido|cancelado
    prioridade = Column(String, default="normal")  # baixa|normal|alta|urgente
    
    custo_estimado = Column(Numeric(10, 2))
    custo_real = Column(Numeric(10, 2))
    
    identificado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolvido_em = Column(DateTime)
    prazo_resolucao = Column(DateTime)
    
    # Relacionamentos
    checklist = relationship("Checklist", back_populates="defeitos")
    item = relationship("ChecklistItem")
    veiculo = relationship("Veiculo", back_populates="defeitos")
    ordens_servico = relationship("OrdemServico", back_populates="defeito")

class OrdemServico(Base):
    """Ordem de serviço para correção de defeitos"""
    __tablename__ = "ordens_servico"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, index=True)  # Número da OS
    
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    defeito_id = Column(Integer, ForeignKey("defeitos.id"))
    
    tipo = Column(String, default="corretiva")  # preventiva|corretiva|preditiva
    descricao = Column(Text, nullable=False)
    servicos_realizados = Column(Text)
    pecas_utilizadas = Column(Text)
    
    responsavel_abertura = Column(String)
    responsavel_execucao = Column(String)
    aprovador = Column(String)
    
    abertura_dt = Column(DateTime, default=datetime.utcnow, nullable=False)
    inicio_execucao_dt = Column(DateTime)
    conclusao_dt = Column(DateTime)
    aprovacao_dt = Column(DateTime)
    
    prazo_execucao = Column(DateTime)
    
    # Custos
    custo_peca = Column(Numeric(10, 2), default=0)
    custo_mo = Column(Numeric(10, 2), default=0)  # mão de obra
    custo_terceiros = Column(Numeric(10, 2), default=0)
    custo_total = Column(Numeric(10, 2), default=0)
    
    # Controle
    centro_custo = Column(String)
    fornecedor = Column(String)
    nota_fiscal = Column(String)
    
    status = Column(String, default="aberta")  # aberta|em_execucao|aguardando_peca|finalizada|cancelada
    prioridade = Column(String, default="normal")  # baixa|normal|alta|urgente
    
    km_veiculo = Column(Integer)  # KM do veículo na abertura
    
    # Campos de auditoria
    observacoes = Column(Text)
    anexos = Column(Text)  # URLs de anexos
    
    # Relacionamentos
    veiculo = relationship("Veiculo", back_populates="ordens_servico")
    defeito = relationship("Defeito", back_populates="ordens_servico")