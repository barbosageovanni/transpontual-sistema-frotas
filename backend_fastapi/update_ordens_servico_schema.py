#!/usr/bin/env python3
"""
Script para atualizar a estrutura da tabela ordens_servico
"""
from app.core.database import engine
from sqlalchemy import text

def update_ordens_servico_schema():
    """Atualiza a estrutura da tabela ordens_servico para corresponder ao modelo"""
    try:
        with engine.connect() as conn:
            print("Atualizando estrutura da tabela ordens_servico...")

            # Lista das colunas que precisamos adicionar
            columns_to_add = [
                "tipo_servico VARCHAR(100) NOT NULL DEFAULT 'Preventiva'",
                "data_abertura TIMESTAMP DEFAULT NOW()",
                "data_prevista TIMESTAMP",
                "data_conclusao TIMESTAMP",
                "oficina VARCHAR(200)",
                "odometro BIGINT",
                "descricao_problema TEXT",
                "descricao_servico TEXT",
                "valor_total VARCHAR(20)",
                "observacoes TEXT",
                "criado_em TIMESTAMP DEFAULT NOW() NOT NULL"
            ]

            # Verificar quais colunas já existem
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='ordens_servico'
            """))

            existing_columns = {row[0] for row in result}
            print(f"Colunas existentes: {sorted(existing_columns)}")

            # Adicionar colunas que não existem
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                if column_name not in existing_columns:
                    print(f"Adicionando coluna: {column_name}")
                    try:
                        conn.execute(text(f"ALTER TABLE ordens_servico ADD COLUMN {column_def}"))
                        print(f"  OK - Coluna {column_name} adicionada")
                    except Exception as e:
                        print(f"  ERRO - Erro ao adicionar {column_name}: {e}")
                else:
                    print(f"  - Coluna {column_name} já existe")

            # Atualizar status default se necessário
            try:
                conn.execute(text("ALTER TABLE ordens_servico ALTER COLUMN status SET DEFAULT 'Aberta'"))
                print("Status default atualizado para 'Aberta'")
            except Exception as e:
                print(f"Aviso: Erro ao atualizar default do status: {e}")

            conn.commit()
            print("\nEstrutura da tabela atualizada com sucesso!")

            # Verificar estrutura final
            print("\nEstrutura final da tabela:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name='ordens_servico'
                ORDER BY ordinal_position
            """))

            for row in result:
                nullable = 'NULL' if row[2] == 'YES' else 'NOT NULL'
                default = f" DEFAULT {row[3]}" if row[3] else ""
                print(f"  {row[0]} - {row[1]} - {nullable}{default}")

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    update_ordens_servico_schema()