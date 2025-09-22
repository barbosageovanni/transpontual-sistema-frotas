#!/usr/bin/env python3
"""
Force Database Cleanup - Limpeza forçada e robusta do banco
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / "backend_fastapi"))
    from app.core.database import SessionLocal
    from sqlalchemy import text
except ImportError as e:
    print(f"[ERROR] Erro ao importar dependências: {e}")
    sys.exit(1)


def force_cleanup():
    print("[FORCE] LIMPEZA FORÇADA DO BANCO DE DADOS")
    print("=" * 50)

    try:
        with SessionLocal() as session:
            # Lista de tabelas na ordem correta para limpeza
            tables_to_clean = [
                "checklist_respostas",
                "checklist_itens",
                "checklists",
                "checklist_modelos",
                "viagens",
                "ctes",
                "defeitos",
                "ordens_servico",
                "transacoes",
                "comprovantes",
                "comprovantes_simples",
                "comprovantes_reais",
                "comprovantes_debug",
                "despesas",
                "conciliacao",
                "regras_classificacao",
                "dashboard_baker"
            ]

            for table in tables_to_clean:
                try:
                    # Verificar se tabela existe
                    exists = session.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table)"
                    ), {"table": table}).scalar()

                    if exists:
                        # Contar registros antes
                        count_before = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()

                        # Deletar todos os registros
                        result = session.execute(text(f"DELETE FROM {table}"))
                        session.commit()  # Commit individual para cada tabela

                        print(f"[CLEAN] {table:<25} {count_before:>5} registros removidos")
                    else:
                        print(f"[SKIP] {table:<25} tabela não existe")

                except Exception as e:
                    print(f"[ERROR] {table:<25} {str(e)}")
                    session.rollback()  # Rollback apenas esta operação
                    continue

            # Resetar sequences
            print("\n[RESET] Resetando sequences...")
            try:
                sequences = session.execute(text(
                    "SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'"
                )).fetchall()

                for (seq_name,) in sequences:
                    try:
                        session.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH 1"))
                        print(f"[RESET] {seq_name}")
                    except Exception as e:
                        print(f"[ERROR] Erro ao resetar {seq_name}: {e}")

                session.commit()

            except Exception as e:
                print(f"[ERROR] Erro ao resetar sequences: {e}")

            print("\n[SUCCESS] Limpeza forçada concluída!")

    except Exception as e:
        print(f"[ERROR] Erro na limpeza forçada: {e}")


def show_final_status():
    print("\n[STATUS] Estado final do banco:")
    print("=" * 50)

    try:
        with SessionLocal() as session:
            # Lista de tabelas principais
            main_tables = [
                "usuarios", "veiculos", "motoristas", "checklists",
                "checklist_modelos", "checklist_itens", "viagens",
                "transacoes", "comprovantes", "dashboard_baker"
            ]

            total = 0
            for table in main_tables:
                try:
                    count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    total += count
                    print(f"[DATA] {table:<20} {count:>6} registros")
                except Exception as e:
                    print(f"[ERROR] {table:<20} Erro: {e}")

            print("=" * 50)
            print(f"[TOTAL] {total} registros restantes")

    except Exception as e:
        print(f"[ERROR] Erro ao verificar status: {e}")


if __name__ == "__main__":
    force_cleanup()
    show_final_status()