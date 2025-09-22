"""
Router para Checklist - Sistema Transpontual
Endpoints completos para gestão de checklist veicular
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, desc, and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.core.exceptions import BusinessRuleException
from app.models import (
    ChecklistModelo, ChecklistItem, Checklist, ChecklistResposta,
    Veiculo, Motorista, Viagem, Defeito, OrdemServico, Usuario
)
from app.schemas import (
    ChecklistModeloCreate, ChecklistModeloResponse, ChecklistModeloUpdate,
    ChecklistItemResponse, ChecklistStartRequest, ChecklistAnswerRequest,
    ChecklistFinishRequest, ChecklistResponse, RespostaItemResponse,
    DefeitoCreate, DefeitoResponse, OrdemServicoCreate
)
from app.services.checklist_service import ChecklistService
from app.services.notification_service import NotificationService
from app.tasks.background import (
    process_checklist_completion, 
    generate_automatic_os,
    refresh_materialized_views
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ==============================
# DEPENDENCY INJECTION
# ==============================

def get_checklist_service(db: Session = Depends(get_db)) -> ChecklistService:
    """Injeção do serviço de checklist"""
    return ChecklistService(db)

def get_notification_service() -> NotificationService:
    """Injeção do serviço de notificação"""
    return NotificationService()

# ==============================
# MODELOS DE CHECKLIST
# ==============================

@router.get("/modelos", response_model=List[ChecklistModeloResponse], tags=["Modelos"])
async def list_modelos(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    categoria_veiculo: Optional[str] = Query(None, description="Filtrar por categoria"),
    ativo: bool = Query(True, description="Apenas modelos ativos"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar modelos de checklist disponíveis"""
    try:
        query = db.query(ChecklistModelo).filter(ChecklistModelo.ativo == ativo)
        
        if tipo:
            query = query.filter(ChecklistModelo.tipo == tipo)
        if categoria_veiculo:
            query = query.filter(ChecklistModelo.categoria_veiculo == categoria_veiculo)
        
        modelos = query.order_by(ChecklistModelo.nome).all()
        
        # Buscar estatísticas dos modelos
        for modelo in modelos:
            stats = db.execute(text("""
                SELECT 
                    COUNT(*) as total_itens,
                    COUNT(*) FILTER (WHERE bloqueia_viagem = true) as itens_bloqueantes,
                    COUNT(*) FILTER (WHERE severidade = 'critica') as itens_criticos
                FROM checklist_itens 
                WHERE modelo_id = :modelo_id AND ativo = true
            """), {"modelo_id": modelo.id}).mappings().first()
            
            modelo.total_itens = stats['total_itens'] if stats else 0
            modelo.itens_bloqueantes = stats['itens_bloqueantes'] if stats else 0
            modelo.itens_criticos = stats['itens_criticos'] if stats else 0
        
        return modelos
        
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar modelos de checklist"
        )

