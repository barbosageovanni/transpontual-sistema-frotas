# backend_fastapi/app/schemas.py
"""
Pydantic Schemas - Versão simplificada funcional
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class PapelUsuario(str, Enum):
    ADMIN = "admin"
    GESTOR = "gestor"
    FISCAL = "fiscal"
    FINANCEIRO = "financeiro"
    OPERACIONAL = "operacional"
    ESTAGIARIO = "estagiario"
    MECANICO = "mecanico"
    MOTORISTA = "motorista"

class TipoChecklist(str, Enum):
    PRE = "pre"
    POS = "pos"
    EXTRA = "extra"

class StatusChecklist(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    EM_ANDAMENTO = "em_andamento"

# Base
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Auth
class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: "UsuarioResponse"

class LoginRequest(BaseSchema):
    email: EmailStr
    senha: str

# Usuario
class UsuarioBase(BaseSchema):
    nome: str
    email: EmailStr
    papel: PapelUsuario
    ativo: Optional[bool] = True
    # Controles de acesso avançado
    horario_inicio: Optional[time] = None
    horario_fim: Optional[time] = None
    dias_semana: Optional[str] = None
    ips_permitidos: Optional[str] = None
    localizacao_restrita: Optional[bool] = False
    data_validade: Optional[date] = None
    max_sessoes: Optional[int] = 1

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseSchema):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    papel: Optional[PapelUsuario] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None
    # Controles de acesso avançado
    horario_inicio: Optional[time] = None
    horario_fim: Optional[time] = None
    dias_semana: Optional[str] = None
    ips_permitidos: Optional[str] = None
    localizacao_restrita: Optional[bool] = None
    data_validade: Optional[date] = None
    max_sessoes: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id: int
    criado_em: datetime
    ultimo_acesso: Optional[datetime] = None
    ultimo_ip: Optional[str] = None
    tentativas_login: Optional[int] = 0
    bloqueado_ate: Optional[datetime] = None

# Veiculo
class VeiculoBase(BaseSchema):
    placa: str
    modelo: Optional[str] = None
    ano: Optional[int] = None
    km_atual: int = 0

class VeiculoCreate(VeiculoBase):
    renavam: Optional[str] = None
    ativo: Optional[bool] = True
    em_manutencao: bool = False
    observacoes_manutencao: Optional[str] = None

class VeiculoResponse(VeiculoCreate):
    id: int

# Motorista
class MotoristaBase(BaseSchema):
    nome: str
    cnh: Optional[str] = None
    categoria: Optional[str] = None
    validade_cnh: Optional[date] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = True

class MotoristaCreate(MotoristaBase):
    usuario_id: Optional[int] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None

class MotoristaUpdate(BaseSchema):
    nome: Optional[str] = None
    cnh: Optional[str] = None
    categoria: Optional[str] = None
    validade_cnh: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None
    email: Optional[EmailStr] = None

class MotoristaResponse(MotoristaBase):
    id: int
    usuario_id: Optional[int] = None
    usuario: Optional["UsuarioResponse"] = None

# Checklist
class ChecklistItemBase(BaseSchema):
    ordem: int
    descricao: str
    tipo_resposta: str = "ok"
    severidade: str = "media"
    exige_foto: bool = False
    bloqueia_viagem: bool = False

class ChecklistItemResponse(ChecklistItemBase):
    id: int
    modelo_id: int

# CRUD - Checklist Item
class ChecklistItemCreate(ChecklistItemBase):
    modelo_id: int

class ChecklistItemUpdate(BaseSchema):
    ordem: Optional[int] = None
    descricao: Optional[str] = None
    tipo_resposta: Optional[str] = None
    severidade: Optional[str] = None
    exige_foto: Optional[bool] = None
    bloqueia_viagem: Optional[bool] = None

class ChecklistModeloBase(BaseSchema):
    nome: str
    tipo: TipoChecklist
    versao: int = 1
    ativo: bool = True

class ChecklistModeloResponse(ChecklistModeloBase):
    id: int
    criado_em: datetime

# CRUD - Checklist Modelo
class ChecklistModeloCreate(BaseSchema):
    nome: str
    tipo: TipoChecklist
    ativo: bool = True

class ChecklistModeloUpdate(BaseSchema):
    nome: Optional[str] = None
    tipo: Optional[TipoChecklist] = None
    ativo: Optional[bool] = None

class ChecklistStartRequest(BaseSchema):
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    tipo: TipoChecklist
    odometro_ini: Optional[int] = None

class RespostaItemRequest(BaseSchema):
    item_id: int
    valor: str
    observacao: Optional[str] = None

class ChecklistAnswerRequest(BaseSchema):
    checklist_id: int
    respostas: List[RespostaItemRequest]

class ChecklistFinishRequest(BaseSchema):
    checklist_id: int
    odometro_fim: Optional[int] = None

class ChecklistResponse(BaseSchema):
    id: int
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    tipo: TipoChecklist
    status: StatusChecklist
    dt_inicio: datetime
    dt_fim: Optional[datetime] = None

# Upload
class UploadResponse(BaseSchema):
    filename: str

# Pydantic forward refs
Token.model_rebuild()

