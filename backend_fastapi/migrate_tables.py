#!/usr/bin/env python3
"""
Script para adicionar colunas ausentes nas tabelas existentes
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db

def migrate_tables():
    """Adiciona colunas ausentes nas tabelas existentes"""
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)

        print("Adicionando colunas ausentes nas tabelas...")

        # Add missing columns to various tables
        migrations = [
            # Veiculos table
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS renavam VARCHAR(11)",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS ano INTEGER",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS marca VARCHAR(100)",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS tipo VARCHAR(50)",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS modelo VARCHAR(100)",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS km_atual BIGINT DEFAULT 0",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT true",
            "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",

            # Checklist_itens table
            "ALTER TABLE checklist_itens ADD COLUMN IF NOT EXISTS categoria VARCHAR(50)",
            "ALTER TABLE checklist_itens ADD COLUMN IF NOT EXISTS tipo_resposta VARCHAR(20) DEFAULT 'multipla_escolha'",
            "ALTER TABLE checklist_itens ADD COLUMN IF NOT EXISTS severidade VARCHAR(20) DEFAULT 'baixa'",
            "ALTER TABLE checklist_itens ADD COLUMN IF NOT EXISTS exige_foto BOOLEAN DEFAULT false",
            "ALTER TABLE checklist_itens ADD COLUMN IF NOT EXISTS bloqueia_viagem BOOLEAN DEFAULT false",

            # Motoristas table
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS nome VARCHAR(200)",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS cnh VARCHAR(11)",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS categoria VARCHAR(5)",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS validade_cnh TIMESTAMP",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS usuario_id INTEGER",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT true",
            "ALTER TABLE motoristas ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()"
        ]

        for migration in migrations:
            try:
                db.execute(text(migration))
                print(f"Executado: {migration}")
            except Exception as e:
                print(f"Erro na migração '{migration}': {e}")

        # Commit changes
        db.commit()
        print("Migrações concluídas com sucesso!")

        # Test query to verify columns
        result = db.execute(text("SELECT COUNT(*) FROM veiculos")).fetchone()
        print(f"Contagem de veículos: {result[0] if result else 0}")

    except Exception as e:
        print(f"Erro durante migração: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    migrate_tables()