@router.post("/modelos", response_model=ChecklistModeloResponse, status_code=201, tags=["Modelos"])
async def create_modelo(
    body: ChecklistModeloCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gestor"]))
):
    """Criar novo modelo de checklist"""
    try:
        # Verificar se já existe modelo com mesmo nome e tipo
        existing = db.query(ChecklistModelo).filter(
            ChecklistModelo.nome == body.nome,
            ChecklistModelo.tipo == body.tipo,
            ChecklistModelo.ativo == True
        ).first()
        
        if existing:
            raise BusinessRuleException(
                "Já existe um modelo ativo com este nome e tipo",
                code="MODELO_DUPLICADO"
            )
        
        # Validar ordens dos itens (não pode haver duplicatas)
        ordens = [item.ordem for item in body.itens]
        if len(ordens) != len(set(ordens)):
            raise BusinessRuleException(
                "Não pode haver itens com a mesma ordem",
                code="ORDEM_DUPLICADA"
            )
        
        # Criar modelo
        modelo = ChecklistModelo(
            nome=body.nome,
            tipo=body.tipo,
            categoria_veiculo=body.categoria_veiculo,
            descricao=body.descricao,
            tempo_estimado_minutos=body.tempo_estimado_minutos,
            obrigatorio=body.obrigatorio,
            criado_por=current_user.id
        )
        db.add(modelo)
        db.flush()
        
        # Criar itens
        for item_data in body.itens:
            item = ChecklistItem(
                modelo_id=modelo.id,
                ordem=item_data.ordem,
                categoria=item_data.categoria,
                subcategoria=item_data.subcategoria,
                descricao=item_data.descricao,
                descricao_detalhada=item_data.descricao_detalhada,
                tipo_resposta=item_data.tipo_resposta,
                opcoes=item_data.opcoes,
                severidade=item_data.severidade,
                exige_foto=item_data.exige_foto,
                exige_observacao=item_data.exige_observacao,
                bloqueia_viagem=item_data.bloqueia_viagem,
                gera_os=item_data.gera_os,
                codigo_item=item_data.codigo_item,
                valor_min=item_data.valor_min,
                valor_max=item_data.valor_max,
                unidade=item_data.unidade,
                criado_por=current_user.id
            )
            db.add(item)
        
        db.commit()
        db.refresh(modelo)
        
        # Agendar refresh das views materializadas
        background_tasks.add_task(refresh_materialized_views)
        
        logger.info(f"Modelo de checklist criado: {modelo.nome} (ID: {modelo.id})")
        return modelo
        
    except BusinessRuleException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar modelo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar modelo de checklist"
        )

@router.get("/modelos/{modelo_id}/itens", response_model=List[ChecklistItemResponse], tags=["Modelos"])
async def get_modelo_itens(
    modelo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Buscar itens de um modelo específico"""
    modelo = db.get(ChecklistModelo, modelo_id)
    if not modelo or not modelo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo de checklist não encontrado"
        )
    
    itens = db.query(ChecklistItem).filter(
        ChecklistItem.modelo_id == modelo_id,
        ChecklistItem.ativo == True
    ).order_by(ChecklistItem.ordem).all()
    
    return itens

@router.put("/modelos/{modelo_id}", response_model=ChecklistModeloResponse, tags=["Modelos"])
async def update_modelo(
    modelo_id: int,
    body: ChecklistModeloUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gestor"]))
):
    """Atualizar modelo de checklist"""
    modelo = db.get(ChecklistModelo, modelo_id)
    if not modelo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modelo não encontrado"
        )
    
    # Atualizar campos
    for field, value in body.dict(exclude_unset=True).items():
        setattr(modelo, field, value)
    
    db.commit()
    db.refresh(modelo)
    
    logger.info(f"Modelo atualizado: {modelo.nome} (ID: {modelo.id})")
    return modelo

@router.post("/modelos/{modelo_id}/clone", response_model=ChecklistModeloResponse, tags=["Modelos"])
async def clone_modelo(
    modelo_id: int,
    novo_nome: str = Query(..., description="Nome para o novo modelo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gestor"]))
):
    """Clonar modelo existente"""
    try:
        result = db.execute(
            text("SELECT clone_checklist_modelo(:modelo_id, :novo_nome)"),
            {"modelo_id": modelo_id, "novo_nome": novo_nome}
        ).scalar()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modelo original não encontrado"
            )
        
        db.commit()
        novo_modelo = db.get(ChecklistModelo, result)
        
        logger.info(f"Modelo clonado: {novo_nome} (ID: {result})")
        return novo_modelo
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao clonar modelo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao clonar modelo"
        )

# ==============================
# EXECUÇÃO DE CHECKLIST
# ==============================

@router.post("/start", response_model=ChecklistResponse, status_code=201, tags=["Execução"])
async def start_checklist(
    body: ChecklistStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    checklist_service: ChecklistService = Depends(get_checklist_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Iniciar novo checklist"""
    try:
        # Validações de negócio
        veiculo = db.get(Veiculo, body.veiculo_id)
        if not veiculo or not veiculo.ativo:
            raise BusinessRuleException(
                "Veículo não encontrado ou inativo",
                code="VEICULO_INATIVO"
            )
        
        motorista = db.get(Motorista, body.motorista_id)
        if not motorista or not motorista.ativo:
            raise BusinessRuleException(
                "Motorista não encontrado ou inativo", 
                code="MOTORISTA_INATIVO"
            )
        
        modelo = db.get(ChecklistModelo, body.modelo_id)
        if not modelo or not modelo.ativo:
            raise BusinessRuleException(
                "Modelo de checklist não encontrado ou inativo",
                code="MODELO_INATIVO"
            )
        
        # Verificar se há checklist pendente para mesmo veículo/tipo
        checklist_pendente = db.query(Checklist).filter(
            Checklist.veiculo_id == body.veiculo_id,
            Checklist.tipo == body.tipo,
            Checklist.status.in_(['pendente', 'em_andamento'])
        ).first()
        
        if checklist_pendente:
            raise BusinessRuleException(
                f"Já existe checklist {body.tipo} pendente para este veículo",
                code="CHECKLIST_PENDENTE"
            )
        
        # Para checklist pré-viagem, verificar se viagem está liberada
        if body.tipo == "pre" and body.viagem_id:
            viagem = db.get(Viagem, body.viagem_id)
            if viagem and viagem.status == "bloqueada":
                raise BusinessRuleException(
                    "Não é possível iniciar checklist para viagem bloqueada",
                    code="VIAGEM_BLOQUEADA"
                )
        
        # Criar checklist usando service
        checklist = checklist_service.create_checklist(
            veiculo_id=body.veiculo_id,
            motorista_id=body.motorista_id,
            modelo_id=body.modelo_id,
            tipo=body.tipo,
            viagem_id=body.viagem_id,
            odometro_ini=body.odometro_ini,
            geo_inicio=body.geo_inicio,
            dispositivo_info=body.dispositivo_info,
            created_by=current_user.id
        )
        
        db.commit()
        
        # Carregar dados completos para resposta
        checklist_completo = db.query(Checklist).options(
            joinedload(Checklist.respostas),
            joinedload(Checklist.modelo).joinedload(ChecklistModelo.itens)
        ).filter(Checklist.id == checklist.id).first()
        
        logger.info(f"Checklist iniciado: {checklist.codigo} para veículo {veiculo.placa}")
        return checklist_completo
        
    except BusinessRuleException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao iniciar checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao iniciar checklist"
        )

