"""
Pydantic Schemas - Sistema Transpontual (Pydantic v2)
Validação de dados e serialização para API
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re

# ==============================
# ENUMS PARA VALIDAÇÃO
# ==============================

class PapelUsuario(str, Enum):
    GESTOR = "gestor"
    MECANICO = "mecanico"
    MOTORISTA = "motorista"
    ADMIN = "admin"

class StatusChecklist(str, Enum):
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    CANCELADO = "cancelado"

class TipoChecklist(str, Enum):
    PRE = "pre"
    POS = "pos"
    EXTRA = "extra"

class SeveridadeItem(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"

# ==============================
# SCHEMAS BASE
# ==============================

class BaseSchema(BaseModel):
    """Schema base com configurações comuns"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

# ==============================
# AUTHENTICATION SCHEMAS
# ==============================

class Token(BaseSchema):
    """Token de acesso"""
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseSchema):
    """Request de login"""
    email: EmailStr = Field(..., description="Email do usuário")
    senha: str = Field(..., min_length=6, description="Senha do usuário")

# ==============================
# USER SCHEMAS
# ==============================

class UsuarioBase(BaseSchema):
    """Dados base do usuário"""
    nome: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    papel: PapelUsuario
    ativo: bool = Field(default=True)

class UsuarioCreate(UsuarioBase):
    """Criação de usuário"""
    senha: str = Field(..., min_length=8)

class UsuarioResponse(UsuarioBase):
    """Resposta com dados do usuário"""
    id: int
    criado_em: datetime

# ==============================
# VEHICLE SCHEMAS
# ==============================

class VeiculoBase(BaseSchema):
    """Dados base do veículo"""
    placa: str = Field(..., min_length=7, max_length=8)
    modelo: Optional[str] = None
    ano: Optional[int] = Field(None, ge=1900, le=2030)
    km_atual: int = Field(default=0, ge=0)
    
    @field_validator('placa')
    @classmethod
    def validate_placa(cls, v):
        if not re.match(r'^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$', v.upper()):
            raise ValueError('Placa deve estar no formato ABC1234 ou ABC1D23')
        return v.upper()

class VeiculoCreate(VeiculoBase):
    """Criação de veículo"""
    renavam: Optional[str] = None

class VeiculoResponse(VeiculoCreate):
    """Resposta com dados do veículo"""
    id: int
    ativo: bool

# ==============================
# DRIVER SCHEMAS  
# ==============================

class MotoristaBase(BaseSchema):
    """Dados base do motorista"""
    nome: str = Field(..., min_length=2, max_length=200)
    cnh: Optional[str] = None
    categoria: Optional[str] = None
    validade_cnh: Optional[date] = None

class MotoristaCreate(MotoristaBase):
    """Criação de motorista"""
    usuario_id: Optional[int] = None

class MotoristaResponse(MotoristaCreate):
    """Resposta com dados do motorista"""
    id: int
    ativo: bool

# ==============================
# CHECKLIST SCHEMAS
# ==============================

class ChecklistItemBase(BaseSchema):
    """Dados base do item de checklist"""
    ordem: int = Field(..., ge=1)
    descricao: str = Field(..., max_length=500)
    tipo_resposta: str = Field(default="ok")
    severidade: SeveridadeItem = Field(default=SeveridadeItem.MEDIA)
    exige_foto: bool = Field(default=False)
    bloqueia_viagem: bool = Field(default=False)

class ChecklistItemCreate(ChecklistItemBase):
    """Criação de item de checklist"""
    opcoes: List[str] = Field(default=[])

class ChecklistItemResponse(ChecklistItemCreate):
    """Resposta com dados do item"""
    id: int
    modelo_id: int

class ChecklistModeloBase(BaseSchema):
    """Dados base do modelo de checklist"""
    nome: str = Field(..., max_length=200)
    tipo: TipoChecklist
    versao: int = Field(default=1)
    ativo: bool = Field(default=True)

class ChecklistModeloCreate(ChecklistModeloBase):
    """Criação de modelo de checklist"""
    itens: List[ChecklistItemCreate] = Field(default=[])

class ChecklistModeloResponse(ChecklistModeloBase):
    """Resposta com dados do modelo"""
    id: int
    criado_em: datetime

# ==============================
# CHECKLIST EXECUTION SCHEMAS
# ==============================

class ChecklistStartRequest(BaseSchema):
    """Request para iniciar checklist"""
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    tipo: TipoChecklist
    odometro_ini: Optional[int] = Field(None, ge=0)
    geo_inicio: Optional[str] = None

class RespostaItemRequest(BaseSchema):
    """Request para resposta de item"""
    item_id: int
    valor: str
    observacao: Optional[str] = Field(None, max_length=1000)
    foto_url: Optional[str] = None
    geo: Optional[str] = None

class ChecklistAnswerRequest(BaseSchema):
    """Request para envio de respostas"""
    checklist_id: int
    respostas: List[RespostaItemRequest] = Field(..., min_length=1)

class ChecklistFinishRequest(BaseSchema):
    """Request para finalizar checklist"""
    checklist_id: int
    odometro_fim: Optional[int] = Field(None, ge=0)
    geo_fim: Optional[str] = None
    assinatura_motorista: Optional[str] = None

class ChecklistResponse(BaseSchema):
    """Resposta completa do checklist"""
    id: int
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    tipo: TipoChecklist
    status: StatusChecklist
    dt_inicio: datetime
    dt_fim: Optional[datetime] = None
    odometro_ini: Optional[int] = None
    odometro_fim: Optional[int] = None

# ==============================
# KPI SCHEMAS
# ==============================

class KPIChecklistSummary(BaseSchema):
    """Resumo de KPIs de checklist"""
    total_checklists: int
    aprovados: int
    reprovados: int
    taxa_aprovacao: float

# ==============================
# UPLOAD SCHEMAS
# ==============================

class UploadResponse(BaseSchema):
    """Resposta de upload de arquivo"""
    filename: str