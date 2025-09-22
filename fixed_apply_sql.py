# scripts/apply_sql_fixed.py
"""
Aplicar DDL e estrutura do banco de dados - VERSÃO CORRIGIDA
Compatível com estrutura original dos arquivos fornecidos
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"

def get_database_url():
    """Obter URL do banco de dados"""
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ Variável DATABASE_URL não encontrada no .env")
        print("💡 Verifique se o arquivo .env foi criado corretamente")
        print("💡 Exemplo: DATABASE_URL=postgresql+psycopg://postgres:senha@host:5432/db")
        sys.exit(1)
    return url

def execute_sql_file(engine, filepath, description=""):
    """Executar arquivo SQL"""
    if not filepath.exists():
        print(f"⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    print(f"🔄 Executando {description}: {filepath.name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with engine.begin() as conn:
            # Dividir por statements mais inteligentemente
            statements = []
            current_statement = ""
            in_function = False
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # Detectar início/fim de função
                if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                    in_function = True
                
                current_statement += line + '\n'
                
                # Se não estamos em função e linha termina com ;
                if not in_function and line.endswith(';') and not line.startswith('--'):
                    statements.append(current_statement.strip())
                    current_statement = ""
                
                # Fim de função
                if in_function and line.upper().startswith('$$ LANGUAGE'):
                    in_function = False
                    statements.append(current_statement.strip())
                    current_statement = ""
            
            # Adicionar último statement se houver
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            # Executar statements
            for i, statement in enumerate(statements):
                if statement and not statement.startswith('--') and statement != '\n':
                    try:
                        conn.execute(text(statement))
                        if i < 5:  # Mostrar primeiros statements
                            print(f"  ✓ Statement {i+1} executado")
                    except Exception as e:
                        print(f"  ❌ Erro no statement {i+1}: {str(e)[:100]}...")
                        print(f"     Statement: {statement[:100]}...")
                        return False
        
        print(f"✅ {description} executado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar {filepath.name}: {e}")
        return False

def execute_sql_direct(ddl_content, seed_content):
    """Executar SQL diretamente do conteúdo"""
    database_url = get_database_url()
    engine = create_engine(database_url, pool_pre_ping=True)
    
    print("📊 Aplicando estrutura do banco de dados")
    print("=" * 50)
    
    # Criar arquivo temporário para DDL
    ddl_temp = SQL_DIR / "ddl_temp.sql"
    seed_temp = SQL_DIR / "seed_temp.sql"
    
    try:
        # Criar diretório se não existir
        SQL_DIR.mkdir(exist_ok=True)
        
        # Escrever conteúdo nos arquivos temporários
        with open(ddl_temp, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        with open(seed_temp, 'w', encoding='utf-8') as f:
            f.write(seed_content)
        
        success = True
        
        # Executar DDL
        if not execute_sql_file(engine, ddl_temp, "Estrutura do banco (DDL)"):
            success = False
        
        # Executar Seeds
        if success and not execute_sql_file(engine, seed_temp, "Dados iniciais (Seeds)"):
            success = False
        
        if success:
            print("\n" + "=" * 50)
            print("✅ Estrutura do banco aplicada com sucesso!")
            print("\n🎯 Próximos passos:")
            print("1. make dev     # Iniciar todos os serviços")
            print("2. Acessar http://localhost:8050")
            print("3. Login: admin@transpontual.com / admin123")
        else:
            print("\n❌ Erro ao aplicar estrutura do banco")
            return False
            
    finally:
        # Limpar arquivos temporários
        if ddl_temp.exists():
            ddl_temp.unlink()
        if seed_temp.exists():
            seed_temp.unlink()
    
    return success

def main():
    """Aplicar scripts SQL corrigidos"""
    # DDL Corrigido (baseado na estrutura original)
    ddl_content = """-- DDL Corrigido - Compatível com estrutura original

-- USUÁRIOS
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('gestor','mecanico','motorista')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- MOTORISTAS
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

-- VEÍCULOS  
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

-- VIAGENS
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

-- CHECKLIST MODELOS
CREATE TABLE IF NOT EXISTS checklist_modelos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra')),
    versao INT NOT NULL DEFAULT 1,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- CHECKLIST ITENS (COM OPCOES JSONB)
