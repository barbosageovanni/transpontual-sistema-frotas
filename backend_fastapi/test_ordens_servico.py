#!/usr/bin/env python3
"""
Script para testar o acesso à tabela ordens_servico
"""
from app.core.database import engine
from sqlalchemy import text

def test_ordens_servico_table():
    """Testa a tabela ordens_servico"""
    try:
        with engine.connect() as conn:
            print("Testando acesso à tabela ordens_servico...")

            # Contar registros
            result = conn.execute(text("SELECT COUNT(*) FROM ordens_servico"))
            count = result.fetchone()[0]
            print(f"Total de registros na tabela: {count}")

            # Verificar estrutura da tabela
            print("\nColunas da tabela ordens_servico:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name='ordens_servico'
                ORDER BY ordinal_position
            """))

            for row in result:
                print(f"  {row[0]} - {row[1]} - {'NULL' if row[2] == 'YES' else 'NOT NULL'}")

            # Tentar inserir um registro de teste
            print("\nTentando inserir registro de teste...")
            test_numero = "TEST20250918001"
            conn.execute(text("""
                INSERT INTO ordens_servico (numero_os, veiculo_id, tipo_servico, status)
                VALUES (:numero_os, 1, 'Teste', 'Aberta')
            """), {"numero_os": test_numero})
            print("Registro inserido com sucesso!")

            # Remover registro de teste
            conn.execute(text("DELETE FROM ordens_servico WHERE numero_os = :numero_os"),
                        {"numero_os": test_numero})
            print("Registro de teste removido.")

            conn.commit()
            print("Tabela ordens_servico funciona corretamente!")

    except Exception as e:
        print(f"Erro ao testar tabela: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_ordens_servico_table()