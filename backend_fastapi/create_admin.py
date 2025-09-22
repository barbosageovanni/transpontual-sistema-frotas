#!/usr/bin/env python3
"""
Script para criar usuário administrador
"""

from app.database import SessionLocal
from app.models import Usuario
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_admin_user():
    db = SessionLocal()
    
    try:
        # Verificar se já existe admin
        existing_admin = db.query(Usuario).filter(Usuario.email == 'admin@transpontual.com').first()
        
        if not existing_admin:
            admin_user = Usuario(
                nome='Administrador',
                email='admin@transpontual.com',
                senha=pwd_context.hash('admin123'),
                papel='admin',
                ativo=True,
                criado_em=datetime.now()
            )
            db.add(admin_user)
            db.commit()
            print('Usuário administrador criado com sucesso!')
            print('Email: admin@transpontual.com')
            print('Senha: admin123')
            print('IMPORTANTE: Altere a senha após o primeiro login!')
        else:
            print('Usuário administrador já existe')
            
    except Exception as e:
        print(f'Erro ao criar usuário administrador: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_admin_user()