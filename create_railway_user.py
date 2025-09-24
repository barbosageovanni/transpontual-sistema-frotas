#!/usr/bin/env python3
"""
Script para criar usuário específico no Railway
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_railway_user():
    """Criar usuário específico para Railway"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

        engine = create_engine(DATABASE_URL)

        # Credenciais do novo usuário
        email = "teste@transpontual.com"
        password = "123456"
        nome = "Usuario Teste Railway"

        # Hash da senha
        password_hash = generate_password_hash(password)

        with engine.connect() as conn:
            # Verificar se usuário já existe
            result = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
            if result.fetchone():
                print(f"Usuario {email} ja existe!")
                # Atualizar senha
                conn.execute(text("""
                    UPDATE users
                    SET password_hash = :password_hash, updated_at = NOW()
                    WHERE email = :email
                """), {"password_hash": password_hash, "email": email})
                conn.commit()
                print(f"Senha do usuario {email} atualizada!")
            else:
                # Criar novo usuário
                conn.execute(text("""
                    INSERT INTO users (nome, email, password_hash, ativo, created_at, updated_at)
                    VALUES (:nome, :email, :password_hash, true, NOW(), NOW())
                """), {
                    "nome": nome,
                    "email": email,
                    "password_hash": password_hash
                })
                conn.commit()
                print(f"Usuario {email} criado com sucesso!")

        print(f"\n=== CREDENCIAIS PARA LOGIN ===")
        print(f"Email: {email}")
        print(f"Senha: {password}")
        print("=" * 35)

    except Exception as e:
        print(f"Erro: {e}")
        return False

    return True

if __name__ == "__main__":
    create_railway_user()