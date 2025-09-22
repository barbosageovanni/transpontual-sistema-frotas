#!/usr/bin/env python3
"""
Script para adicionar coluna numero_os na tabela ordens_servico
"""
from app.core.database import engine
from sqlalchemy import text

def add_numero_os_column():
    """Adiciona a coluna numero_os na tabela ordens_servico"""
    try:
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='ordens_servico'
                AND column_name='numero_os'
            """))

            if result.rowcount == 0:
                # Adicionar a coluna se não existir
                conn.execute(text("""
                    ALTER TABLE ordens_servico
                    ADD COLUMN numero_os VARCHAR(50) UNIQUE
                """))
                conn.commit()
                print("Coluna numero_os adicionada com sucesso!")
            else:
                print("Coluna numero_os ja existe.")

    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    add_numero_os_column()