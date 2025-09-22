# backend_fastapi/app/api/v1/users.py
"""
Endpoints para usuários
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user, require_role
from models.user import Usuario, Motorista
from schemas.user import UsuarioOut, MotoristaOut

router = APIRouter()

@router.get("/", response_model=List[UsuarioOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("gestor"))
):
    """Listar usuários (apenas gestores)"""
    users = db.query(Usuario).filter(Usuario.ativo == True).all()
    return users

@router.get("/drivers", response_model=List[MotoristaOut])
def list_drivers(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar motoristas"""
    drivers = db.query(Motorista).filter(Motorista.ativo == True).all()
    return drivers

@router.get("/me", response_model=UsuarioOut)
def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obter informações do usuário atual"""
    return current_user