@router.get("/{checklist_id}", response_model=ChecklistResponse, tags=["Execução"])
async def get_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Buscar checklist específico com todos os dados"""
    checklist = db.query(Checklist).options(
        joinedload(Checklist.respostas),
        joinedload(Checklist.veiculo),
        joinedload(Checklist.motorista),
        joinedload(Checklist.modelo).joinedload(ChecklistModelo.itens)
    ).filter(Checklist.id == checklist_id).first()
    
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist não encontrado"
        )
    
    # Verificar permissão (motorista só vê seus próprios checklists)
    if (current_user.papel == "motorista" and 
        checklist.motorista_id != current_user.motorista.id if current_user.motorista else True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este checklist"
        )
    
    # Preparar resposta com itens ordenados
    response_data = {
        **checklist.__dict__,
        "itens": sorted(checklist.modelo.itens, key=lambda x: x.ordem),
        "respostas": checklist.respostas
    }
    
    return ChecklistResponse(**response_data)

@router.post("/answer", tags=["Execução"])
async def answer_checklist(
    body: ChecklistAnswerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    checklist_service: ChecklistService = Depends(get_checklist_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar respostas do checklist"""
    try:
        checklist = db.get(Checklist, body.checklist_id)
        if not checklist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checklist não encontrado"
            )
        
        if checklist.status not in ['pendente', 'em_andamento']:
            raise BusinessRuleException(
                "Não é possível alterar respostas de checklist finalizado",
                code="CHECKLIST_FINALIZADO"
            )
        
        # Verificar permissão
        if (current_user.papel == "motorista" and 
            checklist.motorista_id != current_user.motorista.id if current_user.motorista else True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para modificar este checklist"
            )
        
        # Atualizar status para em_andamento se necessário
        if checklist.status == 'pendente':
            checklist.status = 'em_andamento'
        
        bloqueios_criados = 0
        defeitos_criados = []
        
        # Processar cada resposta
        for resposta_data in body.respostas:
            item = db.get(ChecklistItem, resposta_data.item_id)
            if not item or item.modelo_id != checklist.modelo_id:
                continue
            
            # Verificar se já existe resposta para este item
            resposta_existente = db.query(ChecklistResposta).filter(
                ChecklistResposta.checklist_id == checklist.id,
                ChecklistResposta.item_id == resposta_data.item_id
            ).first()
            
            if resposta_existente:
                # Atualizar resposta existente
                for field, value in resposta_data.dict(exclude_unset=True, exclude={'item_id'}).items():
                    setattr(resposta_existente, field, value)
                resposta = resposta_existente
            else:
                # Criar nova resposta
                resposta = ChecklistResposta(
                    checklist_id=checklist.id,
                    item_id=resposta_data.item_id,
                    valor=resposta_data.valor,
                    valor_numerico=resposta_data.valor_numerico,
                    opcao_selecionada=resposta_data.opcao_selecionada,
                    observacao=resposta_data.observacao,
                    foto_url=resposta_data.foto_url,
                    geo=resposta_data.geo,
                    tempo_resposta_segundos=resposta_data.tempo_resposta_segundos
                )
                db.add(resposta)
                db.flush()
            
            # Processar item reprovado que bloqueia viagem ou gera OS
            if resposta_data.valor == "nao_ok":
                if item.bloqueia_viagem or item.gera_os:
                    defeito = Defeito(
                        checklist_id=checklist.id,
                        item_id=item.id,
                        resposta_id=resposta.id,
                        veiculo_id=checklist.veiculo_id,
                        severidade=item.severidade,
                        categoria=item.categoria,
                        descricao=f"{item.descricao}: {resposta_data.observacao or resposta_data.opcao_selecionada or 'Reprovado'}",
                        status="identificado",
                        prioridade="alta" if item.severidade in ["alta", "critica"] else "normal",
                        criado_por=current_user.id
                    )
                    db.add(defeito)
                    db.flush()
                    defeitos_criados.append(defeito.id)
                    
                    if item.bloqueia_viagem:
                        bloqueios_criados += 1
                    
                    if item.gera_os:
                        # Agendar criação de OS em background
                        background_tasks.add_task(
                            generate_automatic_os,
                            defeito.id,
                            current_user.id
                        )
        
        db.commit()
        
        # Notificar sobre bloqueios se houver
        if bloqueios_criados > 0:
            background_tasks.add_task(
                notification_service.notify_checklist_blocked,
                checklist.id,
                bloqueios_criados
            )
        
        logger.info(f"Respostas registradas para checklist {checklist.codigo}: {len(body.respostas)} itens")
        
        return {
            "success": True,
            "respostas_processadas": len(body.respostas),
            "bloqueios_criados": bloqueios_criados,
            "defeitos_criados": len(defeitos_criados),
            "checklist_status": checklist.status
        }
        
    except BusinessRuleException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao registrar respostas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar respostas"
        )

