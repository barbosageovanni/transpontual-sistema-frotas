#!/usr/bin/env python3
"""
Aplicar migração para adicionar campos de manutenção
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_database_url():
    """Obter URL do banco de dados"""
    url = os.getenv("DATABASE_URL")
    if not url:
        print("[ERRO] Variável DATABASE_URL não encontrada no .env")
        print("[INFO] Configure DATABASE_URL no arquivo .env")
        print("   Exemplo: DATABASE_URL=postgresql://user:password@localhost:5432/database")
        sys.exit(1)
    return url

def apply_migration():
    """Aplicar migração de manutenção"""
    print("[MIGRACAO] Aplicando migração: campos de manutenção para veículos")

    database_url = get_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)

    migration_sql = """
    -- Verificar se as colunas já existem
    DO $$
    BEGIN
        -- Adicionar em_manutencao se não existir
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'veiculos' AND column_name = 'em_manutencao'
        ) THEN
            ALTER TABLE veiculos ADD COLUMN em_manutencao BOOLEAN DEFAULT FALSE NOT NULL;
            RAISE NOTICE 'Coluna em_manutencao adicionada';
        ELSE
            RAISE NOTICE 'Coluna em_manutencao já existe';
        END IF;

        -- Adicionar observacoes_manutencao se não existir
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'veiculos' AND column_name = 'observacoes_manutencao'
        ) THEN
            ALTER TABLE veiculos ADD COLUMN observacoes_manutencao TEXT;
            RAISE NOTICE 'Coluna observacoes_manutencao adicionada';
        ELSE
            RAISE NOTICE 'Coluna observacoes_manutencao já existe';
        END IF;
    END $$;

    -- Atualizar registros existentes
    UPDATE veiculos SET em_manutencao = FALSE WHERE em_manutencao IS NULL;
    """

    try:
        with engine.begin() as conn:
            conn.execute(text(migration_sql))

        print("[OK] Migração aplicada com sucesso!")
        print("[INFO] Campos adicionados:")
        print("   - em_manutencao (BOOLEAN)")
        print("   - observacoes_manutencao (TEXT)")

    except Exception as e:
        print(f"[ERRO] Erro ao aplicar migração: {e}")
        sys.exit(1)

def verify_migration():
    """Verificar se a migração foi aplicada corretamente"""
    print("\n[VERIFICA] Verificando migração...")

    database_url = get_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)

    verify_sql = """
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = 'veiculos'
    AND column_name IN ('em_manutencao', 'observacoes_manutencao')
    ORDER BY column_name;
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(verify_sql))
            columns = result.fetchall()

            if len(columns) == 2:
                print("[OK] Verificação bem-sucedida!")
                print("[INFO] Colunas encontradas:")
                for col in columns:
                    print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print(f"[AVISO] Esperava 2 colunas, encontradas: {len(columns)}")

    except Exception as e:
        print(f"[ERRO] Erro na verificação: {e}")

if __name__ == "__main__":
    apply_migration()
    verify_migration()