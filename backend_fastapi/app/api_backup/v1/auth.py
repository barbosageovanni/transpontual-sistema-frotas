# backend_fastapi/app/api/v1/auth.py
"""
Endpoints de autenticação
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import verify_password, create_access_token
from models.user import Usuario
from schemas.auth import LoginRequest, TokenResponse

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login do usuário"""
    user = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    
    if not user or not verify_password(credentials.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    # Criar token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "papel": user.papel
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "papel": user.papel
        }
    }

@router.post("/logout")
def logout():
    """Logout (sem estado no servidor)"""
    return {"message": "Logout realizado com sucesso"}
