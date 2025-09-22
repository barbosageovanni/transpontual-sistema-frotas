#!/usr/bin/env python3
"""
Script para criar as tabelas necessárias no banco de dados
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app import models

def create_tables():
    """Cria todas as tabelas no banco de dados"""
    try:
        print("Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")

        # Verificar se as tabelas foram criadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tabelas encontradas: {tables}")

    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        raise

if __name__ == "__main__":
    create_tables()