@router.post("/finish", response_model=ChecklistResponse, tags=["Execução"])
async def finish_checklist(
    body: ChecklistFinishRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    checklist_service: ChecklistService = Depends(get_checklist_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: Usuario = Depends(get_current_user)
):
    """Finalizar checklist"""
    try:
        checklist = db.query(Checklist).options(
            joinedload(Checklist.respostas),
            joinedload(Checklist.defeitos)
        ).filter(Checklist.id == body.checklist_id).first()
        
        if not checklist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checklist não encontrado"
            )
        
        if checklist.status in ['aprovado', 'reprovado', 'cancelado']:
            raise BusinessRuleException(
                "Checklist já foi finalizado",
                code="CHECKLIST_JA_FINALIZADO"
            )
        
        # Verificar permissão
        if (current_user.papel == "motorista" and 
            checklist.motorista_id != current_user.motorista.id if current_user.motorista else True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para finalizar este checklist"
            )
        
        # Validar se todas as respostas obrigatórias foram preenchidas
        total_itens_obrigatorios = db.query(ChecklistItem).filter(
            ChecklistItem.modelo_id == checklist.modelo_id,
            ChecklistItem.ativo == True
        ).count()
        
        total_respostas = len(checklist.respostas)
        
        if total_respostas < total_itens_obrigatorios:
            raise BusinessRuleException(
                f"Checklist incompleto: {total_respostas}/{total_itens_obrigatorios} itens respondidos",
                code="CHECKLIST_INCOMPLETO"
            )
        
        # Finalizar usando service
        checklist = checklist_service.finish_checklist(
            checklist_id=body.checklist_id,
            odometro_fim=body.odometro_fim,
            geo_fim=body.geo_fim,
            assinatura_motorista=body.assinatura_motorista,
            observacoes_gerais=body.observacoes_gerais
        )
        
        db.commit()
        
        # Processar finalização em background
        background_tasks.add_task(
            process_checklist_completion,
            checklist.id
        )
        
        # Atualizar status da viagem se aplicável
        if checklist.viagem_id and checklist.tipo == "pre":
            viagem = db.get(Viagem, checklist.viagem_id)
            if viagem:
                if checklist.status == "aprovado":
                    viagem.status = "liberada"
                elif checklist.status == "reprovado":
                    viagem.status = "bloqueada"
                db.commit()
        
        logger.info(f"Checklist finalizado: {checklist.codigo} - Status: {checklist.status}")
        return checklist
        
    except BusinessRuleException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao finalizar checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao finalizar checklist"
        )

