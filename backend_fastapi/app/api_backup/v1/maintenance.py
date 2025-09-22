# backend_fastapi/app/api/v1/maintenance.py
"""
Endpoints para manutenção
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from core.database import get_db
from core.security import get_current_user, require_role
from models.user import Usuario
from models.maintenance import Defeito, OrdemServico
from schemas.checklist import DefeitoOut, OrdemServicoOut

router = APIRouter()

@router.get("/defeitos", response_model=List[DefeitoOut])
def list_defeitos(
    status: Optional[str] = None,
    severidade: Optional[str] = None,
    veiculo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar defeitos"""
    query = db.query(Defeito)
    
    if status:
        query = query.filter(Defeito.status == status)
    if severidade:
        query = query.filter(Defeito.severidade == severidade)
    if veiculo_id:
        query = query.filter(Defeito.veiculo_id == veiculo_id)
    
    defeitos = query.order_by(Defeito.identificado_em.desc()).offset(skip).limit(limit).all()
    return defeitos

@router.get("/ordens-servico", response_model=List[OrdemServicoOut])
def list_ordens_servico(
    status: Optional[str] = None,
    veiculo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar ordens de serviço"""
    query = db.query(OrdemServico).options(joinedload(OrdemServico.veiculo))
    
    if status:
        query = query.filter(OrdemServico.status == status)
    if veiculo_id:
        query = query.filter(OrdemServico.veiculo_id == veiculo_id)
    
    ordens = query.order_by(OrdemServico.abertura_dt.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": os.id,
        "numero": os.numero,
        "tipo": os.tipo,
        "descricao": os.descricao,
        "status": os.status,
        "prioridade": os.prioridade,
        "abertura_dt": os.abertura_dt,
        "conclusao_dt": os.conclusao_dt,
        "custo_total": float(os.custo_total or 0),
        "veiculo_placa": os.veiculo.placa if os.veiculo else None
    } for os in ordens]

@router.get("/stats/summary")
def get_maintenance_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resumo de manutenção"""
    query = text("""
        SELECT
            COUNT(DISTINCT d.id) as total_defeitos,
            COUNT(DISTINCT d.id) FILTER (WHERE d.status = 'identificado') as defeitos_abertos,
            COUNT(DISTINCT d.id) FILTER (WHERE d.severidade = 'critica') as defeitos_criticos,
            COUNT(DISTINCT os.id) as total_os,
            COUNT(DISTINCT os.id) FILTER (WHERE os.status = 'aberta') as os_abertas,
            COUNT(DISTINCT os.id) FILTER (WHERE os.status = 'finalizada') as os_finalizadas,
            COALESCE(SUM(os.custo_total), 0) as custo_total_periodo
        FROM defeitos d
        LEFT JOIN ordens_servico os ON os.defeito_id = d.id
        WHERE d.identificado_em >= NOW() - INTERVAL '%s days'
    """, days)
    
    result = db.execute(query).mappings().first()
    
    return {
        "total_defeitos": result["total_defeitos"] or 0,
        "defeitos_abertos": result["defeitos_abertos"] or 0,
        "defeitos_criticos": result["defeitos_criticos"] or 0,
        "total_os": result["total_os"] or 0,
        "os_abertas": result["os_abertas"] or 0,
        "os_finalizadas": result["os_finalizadas"] or 0,
        "custo_total_periodo": float(result["custo_total_periodo"] or 0)
    }

@router.patch("/ordens-servico/{os_id}/status")
def update_os_status(
    os_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("gestor", "mecanico"))
):
    """Atualizar status de ordem de serviço"""
    os = db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(404, "Ordem de serviço não encontrada")
    
    valid_status = ["aberta", "em_execucao", "aguardando_peca", "finalizada", "cancelada"]
    if status not in valid_status:
        raise HTTPException(400, f"Status deve ser um de: {', '.join(valid_status)}")
    
    os.status = status
    
    # Atualizar timestamps conforme status
    from datetime import datetime
    now = datetime.utcnow()
    
    if status == "em_execucao" and not os.inicio_execucao_dt:
        os.inicio_execucao_dt = now
    elif status == "finalizada":
        os.conclusao_dt = now
        # Resolver defeito associado
        if os.defeito:
            os.defeito.status = "resolvido"
            os.defeito.resolvido_em = now
    
    db.commit()
    
    return {"success": True, "message": f"Status atualizado para: {status}"}

