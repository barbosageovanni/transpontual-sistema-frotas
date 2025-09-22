#!/usr/bin/env python3
"""
Script para criar usuário de teste rapidamente
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

def create_test_user():
    """Criar usuário de teste"""
    db = SessionLocal()

    try:
        print("Criando usuário de teste...")

        # Verificar se já existe
        existing = db.execute(text("SELECT id FROM usuarios WHERE email = 'admin@transpontual.com'")).fetchone()

        if existing:
            print("Usuário admin@transpontual.com já existe!")
            return

        # Hash simples para teste (em produção usar bcrypt)
        senha_hash = "admin123"  # Senha em texto plano para teste

        # Inserir usuário
        db.execute(text("""
            INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, criado_em, atualizado_em)
            VALUES (:nome, :email, :senha_hash, :papel, true, NOW(), NOW())
        """), {
            "nome": "Admin Sistema",
            "email": "admin@transpontual.com",
            "senha_hash": senha_hash,
            "papel": "gestor"
        })

        db.commit()
        print("✅ Usuário criado com sucesso!")
        print("Email: admin@transpontual.com")
        print("Senha: admin123")

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()