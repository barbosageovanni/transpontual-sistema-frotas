#!/usr/bin/env python3
"""
Setup Production Data - Transpontual Sistema de Gestão de Frotas
Versão automática para execução sem interação (demonstração).
"""

import os
import sys
import hashlib
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / "backend_fastapi"))
    from app.core.database import SessionLocal
    from sqlalchemy import text
except ImportError as e:
    print(f"[ERROR] Erro ao importar dependências: {e}")
    sys.exit(1)


class ProductionDataSetupAuto:
    def __init__(self):
        pass

    def hash_password(self, password: str) -> str:
        """Hash da senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_admin_user_auto(self, session):
        """Criar usuário administrador padrão (apenas para demonstração)"""
        print("[USER] Criando usuário administrador de demonstração...")

        # NOTA: Em produção real, use credenciais seguras fornecidas pelo usuário
        admin_email = "admin@transpontual.com"
        admin_nome = "Administrador Sistema"
        admin_password = "admin123456"  # Senha temporária - DEVE SER ALTERADA

        password_hash = self.hash_password(admin_password)

        try:
            # Verificar se já existe
            existing = session.execute(
                text("SELECT id FROM usuarios WHERE email = :email"),
                {"email": admin_email}
            ).fetchone()

            if existing:
                print(f"[WARNING] Usuário com email {admin_email} já existe")
                return True

            # Inserir novo administrador
            session.execute(text("""
                INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, criado_em)
                VALUES (:nome, :email, :senha_hash, 'admin', true, NOW())
            """), {
                "nome": admin_nome,
                "email": admin_email,
                "senha_hash": password_hash
            })

            session.commit()
            print(f"[SUCCESS] Administrador criado: {admin_nome} ({admin_email})")
            print(f"[WARNING] Senha temporária: {admin_password} - ALTERE IMEDIATAMENTE!")
            return True

        except Exception as e:
            print(f"[ERROR] Erro ao criar administrador: {e}")
            return False

    def create_basic_checklist_models(self, session):
        """Criar modelos básicos de checklist"""
        print("[MODELS] Criando modelos básicos de checklist...")

        models = [
            {
                "nome": "Checklist Pré-viagem Básico",
                "tipo": "pre",
                "descricao": "Verificações básicas antes da viagem"
            },
            {
                "nome": "Checklist Pós-viagem Básico",
                "tipo": "pos",
                "descricao": "Verificações básicas após a viagem"
            },
            {
                "nome": "Checklist Manutenção Preventiva",
                "tipo": "manutencao",
                "descricao": "Verificações para manutenção preventiva"
            }
        ]

        for model in models:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM checklist_modelos WHERE nome = :nome"),
                    {"nome": model["nome"]}
                ).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO checklist_modelos (nome, tipo, descricao, ativo, criado_em)
                        VALUES (:nome, :tipo, :descricao, true, NOW())
                    """), model)
                    print(f"[SUCCESS] Modelo criado: {model['nome']}")
                else:
                    print(f"[WARNING] Modelo já existe: {model['nome']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar modelo {model['nome']}: {e}")

        session.commit()

    def create_basic_checklist_items(self, session):
        """Criar itens básicos de checklist"""
        print("[ITEMS] Criando itens básicos de checklist...")

        items = [
            {
                "categoria": "Motor",
                "descricao": "Verificar nível de óleo do motor",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 1
            },
            {
                "categoria": "Motor",
                "descricao": "Verificar nível de água do radiador",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 2
            },
            {
                "categoria": "Pneus",
                "descricao": "Verificar calibragem dos pneus",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 3
            },
            {
                "categoria": "Pneus",
                "descricao": "Verificar estado dos pneus (desgaste, furos)",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 4
            },
            {
                "categoria": "Freios",
                "descricao": "Testar funcionamento dos freios",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 5
            },
            {
                "categoria": "Iluminação",
                "descricao": "Verificar faróis dianteiros",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 6
            },
            {
                "categoria": "Iluminação",
                "descricao": "Verificar lanternas traseiras",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 7
            },
            {
                "categoria": "Documentação",
                "descricao": "Verificar CRLV em dia",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 8
            },
            {
                "categoria": "Segurança",
                "descricao": "Verificar extintor de incêndio",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 9
            },
            {
                "categoria": "Segurança",
                "descricao": "Verificar triângulo de segurança",
                "tipo_resposta": "ok_nok_na",
                "obrigatorio": True,
                "ordem": 10
            }
        ]

        for item in items:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM checklist_itens WHERE descricao = :descricao"),
                    {"descricao": item["descricao"]}
                ).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO checklist_itens
                        (categoria, descricao, tipo_resposta, obrigatorio, ordem, ativo, criado_em)
                        VALUES
                        (:categoria, :descricao, :tipo_resposta, :obrigatorio, :ordem, true, NOW())
                    """), item)
                    print(f"[SUCCESS] Item criado: {item['descricao']}")
                else:
                    print(f"[WARNING] Item já existe: {item['descricao']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar item {item['descricao']}: {e}")

        session.commit()

    def create_sample_vehicles(self, session):
        """Criar veículos de exemplo"""
        print("[VEHICLES] Criando veículos de exemplo...")

        vehicles = [
            {
                "placa": "ABC1234",
                "marca": "Volkswagen",
                "modelo": "Delivery",
                "ano": 2020,
                "cor": "Branco",
                "km_atual": 15000
            },
            {
                "placa": "DEF5678",
                "marca": "Mercedes-Benz",
                "modelo": "Sprinter",
                "ano": 2021,
                "cor": "Prata",
                "km_atual": 8000
            }
        ]

        for vehicle in vehicles:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM veiculos WHERE placa = :placa"),
                    {"placa": vehicle["placa"]}
                ).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO veiculos
                        (placa, marca, modelo, ano, cor, km_atual, ativo, criado_em)
                        VALUES
                        (:placa, :marca, :modelo, :ano, :cor, :km_atual, true, NOW())
                    """), vehicle)
                    print(f"[SUCCESS] Veículo criado: {vehicle['placa']} - {vehicle['marca']} {vehicle['modelo']}")
                else:
                    print(f"[WARNING] Veículo já existe: {vehicle['placa']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar veículo {vehicle['placa']}: {e}")

        session.commit()

    def setup_all_auto(self):
        """Executar toda a configuração automaticamente"""
        print("[SETUP] CONFIGURAÇÃO AUTOMÁTICA DE DADOS DE PRODUÇÃO")
        print("=" * 50)

        try:
            with SessionLocal() as session:
                # 1. Criar administrador
                if not self.create_admin_user_auto(session):
                    print("[ERROR] Falha ao criar administrador. Abortando.")
                    return False

                # 2. Criar modelos de checklist
                self.create_basic_checklist_models(session)

                # 3. Criar itens de checklist
                self.create_basic_checklist_items(session)

                # 4. Criar veículos de exemplo
                self.create_sample_vehicles(session)

                print("\n[SUCCESS] CONFIGURAÇÃO AUTOMÁTICA CONCLUÍDA!")
                print("=" * 50)
                print("[INFO] Sistema pronto para uso em produção!")
                print("[NEXT] Próximos passos:")
                print("   1. ALTERE a senha do administrador imediatamente")
                print("   2. Cadastre usuários reais (motoristas, gestores)")
                print("   3. Cadastre veículos da frota")
                print("   4. Customize modelos de checklist conforme necessário")
                print("   5. Configure variáveis de ambiente de produção")

                return True

        except Exception as e:
            print(f"[ERROR] Erro durante a configuração: {e}")
            return False


def main():
    setup = ProductionDataSetupAuto()
    success = setup.setup_all_auto()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())