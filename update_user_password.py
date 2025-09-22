#!/usr/bin/env python3
"""
Script para atualizar senha do usuário de teste
"""

import os
import sys
from datetime import datetime

# Adicionar o backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend_fastapi'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar conexão com o banco
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_user_password():
    """Atualizar senha do usuário de teste"""
    db = SessionLocal()

    try:
        print("Atualizando senha do usuário admin@transpontual.com...")

        # Atualizar senha
        result = db.execute(text("""
            UPDATE usuarios
            SET senha_hash = :senha_hash
            WHERE email = :email
        """), {
            "senha_hash": "admin123",
            "email": "admin@transpontual.com"
        })

        db.commit()

        if result.rowcount > 0:
            print("✅ Senha atualizada com sucesso!")
            print("Email: admin@transpontual.com")
            print("Senha: admin123")
        else:
            print("❌ Usuário não encontrado!")

    except Exception as e:
        print(f"❌ Erro ao atualizar senha: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_user_password()