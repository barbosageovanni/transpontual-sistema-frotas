from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.core.database import get_db
from app import models, schemas
from app.core.security import get_current_user, require_role

router = APIRouter()

ALLOWED_RESPOSTA = {"ok", "nao_ok", "na"}
ALLOWED_SEVERIDADE = {"baixa", "media", "alta"}


# Listagem com filtros e paginação
@router.get("/", response_model=dict)
def list_checklists(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    tipo: str | None = Query(None),
    veiculo_id: int | None = Query(None),
    motorista_id: int | None = Query(None),
    modelo_id: int | None = Query(None),
    placa: str | None = Query(None),
    motorista_nome: str | None = Query(None),
    odometro_ini_min: int | None = Query(None, ge=0),
    odometro_ini_max: int | None = Query(None, ge=0),
    data_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(None, description="YYYY-MM-DD"),
    order_by: str = Query("dt_inicio"),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    q = db.query(models.Checklist)
    if status:
        q = q.filter(models.Checklist.status == status)
    if tipo:
        q = q.filter(models.Checklist.tipo == tipo)
    if veiculo_id:
        q = q.filter(models.Checklist.veiculo_id == veiculo_id)
    if motorista_id:
        q = q.filter(models.Checklist.motorista_id == motorista_id)
    if modelo_id:
        q = q.filter(models.Checklist.modelo_id == modelo_id)
    if odometro_ini_min is not None:
        q = q.filter(models.Checklist.odometro_ini >= odometro_ini_min)
    if odometro_ini_max is not None:
        q = q.filter(models.Checklist.odometro_ini <= odometro_ini_max)
    if placa:
        q = (
            q.join(models.Veiculo, models.Veiculo.id == models.Checklist.veiculo_id)
            .filter(func.lower(models.Veiculo.placa).like(f"%{placa.lower()}%"))
        )
    if motorista_nome:
        q = (
            q.join(models.Motorista, models.Motorista.id == models.Checklist.motorista_id)
            .filter(func.lower(models.Motorista.nome).like(f"%{motorista_nome.lower()}%"))
        )
    from datetime import datetime
    if data_inicio:
        try:
            di = datetime.fromisoformat(data_inicio).date()
            q = q.filter(models.Checklist.dt_inicio >= di)
        except Exception:
            raise HTTPException(400, "data_inicio inválida (use YYYY-MM-DD)")
    if data_fim:
        try:
            df = datetime.fromisoformat(data_fim).date()
            q = q.filter(models.Checklist.dt_inicio <= df)
        except Exception:
            raise HTTPException(400, "data_fim inválida (use YYYY-MM-DD)")

    total = q.count()
    # ordenação segura
    order_col = getattr(models.Checklist, order_by, models.Checklist.dt_inicio)
    q = q.order_by(order_col.desc() if order_dir == "desc" else order_col.asc())
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    # Carregar dados relacionados básicos
    veiculo_ids = {c.veiculo_id for c in items}
    motorista_ids = {c.motorista_id for c in items}
    veiculos = {}
    if veiculo_ids:
        for v in (
            db.query(models.Veiculo)
            .filter(models.Veiculo.id.in_(veiculo_ids))
            .all()
        ):
            veiculos[v.id] = {"placa": v.placa, "modelo": v.modelo}
    motoristas = {}
    if motorista_ids:
        for m in (
            db.query(models.Motorista)
            .filter(models.Motorista.id.in_(motorista_ids))
            .all()
        ):
            motoristas[m.id] = {"nome": m.nome}

    # Load checklist models
    modelo_ids = {c.modelo_id for c in items}
    modelos = {}
    if modelo_ids:
        for mod in (
            db.query(models.ChecklistModelo)
            .filter(models.ChecklistModelo.id.in_(modelo_ids))
            .all()
        ):
            modelos[mod.id] = {"nome": mod.nome, "tipo": mod.tipo}

    def ser(c: models.Checklist):
        v = veiculos.get(c.veiculo_id, {})
        m = motoristas.get(c.motorista_id, {})
        mod = modelos.get(c.modelo_id, {})
        return {
            "id": c.id,
            "veiculo_id": c.veiculo_id,
            "veiculo_placa": v.get("placa"),
            "veiculo_modelo": v.get("modelo"),
            "motorista_id": c.motorista_id,
            "motorista_nome": m.get("nome"),
            "modelo_id": c.modelo_id,
            "modelo_nome": mod.get("nome"),
            "modelo_tipo": mod.get("tipo"),
            "tipo": c.tipo,
            "status": c.status,
            "dt_inicio": c.dt_inicio.isoformat() if c.dt_inicio else None,
            "dt_fim": c.dt_fim.isoformat() if c.dt_fim else None,
            "odometro_ini": c.odometro_ini,
            "odometro_fim": c.odometro_fim,
        }

    return {
        "items": [ser(c) for c in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/modelos", response_model=list[schemas.ChecklistModeloResponse])
def list_checklist_models(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    # Check database availability
    if db is None:
        return []

    return db.query(models.ChecklistModelo).filter(models.ChecklistModelo.ativo == True).all()


@router.post("/modelos", response_model=schemas.ChecklistModeloResponse, status_code=201)
def create_checklist_model(
    body: schemas.ChecklistModeloCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    if not body.nome or not body.nome.strip():
        raise HTTPException(400, "Nome do modelo é obrigatório")
    # Evitar duplicidade de nome ativo por tipo
    exists = (
        db.query(models.ChecklistModelo)
        .filter(models.ChecklistModelo.nome == body.nome.strip())
        .filter(models.ChecklistModelo.tipo == body.tipo)
        .filter(models.ChecklistModelo.ativo == True)
        .first()
    )
    if exists:
        raise HTTPException(409, "Já existe um modelo ativo com este nome e tipo")
    model = models.ChecklistModelo(**body.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.put("/modelos/{modelo_id}", response_model=schemas.ChecklistModeloResponse)
def update_checklist_model(
    modelo_id: int,
    body: schemas.ChecklistModeloUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    model = db.get(models.ChecklistModelo, modelo_id)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    data = body.model_dump(exclude_unset=True)
    if "nome" in data and (not data["nome"] or not data["nome"].strip()):
        raise HTTPException(400, "Nome do modelo é obrigatório")
    if "nome" in data or "tipo" in data:
        nome = data.get("nome", model.nome)
        tipo = data.get("tipo", model.tipo)
        exists = (
            db.query(models.ChecklistModelo)
            .filter(models.ChecklistModelo.id != model.id)
            .filter(models.ChecklistModelo.nome == nome)
            .filter(models.ChecklistModelo.tipo == tipo)
            .filter(models.ChecklistModelo.ativo == True)
            .first()
        )
        if exists:
            raise HTTPException(409, "Já existe um modelo ativo com este nome e tipo")
    for k, v in data.items():
        setattr(model, k, v)
    db.commit()
    db.refresh(model)
    return model


@router.delete("/modelos/{modelo_id}")
def delete_checklist_model(
    modelo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    model = db.get(models.ChecklistModelo, modelo_id)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    model.ativo = False
    db.commit()
    return {"ok": True}


@router.get("/modelos/{modelo_id}/itens")
def list_model_items(
    modelo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    itens = (
        db.query(models.ChecklistItem)
        .filter(models.ChecklistItem.modelo_id == modelo_id)
        .order_by(models.ChecklistItem.ordem)
        .all()
    )
    return [
        {
            "id": item.id,
            "ordem": item.ordem,
            "descricao": item.descricao,
            "severidade": item.severidade,
            "exige_foto": item.exige_foto,
            "bloqueia_viagem": item.bloqueia_viagem,
            "opcoes": [],
        }
        for item in itens
    ]


@router.post("/modelos/{modelo_id}/itens", response_model=schemas.ChecklistItemResponse, status_code=201)
def create_model_item(
    modelo_id: int,
    body: schemas.ChecklistItemCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    if body.modelo_id != modelo_id:
        raise HTTPException(400, "modelo_id inconsistente")
    if not db.get(models.ChecklistModelo, modelo_id):
        raise HTTPException(404, "Modelo não encontrado")
    if body.ordem is None or body.ordem < 1:
        raise HTTPException(400, "Ordem deve ser >= 1")
    if not body.descricao or not body.descricao.strip():
        raise HTTPException(400, "Descrição é obrigatória")
    if body.severidade and str(body.severidade).lower() not in ALLOWED_SEVERIDADE:
        raise HTTPException(400, "Severidade inválida")
    if body.tipo_resposta and str(body.tipo_resposta).lower() not in ALLOWED_RESPOSTA:
        raise HTTPException(400, "Tipo de resposta inválido")
    # Unicidade de ordem por modelo
    dup = (
        db.query(models.ChecklistItem)
        .filter(models.ChecklistItem.modelo_id == modelo_id)
        .filter(models.ChecklistItem.ordem == body.ordem)
        .first()
    )
    if dup:
        raise HTTPException(409, "Já existe um item com esta ordem neste modelo")
    item = models.ChecklistItem(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/itens/{item_id}", response_model=schemas.ChecklistItemResponse)
def update_model_item(
    item_id: int,
    body: schemas.ChecklistItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    item = db.get(models.ChecklistItem, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    data = body.model_dump(exclude_unset=True)
    if "ordem" in data and data["ordem"] is not None and data["ordem"] < 1:
        raise HTTPException(400, "Ordem deve ser >= 1")
    if "descricao" in data and (not data["descricao"] or not data["descricao"].strip()):
        raise HTTPException(400, "Descrição é obrigatória")
    if "severidade" in data and data["severidade"] and str(data["severidade"]).lower() not in ALLOWED_SEVERIDADE:
        raise HTTPException(400, "Severidade inválida")
    if "tipo_resposta" in data and data["tipo_resposta"] and str(data["tipo_resposta"]).lower() not in ALLOWED_RESPOSTA:
        raise HTTPException(400, "Tipo de resposta inválido")
    # Unicidade de ordem por modelo (se alterar)
    if "ordem" in data and data["ordem"] is not None and data["ordem"] != item.ordem:
        dup = (
            db.query(models.ChecklistItem)
            .filter(models.ChecklistItem.modelo_id == item.modelo_id)
            .filter(models.ChecklistItem.ordem == data["ordem"]) 
            .first()
        )
        if dup:
            raise HTTPException(409, "Já existe um item com esta ordem neste modelo")
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/itens/{item_id}")
def delete_model_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    item = db.get(models.ChecklistItem, item_id)
    if not item:
        raise HTTPException(404, "Item não encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/start", response_model=schemas.ChecklistResponse)
def start_checklist(
    body: schemas.ChecklistStartRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    if not db.get(models.Veiculo, body.veiculo_id):
        raise HTTPException(404, "Veículo não encontrado")
    if not db.get(models.Motorista, body.motorista_id):
        raise HTTPException(404, "Motorista não encontrado")
    model = db.get(models.ChecklistModelo, body.modelo_id)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    expected_tipo = getattr(body.tipo, "value", body.tipo)
    if expected_tipo != model.tipo:
        raise HTTPException(400, "Tipo do checklist não corresponde ao modelo")
    if body.odometro_ini is not None and body.odometro_ini < 0:
        raise HTTPException(400, "Odômetro inicial inválido")

    checklist = models.Checklist(
        veiculo_id=body.veiculo_id,
        motorista_id=body.motorista_id,
        modelo_id=body.modelo_id,
        tipo=body.tipo,
        odometro_ini=body.odometro_ini,
        status="em_andamento",
    )
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist


@router.get("/{checklist_id}")
def get_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    # Get related data
    veiculo = db.get(models.Veiculo, checklist.veiculo_id) if checklist.veiculo_id else None
    motorista = db.get(models.Motorista, checklist.motorista_id) if checklist.motorista_id else None
    modelo = db.get(models.ChecklistModelo, checklist.modelo_id) if checklist.modelo_id else None

    respostas = (
        db.query(models.ChecklistResposta)
        .filter(models.ChecklistResposta.checklist_id == checklist_id)
        .all()
    )
    itens = (
        db.query(models.ChecklistItem)
        .filter(models.ChecklistItem.modelo_id == checklist.modelo_id)
        .order_by(models.ChecklistItem.ordem)
        .all()
    )

    # Calculate score and counts
    total_respostas = len(respostas)
    total_itens = len(itens)
    itens_ok = len([r for r in respostas if r.valor == 'ok'])
    itens_nok = len([r for r in respostas if r.valor == 'nao_ok'])
    itens_na = len([r for r in respostas if r.valor == 'na'])

    # Calculate approval score (OK items / Total items * 100)
    score_aprovacao = None
    if total_itens > 0:
        score_aprovacao = (itens_ok / total_itens) * 100

    return {
        "id": checklist.id,
        "veiculo_id": checklist.veiculo_id,
        "veiculo_placa": veiculo.placa if veiculo else None,
        "veiculo_modelo": veiculo.modelo if veiculo else None,
        "motorista_id": checklist.motorista_id,
        "motorista_nome": motorista.nome if motorista else None,
        "modelo_id": checklist.modelo_id,
        "modelo_nome": modelo.nome if modelo else None,
        "modelo_tipo": modelo.tipo if modelo else None,
        "tipo": checklist.tipo,
        "status": checklist.status,
        "dt_inicio": checklist.dt_inicio.isoformat(),
        "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None,
        "odometro_ini": checklist.odometro_ini,
        "odometro_fim": checklist.odometro_fim,
        "score_aprovacao": score_aprovacao,
        "itens_ok": itens_ok,
        "itens_nok": itens_nok,
        "itens_na": itens_na,
        "tem_bloqueios": any(item.bloqueia_viagem and any(r.item_id == item.id and r.valor == 'nao_ok' for r in respostas) for item in itens),
        "respostas": [
            {
                "item_id": r.item_id,
                "valor": r.valor,
                "observacao": r.observacao,
                "dt": r.dt.isoformat(),
            }
            for r in respostas
        ],
        "itens": [
            {
                "id": item.id,
                "ordem": item.ordem,
                "descricao": item.descricao,
                "severidade": item.severidade,
                "exige_foto": item.exige_foto,
                "bloqueia_viagem": item.bloqueia_viagem,
            }
            for item in itens
        ],
    }


@router.post("/answer")
def answer_checklist(
    body: schemas.ChecklistAnswerRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    checklist = db.get(models.Checklist, body.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    # Validar itens e valores
    valid_item_ids = {
        i.id
        for i in db.query(models.ChecklistItem)
        .filter(models.ChecklistItem.modelo_id == checklist.modelo_id)
        .all()
    }
    for resposta in body.respostas:
        if resposta.item_id not in valid_item_ids:
            raise HTTPException(400, f"Item {resposta.item_id} não pertence ao modelo do checklist")
        if resposta.valor not in ALLOWED_RESPOSTA:
            raise HTTPException(400, "Valor de resposta inválido")
        db.add(
            models.ChecklistResposta(
                checklist_id=body.checklist_id,
                item_id=resposta.item_id,
                valor=resposta.valor,
                observacao=resposta.observacao,
            )
        )
    db.commit()
    return {"ok": True}


@router.post("/finish", response_model=schemas.ChecklistResponse)
def finish_checklist(
    body: schemas.ChecklistFinishRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    checklist = db.get(models.Checklist, body.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    if body.odometro_fim is not None:
        if checklist.odometro_ini is not None and body.odometro_fim < checklist.odometro_ini:
            raise HTTPException(400, "Odômetro final não pode ser menor que o inicial")
        if body.odometro_fim < 0:
            raise HTTPException(400, "Odômetro final inválido")
        checklist.odometro_fim = body.odometro_fim
    checklist.status = "aprovado"
    from datetime import datetime
    checklist.dt_fim = datetime.utcnow()
    db.commit()
    db.refresh(checklist)
    return checklist


@router.delete("/{checklist_id}")
def delete_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor")),
):
    """Delete a checklist and all its responses"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    # Delete all responses first (foreign key constraint)
    db.query(models.ChecklistResposta).filter(
        models.ChecklistResposta.checklist_id == checklist_id
    ).delete()

    # Delete the checklist
    db.delete(checklist)
    db.commit()
    return {"message": "Checklist excluído com sucesso"}


@router.post("/{checklist_id}/add-item")
def add_item_to_checklist(
    checklist_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Add a new item to an existing checklist"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    if checklist.status == "concluido":
        raise HTTPException(400, "Não é possível adicionar itens a checklists concluídos")

    # Get the highest order for this model to add new item at the end
    max_order = (
        db.query(func.max(models.ChecklistItem.ordem))
        .filter(models.ChecklistItem.modelo_id == checklist.modelo_id)
        .scalar()
    ) or 0

    # Create the new item
    new_item = models.ChecklistItem(
        modelo_id=checklist.modelo_id,
        categoria=body.get("categoria", "outros"),
        descricao=body.get("descricao", ""),
        ordem=max_order + 1,
        tipo_resposta="multipla_escolha",
        severidade=body.get("severidade", "media"),
        exige_foto=body.get("exige_foto", False),
        bloqueia_viagem=body.get("bloqueia_viagem", False)
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "message": "Item adicionado com sucesso",
        "item": {
            "id": new_item.id,
            "ordem": new_item.ordem,
            "descricao": new_item.descricao,
            "categoria": new_item.categoria,
            "severidade": new_item.severidade
        }
    }


@router.get("/{checklist_id}/approval-report")
def get_approval_report(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Get detailed approval report showing all items and their status"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    # Get checklist details
    veiculo = db.get(models.Veiculo, checklist.veiculo_id)
    motorista = db.get(models.Motorista, checklist.motorista_id)
    modelo = db.get(models.ChecklistModelo, checklist.modelo_id)

    # Get all items for this checklist model
    itens = (
        db.query(models.ChecklistItem)
        .filter(models.ChecklistItem.modelo_id == checklist.modelo_id)
        .order_by(models.ChecklistItem.ordem)
        .all()
    )

    # Get all responses
    respostas = {}
    responses_query = (
        db.query(models.ChecklistResposta)
        .filter(models.ChecklistResposta.checklist_id == checklist_id)
        .all()
    )

    for resp in responses_query:
        respostas[resp.item_id] = {
            "valor": resp.valor,
            "observacao": resp.observacao,
            "dt": resp.dt.isoformat() if resp.dt else None
        }

    # Categorize items
    conformes = []
    nao_conformes = []
    nao_aplicaveis = []
    nao_respondidos = []

    for item in itens:
        item_data = {
            "id": item.id,
            "ordem": item.ordem,
            "categoria": item.categoria,
            "descricao": item.descricao,
            "severidade": item.severidade,
            "exige_foto": item.exige_foto,
            "bloqueia_viagem": item.bloqueia_viagem
        }

        if item.id in respostas:
            resp = respostas[item.id]
            item_data.update({
                "valor": resp["valor"],
                "observacao": resp["observacao"],
                "respondido_em": resp["dt"]
            })

            # Categorize based on response
            if resp["valor"] == "ok":
                conformes.append(item_data)
            elif resp["valor"] == "nao_ok":
                nao_conformes.append(item_data)
            elif resp["valor"] == "na":
                nao_aplicaveis.append(item_data)
        else:
            nao_respondidos.append(item_data)

    return {
        "checklist": {
            "id": checklist.id,
            "tipo": checklist.tipo,
            "status": checklist.status,
            "dt_inicio": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
            "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None,
            "odometro_ini": checklist.odometro_ini,
            "odometro_fim": checklist.odometro_fim
        },
        "veiculo": {
            "id": veiculo.id if veiculo else None,
            "placa": veiculo.placa if veiculo else "N/A",
            "modelo": veiculo.modelo if veiculo else "N/A"
        },
        "motorista": {
            "id": motorista.id if motorista else None,
            "nome": motorista.nome if motorista else "N/A"
        },
        "modelo": {
            "id": modelo.id if modelo else None,
            "nome": modelo.nome if modelo else "N/A",
            "tipo": modelo.tipo if modelo else "N/A"
        },
        "resumo": {
            "total_itens": len(itens),
            "conformes": len(conformes),
            "nao_conformes": len(nao_conformes),
            "nao_aplicaveis": len(nao_aplicaveis),
            "nao_respondidos": len(nao_respondidos),
            "percentual_conformidade": round((len(conformes) / len(itens) * 100), 2) if len(itens) > 0 else 0
        },
        "itens": {
            "conformes": conformes,
            "nao_conformes": nao_conformes,
            "nao_aplicaveis": nao_aplicaveis,
            "nao_respondidos": nao_respondidos
        }
    }


@router.post("/{checklist_id}/approve")
def approve_checklist(
    checklist_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role("gestor", "admin")),
):
    """Approve or reject a checklist"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    if checklist.status not in ["aguardando_aprovacao", "em_andamento", "concluido"]:
        raise HTTPException(400, "Checklist não pode ser aprovado neste status")

    action = body.get("action")  # "aprovar" or "reprovar"
    observacao_gestor = body.get("observacao", "")

    if action == "aprovar":
        checklist.status = "aprovado"
    elif action == "reprovar":
        checklist.status = "reprovado"
    else:
        raise HTTPException(400, "Ação deve ser 'aprovar' ou 'reprovar'")

    # Store manager's observation (you might want to add this field to the model)
    # For now, we'll add it as a response to a special "manager review" item if it exists
    from datetime import datetime
    checklist.dt_fim = datetime.utcnow()

    db.commit()
    db.refresh(checklist)

    return {
        "message": f"Checklist {action}do com sucesso",
        "checklist": {
            "id": checklist.id,
            "status": checklist.status,
            "dt_fim": checklist.dt_fim.isoformat()
        }
    }


@router.patch("/{checklist_id}/items/batch")
def update_multiple_items(
    checklist_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Salvamento em lote de múltiplos itens do checklist"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    if checklist.status not in ["em_andamento"]:
        raise HTTPException(400, "Checklist deve estar em andamento para ser editado")

    items = body.get("items", [])
    if not items:
        raise HTTPException(400, "Nenhum item fornecido")

    saved_items = []
    errors = []

    try:
        for item_data in items:
            try:
                item_id = item_data.get("item_id")
                valor = item_data.get("valor")
                observacao = item_data.get("observacao")

                if not item_id or not valor:
                    errors.append(f"Item {item_id}: dados incompletos")
                    continue

                if valor not in ALLOWED_RESPOSTA:
                    errors.append(f"Item {item_id}: valor inválido")
                    continue

                # Verificar se o item existe
                item = db.query(models.ChecklistItem).filter(
                    models.ChecklistItem.id == item_id,
                    models.ChecklistItem.modelo_id == checklist.modelo_id
                ).first()

                if not item:
                    errors.append(f"Item {item_id}: não encontrado")
                    continue

                # Buscar resposta existente
                resposta = db.query(models.ChecklistResposta).filter(
                    models.ChecklistResposta.checklist_id == checklist_id,
                    models.ChecklistResposta.item_id == item_id
                ).first()

                if resposta:
                    # Atualizar resposta existente
                    resposta.valor = valor
                    resposta.observacao = observacao
                    resposta.dt = datetime.utcnow()
                else:
                    # Criar nova resposta
                    resposta = models.ChecklistResposta(
                        checklist_id=checklist_id,
                        item_id=item_id,
                        valor=valor,
                        observacao=observacao,
                        dt=datetime.utcnow()
                    )
                    db.add(resposta)

                saved_items.append({
                    "item_id": item_id,
                    "valor": valor,
                    "observacao": observacao
                })

            except Exception as e:
                errors.append(f"Item {item_id}: {str(e)}")

        db.commit()

        return {
            "message": f"Salvamento em lote concluído",
            "saved_count": len(saved_items),
            "error_count": len(errors),
            "saved_items": saved_items,
            "errors": errors if errors else None
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro no salvamento em lote: {str(e)}")


@router.patch("/{checklist_id}")
def update_checklist(
    checklist_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Atualizar dados básicos do checklist"""
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")

    # Validar campos atualizáveis
    updateable_fields = {
        'tipo', 'veiculo_id', 'motorista_id', 'modelo_id',
        'odometro_ini', 'odometro_fim'
    }

    updates = {}
    for field, value in body.items():
        if field in updateable_fields:
            # Validações específicas
            if field == 'tipo' and value not in ['pre', 'pos', 'extra']:
                raise HTTPException(400, f"Tipo inválido: {value}")

            if field in ['veiculo_id', 'motorista_id', 'modelo_id'] and value:
                # Verificar se os IDs existem
                if field == 'veiculo_id':
                    if not db.get(models.Veiculo, value):
                        raise HTTPException(400, f"Veículo {value} não encontrado")
                elif field == 'motorista_id':
                    if not db.get(models.Motorista, value):
                        raise HTTPException(400, f"Motorista {value} não encontrado")
                elif field == 'modelo_id':
                    if not db.get(models.ChecklistModelo, value):
                        raise HTTPException(400, f"Modelo {value} não encontrado")

            if field in ['odometro_ini', 'odometro_fim'] and value is not None:
                if value < 0:
                    raise HTTPException(400, f"Odômetro não pode ser negativo: {value}")

            updates[field] = value

    if not updates:
        return {"message": "Nenhum campo para atualizar", "checklist": checklist}

    try:
        # Aplicar atualizações
        for field, value in updates.items():
            setattr(checklist, field, value)

        db.commit()
        db.refresh(checklist)

        return {
            "message": "Checklist atualizado com sucesso",
            "checklist": {
                "id": checklist.id,
                "tipo": checklist.tipo,
                "veiculo_id": checklist.veiculo_id,
                "motorista_id": checklist.motorista_id,
                "modelo_id": checklist.modelo_id,
                "odometro_ini": checklist.odometro_ini,
                "odometro_fim": checklist.odometro_fim,
                "status": checklist.status,
                "dt_inicio": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
                "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None
            },
            "updated_fields": list(updates.keys())
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro ao atualizar checklist: {str(e)}")
