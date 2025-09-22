# backend_fastapi/app/api_v1.py
"""
Router principal da API v1 - Versão simplificada
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app import models, schemas

# Router principal
api_router = APIRouter()

# Health check
@api_router.get("/health")
async def api_health():
    return {"status": "ok", "api": "v1"}

# Auth básico
@api_router.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Verificação simples (em produção usar hash)
    if payload.senha != user.senha_hash:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}

# Veículos
@api_router.get("/vehicles", response_model=List[schemas.VeiculoResponse])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(models.Veiculo).all()

@api_router.post("/vehicles", response_model=schemas.VeiculoResponse, status_code=201)
def create_vehicle(body: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    veiculo = models.Veiculo(**body.model_dump())
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo

# Motoristas
@api_router.get("/drivers", response_model=List[schemas.MotoristaResponse])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(models.Motorista).all()

# Checklist modelos
@api_router.get("/checklist/modelos", response_model=List[schemas.ChecklistModeloResponse])
def list_checklist_models(db: Session = Depends(get_db)):
    return db.query(models.ChecklistModelo).filter(models.ChecklistModelo.ativo == True).all()

@api_router.get("/checklist/modelos/{modelo_id}/itens")
def list_model_items(modelo_id: int, db: Session = Depends(get_db)):
    itens = db.query(models.ChecklistItem).filter(
        models.ChecklistItem.modelo_id == modelo_id
    ).order_by(models.ChecklistItem.ordem).all()
    
    return [
        {
            "id": item.id,
            "ordem": item.ordem,
            "descricao": item.descricao,
            "severidade": item.severidade,
            "exige_foto": item.exige_foto,
            "bloqueia_viagem": item.bloqueia_viagem,
            "opcoes": []  # Lista vazia por enquanto
        }
        for item in itens
    ]

# Checklist execução
@api_router.post("/checklist/start", response_model=schemas.ChecklistResponse, status_code=201)
def start_checklist(body: schemas.ChecklistStartRequest, db: Session = Depends(get_db)):
    checklist = models.Checklist(
        veiculo_id=body.veiculo_id,
        motorista_id=body.motorista_id,
        modelo_id=body.modelo_id,
        tipo=body.tipo,
        odometro_ini=body.odometro_ini,
        status="pendente"
    )
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist

@api_router.get("/checklist/{checklist_id}")
def get_checklist(checklist_id: int, db: Session = Depends(get_db)):
    checklist = db.get(models.Checklist, checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    respostas = db.query(models.ChecklistResposta).filter(
        models.ChecklistResposta.checklist_id == checklist_id
    ).all()
    
    itens = db.query(models.ChecklistItem).filter(
        models.ChecklistItem.modelo_id == checklist.modelo_id
    ).order_by(models.ChecklistItem.ordem).all()
    
    return {
        "id": checklist.id,
        "veiculo_id": checklist.veiculo_id,
        "motorista_id": checklist.motorista_id,
        "modelo_id": checklist.modelo_id,
        "tipo": checklist.tipo,
        "status": checklist.status,
        "dt_inicio": checklist.dt_inicio.isoformat(),
        "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None,
        "odometro_ini": checklist.odometro_ini,
        "odometro_fim": checklist.odometro_fim,
        "respostas": [
            {
                "item_id": r.item_id,
                "valor": r.valor,
                "observacao": r.observacao,
                "dt": r.dt.isoformat()
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
                "bloqueia_viagem": item.bloqueia_viagem
            }
            for item in itens
        ]
    }

@api_router.post("/checklist/answer")
def answer_checklist(body: schemas.ChecklistAnswerRequest, db: Session = Depends(get_db)):
    checklist = db.get(models.Checklist, body.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    for resposta in body.respostas:
        db_resposta = models.ChecklistResposta(
            checklist_id=body.checklist_id,
            item_id=resposta.item_id,
            valor=resposta.valor,
            observacao=resposta.observacao
        )
        db.add(db_resposta)
    
    db.commit()
    return {"ok": True}

@api_router.post("/checklist/finish", response_model=schemas.ChecklistResponse)
def finish_checklist(body: schemas.ChecklistFinishRequest, db: Session = Depends(get_db)):
    checklist = db.get(models.Checklist, body.checklist_id)
    if not checklist:
        raise HTTPException(404, "Checklist não encontrado")
    
    checklist.odometro_fim = body.odometro_fim
    checklist.status = "aprovado"  # Simplificado
    
    from datetime import datetime
    checklist.dt_fim = datetime.utcnow()
    
    db.commit()
    db.refresh(checklist)
    return checklist

# Upload básico
@api_router.post("/uploads/image", response_model=schemas.UploadResponse)
async def upload_image():
    # Implementação básica
    return {"filename": "test.jpg"}

# KPIs básicos
@api_router.get("/kpis/summary")
def kpi_summary(db: Session = Depends(get_db)):
    total = db.query(models.Checklist).count()
    aprovados = db.query(models.Checklist).filter(models.Checklist.status == "aprovado").count()
    
    return {
        "total": total,
        "aprovados": aprovados,
        "reprovados": total - aprovados,
        "taxa_aprovacao": (aprovados / total * 100) if total > 0 else 0
    }