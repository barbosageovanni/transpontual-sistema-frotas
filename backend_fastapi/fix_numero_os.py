#!/usr/bin/env python3
"""
Script para corrigir a tabela ordens_servico adicionando coluna numero_os
"""
from app.core.database import engine
from sqlalchemy import text

def fix_numero_os_column():
    """Corrige a coluna numero_os na tabela ordens_servico"""
    try:
        with engine.connect() as conn:
            # Primeiro, verificar se a tabela existe
            print("Verificando se a tabela ordens_servico existe...")
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'ordens_servico'
            """))

            if result.rowcount == 0:
                print("Tabela ordens_servico nao existe. Criando tabela...")
                conn.execute(text("""
                    CREATE TABLE ordens_servico (
                        id SERIAL PRIMARY KEY,
                        numero_os VARCHAR(50) UNIQUE,
                        veiculo_id INTEGER REFERENCES veiculos(id),
                        tipo_servico VARCHAR(100) NOT NULL,
                        status VARCHAR(30) DEFAULT 'Aberta' NOT NULL,
                        data_abertura TIMESTAMP DEFAULT NOW() NOT NULL,
                        data_prevista TIMESTAMP,
                        data_conclusao TIMESTAMP,
                        oficina VARCHAR(200),
                        odometro BIGINT,
                        descricao_problema TEXT,
                        descricao_servico TEXT,
                        valor_total VARCHAR(20),
                        observacoes TEXT,
                        criado_em TIMESTAMP DEFAULT NOW() NOT NULL
                    )
                """))
                print("Tabela ordens_servico criada com sucesso!")
            else:
                print("Tabela ordens_servico existe. Verificando coluna numero_os...")
                # Verificar se a coluna numero_os existe
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='ordens_servico'
                    AND column_name='numero_os'
                """))

                if result.rowcount == 0:
                    print("Adicionando coluna numero_os...")
                    conn.execute(text("""
                        ALTER TABLE ordens_servico
                        ADD COLUMN numero_os VARCHAR(50) UNIQUE
                    """))
                    print("Coluna numero_os adicionada!")
                else:
                    print("Coluna numero_os ja existe.")

            conn.commit()
            print("Operacao concluida com sucesso!")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    fix_numero_os_column()