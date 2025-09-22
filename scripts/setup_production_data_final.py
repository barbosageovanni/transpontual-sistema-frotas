#!/usr/bin/env python3
"""
Setup Production Data - Transpontual Sistema de Gestão de Frotas
Versão final compatível com a estrutura atual do banco.
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


class ProductionDataSetupFinal:
    def __init__(self):
        pass

    def hash_password(self, password: str) -> str:
        """Hash da senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_admin_user_final(self, session):
        """Criar usuário administrador"""
        print("[USER] Criando usuário administrador...")

        admin_email = "admin@transpontual.com"
        admin_nome = "Administrador Sistema"
        admin_password = "TransponTual2024!"  # Senha mais segura

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
            print(f"[INFO] Senha: {admin_password}")
            return True

        except Exception as e:
            print(f"[ERROR] Erro ao criar administrador: {e}")
            return False

    def create_checklist_models_final(self, session):
        """Criar modelos de checklist usando estrutura atual"""
        print("[MODELS] Criando modelos de checklist...")

        models = [
            {
                "nome": "Checklist Pré-viagem Padrão",
                "tipo": "pre_viagem",
                "versao": 1
            },
            {
                "nome": "Checklist Pós-viagem Padrão",
                "tipo": "pos_viagem",
                "versao": 1
            },
            {
                "nome": "Checklist Manutenção Preventiva",
                "tipo": "manutencao",
                "versao": 1
            }
        ]

        model_ids = {}

        for model in models:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM checklist_modelos WHERE nome = :nome"),
                    {"nome": model["nome"]}
                ).fetchone()

                if not existing:
                    result = session.execute(text("""
                        INSERT INTO checklist_modelos (nome, tipo, versao, ativo, criado_em)
                        VALUES (:nome, :tipo, :versao, true, NOW())
                        RETURNING id
                    """), model)
                    model_id = result.fetchone()[0]
                    model_ids[model["nome"]] = model_id
                    print(f"[SUCCESS] Modelo criado: {model['nome']} (ID: {model_id})")
                else:
                    model_ids[model["nome"]] = existing[0]
                    print(f"[WARNING] Modelo já existe: {model['nome']} (ID: {existing[0]})")

            except Exception as e:
                print(f"[ERROR] Erro ao criar modelo {model['nome']}: {e}")

        session.commit()
        return model_ids

    def create_checklist_items_final(self, session, model_ids):
        """Criar itens de checklist usando estrutura atual"""
        print("[ITEMS] Criando itens de checklist...")

        # Buscar o primeiro modelo para vinculação
        if not model_ids:
            print("[WARNING] Nenhum modelo disponível para vincular itens")
            return

        primeiro_modelo_id = list(model_ids.values())[0]

        items = [
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 1,
                "descricao": "Verificar nível de óleo do motor",
                "tipo_resposta": "ok_nok_na",
                "severidade": "critica",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Motor"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 2,
                "descricao": "Verificar nível de água do radiador",
                "tipo_resposta": "ok_nok_na",
                "severidade": "critica",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Motor"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 3,
                "descricao": "Verificar calibragem dos pneus",
                "tipo_resposta": "ok_nok_na",
                "severidade": "alta",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Pneus"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 4,
                "descricao": "Verificar estado dos pneus (desgaste, furos)",
                "tipo_resposta": "ok_nok_na",
                "severidade": "alta",
                "exige_foto": True,
                "bloqueia_viagem": True,
                "categoria": "Pneus"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 5,
                "descricao": "Testar funcionamento dos freios",
                "tipo_resposta": "ok_nok_na",
                "severidade": "critica",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Freios"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 6,
                "descricao": "Verificar faróis dianteiros",
                "tipo_resposta": "ok_nok_na",
                "severidade": "media",
                "exige_foto": False,
                "bloqueia_viagem": False,
                "categoria": "Iluminação"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 7,
                "descricao": "Verificar lanternas traseiras",
                "tipo_resposta": "ok_nok_na",
                "severidade": "media",
                "exige_foto": False,
                "bloqueia_viagem": False,
                "categoria": "Iluminação"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 8,
                "descricao": "Verificar CRLV em dia",
                "tipo_resposta": "ok_nok_na",
                "severidade": "critica",
                "exige_foto": True,
                "bloqueia_viagem": True,
                "categoria": "Documentação"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 9,
                "descricao": "Verificar extintor de incêndio",
                "tipo_resposta": "ok_nok_na",
                "severidade": "critica",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Segurança"
            },
            {
                "modelo_id": primeiro_modelo_id,
                "ordem": 10,
                "descricao": "Verificar triângulo de segurança",
                "tipo_resposta": "ok_nok_na",
                "severidade": "alta",
                "exige_foto": False,
                "bloqueia_viagem": True,
                "categoria": "Segurança"
            }
        ]

        for item in items:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM checklist_itens WHERE descricao = :descricao AND modelo_id = :modelo_id"),
                    {"descricao": item["descricao"], "modelo_id": item["modelo_id"]}
                ).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO checklist_itens
                        (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, categoria)
                        VALUES
                        (:modelo_id, :ordem, :descricao, :tipo_resposta, :severidade, :exige_foto, :bloqueia_viagem, :categoria)
                    """), item)
                    print(f"[SUCCESS] Item criado: {item['descricao']}")
                else:
                    print(f"[WARNING] Item já existe: {item['descricao']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar item {item['descricao']}: {e}")

        session.commit()

    def create_sample_vehicles_final(self, session):
        """Criar veículos usando estrutura atual"""
        print("[VEHICLES] Criando veículos de exemplo...")

        vehicles = [
            {
                "placa": "ABC1234",
                "marca": "Volkswagen",
                "modelo": "Delivery 8.160",
                "ano": 2020,
                "km_atual": 15000,
                "tipo": "Caminhão"
            },
            {
                "placa": "DEF5678",
                "marca": "Mercedes-Benz",
                "modelo": "Sprinter 515",
                "ano": 2021,
                "km_atual": 8000,
                "tipo": "Van"
            },
            {
                "placa": "GHI9012",
                "marca": "Ford",
                "modelo": "Transit 350",
                "ano": 2022,
                "km_atual": 5000,
                "tipo": "Van"
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
                        (placa, marca, modelo, ano, km_atual, tipo, ativo, criado_em)
                        VALUES
                        (:placa, :marca, :modelo, :ano, :km_atual, :tipo, true, NOW())
                    """), vehicle)
                    print(f"[SUCCESS] Veículo criado: {vehicle['placa']} - {vehicle['marca']} {vehicle['modelo']}")
                else:
                    print(f"[WARNING] Veículo já existe: {vehicle['placa']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar veículo {vehicle['placa']}: {e}")

        session.commit()

    def create_sample_drivers(self, session):
        """Criar motoristas de exemplo"""
        print("[DRIVERS] Criando motoristas de exemplo...")

        drivers = [
            {
                "nome": "João Silva Santos",
                "cnh": "12345678901",
                "categoria_cnh": "D",
                "telefone": "(11) 99999-1234",
                "email": "joao.santos@transpontual.com"
            },
            {
                "nome": "Maria Oliveira Costa",
                "cnh": "98765432109",
                "categoria_cnh": "D",
                "telefone": "(11) 99999-5678",
                "email": "maria.costa@transpontual.com"
            }
        ]

        for driver in drivers:
            try:
                # Verificar se já existe
                existing = session.execute(
                    text("SELECT id FROM motoristas WHERE cnh = :cnh"),
                    {"cnh": driver["cnh"]}
                ).fetchone()

                if not existing:
                    session.execute(text("""
                        INSERT INTO motoristas
                        (nome, cnh, categoria_cnh, telefone, email, ativo, criado_em)
                        VALUES
                        (:nome, :cnh, :categoria_cnh, :telefone, :email, true, NOW())
                    """), driver)
                    print(f"[SUCCESS] Motorista criado: {driver['nome']} (CNH: {driver['cnh']})")
                else:
                    print(f"[WARNING] Motorista já existe: {driver['nome']}")

            except Exception as e:
                print(f"[ERROR] Erro ao criar motorista {driver['nome']}: {e}")

        session.commit()

    def setup_all_final(self):
        """Executar configuração completa"""
        print("[SETUP] CONFIGURAÇÃO FINAL DE DADOS DE PRODUÇÃO")
        print("=" * 60)

        try:
            with SessionLocal() as session:
                # 1. Criar administrador
                if not self.create_admin_user_final(session):
                    print("[ERROR] Falha ao criar administrador. Abortando.")
                    return False

                # 2. Criar modelos de checklist
                model_ids = self.create_checklist_models_final(session)

                # 3. Criar itens de checklist
                self.create_checklist_items_final(session, model_ids)

                # 4. Criar veículos de exemplo
                self.create_sample_vehicles_final(session)

                # 5. Criar motoristas de exemplo
                self.create_sample_drivers(session)

                print("\n[SUCCESS] CONFIGURAÇÃO FINAL CONCLUÍDA!")
                print("=" * 60)
                print("[INFO] Sistema configurado com dados iniciais de produção!")
                print("[SECURITY] IMPORTANTE - Credenciais de acesso:")
                print("   Email: admin@transpontual.com")
                print("   Senha: TransponTual2024!")
                print("   [ATENÇÃO] Altere a senha após o primeiro login!")

                print("\n[NEXT] Próximos passos:")
                print("   1. Acesse o sistema e altere a senha do administrador")
                print("   2. Configure variáveis de ambiente para produção")
                print("   3. Cadastre usuários reais da empresa")
                print("   4. Cadastre veículos reais da frota")
                print("   5. Customize os modelos de checklist")
                print("   6. Execute testes de funcionalidade")
                print("   7. Configure backup automático")

                return True

        except Exception as e:
            print(f"[ERROR] Erro durante a configuração: {e}")
            return False


def main():
    setup = ProductionDataSetupFinal()
    success = setup.setup_all_final()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())