# backend_fastapi/app/routers/fornecedores.py
"""
Router para endpoints de fornecedores
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app import models, schemas

router = APIRouter()

@router.get("/fornecedores", response_model=List[schemas.FornecedorResponse])
def list_fornecedores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tipo: Optional[str] = Query(None),
    ativo: Optional[bool] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lista fornecedores com filtros"""
    query = db.query(models.Fornecedor)

    if tipo:
        query = query.filter(models.Fornecedor.tipo == tipo)

    if ativo is not None:
        query = query.filter(models.Fornecedor.ativo == ativo)

    if busca:
        busca_pattern = f"%{busca}%"
        query = query.filter(
            (models.Fornecedor.nome.ilike(busca_pattern)) |
            (models.Fornecedor.cnpj.ilike(busca_pattern))
        )

    fornecedores = query.order_by(models.Fornecedor.nome).offset(skip).limit(limit).all()
    return fornecedores

@router.get("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def get_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    """Busca fornecedor por ID"""
    fornecedor = db.query(models.Fornecedor).filter(models.Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return fornecedor

@router.post("/fornecedores", response_model=schemas.FornecedorResponse, status_code=201)
def create_fornecedor(fornecedor_data: schemas.FornecedorCreate, db: Session = Depends(get_db)):
    """Cria novo fornecedor"""
    try:
        # Verificar se CNPJ já existe
        if fornecedor_data.cnpj:
            existing = db.query(models.Fornecedor).filter(
                models.Fornecedor.cnpj == fornecedor_data.cnpj
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

        fornecedor = models.Fornecedor(**fornecedor_data.model_dump())
        db.add(fornecedor)
        db.commit()
        db.refresh(fornecedor)

        return fornecedor

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar fornecedor: {str(e)}")

@router.put("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def update_fornecedor(
    fornecedor_id: int,
    fornecedor_data: schemas.FornecedorUpdate,
    db: Session = Depends(get_db)
):
    """Atualizar fornecedor existente"""
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    try:
        # Verificar se CNPJ já existe em outro fornecedor
        if fornecedor_data.cnpj and fornecedor_data.cnpj != fornecedor.cnpj:
            existing = db.query(models.Fornecedor).filter(
                models.Fornecedor.cnpj == fornecedor_data.cnpj,
                models.Fornecedor.id != fornecedor_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

        # Atualizar campos fornecidos
        update_data = fornecedor_data.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(fornecedor, campo, valor)

        db.commit()
        db.refresh(fornecedor)

        return fornecedor

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar fornecedor: {str(e)}")

@router.delete("/fornecedores/{fornecedor_id}")
def delete_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    """Excluir fornecedor"""
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    try:
        db.delete(fornecedor)
        db.commit()
        return {"message": "Fornecedor excluído com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao excluir fornecedor: {str(e)}")
