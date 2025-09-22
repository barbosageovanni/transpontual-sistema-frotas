#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo para demonstração
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

def create_sample_data():
    """Criar dados de exemplo para demonstração"""

    db = SessionLocal()

    try:
        print("Iniciando população do banco de dados...")

        # 1. Criar usuários
        print("Criando usuários...")
        usuarios_sql = """
        INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES
        ('Admin Sistema', 'admin@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'gestor', true),
        ('João Silva', 'joao.silva@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'motorista', true),
        ('Maria Santos', 'maria.santos@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'motorista', true),
        ('Pedro Costa', 'pedro.costa@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'mecanico', true),
        ('Ana Oliveira', 'ana.oliveira@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'motorista', true),
        ('Carlos Mendes', 'carlos.mendes@transpontual.com', '$2b$12$rHG5BxJqMX.xQzgx8g8Bie8q0PvX6XkXE2YKzF.123', 'gestor', true)
        ON CONFLICT (email) DO NOTHING;
        """
        db.execute(text(usuarios_sql))

        # 2. Criar motoristas
        print("Criando motoristas...")
        motoristas_sql = """
        INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, telefone, ativo, usuario_id) VALUES
        ('João Silva', '12345678901', 'D', '2025-12-31', '(11) 99999-0001', true, (SELECT id FROM usuarios WHERE email = 'joao.silva@transpontual.com')),
        ('Maria Santos', '12345678902', 'D', '2026-06-15', '(11) 99999-0002', true, (SELECT id FROM usuarios WHERE email = 'maria.santos@transpontual.com')),
        ('Ana Oliveira', '12345678903', 'D', '2024-12-31', '(11) 99999-0003', true, (SELECT id FROM usuarios WHERE email = 'ana.oliveira@transpontual.com')),
        ('Roberto Lima', '12345678904', 'E', '2025-08-20', '(11) 99999-0004', true, NULL),
        ('Fernanda Costa', '12345678905', 'D', '2026-02-10', '(11) 99999-0005', true, NULL),
        ('José Santos', '12345678906', 'E', '2025-11-30', '(11) 99999-0006', true, NULL),
        ('Luciana Silva', '12345678907', 'D', '2024-10-15', '(11) 99999-0007', true, NULL),
        ('Marcos Pereira', '12345678908', 'E', '2025-09-05', '(11) 99999-0008', true, NULL)
        ON CONFLICT (cnh) DO NOTHING;
        """
        db.execute(text(motoristas_sql))

        # 3. Criar veículos
        print("Criando veículos...")
        veiculos_sql = """
        INSERT INTO veiculos (placa, marca, modelo, ano, categoria, km_atual, status, ativo) VALUES
        ('ABC-1234', 'Mercedes-Benz', 'Sprinter 415', 2020, 'van', 85420, 'disponivel', true),
        ('DEF-5678', 'Iveco', 'Daily 35S14', 2019, 'caminhao_leve', 142350, 'disponivel', true),
        ('GHI-9012', 'Volkswagen', 'Delivery 11.180', 2021, 'caminhao_medio', 67890, 'disponivel', true),
        ('JKL-3456', 'Ford', 'Transit 350', 2022, 'van', 34567, 'disponivel', true),
        ('MNO-7890', 'Scania', 'R440', 2018, 'caminhao_pesado', 298750, 'manutencao', true),
        ('PQR-1357', 'Volvo', 'VM 270', 2020, 'caminhao_medio', 156890, 'disponivel', true),
        ('STU-2468', 'Mercedes-Benz', 'Accelo 815', 2019, 'caminhao_leve', 189432, 'disponivel', true),
        ('VWX-9753', 'Renault', 'Master 2.5', 2021, 'van', 45678, 'disponivel', true),
        ('YZA-1598', 'Hyundai', 'HR 2.5', 2020, 'caminhao_leve', 78901, 'bloqueado', false),
        ('BCD-3571', 'Fiat', 'Ducato 2.8', 2022, 'van', 23456, 'disponivel', true)
        ON CONFLICT (placa) DO NOTHING;
        """
        db.execute(text(veiculos_sql))

        # 4. Criar modelos de checklist
        print("Criando modelos de checklist...")
        modelos_sql = """
        INSERT INTO checklist_modelos (nome, tipo, descricao, ativo) VALUES
        ('Pré-Viagem Padrão', 'pre', 'Checklist padrão para inspeção antes da viagem', true),
        ('Pós-Viagem Padrão', 'pos', 'Checklist padrão para inspeção após a viagem', true),
        ('Manutenção Preventiva', 'manutencao', 'Checklist para manutenção preventiva mensal', true),
        ('Pré-Viagem Carga Pesada', 'pre', 'Checklist específico para transporte de carga pesada', true),
        ('Inspeção Semanal', 'manutencao', 'Checklist semanal de rotina', true)
        ON CONFLICT (nome) DO NOTHING;
        """
        db.execute(text(modelos_sql))

        # 5. Criar itens dos modelos
        print("Criando itens dos modelos...")

        # Itens para Pré-Viagem Padrão
        itens_pre_viagem = [
            ("Pneus dianteiros - estado geral", "ok", "alta", True, True),
            ("Pneus traseiros - estado geral", "ok", "alta", True, True),
            ("Pressão dos pneus", "ok", "media", False, False),
            ("Faróis e lanternas", "ok", "alta", False, True),
            ("Pisca-alerta e setas", "ok", "media", False, False),
            ("Freios - teste e funcionamento", "ok", "alta", False, True),
            ("Direção - folgas e alinhamento", "ok", "alta", False, True),
            ("Espelhos retrovisores", "ok", "media", False, False),
            ("Limpador de para-brisa", "ok", "baixa", False, False),
            ("Água do radiador", "ok", "media", False, False),
            ("Óleo do motor - nível", "ok", "alta", False, False),
            ("Combustível - nível adequado", "ok", "media", False, False),
            ("Documentos do veículo", "ok", "alta", False, True),
            ("Kit de primeiros socorros", "ok", "media", False, False),
            ("Extintor de incêndio", "ok", "alta", False, True),
            ("Triângulo de sinalização", "ok", "media", False, False),
            ("Macaco e chave de roda", "ok", "baixa", False, False),
            ("Estepe - estado e calibragem", "ok", "media", False, False),
            ("Carroceria - avarias externas", "ok", "baixa", True, False),
            ("Sistema elétrico geral", "ok", "media", False, False)
        ]

        for ordem, (descricao, tipo_resp, severidade, exige_foto, bloqueia) in enumerate(itens_pre_viagem, 1):
            item_sql = f"""
            INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem)
            SELECT id, {ordem}, '{descricao}', '{tipo_resp}', '{severidade}', {exige_foto}, {bloqueia}
            FROM checklist_modelos WHERE nome = 'Pré-Viagem Padrão'
            ON CONFLICT DO NOTHING;
            """
            db.execute(text(item_sql))

        # Itens para Pós-Viagem
        itens_pos_viagem = [
            ("Combustível - nível final", "ok", "baixa", False, False),
            ("Odômetro - registro final", "ok", "baixa", False, False),
            ("Avarias durante viagem", "ok", "media", True, False),
            ("Limpeza interna do veículo", "ok", "baixa", False, False),
            ("Documentos de carga/entrega", "ok", "media", False, False),
            ("Ocorrências na viagem", "ok", "media", False, False),
            ("Estado geral dos pneus", "ok", "media", True, False),
            ("Funcionamento de freios", "ok", "alta", False, False),
            ("Sistema de iluminação", "ok", "media", False, False),
            ("Combustível suficiente p/ próxima viagem", "ok", "baixa", False, False)
        ]

        for ordem, (descricao, tipo_resp, severidade, exige_foto, bloqueia) in enumerate(itens_pos_viagem, 1):
            item_sql = f"""
            INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem)
            SELECT id, {ordem}, '{descricao}', '{tipo_resp}', '{severidade}', {exige_foto}, {bloqueia}
            FROM checklist_modelos WHERE nome = 'Pós-Viagem Padrão'
            ON CONFLICT DO NOTHING;
            """
            db.execute(text(item_sql))

        # 6. Criar alguns checklists de exemplo
        print("Criando checklists de exemplo...")

        # Checklists dos últimos 30 dias
        for i in range(25):  # 25 checklists de exemplo
            days_ago = random.randint(0, 30)
            dt_inicio = datetime.now() - timedelta(days=days_ago, hours=random.randint(6, 18), minutes=random.randint(0, 59))

            # Alguns checklists finalizados, outros em andamento
            status_options = ['aprovado', 'reprovado', 'em_andamento']
            status = random.choices(status_options, weights=[60, 25, 15])[0]  # 60% aprovados, 25% reprovados, 15% em andamento

            dt_fim = None
            if status != 'em_andamento':
                dt_fim = dt_inicio + timedelta(minutes=random.randint(15, 45))

            # Selecionar IDs aleatórios (assumindo que existem)
            veiculo_id = random.randint(1, 8)  # 8 veículos criados
            motorista_id = random.randint(1, 8)  # 8 motoristas criados
            modelo_id = random.choice([1, 2])  # Pre ou pos viagem

            odometro_ini = random.randint(50000, 300000)
            odometro_fim = odometro_ini + random.randint(50, 500) if dt_fim else None

            # Score baseado no status
            if status == 'aprovado':
                score = random.randint(85, 100)
            elif status == 'reprovado':
                score = random.randint(30, 70)
            else:
                score = None

            checklist_sql = f"""
            INSERT INTO checklists (veiculo_id, motorista_id, modelo_id, tipo, status, dt_inicio, dt_fim,
                                 odometro_ini, odometro_fim, score_aprovacao, observacoes_gerais)
            VALUES ({veiculo_id}, {motorista_id}, {modelo_id},
                   (SELECT tipo FROM checklist_modelos WHERE id = {modelo_id}),
                   '{status}', '{dt_inicio}',
                   {'NULL' if dt_fim is None else f"'{dt_fim}'"},
                   {odometro_ini}, {'NULL' if odometro_fim is None else odometro_fim},
                   {'NULL' if score is None else score},
                   {'NULL' if random.random() < 0.7 else "'Checklist realizado conforme procedimento padrão.'"});
            """
            db.execute(text(checklist_sql))

        # 7. Criar algumas respostas de exemplo para checklists finalizados
        print("Criando respostas de exemplo...")

        # Buscar checklists finalizados
        checklists = db.execute(text("SELECT id FROM checklists WHERE status != 'em_andamento' LIMIT 15")).fetchall()

        for checklist_id_row in checklists:
            checklist_id = checklist_id_row[0]

            # Buscar itens do modelo deste checklist
            itens = db.execute(text("""
                SELECT ci.id FROM checklist_itens ci
                JOIN checklists c ON c.modelo_id = ci.modelo_id
                WHERE c.id = :checklist_id
            """), {"checklist_id": checklist_id}).fetchall()

            for item_row in itens:
                item_id = item_row[0]

                # Gerar resposta aleatória
                if random.random() < 0.85:  # 85% OK
                    valor = 'ok'
                    observacao = None
                elif random.random() < 0.10:  # 10% NOK
                    valor = 'nao_ok'
                    observacoes_defeitos = [
                        'Desgaste excessivo identificado',
                        'Pequena rachadura observada',
                        'Ruído anormal detectado',
                        'Vazamento leve encontrado',
                        'Folga além do aceitável',
                        'Necessita limpeza',
                        'Calibragem inadequada'
                    ]
                    observacao = random.choice(observacoes_defeitos)
                else:  # 5% N/A
                    valor = 'na'
                    observacao = None

                resposta_sql = f"""
                INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao)
                VALUES ({checklist_id}, {item_id}, '{valor}',
                       {'NULL' if observacao is None else f"'{observacao}'"});
                """
                db.execute(text(resposta_sql))

        # 8. Commit das transações
        db.commit()

        print("\nDados de exemplo criados com sucesso!")
        print("\nResumo dos dados criados:")
        print("   - 6 usuários (1 admin, 1 gestor, 1 mecânico, 3 motoristas)")
        print("   - 8 motoristas")
        print("   - 10 veículos variados")
        print("   - 5 modelos de checklist")
        print("   - 30 itens de checklist")
        print("   - 25 checklists de exemplo")
        print("   - Respostas para checklists finalizados")
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
    create_sample_data()