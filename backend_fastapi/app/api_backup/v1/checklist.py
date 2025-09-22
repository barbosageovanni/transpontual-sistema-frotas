# backend_fastapi/app/api/v1/checklist.py
"""
Endpoints para checklist - Módulo 1 completo
"""
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from core.database import get_db
from core.security import get_current_user
from models.user import Usuario
from models.checklist import ChecklistModelo, ChecklistItem, Checklist, ChecklistResposta
from models.vehicle import Veiculo
from models.user import Motorista
from models.maintenance import Defeito, OrdemServico
from schemas.checklist import (
    ChecklistModeloOut, ChecklistModeloCreate,
    ChecklistStartRequest, ChecklistOut, ChecklistDetailOut,
    ChecklistAnswerRequest, ChecklistFinishRequest,
    ChecklistSummary
)

router = APIRouter()

# ========== MODELOS DE CHECKLIST ==========

@router.get("/modelos", response_model=List[ChecklistModeloOut])
def list_models(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar modelos de checklist ativos"""
    models = db.query(ChecklistModelo).filter(
        ChecklistModelo.ativo == True
    ).order_by(ChecklistModelo.nome).all()
    return models

@router.get("/modelos/{modelo_id}/itens")
def get_model_items(
    modelo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obter itens de um modelo de checklist"""
    modelo = db.get(ChecklistModelo, modelo_id)
    if not modelo:
        raise HTTPException(404, "Modelo não encontrado")
    
    # Query raw para incluir campo opcoes (JSON)
    query = text("""
        SELECT id, ordem, descricao, categoria, tipo_resposta, severidade, 
               exige_foto, bloqueia_viagem, instrucoes,
               COALESCE(opcoes, '[]'::jsonb) AS opcoes
        FROM checklist_itens
        WHERE modelo_id = :modelo_id
        ORDER BY ordem
    """)
    
    items = db.execute(query, {"modelo_id": modelo_id}).mappings().all()
    return [dict(item) for item in items]

@router.post("/modelos", response_model=ChecklistModeloOut)
def create_model(
    payload: ChecklistModeloCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Criar novo modelo de checklist (apenas gestores)"""
    if current_user.papel not in ["gestor"]:
        raise HTTPException(403, "Permissão insuficiente")
    
    modelo = ChecklistModelo(
        nome=payload.nome,
        tipo=payload.tipo,
        versao=1,
        ativo=True
    )
    db.add(modelo)
    db.flush()  # Para obter o ID
    
    # Adicionar itens
    ordem_set = set()
    for item_data in payload.itens:
        if item_data.ordem in ordem_set:
            raise HTTPException(400, f"Ordem duplicada: {item_data.ordem}")
        ordem_set.add(item_data.ordem)
        
        item = ChecklistItem(
            modelo_id=modelo.id,
            ordem=item_data.ordem,
            descricao=item_data.descricao,
            categoria=item_data.categoria,
            tipo_resposta=item_data.tipo_resposta,
            severidade=item_data.severidade,
            exige_foto=item_data.exige_foto,
            bloqueia_viagem=item_data.bloqueia_viagem,
            opcoes=item_data.opcoes or [],
            instrucoes=item_data.instrucoes
        )
        db.add(item)
    
    db.commit()
    db.refresh(modelo)
    return modelo

# ========== EXECUÇÃO DE CHECKLIST ==========

@router.post("/start", response_model=ChecklistOut)
def start_checklist(
    payload: ChecklistStartRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Iniciar novo checklist"""
    
    # Validações
    veiculo = db.get(Veiculo, payload.veiculo_id)
    if not veiculo or not veiculo.ativo:
        raise HTTPException(404, "Veículo não encontrado ou inativo")
    
    motorista = db.get(Motorista, payload.motorista_id)
    if not motorista or not motorista.ativo:
        raise HTTPException(404, "Motorista não encontrado ou inativo")
    
    modelo = db.get(ChecklistModelo, payload.modelo_id)
    if not modelo or not modelo.ativo:
        raise HTTPException(404, "Modelo de checklist não encontrado ou inativo")
    
    # Verificar se já existe checklist pendente para o veículo
    existing = db.query(Checklist).filter(
        Checklist.veiculo_id == payload.veiculo_id,
        Checklist.status.in_(["pendente", "em_andamento"])
    ).first()
    
    if existing:
        raise HTTPException(400, f"Já existe checklist pendente para este veículo (ID: {existing.id})")
    
    # Criar checklist
    codigo = f"CL-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    checklist = Checklist(
        codigo=codigo,
        viagem_id=payload.viagem_id,
        veiculo_id=payload.veiculo_id,
        motorista_id=payload.motorista_id,
        modelo_id=payload.modelo_id,
        tipo=payload.tipo,
        odometro_ini=payload.odometro_ini,
        geo_inicio=payload.geo_inicio,
        status="em_andamento"
    )
    
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    
    return checklist

@router.get("/{checklist_id}", response_model=ChecklistDetailOut)
def get_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obter detalhes de um checklist"""
    checklist = db.query(Checklist).options(
        joinedload(Checklist.veiculo),
        joinedload(Checklist.motorista),
        joinedload(Checklist.modelo),
        joinedload(Checklist.respostas)
    ).filter(Checklist.id == checklist_id).first()
    
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    # Obter itens do modelo
    query = text("""
        SELECT id, ordem, descricao, categoria, severidade, exige_foto, 
               bloqueia_viagem, instrucoes,
               COALESCE(opcoes, '[]'::jsonb) AS opcoes
        FROM checklist_itens
        WHERE modelo_id = :modelo_id
        ORDER BY ordem
    """)
    
    itens = db.execute(query, {"modelo_id": checklist.modelo_id}).mappings().all()
    
    # Mapear respostas por item_id
    respostas_map = {r.item_id: r for r in checklist.respostas}
    
    return {
        "id": checklist.id,
        "codigo": checklist.codigo,
        "tipo": checklist.tipo,
        "status": checklist.status,
        "veiculo_id": checklist.veiculo_id,
        "veiculo_placa": checklist.veiculo.placa if checklist.veiculo else None,
        "motorista_id": checklist.motorista_id,
        "motorista_nome": checklist.motorista.nome if checklist.motorista else None,
        "modelo_id": checklist.modelo_id,
        "modelo_nome": checklist.modelo.nome if checklist.modelo else None,
        "dt_inicio": checklist.dt_inicio,
        "dt_fim": checklist.dt_fim,
        "odometro_ini": checklist.odometro_ini,
        "odometro_fim": checklist.odometro_fim,
        "duracao_minutos": checklist.duracao_minutos,
        "geo_inicio": checklist.geo_inicio,
        "geo_fim": checklist.geo_fim,
        "itens": [dict(item) for item in itens],
        "respostas": [{
            "item_id": r.item_id,
            "valor": r.valor,
            "observacao": r.observacao,
            "opcao_defeito": r.opcao_defeito,
            "foto_url": r.foto_url,
            "geo": r.geo,
            "dt": r.dt
        } for r in checklist.respostas]
    }

@router.post("/answer")
def answer_checklist(
    payload: ChecklistAnswerRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar respostas do checklist"""
    checklist = db.get(Checklist, payload.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    if checklist.status not in ["em_andamento", "pendente"]:
        raise HTTPException(400, "Checklist já finalizado")
    
    bloqueios_criados = 0
    defeitos_criados = []
    
    # Processar cada resposta
    for resposta_data in payload.respostas:
        # Verificar se item existe
        item = db.get(ChecklistItem, resposta_data.item_id)
        if not item:
            continue
        
        # Remover resposta existente se houver
        db.query(ChecklistResposta).filter(
            ChecklistResposta.checklist_id == checklist.id,
            ChecklistResposta.item_id == resposta_data.item_id
        ).delete()
        
        # Criar nova resposta
        resposta = ChecklistResposta(
            checklist_id=checklist.id,
            item_id=resposta_data.item_id,
            valor=resposta_data.valor,
            observacao=resposta_data.observacao,
            opcao_defeito=resposta_data.opcao_defeito,
            foto_url=resposta_data.foto_url,
            geo=resposta_data.geo
        )
        db.add(resposta)
        
        # Se resposta é "nao_ok" e item bloqueia viagem -> criar defeito
        if (resposta_data.valor == "nao_ok" and 
            item.bloqueia_viagem and 
            item.severidade in ["alta", "critica"]):
            
            # Criar defeito
            defeito_codigo = f"DEF-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
            
            descricao_defeito = item.descricao
            if resposta_data.opcao_defeito:
                descricao_defeito += f" - {resposta_data.opcao_defeito}"
            if resposta_data.observacao:
                descricao_defeito += f" - {resposta_data.observacao}"
            
            defeito = Defeito(
                codigo=defeito_codigo,
                checklist_id=checklist.id,
                item_id=item.id,
                veiculo_id=checklist.veiculo_id,
                categoria=item.categoria or "geral",
                severidade=item.severidade,
                descricao=descricao_defeito,
                observacao=resposta_data.observacao,
                status="identificado",
                prioridade="alta" if item.severidade == "critica" else "normal"
            )
            db.add(defeito)
            db.flush()  # Para obter ID
            
            # Criar OS automaticamente
            os_numero = f"OS-{datetime.now().strftime('%Y%m%d')}-{defeito.id:04d}"
            
            ordem_servico = OrdemServico(
                numero=os_numero,
                veiculo_id=checklist.veiculo_id,
                defeito_id=defeito.id,
                tipo="corretiva",
                descricao=descricao_defeito,
                responsavel_abertura=current_user.nome,
                prioridade="alta" if item.severidade == "critica" else "normal",
                km_veiculo=checklist.odometro_ini,
                status="aberta"
            )
            db.add(ordem_servico)
            
            bloqueios_criados += 1
            defeitos_criados.append({
                "id": defeito.id,
                "codigo": defeito_codigo,
                "descricao": descricao_defeito,
                "severidade": defeito.severidade
            })
    
    # Atualizar status do checklist se necessário
    if checklist.status == "pendente":
        checklist.status = "em_andamento"
    
    db.commit()
    
    return {
        "success": True,
        "checklist_id": checklist.id,
        "respostas_processadas": len(payload.respostas),
        "bloqueios_criados": bloqueios_criados,
        "defeitos": defeitos_criados,
        "message": f"Respostas salvas. {bloqueios_criados} bloqueio(s) identificado(s)." if bloqueios_criados > 0 else "Respostas salvas com sucesso."
    }

@router.post("/finish", response_model=ChecklistOut)
def finish_checklist(
    payload: ChecklistFinishRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Finalizar checklist"""
    checklist = db.get(Checklist, payload.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    if checklist.status in ["aprovado", "reprovado"]:
        raise HTTPException(400, "Checklist já finalizado")
    
    # Atualizar dados finais
    now = datetime.utcnow()
    checklist.dt_fim = now
    checklist.odometro_fim = payload.odometro_fim
    checklist.geo_fim = payload.geo_fim
    checklist.assinatura_motorista = payload.assinatura_motorista
    checklist.observacoes_gerais = payload.observacoes_gerais
    
    # Calcular duração
    if checklist.dt_inicio:
        delta = now - checklist.dt_inicio
        checklist.duracao_minutos = int(delta.total_seconds() / 60)
    
    # Determinar status final baseado em defeitos bloqueadores
    defeitos_bloqueadores = db.query(Defeito).join(ChecklistItem).filter(
        Defeito.checklist_id == checklist.id,
        ChecklistItem.bloqueia_viagem == True,
        Defeito.status.in_(["identificado", "aberto"])
    ).count()
    
    checklist.status = "reprovado" if defeitos_bloqueadores > 0 else "aprovado"
    
    # Atualizar KM do veículo se fornecido
    if payload.odometro_fim and checklist.veiculo:
        checklist.veiculo.km_atual = payload.odometro_fim
    
    db.commit()
    db.refresh(checklist)
    
    return checklist

# ========== CONSULTAS E RELATÓRIOS ==========

@router.get("/", response_model=List[ChecklistSummary])
def list_checklists(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    veiculo_id: Optional[int] = None,
    motorista_id: Optional[int] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar checklists com filtros"""
    query = db.query(Checklist).options(
        joinedload(Checklist.veiculo),
        joinedload(Checklist.motorista),
        joinedload(Checklist.modelo)
    )
    
    # Aplicar filtros
    if status:
        query = query.filter(Checklist.status == status)
    if veiculo_id:
        query = query.filter(Checklist.veiculo_id == veiculo_id)
    if motorista_id:
        query = query.filter(Checklist.motorista_id == motorista_id)
    if tipo:
        query = query.filter(Checklist.tipo == tipo)
    
    # Ordenação e paginação
    checklists = query.order_by(Checklist.dt_inicio.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": c.id,
        "codigo": c.codigo,
        "tipo": c.tipo,
        "status": c.status,
        "veiculo_placa": c.veiculo.placa if c.veiculo else None,
        "motorista_nome": c.motorista.nome if c.motorista else None,
        "modelo_nome": c.modelo.nome if c.modelo else None,
        "dt_inicio": c.dt_inicio,
        "dt_fim": c.dt_fim,
        "duracao_minutos": c.duracao_minutos
    } for c in checklists]

@router.get("/pending")
def get_pending_checklists(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar checklists pendentes/em andamento"""
    query = text("""
        SELECT 
            c.id, c.codigo, c.tipo, c.status,
            v.placa as veiculo_placa,
            m.nome as motorista_nome,
            cm.nome as modelo_nome,
            c.dt_inicio,
            EXTRACT(EPOCH FROM (NOW() - c.dt_inicio)) / 60 as minutos_pendente
        FROM checklists c
        JOIN veiculos v ON v.id = c.veiculo_id
        JOIN motoristas m ON m.id = c.motorista_id
        JOIN checklist_modelos cm ON cm.id = c.modelo_id
        WHERE c.status IN ('pendente', 'em_andamento')
        ORDER BY c.dt_inicio
    """)
    
    result = db.execute(query).mappings().all()
    return [dict(row) for row in result]

@router.get("/stats/summary")
def get_checklist_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resumo estatístico de checklists"""
    query = text("""
        SELECT
            COUNT(*) as total_checklists,
            COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
            COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados,
            COUNT(*) FILTER (WHERE status IN ('pendente', 'em_andamento')) as pendentes,
            ROUND(AVG(duracao_minutos), 1) as tempo_medio_minutos,
            COUNT(DISTINCT veiculo_id) as veiculos_distintos,
            COUNT(DISTINCT motorista_id) as motoristas_distintos
        FROM checklists
        WHERE dt_inicio >= NOW() - INTERVAL '%s days'
    """, days)
    
    result = db.execute(query).mappings().first()
    
    if not result or result.get("total_checklists", 0) == 0:
        return {
            "total_checklists": 0,
            "aprovados": 0,
            "reprovados": 0,
            "pendentes": 0,
            "taxa_aprovacao": 0.0,
            "tempo_medio_minutos": 0.0,
            "veiculos_distintos": 0,
            "motoristas_distintos": 0
        }
    
    total = result["total_checklists"]
    aprovados = result["aprovados"] or 0
    taxa_aprovacao = (aprovados / total * 100) if total > 0 else 0
    
    return {
        "total_checklists": total,
        "aprovados": aprovados,
        "reprovados": result["reprovados"] or 0,
        "pendentes": result["pendentes"] or 0,
        "taxa_aprovacao": round(taxa_aprovacao, 1),
        "tempo_medio_minutos": result["tempo_medio_minutos"] or 0,
        "veiculos_distintos": result["veiculos_distintos"] or 0,
        "motoristas_distintos": result["motoristas_distintos"] or 0
    }

@router.get("/stats/top-issues")
def get_top_issues(
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Top itens com mais problemas"""
    query = text("""
        SELECT 
            ci.descricao,
            ci.categoria,
            ci.severidade,
            COUNT(cr.id) as total_nao_ok,
            COUNT(cr.id) * 100.0 / (
                SELECT COUNT(*) 
                FROM checklist_respostas cr2 
                JOIN checklists c2 ON c2.id = cr2.checklist_id
                WHERE cr2.item_id = ci.id 
                AND c2.dt_inicio >= NOW() - INTERVAL '%s days'
            ) as percentual_nao_ok
        FROM checklist_itens ci
        JOIN checklist_respostas cr ON cr.item_id = ci.id
        JOIN checklists c ON c.id = cr.checklist_id
        WHERE cr.valor = 'nao_ok'
        AND c.dt_inicio >= NOW() - INTERVAL '%s days'
        GROUP BY ci.id, ci.descricao, ci.categoria, ci.severidade
        HAVING COUNT(cr.id) > 0
        ORDER BY total_nao_ok DESC, percentual_nao_ok DESC
        LIMIT %s
    """, days, days, limit)
    
    result = db.execute(query).mappings().all()
    return [dict(row) for row in result]