CREATE TABLE IF NOT EXISTS checklist_itens (
    id SERIAL PRIMARY KEY,
    modelo_id INT NOT NULL REFERENCES checklist_modelos(id) ON DELETE CASCADE,
    ordem INT NOT NULL,
    descricao TEXT NOT NULL,
    tipo_resposta TEXT NOT NULL CHECK (tipo_resposta IN ('ok','na','obs','foto')),
    severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta')),
    exige_foto BOOLEAN NOT NULL DEFAULT FALSE,
    bloqueia_viagem BOOLEAN NOT NULL DEFAULT FALSE,
    opcoes JSONB DEFAULT '[]'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_checklist_item_ordem ON checklist_itens(modelo_id, ordem);

-- CHECKLISTS
CREATE TABLE IF NOT EXISTS checklists (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE,
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
        CHECK (status IN ('pendente','aprovado','reprovado','em_andamento')),
    assinatura_motorista TEXT,
    observacoes_gerais TEXT,
    duracao_minutos INT
);

-- CHECKLIST RESPOSTAS
CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    checklist_id INT NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    valor TEXT NOT NULL CHECK (valor IN ('ok','nao_ok','na')),
    observacao TEXT,
    opcao_defeito TEXT,
    foto_url TEXT,
    geo TEXT,
    dt TIMESTAMP NOT NULL DEFAULT NOW()
);

-- DEFEITOS
CREATE TABLE IF NOT EXISTS defeitos (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE,
    checklist_id INT NOT NULL REFERENCES checklists(id),
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta')),
    descricao TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status IN ('aberto','em_andamento','resolvido','identificado')),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ORDENS DE SERVIÇO
