#!/usr/bin/env python3
"""
Deploy Readiness Check - Transpontual Sistema de Gestão de Frotas
Verifica conformidades e boas práticas para deploy em produção.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))


class DeployReadinessChecker:
    def __init__(self):
        self.root_path = Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        self.passed = []

    def check_security(self) -> Dict:
        """Verificar configurações de segurança"""
        print("[SECURITY] VERIFICANDO SEGURANÇA...")

        security_issues = []
        security_passed = []

        # 1. Verificar arquivos de ambiente
        env_files = [
            self.root_path / ".env",
            self.root_path / "backend_fastapi" / ".env",
            self.root_path / "flask_dashboard" / ".env"
        ]

        for env_file in env_files:
            if env_file.exists():
                content = env_file.read_text()

                # Verificar se há senhas padrão
                if "password123" in content.lower() or "admin123" in content.lower():
                    security_issues.append(f"Senha padrão encontrada em {env_file}")

                # Verificar se DEBUG está desabilitado
                if "DEBUG=True" in content or "FLASK_DEBUG=True" in content:
                    security_issues.append(f"DEBUG habilitado em {env_file}")
                else:
                    security_passed.append(f"DEBUG desabilitado em {env_file}")

                # Verificar se SECRET_KEY é forte
                if "SECRET_KEY=" in content:
                    for line in content.split('\n'):
                        if line.startswith('SECRET_KEY='):
                            secret = line.split('=')[1].strip()
                            if len(secret) < 32:
                                security_issues.append(f"SECRET_KEY muito curta em {env_file}")
                            else:
                                security_passed.append(f"SECRET_KEY adequada em {env_file}")

        # 2. Verificar se .env está no .gitignore
        gitignore_path = self.root_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if ".env" in gitignore_content:
                security_passed.append(".env está no .gitignore")
            else:
                security_issues.append(".env não está no .gitignore")

        # 3. Verificar permissões de arquivos sensíveis
        for env_file in env_files:
            if env_file.exists():
                # No Windows, verificar se o arquivo não é público
                try:
                    stat = env_file.stat()
                    security_passed.append(f"Permissões verificadas para {env_file}")
                except Exception as e:
                    security_issues.append(f"Erro ao verificar permissões de {env_file}: {e}")

        return {
            "issues": security_issues,
            "passed": security_passed
        }

    def check_database(self) -> Dict:
        """Verificar configurações do banco de dados"""
        print("[DATABASE] VERIFICANDO BANCO DE DADOS...")

        db_issues = []
        db_passed = []

        try:
            from backend_fastapi.app.core.database import test_connection, get_settings

            # Testar conexão
            if test_connection():
                db_passed.append("Conexão com banco de dados OK")
            else:
                db_issues.append("Falha na conexão com banco de dados")

            # Verificar configurações
            settings = get_settings()

            # Verificar se não está usando SQLite em produção
            if "sqlite" in settings.DATABASE_URL.lower():
                db_issues.append("SQLite não é recomendado para produção")
            else:
                db_passed.append("Banco de dados apropriado para produção")

            # Verificar SSL/TLS
            if "sslmode=require" in settings.DATABASE_URL or "ssl=true" in settings.DATABASE_URL:
                db_passed.append("SSL habilitado para banco de dados")
            else:
                db_issues.append("SSL não configurado para banco de dados")

        except Exception as e:
            db_issues.append(f"Erro ao verificar configurações do banco: {e}")

        return {
            "issues": db_issues,
            "passed": db_passed
        }

    def check_dependencies(self) -> Dict:
        """Verificar dependências e requirements"""
        print("[DEPENDENCIES] VERIFICANDO DEPENDÊNCIAS...")

        dep_issues = []
        dep_passed = []

        # Verificar requirements.txt
        requirements_files = [
            self.root_path / "requirements.txt",
            self.root_path / "backend_fastapi" / "requirements.txt",
            self.root_path / "flask_dashboard" / "requirements.txt"
        ]

        for req_file in requirements_files:
            if req_file.exists():
                dep_passed.append(f"Arquivo {req_file} encontrado")

                # Verificar se há versões fixas
                content = req_file.read_text()
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]

                unfixed_deps = []
                for line in lines:
                    if '==' not in line and '>=' not in line:
                        unfixed_deps.append(line)

                if unfixed_deps:
                    dep_issues.append(f"Dependências sem versão fixa em {req_file}: {unfixed_deps}")
                else:
                    dep_passed.append(f"Todas as dependências têm versões fixas em {req_file}")

        # Verificar vulnerabilidades conhecidas (se safety estiver disponível)
        try:
            result = subprocess.run(['safety', 'check'], capture_output=True, text=True)
            if result.returncode == 0:
                dep_passed.append("Nenhuma vulnerabilidade conhecida encontrada")
            else:
                dep_issues.append(f"Vulnerabilidades encontradas: {result.stdout}")
        except FileNotFoundError:
            dep_issues.append("Ferramenta 'safety' não instalada para verificar vulnerabilidades")

        return {
            "issues": dep_issues,
            "passed": dep_passed
        }

    def check_configuration(self) -> Dict:
        """Verificar configurações gerais"""
        print("[CONFIG] VERIFICANDO CONFIGURAÇÕES...")

        config_issues = []
        config_passed = []

        # Verificar estrutura de diretórios
        expected_dirs = [
            "backend_fastapi",
            "flask_dashboard",
            "sql",
            "scripts"
        ]

        for dir_name in expected_dirs:
            dir_path = self.root_path / dir_name
            if dir_path.exists():
                config_passed.append(f"Diretório {dir_name} encontrado")
            else:
                config_issues.append(f"Diretório {dir_name} não encontrado")

        # Verificar arquivos essenciais
        essential_files = [
            "README.md",
            ".gitignore",
            "sql/improved_ddl.sql"
        ]

        for file_name in essential_files:
            file_path = self.root_path / file_name
            if file_path.exists():
                config_passed.append(f"Arquivo {file_name} encontrado")
            else:
                config_issues.append(f"Arquivo {file_name} não encontrado")

        return {
            "issues": config_issues,
            "passed": config_passed
        }

    def check_logging(self) -> Dict:
        """Verificar configuração de logging"""
        print("[LOGGING] VERIFICANDO LOGGING...")

        log_issues = []
        log_passed = []

        # Verificar se há configuração de logging
        log_configs = [
            self.root_path / "backend_fastapi" / "app" / "core" / "logging.py",
            self.root_path / "flask_dashboard" / "app" / "logging.py"
        ]

        for log_config in log_configs:
            if log_config.exists():
                log_passed.append(f"Configuração de logging encontrada: {log_config}")
            else:
                log_issues.append(f"Configuração de logging não encontrada: {log_config}")

        # Verificar diretório de logs
        log_dir = self.root_path / "logs"
        if log_dir.exists():
            log_passed.append("Diretório de logs existe")
        else:
            log_issues.append("Diretório de logs não existe")

        return {
            "issues": log_issues,
            "passed": log_passed
        }

    def check_docker(self) -> Dict:
        """Verificar configuração Docker"""
        print("[DOCKER] VERIFICANDO DOCKER...")

        docker_issues = []
        docker_passed = []

        # Verificar Dockerfile
        dockerfiles = [
            self.root_path / "Dockerfile",
            self.root_path / "backend_fastapi" / "Dockerfile",
            self.root_path / "flask_dashboard" / "Dockerfile"
        ]

        dockerfile_found = False
        for dockerfile in dockerfiles:
            if dockerfile.exists():
                dockerfile_found = True
                docker_passed.append(f"Dockerfile encontrado: {dockerfile}")

                # Verificar boas práticas no Dockerfile
                content = dockerfile.read_text()
                if "USER" in content:
                    docker_passed.append(f"Usuário não-root configurado em {dockerfile}")
                else:
                    docker_issues.append(f"Usuário não-root não configurado em {dockerfile}")

        if not dockerfile_found:
            docker_issues.append("Nenhum Dockerfile encontrado")

        # Verificar docker-compose.yml
        compose_files = [
            self.root_path / "docker-compose.yml",
            self.root_path / "docker-compose.yaml"
        ]

        compose_found = False
        for compose_file in compose_files:
            if compose_file.exists():
                compose_found = True
                docker_passed.append(f"Docker Compose encontrado: {compose_file}")

        if not compose_found:
            docker_issues.append("Docker Compose não encontrado")

        return {
            "issues": docker_issues,
            "passed": docker_passed
        }

    def run_all_checks(self) -> Dict:
        """Executar todas as verificações"""
        print("[CHECK] VERIFICAÇÃO DE CONFORMIDADE PARA DEPLOY")
        print("=" * 60)

        results = {
            "security": self.check_security(),
            "database": self.check_database(),
            "dependencies": self.check_dependencies(),
            "configuration": self.check_configuration(),
            "logging": self.check_logging(),
            "docker": self.check_docker()
        }

        return results

    def generate_report(self, results: Dict):
        """Gerar relatório final"""
        print("\n" + "=" * 60)
        print("[REPORT] RELATÓRIO FINAL DE CONFORMIDADE")
        print("=" * 60)

        total_issues = 0
        total_passed = 0

        for category, result in results.items():
            issues = result.get("issues", [])
            passed = result.get("passed", [])

            total_issues += len(issues)
            total_passed += len(passed)

            print(f"\n[{category.upper()}]:")

            if passed:
                for item in passed:
                    print(f"  [OK] {item}")

            if issues:
                for item in issues:
                    print(f"  [FAIL] {item}")

        print("\n" + "=" * 60)
        print(f"[SUMMARY] RESUMO:")
        print(f"  [PASSED] Verificações aprovadas: {total_passed}")
        print(f"  [ISSUES] Problemas encontrados: {total_issues}")

        if total_issues == 0:
            print("\n[SUCCESS] SISTEMA PRONTO PARA DEPLOY!")
            print("   Todas as verificações de conformidade passaram.")
        elif total_issues <= 3:
            print("\n[WARNING] SISTEMA QUASE PRONTO PARA DEPLOY")
            print("   Corrija os problemas menores antes do deploy.")
        else:
            print("\n[ERROR] SISTEMA NÃO ESTÁ PRONTO PARA DEPLOY")
            print("   Corrija os problemas críticos antes de prosseguir.")

        return total_issues == 0

    def save_report(self, results: Dict):
        """Salvar relatório em arquivo JSON"""
        import datetime
        report_file = self.root_path / "scripts" / "deploy_readiness_report.json"

        report_data = {
            "timestamp": str(datetime.datetime.now()),
            "results": results,
            "summary": {
                "total_issues": sum(len(r.get("issues", [])) for r in results.values()),
                "total_passed": sum(len(r.get("passed", [])) for r in results.values())
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n[INFO] Relatório salvo em: {report_file}")


def main():
    import datetime

    checker = DeployReadinessChecker()
    results = checker.run_all_checks()
    ready = checker.generate_report(results)
    checker.save_report(results)

    if ready:
        print("\n[NEXT] PRÓXIMOS PASSOS PARA DEPLOY:")
        print("  1. Execute o database_cleanup.py")
        print("  2. Configure variáveis de ambiente de produção")
        print("  3. Execute testes finais")
        print("  4. Deploy!")
    else:
        print("\n[ACTION] AÇÕES NECESSÁRIAS:")
        print("  1. Corrija os problemas listados acima")
        print("  2. Execute novamente esta verificação")
        print("  3. Proceda com o deploy apenas após 100% de conformidade")

    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())