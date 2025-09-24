# backend_fastapi/app/models.py
"""
Modelos SQLAlchemy - Versão simplificada funcional
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text, Time, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, time, date
from app.core.database import Base

class Usuario(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    nome_completo = Column(String(200), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=True)
    papel = Column(String(20), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    
    # Novos campos para controle de acesso avançado
    horario_inicio = Column(Time, nullable=True, comment="Horário inicial permitido (ex: 08:00)")
    horario_fim = Column(Time, nullable=True, comment="Horário final permitido (ex: 18:00)")
    dias_semana = Column(String(20), nullable=True, comment="Dias permitidos (ex: 1,2,3,4,5)")
    ips_permitidos = Column(Text, nullable=True, comment="IPs permitidos separados por vírgula")
    localizacao_restrita = Column(Boolean, default=False, comment="Restringir por localização")
    data_validade = Column(Date, nullable=True, comment="Data de validade do acesso")
    max_sessoes = Column(Integer, default=1, comment="Máximo de sessões simultâneas")
    ultimo_acesso = Column(DateTime, nullable=True)
    ultimo_ip = Column(String(45), nullable=True)
    tentativas_login = Column(Integer, default=0)
    bloqueado_ate = Column(DateTime, nullable=True)

    # Relacionamentos - temporariamente removido para resolver erro de foreign key
    # motorista = relationship("Motorista", back_populates="usuario", uselist=False)

class Veiculo(Base):
    """Modelo para veículos da frota"""
    __tablename__ = "veiculos"

    id = Column(Integer, primary_key=True)
    placa = Column(String(8), unique=True, index=True, nullable=False)
    renavam = Column(String(11))
    ano = Column(Integer)
    marca = Column(String(100))
    tipo = Column(String(50))
    modelo = Column(String(100))
    km_atual = Column(BigInteger, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    em_manutencao = Column(Boolean, default=False, nullable=False)
    observacoes_manutencao = Column(Text)
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    checklists = relationship("Checklist", back_populates="veiculo")

class Motorista(Base):
    """Modelo para motoristas"""
    __tablename__ = "motoristas"

    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    cnh = Column(String(11))
    categoria = Column(String(5))
    validade_cnh = Column(DateTime)
    observacoes = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="motorista")
    checklists = relationship("Checklist", back_populates="motorista")

class ChecklistModelo(Base):
    """Modelo para templates de checklist"""
    __tablename__ = "checklist_modelos"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    tipo = Column(String(20), nullable=False)
    versao = Column(Integer, default=1, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    itens = relationship("ChecklistItem", back_populates="modelo")
    checklists = relationship("Checklist", back_populates="modelo")

class ChecklistItem(Base):
    """Modelo para itens do checklist"""
    __tablename__ = "checklist_itens"
    
    id = Column(Integer, primary_key=True)
    modelo_id = Column(Integer, ForeignKey("checklist_modelos.id"), nullable=False)
    ordem = Column(Integer, nullable=False)
    descricao = Column(Text, nullable=False)
    categoria = Column(String(50))
    tipo_resposta = Column(String(20), nullable=False)
    severidade = Column(String(20), nullable=False)
    exige_foto = Column(Boolean, default=False)
    bloqueia_viagem = Column(Boolean, default=False)
    
    # Relacionamentos
    modelo = relationship("ChecklistModelo", back_populates="itens")
    respostas = relationship("ChecklistResposta", back_populates="item")

class Checklist(Base):
    """Modelo principal para checklists executados"""
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=False)
    modelo_id = Column(Integer, ForeignKey("checklist_modelos.id"), nullable=False)
    tipo = Column(String(20), nullable=False)
    odometro_ini = Column(BigInteger)
    odometro_fim = Column(BigInteger)
    dt_inicio = Column(DateTime, default=func.now(), nullable=False)
    dt_fim = Column(DateTime)
    status = Column(String(20), default="pendente", nullable=False)
    
    # Relacionamentos
    veiculo = relationship("Veiculo", back_populates="checklists")
    motorista = relationship("Motorista", back_populates="checklists")
    modelo = relationship("ChecklistModelo", back_populates="checklists")
    respostas = relationship("ChecklistResposta", back_populates="checklist")

class ChecklistResposta(Base):
    """Modelo para respostas dos itens"""
    __tablename__ = "checklist_respostas"
    
    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("checklist_itens.id"), nullable=False)
    valor = Column(Text, nullable=False)
    observacao = Column(Text)
    dt = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    checklist = relationship("Checklist", back_populates="respostas")
    item = relationship("ChecklistItem", back_populates="respostas")

class Abastecimento(Base):
    """Modelo para abastecimentos da frota"""
    __tablename__ = "abastecimentos"

    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=False)
    data_abastecimento = Column(DateTime, default=func.now(), nullable=False)
    odometro = Column(BigInteger, nullable=False)
    litros = Column(String(20), nullable=False)  # Decimal como string
    valor_litro = Column(String(20), nullable=False)  # Decimal como string
    valor_total = Column(String(20), nullable=False)  # Decimal como string
    posto = Column(String(200))
    tipo_combustivel = Column(String(50), default="Diesel")
    numero_cupom = Column(String(100))
    observacoes = Column(Text)
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    veiculo = relationship("Veiculo")
    motorista = relationship("Motorista")

class OrdemServico(Base):
    """Modelo para ordens de serviço de manutenção"""
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True)
    numero_os = Column(String(50), unique=True, index=True)  # Número da ordem de serviço
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    tipo_servico = Column(String(100), nullable=False)  # Preventiva, Corretiva, etc.
    status = Column(String(30), default="Aberta", nullable=False)  # Aberta, Em Andamento, Concluída, Cancelada
    data_abertura = Column(DateTime, default=func.now(), nullable=False)
    data_prevista = Column(DateTime)
    data_conclusao = Column(DateTime)
    oficina = Column(String(200))
    odometro = Column(BigInteger)
    descricao_problema = Column(Text)
    descricao_servico = Column(Text)
    valor_total = Column(String(20))  # Decimal como string
    observacoes = Column(Text)
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, **kwargs):
        # Gerar numero_os automaticamente se não fornecido
        if not kwargs.get('numero_os'):
            import uuid
            from datetime import datetime
            kwargs['numero_os'] = f"OS{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        super().__init__(**kwargs)

    # Relacionamentos
    veiculo = relationship("Veiculo")
    itens = relationship("OrdemServicoItem", back_populates="ordem_servico")

class OrdemServicoItem(Base):
    """Modelo para itens de uma ordem de serviço"""
    __tablename__ = "ordem_servico_itens"

    id = Column(Integer, primary_key=True)
    ordem_servico_id = Column(Integer, ForeignKey("ordens_servico.id"), nullable=False)
    tipo_item = Column(String(20), nullable=False)  # 'peca' ou 'servico'
    descricao = Column(String(300), nullable=False)
    quantidade = Column(String(20), default="1")  # Decimal como string
    valor_unitario = Column(String(20))  # Decimal como string
    valor_total = Column(String(20))  # Decimal como string
    observacoes = Column(Text)

    # Relacionamentos
    ordem_servico = relationship("OrdemServico", back_populates="itens")

class UsuarioPermissao(Base):
    """Modelo para permissões específicas de usuários"""
    __tablename__ = "usuario_permissoes"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    modulo = Column(String(50), nullable=False)  # 'veiculos', 'financeiro', 'fiscal', etc.
    acao = Column(String(20), nullable=False)    # 'visualizar', 'criar', 'editar', 'excluir'
    permitido = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario")

class SessaoUsuario(Base):
    """Modelo para controle de sessões ativas"""
    __tablename__ = "sessoes_usuarios"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token_sessao = Column(String(255), unique=True, nullable=False)
    ip_acesso = Column(String(45), nullable=False)
    user_agent = Column(Text)
    inicio_sessao = Column(DateTime, default=func.now(), nullable=False)
    ultima_atividade = Column(DateTime, default=func.now(), nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)

    # Relacionamentos
    usuario = relationship("Usuario")

class LogAcesso(Base):
    """Modelo para logs de acesso e auditoria"""
    __tablename__ = "logs_acesso"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    ip_acesso = Column(String(45), nullable=False)
    user_agent = Column(Text)
    url_acessada = Column(String(500))
    metodo_http = Column(String(10))
    status_resposta = Column(Integer)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    sucesso = Column(Boolean, default=True, nullable=False)
    motivo_falha = Column(String(200))

    # Relacionamentos
    usuario = relationship("Usuario")

class PerfilAcesso(Base):
    """Modelo para perfis de acesso predefinidos"""
    __tablename__ = "perfis_acesso"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(Text)
    permissoes = Column(JSON)  # JSON com as permissões do perfil
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=func.now(), nullable=False)

    # Relacionamentos (temporarily removed due to ambiguous foreign keys)

class UsuarioPerfil(Base):
    """Tabela de associação entre usuários e perfis"""
    __tablename__ = "usuario_perfis"

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    perfil_id = Column(Integer, ForeignKey("perfis_acesso.id"), primary_key=True)
    atribuido_em = Column(DateTime, default=func.now(), nullable=False)
