# backend_fastapi/app/core/deps.py
"""
Dependências do FastAPI
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .security import get_current_user
from ..models.user import Usuario

def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Obter usuário ativo atual"""
    if not current_user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user

def get_current_superuser(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Obter usuário administrador"""
    if current_user.papel != "gestor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui privilégios suficientes"
        )
    return current_user