CREATE TABLE IF NOT EXISTS ordens_servico (
    id SERIAL PRIMARY KEY,
    numero TEXT UNIQUE,
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

-- ÍNDICES BÁSICOS
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_veiculos_placa ON veiculos(placa);
CREATE INDEX IF NOT EXISTS idx_checklists_veiculo_id ON checklists(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_checklists_status ON checklists(status);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_checklist_id ON checklist_respostas(checklist_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_veiculo_id ON defeitos(veiculo_id);

-- TRIGGER PARA GERAR CÓDIGO DO CHECKLIST
CREATE OR REPLACE FUNCTION update_checklist_codigo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.codigo IS NULL THEN
        NEW.codigo := 'CL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT), 1, 8));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_checklist_codigo 
    BEFORE INSERT ON checklists 
    FOR EACH ROW 
    EXECUTE FUNCTION update_checklist_codigo();
"""

    # Seeds Corrigidos
    seed_content = """-- Seeds Corrigidos

-- USUÁRIOS
INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES
('Administrador Sistema', 'admin@transpontual.com', 'admin123', 'gestor', true),
('João Silva', 'joao.silva@transpontual.com', 'motorista123', 'motorista', true),
('Maria Santos', 'maria.santos@transpontual.com', 'motorista123', 'motorista', true),
('Carlos Lima', 'carlos.lima@transpontual.com', 'motorista123', 'motorista', true)
ON CONFLICT (email) DO NOTHING;

-- MOTORISTAS (estrutura original)
INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, usuario_id, ativo) VALUES
('João Silva Santos', '12345678900', 'E', '2028-12-31', 
    (SELECT id FROM usuarios WHERE email = 'joao.silva@transpontual.com'), true),
('Maria Santos Oliveira', '22345678900', 'D', '2027-08-15',
    (SELECT id FROM usuarios WHERE email = 'maria.santos@transpontual.com'), true),
('Carlos Lima Souza', '32345678900', 'E', '2029-05-20',
    (SELECT id FROM usuarios WHERE email = 'carlos.lima@transpontual.com'), true)
ON CONFLICT DO NOTHING;

-- VEÍCULOS (estrutura original)  
INSERT INTO veiculos (placa, renavam, ano, modelo, km_atual, ativo) VALUES
('RTA1A23', '00999887766', 2019, 'VW Constellation', 250000, true),
('RTA2B34', '00999887767', 2020, 'Volvo FH 460', 180050, true),
('RTA3C45', '00999887768', 2018, 'Scania R450', 320000, true),
('RTA4D56', '00999887769', 2017, 'MB Actros 2651', 410000, true),
('RTA5E67', '00999887770', 2021, 'DAF XF', 120000, true)
ON CONFLICT (placa) DO NOTHING;

-- MODELO PADRÃO CAMINHÃO
INSERT INTO checklist_modelos (nome, tipo, versao, ativo) VALUES 
('Caminhão - Pré-viagem', 'pre', 1, true)
ON CONFLICT DO NOTHING;

-- ITENS DO MODELO PADRÃO
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes)
SELECT m.id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes::jsonb
FROM checklist_modelos m
CROSS JOIN (VALUES
  (1, 'Freios funcionando', 'ok', 'alta', false, true, '["Eficiência baixa","Ruído anormal","Pedal baixo","Outros"]'),
  (2, 'Pneus/sulco/pressão', 'ok', 'alta', true, true, '["Pressão baixa","Sulco insuficiente","Fissura","Outros"]'),
  (3, 'Iluminação e setas', 'ok', 'media', false, true, '["Farol queimado","Lanterna quebrada","Seta inoperante","Outros"]'),
  (4, 'Direção sem folga', 'ok', 'alta', false, true, '["Folga excessiva","Barulho anormal","Direção dura","Outros"]'),
  (5, 'Vazamentos visíveis', 'ok', 'alta', true, true, '["Óleo motor","Combustível","Refrigeração","Outros"]'),
  (6, 'Tacógrafo funcionando', 'ok', 'media', false, false, '["Sem lacre","Falha leitura","Display defeituoso","Outros"]'),
  (7, 'Extintor no prazo', 'ok', 'media', false, false, '["Vencido","Pressão baixa","Lacre violado","Outros"]'),
  (8, 'Cinto de segurança', 'ok', 'alta', false, true, '["Sem trava","Rasgado","Fixação solta","Outros"]'),
  (9, 'Para-brisa/limpadores', 'ok', 'baixa', false, false, '["Trincado","Palheta gasta","Reservatório vazio","Outros"]'),
  (10, 'Retrovisores', 'ok', 'baixa', false, false, '["Quebrado","Solto","Desajustado","Outros"]'),
  (11, 'Documentação veículo', 'ok', 'media', false, true, '["CRLV vencido","Seguro vencido","Placa ilegível","Outros"]'),
  (12, 'EPI do motorista', 'ok', 'media', false, false, '["Ausente","Danificado","Vencido","Outros"]')
) AS itens(ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes)
WHERE m.nome = 'Caminhão - Pré-viagem'
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- VIAGEM DE EXEMPLO
INSERT INTO viagens (veiculo_id, motorista_id, origem, destino, data_partida, status)
SELECT v.id, m.id, 'Macaé/RJ', 'Campos/RJ', NOW() + INTERVAL '1 hour', 'planejada'
FROM veiculos v 
CROSS JOIN motoristas m
WHERE v.placa='RTA1A23' AND m.cnh='12345678900'
LIMIT 1;

-- CHECKLIST DE EXEMPLO (APROVADO)
INSERT INTO checklists (viagem_id, veiculo_id, motorista_id, modelo_id, tipo, odometro_ini, geo_inicio, status, duracao_minutos)
SELECT 
    v.id as viagem_id,
    vei.id as veiculo_id, 
    m.id as motorista_id,
    cm.id as modelo_id,
    'pre',
    250000,
    '{"lat": -22.3765, "lng": -41.7869}',
    'aprovado',
    15
FROM viagens v
JOIN veiculos vei ON vei.id = v.veiculo_id
JOIN motoristas m ON m.id = v.motorista_id  
JOIN checklist_modelos cm ON cm.nome = 'Caminhão - Pré-viagem'
WHERE vei.placa = 'RTA1A23'
LIMIT 1;

-- RESPOSTAS DO CHECKLIST (TODAS OK)
INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao)
SELECT 
    c.id,
    ci.id,
    'ok',
    'Item verificado - OK'
FROM checklists c
JOIN checklist_itens ci ON ci.modelo_id = c.modelo_id
WHERE c.status = 'aprovado'
ORDER BY ci.ordem;
"""

    return execute_sql_direct(ddl_content, seed_content)

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)