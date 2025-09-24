#!/usr/bin/env python3
"""
Verificar estrutura da tabela users
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Ver estrutura da tabela
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """))

    print("=== ESTRUTURA DA TABELA USERS ===")
    for row in result:
        print(f"{row[0]}: {row[1]}")

    # Ver usuários existentes
    result = conn.execute(text("SELECT id, email FROM users LIMIT 5"))

    print("\n=== USUÁRIOS EXISTENTES ===")
    for row in result:
        print(f"ID: {row[0]}, Email: {row[1]}")