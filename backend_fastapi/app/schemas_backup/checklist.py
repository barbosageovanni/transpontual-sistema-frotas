# backend_fastapi/app/schemas/checklist.py
"""
Schemas Pydantic para checklist
"""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

# ========== MODELOS DE CHECKLIST ==========

class ChecklistItemCreate(BaseModel):
    ordem: int
    descricao: str
    categoria: Optional[str] = "geral"
    tipo_resposta: str = "ok"  # ok|na|obs|foto
    severidade: str = "media"  # baixa|media|alta|critica
    exige_foto: bool = False
    bloqueia_viagem: bool = False
    opcoes: Optional[List[str]] = []
    instrucoes: Optional[str] = None
    
    @validator("tipo_resposta")
    def validate_tipo_resposta(cls, v):
        if v not in ["ok", "na", "obs", "foto"]:
            raise ValueError("tipo_resposta deve ser: ok, na, obs ou foto")
        return v
    
    @validator("severidade")
    def validate_severidade(cls, v):
        if v not in ["baixa", "media", "alta", "critica"]:
            raise ValueError("severidade deve ser: baixa, media, alta ou critica")
        return v

class ChecklistModeloCreate(BaseModel):
    nome: str
    tipo: str  # pre|pos|extra
    itens: List[ChecklistItemCreate]
    
    @validator("tipo")
    def validate_tipo(cls, v):
        if v not in ["pre", "pos", "extra"]:
            raise ValueError("tipo deve ser: pre, pos ou extra")
        return v
    
    @validator("itens")
    def validate_itens(cls, v):
        if not v:
            raise ValueError("Modelo deve ter pelo menos um item")
        
        # Verificar ordens únicas
        ordens = [item.ordem for item in v]
        if len(ordens) != len(set(ordens)):
            raise ValueError("Ordens dos itens devem ser únicas")
        
        return v

class ChecklistModeloOut(BaseModel):
    id: int
    nome: str
    tipo: str
    versao: int
    ativo: bool
    criado_em: datetime
    
    class Config:
        from_attributes = True

class ChecklistItemOut(BaseModel):
    id: int
    ordem: int
    descricao: str
    categoria: Optional[str]
    tipo_resposta: str
    severidade: str
    exige_foto: bool
    bloqueia_viagem: bool
    opcoes: List[str]
    instrucoes: Optional[str]

# ========== EXECUÇÃO DE CHECKLIST ==========

class ChecklistStartRequest(BaseModel):
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    tipo: str = "pre"
    viagem_id: Optional[int] = None
    odometro_ini: Optional[int] = None
    geo_inicio: Optional[str] = None
    
    @validator("tipo")
    def validate_tipo(cls, v):
        if v not in ["pre", "pos", "extra"]:
            raise ValueError("tipo deve ser: pre, pos ou extra")
        return v

class ChecklistRespostaRequest(BaseModel):
    item_id: int
    valor: str  # ok|nao_ok|na
    observacao: Optional[str] = None
    opcao_defeito: Optional[str] = None
    foto_url: Optional[str] = None
    geo: Optional[str] = None
    
    @validator("valor")
    def validate_valor(cls, v):
        if v not in ["ok", "nao_ok", "na"]:
            raise ValueError("valor deve ser: ok, nao_ok ou na")
        return v

class ChecklistAnswerRequest(BaseModel):
    checklist_id: int
    respostas: List[ChecklistRespostaRequest]
    
    @validator("respostas")
    def validate_respostas(cls, v):
        if not v:
            raise ValueError("Deve haver pelo menos uma resposta")
        
        # Verificar item_ids únicos
        item_ids = [r.item_id for r in v]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("item_ids devem ser únicos")
        
        return v

class ChecklistFinishRequest(BaseModel):
    checklist_id: int
    odometro_fim: Optional[int] = None
    geo_fim: Optional[str] = None
    assinatura_motorista: Optional[str] = None
    observacoes_gerais: Optional[str] = None

class ChecklistOut(BaseModel):
    id: int
    codigo: str
    tipo: str
    status: str
    veiculo_id: int
    motorista_id: int
    modelo_id: int
    viagem_id: Optional[int]
    dt_inicio: datetime
    dt_fim: Optional[datetime]
    duracao_minutos: Optional[int]
    odometro_ini: Optional[int]
    odometro_fim: Optional[int]
    geo_inicio: Optional[str]
    geo_fim: Optional[str]
    
    class Config:
        from_attributes = True

class ChecklistRespostaOut(BaseModel):
    item_id: int
    valor: str
    observacao: Optional[str]
    opcao_defeito: Optional[str]
    foto_url: Optional[str]
    geo: Optional[str]
    dt: datetime

class ChecklistDetailOut(BaseModel):
    id: int
    codigo: str
    tipo: str
    status: str
    veiculo_id: int
    veiculo_placa: Optional[str]
    motorista_id: int
    motorista_nome: Optional[str]
    modelo_id: int
    modelo_nome: Optional[str]
    dt_inicio: datetime
    dt_fim: Optional[datetime]
    duracao_minutos: Optional[int]
    odometro_ini: Optional[int]
    odometro_fim: Optional[int]
    geo_inicio: Optional[str]
    geo_fim: Optional[str]
    itens: List[Dict[str, Any]]
    respostas: List[ChecklistRespostaOut]

class ChecklistSummary(BaseModel):
    id: int
    codigo: str
    tipo: str
    status: str
    veiculo_placa: Optional[str]
    motorista_nome: Optional[str]
    modelo_nome: Optional[str]
    dt_inicio: datetime
    dt_fim: Optional[datetime]
    duracao_minutos: Optional[int]

# ========== UPLOAD DE ARQUIVOS ==========

class PhotoUploadResponse(BaseModel):
    success: bool
    filename: str
    url: str
    message: str

# ========== ESTATÍSTICAS ==========

class ChecklistStats(BaseModel):
    total_checklists: int
    aprovados: int
    reprovados: int
    pendentes: int
    taxa_aprovacao: float
    tempo_medio_minutos: float
    veiculos_distintos: int
    motoristas_distintos: int

class TopIssueItem(BaseModel):
    descricao: str
    categoria: str
    severidade: str
    total_nao_ok: int
    percentual_nao_ok: float

# ========== MANUTENÇÃO ==========

class DefeitoOut(BaseModel):
    id: int
    codigo: str
    categoria: str
    severidade: str
    descricao: str
    status: str
    prioridade: str
    custo_estimado: Optional[float]
    identificado_em: datetime
    resolvido_em: Optional[datetime]
    
    class Config:
        from_attributes = True

class OrdemServicoOut(BaseModel):
    id: int
    numero: str
    tipo: str
    descricao: str
    status: str
    prioridade: str
    abertura_dt: datetime
    conclusao_dt: Optional[datetime]
    custo_total: float
    veiculo_placa: Optional[str]
    
    class Config:
        from_attributes = True