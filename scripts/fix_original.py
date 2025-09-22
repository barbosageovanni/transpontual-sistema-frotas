# scripts/fix_original.py
"""
Script que aplica EXATAMENTE a estrutura original do ddl.sql e seed.sql
fornecidos pelo usuário, sem modificações que causam conflitos
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def apply_original_structure():
    """Aplicar estrutura original exata"""
    
    print("🔧 Aplicando estrutura ORIGINAL do banco...")
    
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL não encontrada no .env")
        return False
    
    engine = create_engine(url, pool_pre_ping=True)
    
    # DDL ORIGINAL EXATO (sem campos que não existem)
    ddl_original = """
    -- DDL principal para Módulo 1: Checklist Veicular
    CREATE TABLE IF NOT EXISTS usuarios (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      senha_hash TEXT NOT NULL,
      papel TEXT NOT NULL CHECK (papel IN ('gestor','mecanico','motorista')),
      ativo BOOLEAN NOT NULL DEFAULT TRUE,
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS veiculos (
      id SERIAL PRIMARY KEY,
      placa TEXT UNIQUE NOT NULL,
      renavam TEXT,
      ano INT,
      modelo TEXT,
      km_atual BIGINT DEFAULT 0,
      ativo BOOLEAN NOT NULL DEFAULT TRUE,
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS motoristas (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      cnh TEXT,
      categoria TEXT,
      validade_cnh DATE,
      usuario_id INT REFERENCES usuarios(id),
      ativo BOOLEAN NOT NULL DEFAULT TRUE,
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS viagens (
      id SERIAL PRIMARY KEY,
      veiculo_id INT NOT NULL REFERENCES veiculos(id),
      motorista_id INT NOT NULL REFERENCES motoristas(id),
      origem TEXT,
      destino TEXT,
      data_partida TIMESTAMP,
      data_chegada_prevista TIMESTAMP,
      status TEXT NOT NULL DEFAULT 'planejada' 
        CHECK (status IN ('planejada','em_andamento','finalizada','bloqueada')),
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS checklist_modelos (
      id SERIAL PRIMARY KEY,
      nome TEXT NOT NULL,
      tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra')),
      versao INT NOT NULL DEFAULT 1,
      ativo BOOLEAN NOT NULL DEFAULT TRUE,
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS checklist_itens (
      id SERIAL PRIMARY KEY,
      modelo_id INT NOT NULL REFERENCES checklist_modelos(id) ON DELETE CASCADE,
      ordem INT NOT NULL,
      descricao TEXT NOT NULL,
      tipo_resposta TEXT NOT NULL CHECK (tipo_resposta IN ('ok','na','obs','foto')),
      severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta')),
      exige_foto BOOLEAN NOT NULL DEFAULT FALSE,
      bloqueia_viagem BOOLEAN NOT NULL DEFAULT FALSE
    );

    CREATE UNIQUE INDEX IF NOT EXISTS uq_checklist_item_ordem ON checklist_itens(modelo_id, ordem);

    CREATE TABLE IF NOT EXISTS checklists (
      id SERIAL PRIMARY KEY,
      viagem_id INT REFERENCES viagens(id),
      veiculo_id INT NOT NULL REFERENCES veiculos(id),
      motorista_id INT NOT NULL REFERENCES motoristas(id),
      modelo_id INT NOT NULL REFERENCES checklist_modelos(id),
      tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra')),
      odometro_ini BIGINT,
      odometro_fim BIGINT,
      geo_inicio TEXT,
      geo_fim TEXT,
      dt_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
      dt_fim TIMESTAMP,
      status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente','aprovado','reprovado')),
      assinatura_motorista TEXT
    );

    CREATE TABLE IF NOT EXISTS checklist_respostas (
      id SERIAL PRIMARY KEY,
      checklist_id INT NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
      item_id INT NOT NULL REFERENCES checklist_itens(id),
      valor TEXT NOT NULL, -- 'ok', 'nao_ok', 'na'
      observacao TEXT,
      foto_url TEXT,
      geo TEXT,
      dt TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS ix_checklist_respostas_ck ON checklist_respostas(checklist_id);

    CREATE TABLE IF NOT EXISTS defeitos (
      id SERIAL PRIMARY KEY,
      checklist_id INT NOT NULL REFERENCES checklists(id),
      item_id INT NOT NULL REFERENCES checklist_itens(id),
      veiculo_id INT NOT NULL REFERENCES veiculos(id),
      severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta')),
      descricao TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status IN ('aberto','em_andamento','resolvido')),
      criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ordens_servico (
      id SERIAL PRIMARY KEY,
      veiculo_id INT NOT NULL REFERENCES veiculos(id),
      defeito_id INT REFERENCES defeitos(id),
      abertura_dt TIMESTAMP NOT NULL DEFAULT NOW(),
      encerramento_dt TIMESTAMP,
      custo_peca NUMERIC(12,2) DEFAULT 0,
      custo_mo NUMERIC(12,2) DEFAULT 0,
      centro_custo TEXT,
      status TEXT NOT NULL DEFAULT 'aberta'
        CHECK (status IN ('aberta','em_execucao','fechada'))
    );

    -- Views úteis
    CREATE OR REPLACE VIEW vw_checklist_bloqueios AS
    SELECT c.id checklist_id, v.placa, c.tipo, c.status,
           COUNT(CASE WHEN i.bloqueia_viagem AND r.valor='nao_ok' THEN 1 END) AS bloqueios
    FROM checklists c
    JOIN veiculos v ON v.id = c.veiculo_id
    JOIN checklist_respostas r ON r.checklist_id = c.id
    JOIN checklist_itens i ON i.id = r.item_id
    GROUP BY c.id, v.placa, c.tipo, c.status;

    -- Índices
    CREATE INDEX IF NOT EXISTS ix_checklists_veic ON checklists(veiculo_id);
    CREATE INDEX IF NOT EXISTS ix_checklists_motor ON checklists(motorista_id);
    CREATE INDEX IF NOT EXISTS ix_checklists_status ON checklists(status);
    """

    # SEED ORIGINAL EXATO (sem campos que não existem)
    seed_original = """
    -- Seeds iniciais (DEV) – ajuste conforme necessário

    -- Usuário admin (senha em texto: admin123 – em produção, substitua por bcrypt)
    INSERT INTO usuarios (nome, email, senha_hash, papel, ativo)
    VALUES ('Administrador', 'admin@transpontual.com', 'admin123', 'gestor', true)
    ON CONFLICT (email) DO NOTHING;

    -- Usuários/motoristas (senha em texto para DEV)
    INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES
    ('João Motorista', 'joao@transpontual.com', 'motorista123', 'motorista', true),
    ('Maria Motorista', 'maria@transpontual.com', 'motorista123', 'motorista', true),
    ('Carlos Motorista', 'carlos@transpontual.com', 'motorista123', 'motorista', true)
    ON CONFLICT (email) DO NOTHING;

    -- Veículos
    INSERT INTO veiculos (placa, renavam, ano, modelo, km_atual, ativo) VALUES
    ('RTA1A23','00999887766', 2019, 'VW Constellation', 250000, true),
    ('RTA2B34','00999887767', 2020, 'Volvo FH 460',     180050, true),
    ('RTA3C45','00999887768', 2018, 'Scania R450',      320000, true),
    ('RTA4D56','00999887769', 2017, 'MB Actros 2651',   410000, true),
    ('RTA5E67','00999887770', 2021, 'DAF XF',           120000, true)
    ON CONFLICT (placa) DO NOTHING;

    -- Motoristas vinculados aos usuários criados
    INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, usuario_id, ativo)
    SELECT u.nome, '1234567890', 'E', CURRENT_DATE + INTERVAL '2 years', u.id, true
    FROM usuarios u
    WHERE u.email IN ('joao@transpontual.com','maria@transpontual.com','carlos@transpontual.com')
    ON CONFLICT DO NOTHING;

    -- Modelo de Checklist Padrão (Pré-viagem)
    WITH m AS (
      INSERT INTO checklist_modelos (nome, tipo, versao, ativo)
      VALUES ('Caminhão - Pré-viagem', 'pre', 1, true)
      RETURNING id
    )
    INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem)
    SELECT id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia
    FROM m
    CROSS JOIN (VALUES
      (1, 'Freios funcionando',            'ok',  'alta',  false, true),
      (2, 'Pneus/sulco/pressão',           'ok',  'alta',  true,  true),
      (3, 'Iluminação e setas',            'ok',  'media', false, true),
      (4, 'Direção sem folga/ruído',       'ok',  'alta',  false, true),
      (5, 'Vazamentos visíveis',           'ok',  'alta',  true,  true),
      (6, 'Tacógrafo lacrado/funcionando', 'ok',  'media', false, false),
      (7, 'Extintor no prazo',             'ok',  'media', false, false),
      (8, 'Cinto de segurança',            'ok',  'alta',  false, true),
      (9, 'Para-brisa/limpadores',         'ok',  'baixa', false, false),
      (10,'Retrovisores',                   'ok',  'baixa', false, false),
      (11,'Documentação do veículo',       'ok',  'media', false, true),
      (12,'EPI do motorista',              'ok',  'media', false, false)
    ) AS itens(ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia);

    -- Viagem de exemplo (planejada)
    INSERT INTO viagens (veiculo_id, motorista_id, origem, destino, data_partida, status)
    SELECT v.id, m.id, 'Macaé/RJ', 'Campos/RJ', NOW(), 'planejada'
    FROM veiculos v JOIN motoristas m ON true
    WHERE v.placa='RTA1A23'
    ORDER BY m.id LIMIT 1;
    """

    try:
        with engine.begin() as conn:
            print("📊 Aplicando DDL original...")
            conn.execute(text(ddl_original))
            
            print("🌱 Aplicando seeds originais...")
            conn.execute(text(seed_original))
        
        print("✅ Estrutura original aplicada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    if apply_original_structure():
        print("\n🎉 Sistema pronto para uso!")
        print("\n📍 Próximos passos:")
        print("1. make dev")
        print("2. Acessar http://localhost:8050")
        print("3. Login: admin@transpontual.com / admin123")
    else:
        print("❌ Falha na aplicação da estrutura")
        sys.exit(1)