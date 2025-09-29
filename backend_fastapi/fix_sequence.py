#!/usr/bin/env python3
"""
Script para corrigir sequência de ID da tabela users
"""

from app.core.database import SessionLocal
from sqlalchemy import text

def fix_user_sequence():
    db = SessionLocal()

    try:
        # Obter o maior ID atual
        result = db.execute(text("SELECT MAX(id) FROM users"))
        max_id = result.scalar() or 0

        # Ajustar a sequência para o próximo valor
        next_val = max_id + 1
        db.execute(text(f"SELECT setval('users_id_seq', {next_val})"))
        db.commit()

        print(f"[OK] Sequência ajustada para {next_val}")
        print(f"[INFO] Maior ID atual: {max_id}")

    except Exception as e:
        print(f"[ERROR] Erro ao ajustar sequência: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    fix_user_sequence()