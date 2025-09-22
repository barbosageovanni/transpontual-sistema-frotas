# fix_database.py - Script de correção rápida
"""
Correção rápida para estrutura do banco Transpontual
Execute: python fix_database.py
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL não encontrada no .env")
        return None
    return url

def fix_database():
    print("🔧 Corrigindo estrutura do banco...")
    
    url = get_db_url()
    if not url:
        return False
    
    engine = create_engine(url, pool_pre_ping=True)
    
    # SQL corrigido e simplificado
    sql_commands = [
        # Limpar estruturas problemáticas
        "DROP TABLE IF EXISTS checklist_respostas CASCADE;",
        "DROP TABLE IF EXISTS checklists CASCADE;", 
        "DROP TABLE IF EXISTS checklist_itens CASCADE;",
        "DROP TABLE IF EXISTS checklist_modelos CASCADE;",
        "DROP TABLE IF EXISTS defeitos CASCADE;",
        "DROP TABLE IF EXISTS ordens_servico CASCADE;",
        
        # Recriar estrutura correta
        """
        CREATE TABLE checklist_modelos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra')),
            versao INT DEFAULT 1,
            ativo BOOLEAN DEFAULT TRUE,
            criado_em TIMESTAMP DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE checklist_itens (
            id SERIAL PRIMARY KEY,
            modelo_id INT REFERENCES checklist_modelos(id) ON DELETE CASCADE,
            ordem INT NOT NULL,
            descricao TEXT NOT NULL,
            tipo_resposta TEXT DEFAULT 'ok',
            severidade TEXT DEFAULT 'media',
            exige_foto BOOLEAN DEFAULT FALSE,
            bloqueia_viagem BOOLEAN DEFAULT FALSE,
            opcoes JSONB DEFAULT '[]'::jsonb,
            UNIQUE(modelo_id, ordem)
        );
        """,
        
        """
        CREATE TABLE checklists (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE,
            veiculo_id INT REFERENCES veiculos(id),
            motorista_id INT REFERENCES motoristas(id), 
            modelo_id INT REFERENCES checklist_modelos(id),
            tipo TEXT DEFAULT 'pre',
            status TEXT DEFAULT 'pendente',
            dt_inicio TIMESTAMP DEFAULT NOW(),
            dt_fim TIMESTAMP,
            odometro_ini BIGINT,
            odometro_fim BIGINT
        );
        """,
        
        """
        CREATE TABLE checklist_respostas (
            id SERIAL PRIMARY KEY,
            checklist_id INT REFERENCES checklists(id) ON DELETE CASCADE,
            item_id INT REFERENCES checklist_itens(id),
            valor TEXT NOT NULL,
            observacao TEXT,
            dt TIMESTAMP DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE defeitos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE,
            veiculo_id INT REFERENCES veiculos(id),
            descricao TEXT NOT NULL,
            severidade TEXT DEFAULT 'media',
            status TEXT DEFAULT 'aberto',
            criado_em TIMESTAMP DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE ordens_servico (
            id SERIAL PRIMARY KEY,
            numero TEXT UNIQUE,
            veiculo_id INT REFERENCES veiculos(id),
            defeito_id INT REFERENCES defeitos(id),
            status TEXT DEFAULT 'aberta',
            abertura_dt TIMESTAMP DEFAULT NOW()
        );
        """,
        
        # Dados básicos
        """
        INSERT INTO checklist_modelos (nome, tipo, ativo) VALUES 
        ('Caminhão Padrão', 'pre', true);
        """,
        
        """
        INSERT INTO checklist_itens (modelo_id, ordem, descricao, severidade, bloqueia_viagem) 
        SELECT id, ordem, descricao, severidade, bloqueia FROM checklist_modelos m
        CROSS JOIN (VALUES
          (1, 'Freios', 'alta', true),
          (2, 'Pneus', 'alta', true),
          (3, 'Iluminação', 'media', false),
          (4, 'Direção', 'alta', true),
          (5, 'Documentação', 'media', true)
        ) AS itens(ordem, descricao, severidade, bloqueia)
        WHERE m.nome = 'Caminhão Padrão';
        """
    ]
    
    try:
        with engine.begin() as conn:
            for i, cmd in enumerate(sql_commands):
                print(f"  Executando comando {i+1}/{len(sql_commands)}...")
                conn.execute(text(cmd))
        
        print("✅ Estrutura corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    if fix_database():
        print("\n🎉 Sistema pronto!")
        print("Próximos passos:")
        print("1. make dev")
        print("2. Acesse http://localhost:8050")
        print("3. Login: admin@transpontual.com / admin123")
    else:
        print("❌ Falha na correção")
        sys.exit(1)