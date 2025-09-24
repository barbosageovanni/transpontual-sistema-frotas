#!/usr/bin/env python3
"""
Reset admin password
"""
import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

engine = create_engine(DATABASE_URL)

# Nova senha
new_password = "123456"
password_hash = generate_password_hash(new_password)

with engine.connect() as conn:
    conn.execute(text("""
        UPDATE users
        SET password_hash = :password_hash
        WHERE email = 'admin@transpontual.com'
    """), {"password_hash": password_hash})
    conn.commit()

print("CREDENCIAIS ATUALIZADAS:")
print("Email: admin@transpontual.com")
print("Senha: 123456")