from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import Veiculo
from ..schemas import VeiculoIn, VeiculoOut

router = APIRouter()

@router.get("/", response_model=List[VeiculoOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Veiculo).order_by(Veiculo.placa).all()

@router.post("/", response_model=VeiculoOut, status_code=201)
def create_vehicle(body: VeiculoIn, db: Session = Depends(get_db)):
    v = Veiculo(**body.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v
