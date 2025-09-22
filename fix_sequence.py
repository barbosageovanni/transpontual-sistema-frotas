#!/usr/bin/env python3
"""
Script para corrigir a sequência de IDs na tabela usuarios
"""
import sys
import os

# Adicionar o diretório backend_fastapi ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend_fastapi'))

from sqlalchemy import text
from app.core.database import engine, get_db

def fix_user_sequence():
    """Corrige a sequência de IDs da tabela usuarios"""
    try:
        with engine.connect() as connection:
            # Verificar o maior ID atual na tabela
            result = connection.execute(text("SELECT MAX(id) FROM usuarios"))
            max_id = result.scalar() or 0

            print(f"Maior ID atual na tabela usuarios: {max_id}")

            # Corrigir a sequência para começar do próximo ID
            next_id = max_id + 1
            connection.execute(text(f"SELECT setval('usuarios_id_seq', {next_id})"))
            connection.commit()

            print(f"Sequência corrigida para iniciar em: {next_id}")

            # Verificar se a sequência foi corrigida
            result = connection.execute(text("SELECT nextval('usuarios_id_seq')"))
            next_val = result.scalar()
            print(f"Próximo valor da sequência: {next_val}")

            # Resetar a sequência para o valor correto (decrementar 1 porque usamos nextval)
            connection.execute(text(f"SELECT setval('usuarios_id_seq', {next_val - 1})"))
            connection.commit()

            print("✅ Sequência de IDs corrigida com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao corrigir sequência: {e}")
        return False

    return True

if __name__ == "__main__":
    print("Corrigindo sequência de IDs da tabela usuarios...")
    success = fix_user_sequence()
    sys.exit(0 if success else 1)