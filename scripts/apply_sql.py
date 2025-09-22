# scripts/apply_sql.py
"""
Aplicar DDL e estrutura do banco de dados
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"

def get_database_url():
    """Obter URL do banco de dados"""
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ Variável DATABASE_URL não encontrada no .env")
        sys.exit(1)
    return url

def execute_sql_file(engine, filepath):
    """Executar arquivo SQL"""
    if not filepath.exists():
        print(f"⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with engine.begin() as conn:
            # Dividir por statements (simples, pode melhorar)
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    conn.execute(text(statement))
        
        print(f"✅ Executado: {filepath.name}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar {filepath.name}: {e}")
        return False

def main():
    """Aplicar todos os scripts SQL"""
    print("📊 Aplicando estrutura do banco de dados")
    
    database_url = get_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)
    
    # Ordem dos arquivos SQL
    sql_files = [
        "ddl.sql",      # Estrutura principal
        "seed.sql",     # Dados iniciais
    ]
    
    success = True
    for filename in sql_files:
        filepath = SQL_DIR / filename
        if not execute_sql_file(engine, filepath):
            success = False
    
    if success:
        print("✅ Estrutura do banco aplicada com sucesso!")
    else:
        print("❌ Erro ao aplicar estrutura do banco")
        sys.exit(1)

if __name__ == "__main__":
    main()

