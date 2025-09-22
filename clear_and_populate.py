#!/usr/bin/env python3
"""
Script para limpar e popular o banco de dados com dados de exemplo
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Adicionar o backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend_fastapi'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar conexão com o banco
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clear_data():
    """Limpar todos os dados das tabelas"""
    db = SessionLocal()

    try:
        print("Limpando dados existentes...")

        # Ordem importa por causa das foreign keys
        tables_to_clear = [
            'checklist_respostas',
            'checklists',
            'checklist_itens',
            'checklist_modelos',
            'motoristas',
            'veiculos',
            'usuarios'
        ]

        for table in tables_to_clear:
            try:
                db.execute(text(f"DELETE FROM {table}"))
                print(f"  - {table} limpo")
            except Exception as e:
                print(f"  - Erro ao limpar {table}: {e}")

        # Reset sequences
        sequences_to_reset = [
            'usuarios_id_seq',
            'veiculos_id_seq',
            'motoristas_id_seq',
            'checklist_modelos_id_seq',
            'checklist_itens_id_seq',
            'checklists_id_seq',
            'checklist_respostas_id_seq'
        ]

        for seq in sequences_to_reset:
            try:
                db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
            except Exception as e:
                print(f"  - Sequencia {seq} nao encontrada ou erro: {e}")

        db.commit()
        print("Dados limpos com sucesso!")

    except Exception as e:
        print(f"Erro ao limpar dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def populate_data():
    """Popular com dados de exemplo"""
    db = SessionLocal()

    try:
        print("Iniciando populacao do banco de dados...")

        # 1. Criar usuários
        print("Criando usuarios...")
        usuarios_data = [
            ("Admin Sistema", "admin@transpontual.com", "admin123", "gestor"),
            ("Joao Silva", "joao.silva@transpontual.com", "motorista123", "motorista"),
            ("Maria Santos", "maria.santos@transpontual.com", "motorista123", "motorista"),
            ("Pedro Costa", "pedro.costa@transpontual.com", "mecanico123", "mecanico"),
            ("Ana Oliveira", "ana.oliveira@transpontual.com", "motorista123", "motorista"),
            ("Carlos Mendes", "carlos.mendes@transpontual.com", "gestor123", "gestor")
        ]

        for nome, email, senha, papel in usuarios_data:
            # Hash simples para desenvolvimento (em prod usar bcrypt real)
            senha_hash = f"hashed_{senha}"
            db.execute(text("""
                INSERT INTO usuarios (nome, email, senha_hash, papel, ativo)
                VALUES (:nome, :email, :senha_hash, :papel, true)
            """), {"nome": nome, "email": email, "senha_hash": senha_hash, "papel": papel})

        # 2. Criar motoristas
        print("Criando motoristas...")
        motoristas_data = [
            ("Joao Silva", "12345678901", "D", "2025-12-31", "(11) 99999-0001"),
            ("Maria Santos", "12345678902", "D", "2026-06-15", "(11) 99999-0002"),
            ("Ana Oliveira", "12345678903", "D", "2024-12-31", "(11) 99999-0003"),
            ("Roberto Lima", "12345678904", "E", "2025-08-20", "(11) 99999-0004"),
            ("Fernanda Costa", "12345678905", "D", "2026-02-10", "(11) 99999-0005"),
        ]

        for nome, cnh, categoria, validade, telefone in motoristas_data:
            db.execute(text("""
                INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, telefone, ativo)
                VALUES (:nome, :cnh, :categoria, :validade, :telefone, true)
            """), {"nome": nome, "cnh": cnh, "categoria": categoria, "validade": validade, "telefone": telefone})

        # 3. Criar veículos
        print("Criando veiculos...")
        veiculos_data = [
            ("ABC-1234", "Mercedes-Benz", "Sprinter 415", 2020, "van", 85420),
            ("DEF-5678", "Iveco", "Daily 35S14", 2019, "caminhao_leve", 142350),
            ("GHI-9012", "Volkswagen", "Delivery 11.180", 2021, "caminhao_medio", 67890),
            ("JKL-3456", "Ford", "Transit 350", 2022, "van", 34567),
            ("MNO-7890", "Scania", "R440", 2018, "caminhao_pesado", 298750),
        ]

        for placa, marca, modelo, ano, categoria, km in veiculos_data:
            db.execute(text("""
                INSERT INTO veiculos (placa, marca, modelo, ano, categoria, km_atual, status, ativo)
                VALUES (:placa, :marca, :modelo, :ano, :categoria, :km, 'disponivel', true)
            """), {"placa": placa, "marca": marca, "modelo": modelo, "ano": ano, "categoria": categoria, "km": km})

        # 4. Criar modelos de checklist
        print("Criando modelos de checklist...")
        modelos_data = [
            ("Pre-Viagem Padrao", "pre", "Checklist padrao para inspecao antes da viagem"),
            ("Pos-Viagem Padrao", "pos", "Checklist padrao para inspecao apos a viagem"),
            ("Manutencao Preventiva", "manutencao", "Checklist para manutencao preventiva mensal"),
        ]

        for nome, tipo, descricao in modelos_data:
            db.execute(text("""
                INSERT INTO checklist_modelos (nome, tipo, descricao, ativo)
                VALUES (:nome, :tipo, :descricao, true)
            """), {"nome": nome, "tipo": tipo, "descricao": descricao})

        # 5. Criar itens dos modelos
        print("Criando itens dos modelos...")

        # Itens para Pré-Viagem
        itens_pre = [
            ("Pneus dianteiros - estado geral", "alta", True, True),
            ("Pneus traseiros - estado geral", "alta", True, True),
            ("Pressao dos pneus", "media", False, False),
            ("Farois e lanternas", "alta", False, True),
            ("Freios - teste e funcionamento", "alta", False, True),
            ("Direcao - folgas e alinhamento", "alta", False, True),
            ("Espelhos retrovisores", "media", False, False),
            ("Oleo do motor - nivel", "alta", False, False),
            ("Combustivel - nivel adequado", "media", False, False),
            ("Documentos do veiculo", "alta", False, True),
        ]

        for ordem, (descricao, severidade, exige_foto, bloqueia) in enumerate(itens_pre, 1):
            db.execute(text("""
                INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem)
                VALUES (1, :ordem, :descricao, 'ok', :severidade, :exige_foto, :bloqueia)
            """), {"ordem": ordem, "descricao": descricao, "severidade": severidade,
                   "exige_foto": exige_foto, "bloqueia": bloqueia})

        # 6. Criar alguns checklists de exemplo
        print("Criando checklists de exemplo...")

        for i in range(10):
            days_ago = random.randint(0, 15)
            dt_inicio = datetime.now() - timedelta(days=days_ago, hours=random.randint(8, 17))

            status_options = ['aprovado', 'reprovado', 'em_andamento']
            status = random.choice(status_options)

            dt_fim = None
            if status != 'em_andamento':
                dt_fim = dt_inicio + timedelta(minutes=random.randint(20, 60))

            veiculo_id = random.randint(1, 5)
            motorista_id = random.randint(1, 5)
            modelo_id = 1  # Pre-viagem

            odometro_ini = random.randint(50000, 200000)
            odometro_fim = odometro_ini + random.randint(50, 300) if dt_fim else None

            score = None
            if status == 'aprovado':
                score = random.randint(85, 100)
            elif status == 'reprovado':
                score = random.randint(30, 70)

            db.execute(text("""
                INSERT INTO checklists (veiculo_id, motorista_id, modelo_id, tipo, status,
                                      dt_inicio, dt_fim, odometro_ini, odometro_fim, score_aprovacao)
                VALUES (:veiculo_id, :motorista_id, :modelo_id, 'pre', :status,
                        :dt_inicio, :dt_fim, :odometro_ini, :odometro_fim, :score)
            """), {
                "veiculo_id": veiculo_id, "motorista_id": motorista_id, "modelo_id": modelo_id,
                "status": status, "dt_inicio": dt_inicio, "dt_fim": dt_fim,
                "odometro_ini": odometro_ini, "odometro_fim": odometro_fim, "score": score
            })

        db.commit()

        print("\nDados de exemplo criados com sucesso!")
        print("\nResumo dos dados criados:")
        print("   - 6 usuarios")
        print("   - 5 motoristas")
        print("   - 5 veiculos")
        print("   - 3 modelos de checklist")
        print("   - 10 itens de checklist")
        print("   - 10 checklists de exemplo")
        print("\nLogin de teste:")
        print("   Email: admin@transpontual.com")
        print("   Senha: admin123")
        print("\nAcesse: http://localhost:8050")

    except Exception as e:
        print(f"Erro ao criar dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_data()
    populate_data()