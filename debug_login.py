#!/usr/bin/env python3
"""
Debug do sistema de login
"""
import os
from sqlalchemy import create_engine, text
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

engine = create_engine(DATABASE_URL)

def debug_user_login():
    email = "admin@transpontual.com"
    password = "123456"

    with engine.connect() as conn:
        # Buscar usuário
        result = conn.execute(text("""
            SELECT id, email, password_hash, ativo, is_active
            FROM users
            WHERE email = :email
        """), {"email": email})

        user = result.fetchone()

        if user:
            print(f"=== USUARIO ENCONTRADO ===")
            print(f"ID: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"password_hash: {user[2][:50] if user[2] else 'None'}...")
            print(f"ativo: {user[3]}")
            print(f"is_active: {user[4]}")

            # Testar verificação de senha
            if user[2]:  # password_hash
                if check_password_hash(user[2], password):
                    print("✅ password_hash VÁLIDO!")
                else:
                    print("❌ password_hash INVÁLIDO!")

            # Gerar novo hash para teste
            new_hash = generate_password_hash(password)
            print(f"\nNovo hash seria: {new_hash[:50]}...")

        else:
            print("❌ USUÁRIO NÃO ENCONTRADO!")

if __name__ == "__main__":
    debug_user_login()