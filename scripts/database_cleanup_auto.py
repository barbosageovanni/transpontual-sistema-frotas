#!/usr/bin/env python3
"""
Database Cleanup Script - Transpontual Sistema de Gestão de Frotas
Versão automática para execução sem interação.
"""

import os
import sys
import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / "backend_fastapi"))
    from app.core.database import engine, SessionLocal
    from app.core.config import get_settings
    from sqlalchemy import text, inspect
except ImportError as e:
    print(f"[ERROR] Erro ao importar dependências: {e}")
    print("Certifique-se de que o backend_fastapi está configurado corretamente")
    sys.exit(1)


class DatabaseCleanerAuto:
    def __init__(self):
        self.settings = get_settings()
        self.db_url = self.settings.DATABASE_URL
        self.backup_dir = Path(__file__).parent.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def get_table_row_counts(self):
        """Obter contagem de registros por tabela"""
        try:
            with engine.connect() as conn:
                inspector = inspect(engine)
                tables = inspector.get_table_names()

                counts = {}
                with SessionLocal() as session:
                    for table in tables:
                        try:
                            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.scalar()
                            counts[table] = count
                        except Exception as e:
                            counts[table] = f"Erro: {e}"

                return counts
        except Exception as e:
            print(f"[ERROR] Erro ao contar registros: {e}")
            return {}

    def show_current_data(self):
        """Mostrar dados atuais do banco"""
        print("\n[INFO] DADOS ATUAIS DO BANCO:")
        print("=" * 50)

        counts = self.get_table_row_counts()
        total_records = 0

        for table, count in counts.items():
            if isinstance(count, int):
                total_records += count
                print(f"[DATA] {table:<25} {count:>10} registros")
            else:
                print(f"[DATA] {table:<25} {count}")

        print("=" * 50)
        print(f"[INFO] TOTAL DE REGISTROS: {total_records}")
        print()

    def clean_test_data_auto(self):
        """Limpar dados de teste automaticamente"""
        print("\n[INFO] Iniciando limpeza automática de dados de teste...")

        try:
            with SessionLocal() as session:
                # Ordem de limpeza (respeitando foreign keys)
                cleanup_order = [
                    # Dados transacionais primeiro
                    "checklist_respostas",
                    "checklists",
                    "checklist_itens",
                    "checklist_modelos",

                    # Dados relacionados a viagens
                    "viagens",
                    "ctes",
                    "defeitos",
                    "ordens_servico",

                    # Dados financeiros
                    "transacoes",
                    "comprovantes",
                    "comprovantes_simples",
                    "comprovantes_reais",
                    "comprovantes_debug",
                    "despesas",
                    "conciliacao",
                    "regras_classificacao",

                    # Dados de usuários (manter apenas admin)
                    "users",  # Manter apenas admin se existir

                    # Dados de dashboard (limpar dados antigos)
                    "dashboard_baker",
                ]

                for table in cleanup_order:
                    try:
                        # Verificar se a tabela existe
                        result = session.execute(text(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table)"
                        ), {"table": table})

                        if result.scalar():
                            # Contar registros antes
                            count_before = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()

                            if table == "users":
                                # Manter usuário admin se existir
                                session.execute(text(f"DELETE FROM {table} WHERE role != 'admin' OR role IS NULL"))
                            elif table == "usuarios":
                                # Manter usuário admin
                                session.execute(text(f"DELETE FROM {table} WHERE papel != 'admin'"))
                            elif table == "veiculos":
                                # Manter apenas 2-3 veículos para teste
                                session.execute(text(f"DELETE FROM {table} WHERE id > 3"))
                            elif table == "motoristas":
                                # Manter apenas alguns motoristas
                                session.execute(text(f"DELETE FROM {table} WHERE id > 5"))
                            elif table == "fornecedores":
                                # Manter alguns fornecedores essenciais
                                session.execute(text(f"DELETE FROM {table} WHERE id > 10"))
                            elif table == "centros_custo":
                                # Manter centros de custo básicos
                                session.execute(text(f"DELETE FROM {table} WHERE id > 10"))
                            else:
                                # Limpar completamente
                                session.execute(text(f"DELETE FROM {table}"))

                            # Contar registros depois
                            count_after = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                            deleted = count_before - count_after

                            print(f"[CLEAN] {table:<25} {deleted:>5} registros removidos ({count_after} mantidos)")

                    except Exception as e:
                        print(f"[WARNING] {table:<25} Erro: {e}")

                # Commit das mudanças
                session.commit()
                print("\n[SUCCESS] Limpeza concluída com sucesso!")

                # Reset das sequences para IDs
                self.reset_sequences(session)

                return True

        except Exception as e:
            print(f"[ERROR] Erro durante a limpeza: {e}")
            return False

    def reset_sequences(self, session):
        """Reset das sequences de auto-increment"""
        print("\n[INFO] Resetando sequences de ID...")

        try:
            # Para PostgreSQL
            if "postgresql" in self.db_url.lower():
                sequences_query = text("""
                    SELECT schemaname, sequencename
                    FROM pg_sequences
                    WHERE schemaname = 'public'
                """)

                sequences = session.execute(sequences_query).fetchall()

                for schema, seq_name in sequences:
                    try:
                        # Reset da sequence
                        session.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH 1"))
                        print(f"[INFO] Sequence {seq_name} resetada")
                    except Exception as e:
                        print(f"[WARNING] Erro ao resetar {seq_name}: {e}")

                session.commit()
                print("[SUCCESS] Sequences resetadas com sucesso!")
            else:
                print("[INFO] Reset de sequences disponível apenas para PostgreSQL")

        except Exception as e:
            print(f"[WARNING] Erro ao resetar sequences: {e}")

    def verify_cleanup(self):
        """Verificar resultado da limpeza"""
        print("\n[INFO] VERIFICANDO RESULTADO DA LIMPEZA:")
        print("=" * 50)
        self.show_current_data()


def main():
    print("[CLEANUP] DATABASE CLEANUP AUTOMÁTICO - TRANSPONTUAL")
    print("=" * 50)

    cleaner = DatabaseCleanerAuto()

    # Mostrar dados atuais
    print("[INFO] Dados antes da limpeza:")
    cleaner.show_current_data()

    # Executar limpeza automaticamente
    print("[INFO] Executando limpeza automática (sem backup)...")
    success = cleaner.clean_test_data_auto()

    if success:
        # Verificar resultado
        cleaner.verify_cleanup()

        print("\n[SUCCESS] LIMPEZA AUTOMÁTICA CONCLUÍDA!")
        print("=" * 50)
        print("[INFO] O banco está pronto para dados de produção.")
        print("[INFO] Próximos passos:")
        print("   1. Executar setup_production_data.py para criar dados iniciais")
        print("   2. Executar deploy_readiness_check.py para verificar conformidade")
        print("   3. Cadastrar usuários reais")
        print("   4. Cadastrar veículos da frota")
        print("   5. Configurar modelos de checklist")
        print("   6. Testar funcionalidades")

        return True
    else:
        print("\n[ERROR] Falha na limpeza automática!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)