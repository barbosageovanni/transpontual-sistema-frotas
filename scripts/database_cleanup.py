#!/usr/bin/env python3
"""
Database Cleanup Script - Transpontual Sistema de Gestão de Frotas
Este script realiza limpeza segura do banco de dados para preparar para dados de produção.
"""

import os
import sys
import datetime
import subprocess
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


class DatabaseCleaner:
    def __init__(self):
        self.settings = get_settings()
        self.db_url = self.settings.DATABASE_URL
        self.backup_dir = Path(__file__).parent.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self):
        """Criar backup do banco antes da limpeza"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_before_cleanup_{timestamp}.sql"

        print(f"[INFO] Criando backup do banco de dados...")
        print(f"[INFO] Arquivo: {backup_file}")

        try:
            # Extrair parâmetros do DATABASE_URL
            if "postgresql" in self.db_url:
                # Parse DATABASE_URL for postgresql
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(self.db_url)

                pg_dump_cmd = [
                    "pg_dump",
                    f"--host={parsed.hostname}",
                    f"--port={parsed.port or 5432}",
                    f"--username={parsed.username}",
                    f"--dbname={parsed.path.lstrip('/')}",
                    "--verbose",
                    "--clean",
                    "--no-owner",
                    "--no-privileges",
                    f"--file={backup_file}"
                ]

                # Set password environment variable
                env = os.environ.copy()
                if parsed.password:
                    env["PGPASSWORD"] = parsed.password

                result = subprocess.run(pg_dump_cmd, env=env, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"[SUCCESS] Backup criado com sucesso: {backup_file}")
                    return backup_file
                else:
                    print(f"[ERROR] Erro ao criar backup: {result.stderr}")
                    return None
            else:
                print("[WARNING] Backup automático disponível apenas para PostgreSQL")
                return None

        except Exception as e:
            print(f"[ERROR] Erro ao criar backup: {e}")
            return None

    def get_table_list(self):
        """Obter lista de tabelas no banco"""
        try:
            with engine.connect() as conn:
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                return tables
        except Exception as e:
            print(f"[ERROR] Erro ao listar tabelas: {e}")
            return []

    def get_table_row_counts(self):
        """Obter contagem de registros por tabela"""
        tables = self.get_table_list()
        counts = {}

        try:
            with SessionLocal() as session:
                for table in tables:
                    try:
                        result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        counts[table] = count
                    except Exception as e:
                        counts[table] = f"Erro: {e}"

        except Exception as e:
            print(f"[ERROR] Erro ao contar registros: {e}")

        return counts

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

    def clean_test_data(self, confirm=False):
        """Limpar dados de teste mantendo estrutura e dados essenciais"""

        if not confirm:
            print("[WARNING] ATENÇÃO: Esta operação irá limpar dados de teste do banco!")
            print("[WARNING] Dados essenciais como usuários admin e configurações serão mantidos.")
            response = input("Deseja continuar? (digite 'CONFIRMAR' para prosseguir): ")
            if response != "CONFIRMAR":
                print("[INFO] Operação cancelada.")
                return False

        print("\n[INFO] Iniciando limpeza de dados de teste...")

        try:
            with SessionLocal() as session:
                # Ordem de limpeza (respeitando foreign keys)
                cleanup_order = [
                    # Dados transacionais primeiro
                    "checklist_respostas",
                    "checklist_itens_resposta",
                    "checklists",

                    # Dados de configuração de checklist
                    "modelos_checklist_itens",
                    "modelos_checklist",
                    "itens_checklist",

                    # Dados de test de veículos e usuários (manter alguns)
                    # "veiculos",  # Comentado - manter alguns veículos
                    # "usuarios",  # Comentado - manter usuários essenciais
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

                            if table == "usuarios":
                                # Manter usuário admin
                                session.execute(text(f"DELETE FROM {table} WHERE papel != 'admin'"))
                            elif table == "veiculos":
                                # Manter apenas 2-3 veículos para teste
                                session.execute(text(f"DELETE FROM {table} WHERE id > 3"))
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
            # Obter todas as sequences
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

        except Exception as e:
            print(f"[WARNING] Erro ao resetar sequences: {e}")

    def verify_cleanup(self):
        """Verificar resultado da limpeza"""
        print("\n[INFO] VERIFICANDO RESULTADO DA LIMPEZA:")
        print("=" * 50)
        self.show_current_data()


def main():
    print("[CLEANUP] DATABASE CLEANUP - TRANSPONTUAL")
    print("=" * 50)

    cleaner = DatabaseCleaner()

    # Mostrar dados atuais
    cleaner.show_current_data()

    # Criar backup
    backup_file = cleaner.create_backup()
    if not backup_file:
        print("[WARNING] Não foi possível criar backup. Deseja continuar mesmo assim?")
        response = input("Digite 'SIM' para continuar sem backup: ")
        if response != "SIM":
            print("[INFO] Operação cancelada.")
            return

    # Executar limpeza
    success = cleaner.clean_test_data()

    if success:
        # Verificar resultado
        cleaner.verify_cleanup()

        print("\n[SUCCESS] LIMPEZA CONCLUÍDA!")
        print("=" * 50)
        print("[INFO] O banco está pronto para dados de produção.")
        print("[INFO] Próximos passos:")
        print("   1. Criar usuários reais")
        print("   2. Cadastrar veículos da frota")
        print("   3. Configurar modelos de checklist")
        print("   4. Testar funcionalidades")

        if backup_file:
            print(f"\n[INFO] Backup disponível em: {backup_file}")


if __name__ == "__main__":
    main()