# ==============================
# CONSULTAS E RELATÓRIOS
# ==============================

@router.get("/", response_model=List[ChecklistResponse], tags=["Consulta"])
async def list_checklists(
    veiculo_id: Optional[int] = Query(None, description="Filtrar por veículo"),
    motorista_id: Optional[int] = Query(None, description="Filtrar por motorista"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    limit: int = Query(50, le=200, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Deslocamento"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar checklists com filtros"""
    query = db.query(Checklist).options(
        joinedload(Checklist.veiculo),
        joinedload(Checklist.motorista)
    )
    
    # Filtros por papel do usuário
    if current_user.papel == "motorista" and current_user.motorista:
        query = query.filter(Checklist.motorista_id == current_user.motorista.id)
    
    # Aplicar filtros
    if veiculo_id:
        query = query.filter(Checklist.veiculo_id == veiculo_id)
    if motorista_id:
        query = query.filter(Checklist.motorista_id == motorista_id)
    if tipo:
        query = query.filter(Checklist.tipo == tipo)
    if status:
        query = query.filter(Checklist.status == status)
    if data_inicio:
        query = query.filter(Checklist.dt_inicio >= data_inicio)
    if data_fim:
        query = query.filter(Checklist.dt_inicio <= data_fim)
    
    # Ordenação e paginação
    query = query.order_by(desc(Checklist.dt_inicio))
    checklists = query.offset(offset).limit(limit).all()
    
    return checklists

@router.get("/pendentes", response_model=List[ChecklistResponse], tags=["Consulta"])
async def list_checklists_pendentes(
    veiculo_id: Optional[int] = Query(None, description="Filtrar por veículo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar checklists pendentes"""
    query = db.query(Checklist).options(
        joinedload(Checklist.veiculo),
        joinedload(Checklist.motorista)
    ).filter(Checklist.status.in_(['pendente', 'em_andamento']))
    
    if current_user.papel == "motorista" and current_user.motorista:
        query = query.filter(Checklist.motorista_id == current_user.motorista.id)
    
    if veiculo_id:
        query = query.filter(Checklist.veiculo_id == veiculo_id)
    
    checklists = query.order_by(Checklist.dt_inicio).all()
    return checklists

@router.get("/bloqueios", tags=["Consulta"])
async def list_bloqueios(
    dias: int = Query(7, ge=1, le=90, description="Últimos N dias"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gestor", "mecanico"]))
):
    """Listar checklists com bloqueios"""
    result = db.execute(text("""
        SELECT 
            c.id,
            c.codigo,
            v.placa,
            m.nome as motorista_nome,
            c.tipo,
            c.dt_inicio,
            c.status,
            COUNT(d.id) as total_defeitos,
            COUNT(d.id) FILTER (WHERE d.status = 'aberto') as defeitos_abertos,
            COUNT(DISTINCT os.id) as total_os
        FROM checklists c
        JOIN veiculos v ON v.id = c.veiculo_id
        JOIN motoristas m ON m.id = c.motorista_id
        LEFT JOIN defeitos d ON d.checklist_id = c.id
        LEFT JOIN ordens_servico os ON os.defeito_id = d.id
        WHERE c.tem_bloqueios = true
          AND c.dt_inicio >= NOW() - make_interval(days => :dias)
        GROUP BY c.id, v.placa, m.nome
        ORDER BY c.dt_inicio DESC
    """), {"dias": dias}).mappings().all()
    
    return [dict(row) for row in result]

@router.delete("/{checklist_id}", tags=["Administração"])
async def cancel_checklist(
    checklist_id: int,
    motivo: str = Query(..., description="Motivo do cancelamento"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gestor"]))
):
    """Cancelar checklist"""
    checklist = db.get(Checklist, checklist_id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist não encontrado"
        )
    
    if checklist.status in ['aprovado', 'reprovado']:
        raise BusinessRuleException(
            "Não é possível cancelar checklist já finalizado",
            code="CHECKLIST_FINALIZADO"
        )
    
    checklist.status = 'cancelado'
    checklist.observacoes_gerais = f"CANCELADO: {motivo}"
    checklist.finalizado_em = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Checklist cancelado: {checklist.codigo} - Motivo: {motivo}")
    return {"success": True, "message": "Checklist cancelado com sucesso"}

# ==============================
# ESTATÍSTICAS E RESUMOS
# ==============================

@router.get("/stats/resumo", tags=["Estatísticas"])
async def get_resumo_checklists(
    dias: int = Query(30, ge=1, le=365, description="Período em dias"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resumo estatístico dos checklists"""
    
    # Filtro por papel do usuário
    motorista_filter = ""
    params = {"dias": dias}
    
    if current_user.papel == "motorista" and current_user.motorista:
        motorista_filter = "AND c.motorista_id = :motorista_id"
        params["motorista_id"] = current_user.motorista.id
    
    result = db.execute(text(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
            COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados,
            COUNT(*) FILTER (WHERE status IN ('pendente', 'em_andamento')) as pendentes,
            COUNT(*) FILTER (WHERE tem_bloqueios = true) as com_bloqueios,
            ROUND(AVG(score_aprovacao), 2) as score_medio,
            ROUND(AVG(duracao_minutos), 1) as duracao_media,
            COUNT(DISTINCT veiculo_id) as veiculos_distintos,
            COUNT(DISTINCT motorista_id) as motoristas_distintos
        FROM checklists c
        WHERE dt_inicio >= NOW() - make_interval(days => :dias)
        {motorista_filter}
    """), params).mappings().first()
    
    # Evolução diária dos últimos 7 dias
    evolucao = db.execute(text(f"""
        SELECT 
            DATE_TRUNC('day', dt_inicio) as data,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
            COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados
        FROM checklists c
        WHERE dt_inicio >= CURRENT_DATE - INTERVAL '7 days'
        {motorista_filter}
        GROUP BY DATE_TRUNC('day', dt_inicio)
        ORDER BY data
    """), params).mappings().all()
    
    return {
        "resumo": dict(result) if result else {},
        "evolucao_semanal": [dict(row) for row in evolucao]
    }