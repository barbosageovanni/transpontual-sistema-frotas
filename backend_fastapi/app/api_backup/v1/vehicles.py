# backend_fastapi/app/api/v1/vehicles.py
"""
Endpoints para veículos
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.vehicle import Veiculo
from models.user import Usuario
from schemas.vehicle import VeiculoOut

router = APIRouter()

@router.get("/", response_model=List[VeiculoOut])
def list_vehicles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar veículos ativos"""
    vehicles = db.query(Veiculo).filter(Veiculo.ativo == True).order_by(Veiculo.placa).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=VeiculoOut)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obter veículo por ID"""
    vehicle = db.query(Veiculo).filter(Veiculo.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Veículo não encontrado")
    return vehicle