-- sql/ddl_fixed.sql
-- DDL corrigido baseado na estrutura original

-- ========== USUÁRIOS ==========
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('gestor','mecanico','motorista')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MOTORISTAS ==========
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

-- ========== VEÍCULOS ==========
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

-- ========== VIAGENS ==========
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

-- ========== CHECKLIST MODELOS ==========
CREATE TABLE IF NOT EXISTS checklist_modelos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra')),
    versao INT NOT NULL DEFAULT 1,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== CHECKLIST ITENS ==========
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

-- ========== CHECKLISTS ==========
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
        CHECK (status IN ('pendente','aprovado','reprovado')),
    assinatura_motorista TEXT,
    observacoes_gerais TEXT,
    duracao_minutos INT
);

-- ========== CHECKLIST RESPOSTAS ==========
CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    checklist_id INT NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    valor TEXT NOT NULL, -- 'ok', 'nao_ok', 'na'
    observacao TEXT,
    opcao_defeito TEXT,
    foto_url TEXT,
    geo TEXT,
    dt TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_checklist_respostas_ck ON checklist_respostas(checklist_id);

-- ========== DEFEITOS ==========
CREATE TABLE IF NOT EXISTS defeitos (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE,
    checklist_id INT NOT NULL REFERENCES checklists(id),
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta')),
    descricao TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status IN ('aberto','em_andamento','resolvido')),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== ORDENS DE SERVIÇO ==========
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

-- ========== ÍNDICES ==========
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON usuarios(papel);
CREATE INDEX IF NOT EXISTS idx_motoristas_nome ON motoristas(nome);
CREATE INDEX IF NOT EXISTS idx_motoristas_cnh ON motoristas(cnh);
CREATE INDEX IF NOT EXISTS idx_veiculos_placa ON veiculos(placa);
CREATE INDEX IF NOT EXISTS idx_veiculos_ativo ON veiculos(ativo);
CREATE INDEX IF NOT EXISTS idx_checklists_veiculo_id ON checklists(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_checklists_motorista_id ON checklists(motorista_id);
CREATE INDEX IF NOT EXISTS idx_checklists_status ON checklists(status);
CREATE INDEX IF NOT EXISTS idx_checklists_dt_inicio ON checklists(dt_inicio);
CREATE INDEX IF NOT EXISTS idx_defeitos_veiculo_id ON defeitos(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_status ON defeitos(status);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_veiculo_id ON ordens_servico(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_status ON ordens_servico(status);

-- ========== VIEWS ==========
CREATE OR REPLACE VIEW vw_checklist_bloqueios AS
SELECT 
    c.id AS checklist_id, 
    v.placa, 
    c.tipo, 
    c.status,
    COUNT(CASE WHEN i.bloqueia_viagem AND r.valor='nao_ok' THEN 1 END) AS bloqueios
FROM checklists c
JOIN veiculos v ON v.id = c.veiculo_id
JOIN checklist_respostas r ON r.checklist_id = c.id
JOIN checklist_itens i ON i.id = r.item_id
GROUP BY c.id, v.placa, c.tipo, c.status;

-- ========== TRIGGERS ==========
CREATE OR REPLACE FUNCTION generate_codigo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.codigo IS NULL THEN
        NEW.codigo := TG_ARGV[0] || '-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(NEW.id::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para gerar código do checklist após inserção
CREATE OR REPLACE FUNCTION update_checklist_codigo()
RETURNS TRIGGER AS $$
BEGIN
    NEW.codigo := 'CL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT), 1, 8));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger apenas se código não for fornecido
CREATE TRIGGER trigger_checklist_codigo 
    BEFORE INSERT ON checklists 
    FOR EACH ROW 
    WHEN (NEW.codigo IS NULL)
    EXECUTE FUNCTION update_checklist_codigo();

-- Trigger similar para defeitos
CREATE OR REPLACE FUNCTION update_defeito_codigo()
RETURNS TRIGGER AS $$
BEGIN
    NEW.codigo := 'DEF-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT), 1, 6));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_defeito_codigo 
    BEFORE INSERT ON defeitos 
    FOR EACH ROW 
    WHEN (NEW.codigo IS NULL)
    EXECUTE FUNCTION update_defeito_codigo();

-- Trigger para ordens de serviço
CREATE OR REPLACE FUNCTION update_os_numero()
RETURNS TRIGGER AS $$
BEGIN
    NEW.numero := 'OS-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(NEW.id::TEXT, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- sql/seed_fixed.sql
-- Seeds corrigidos para estrutura original

-- ========== USUÁRIOS ==========
INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES
('Administrador Sistema', 'admin@transpontual.com', 'admin123', 'gestor', true),
('João Silva', 'joao.silva@transpontual.com', 'motorista123', 'motorista', true),
('Maria Santos', 'maria.santos@transpontual.com', 'motorista123', 'motorista', true),
('Carlos Lima', 'carlos.lima@transpontual.com', 'motorista123', 'motorista', true),
('José Mecânico', 'jose.mecanico@transpontual.com', 'mecanico123', 'mecanico', true),
('Ana Gestora', 'ana.gestora@transpontual.com', 'gestor123', 'gestor', true)
ON CONFLICT (email) DO NOTHING;

-- ========== MOTORISTAS (SEM CAMPOS EXTRAS) ==========
INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, usuario_id, ativo) VALUES
('João Silva Santos', '12345678900', 'E', '2028-12-31', 
    (SELECT id FROM usuarios WHERE email = 'joao.silva@transpontual.com' LIMIT 1), true),
('Maria Santos Oliveira', '22345678900', 'D', '2027-08-15',
    (SELECT id FROM usuarios WHERE email = 'maria.santos@transpontual.com' LIMIT 1), true),
('Carlos Lima Souza', '32345678900', 'E', '2029-05-20',
    (SELECT id FROM usuarios WHERE email = 'carlos.lima@transpontual.com' LIMIT 1), true),
('Roberto Cruz', '42345678900', 'E', '2026-11-10', NULL, true),
('Fernando Alves', '52345678900', 'D', '2028-03-25', NULL, true),
('Ricardo Pereira', '62345678900', 'E', '2025-07-18', NULL, true)
ON CONFLICT DO NOTHING;

-- ========== VEÍCULOS (ESTRUTURA ORIGINAL) ==========
INSERT INTO veiculos (placa, renavam, ano, modelo, km_atual, ativo) VALUES
-- Cavalos mecânicos
('RTA1A23', '00999887766', 2019, 'VW Constellation 17.280', 250000, true),
('RTA2B34', '00999887767', 2020, 'Volvo FH 460', 180050, true),
('RTA3C45', '00999887768', 2018, 'Scania R 450', 320000, true),
('RTA4D56', '00999887769', 2017, 'Mercedes Actros 2651', 410000, true),
('RTA5E67', '00999887770', 2021, 'DAF XF 480', 120000, true),

-- Carretas
('RTB1F78', '00999887771', 2018, 'Bitrem Graneleiro Guerra', 180000, true),
('RTB2G89', '00999887772', 2019, 'Sider 3 Eixos Librelato', 220000, true),
('RTB3H90', '00999887773', 2020, 'Baú Frigorífico Krone', 95000, true),
('RTB4I01', '00999887774', 2017, 'Prancha 4 Eixos Facchini', 380000, true),

-- Veículos leves
('RTC1J12', '00999887775', 2021, 'Mercedes Sprinter 415', 45000, true),
('RTC2K23', '00999887776', 2020, 'Renault Master 2.3', 72000, true),
('RTC3L34', '00999887777', 2022, 'Iveco Daily 70C16', 28000, true),
('RTC4M45', '00999887778', 2019, 'Hyundai HR 2.5', 89000, true)
ON CONFLICT (placa) DO NOTHING;

-- ========== VIAGENS ==========
INSERT INTO viagens (veiculo_id, motorista_id, origem, destino, data_partida, data_chegada_prevista, status) VALUES
(1, 1, 'Macaé/RJ', 'Campos dos Goytacazes/RJ', '2024-01-15 06:00:00', '2024-01-15 10:00:00', 'planejada'),
(2, 2, 'Rio das Ostras/RJ', 'Vitória/ES', '2024-01-15 08:00:00', '2024-01-15 18:00:00', 'planejada'),
(3, 3, 'Campos/RJ', 'Belo Horizonte/MG', '2024-01-15 05:00:00', '2024-01-16 14:00:00', 'planejada')
ON CONFLICT DO NOTHING;

-- ========== MODELOS DE CHECKLIST ==========

-- Modelo Carreta - Pré-viagem
INSERT INTO checklist_modelos (nome, tipo, versao, ativo) VALUES 
('Carreta - Pré-viagem', 'pre', 1, true)
ON CONFLICT DO NOTHING;

-- Itens do modelo Carreta
WITH carreta_modelo AS (
    SELECT id FROM checklist_modelos WHERE nome = 'Carreta - Pré-viagem' LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes) VALUES
((SELECT id FROM carreta_modelo), 1, 'Engate / Pino-rei', 'ok', 'alta', false, true, 
 '["Folga no pino-rei","Trava com desgaste","Engate sem travar","Excesso de graxa","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 2, 'Quinta roda / travamento', 'ok', 'alta', false, true,
 '["Trava não engata","Pino solto","Jogo excessivo","Lubrificação inadequada","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 3, 'Amarração da carga', 'ok', 'alta', true, true,
 '["Cinta desgastada","Catraca quebrada","Lona rasgada","Carga solta","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 4, 'Pneus da carreta', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco insuficiente","Fissura","Desgaste irregular","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 5, 'Iluminação traseira', 'ok', 'media', false, true,
 '["Lanterna quebrada","Sem funcionamento","Fiação aparente","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 6, 'Freios e ar comprimido', 'ok', 'alta', true, true,
 '["Vazamento de ar","Mangueira danificada","Engate com folga","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 7, 'Para-lamas', 'ok', 'media', false, false,
 '["Quebrado","Solto","Faltante","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 8, 'Suspensão pneumática', 'ok', 'alta', true, true,
 '["Bolsa furada","Nivelamento irregular","Barulho anormal","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 9, 'Vazamentos visíveis', 'ok', 'alta', true, true,
 '["Óleo diferencial","Graxa do cubo","Combustível","Outros"]'::jsonb),
((SELECT id FROM carreta_modelo), 10, 'Documentação', 'ok', 'media', false, true,
 '["Placa ilegível","CRLV vencido","Seguro vencido","Outros"]'::jsonb)
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- Modelo Cavalo - Pré-viagem
INSERT INTO checklist_modelos (nome, tipo, versao, ativo) VALUES 
('Cavalo - Pré-viagem', 'pre', 1, true)
ON CONFLICT DO NOTHING;

-- Itens do modelo Cavalo
WITH cavalo_modelo AS (
    SELECT id FROM checklist_modelos WHERE nome = 'Cavalo - Pré-viagem' LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes) VALUES
((SELECT id FROM cavalo_modelo), 1, 'Freios de serviço', 'ok', 'alta', false, true,
 '["Eficiência baixa","Ruído anormal","Luz inoperante","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 2, 'Pneus do cavalo', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco insuficiente","Fissura","Parafusos frouxos","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 3, 'Iluminação e setas', 'ok', 'media', false, true,
 '["Farol queimado","Lanterna quebrada","Fora de foco","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 4, 'Direção', 'ok', 'alta', false, true,
 '["Folga excessiva","Vazamento","Barulho anormal","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 5, 'Vazamentos motor', 'ok', 'alta', true, true,
 '["Óleo motor","Óleo câmbio","Refrigeração","Combustível","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 6, 'Para-brisa', 'ok', 'baixa', false, false,
 '["Trincado","Palheta gasta","Reservatório vazio","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 7, 'Retrovisores', 'ok', 'baixa', false, false,
 '["Quebrado","Solto","Desajustado","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 8, 'Tacógrafo', 'ok', 'media', false, false,
 '["Sem lacre","Falha de leitura","Display defeituoso","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 9, 'Extintor', 'ok', 'media', false, false,
 '["Vencido","Pressão baixa","Lacre violado","Outros"]'::jsonb),
((SELECT id FROM cavalo_modelo), 10, 'Cinto de segurança', 'ok', 'alta', false, true,
 '["Sem trava","Rasgado","Fixação solta","Outros"]'::jsonb)
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- Modelo Leve - Pré-viagem
INSERT INTO checklist_modelos (nome, tipo, versao, ativo) VALUES 
('Leve - Pré-viagem', 'pre', 1, true)
ON CONFLICT DO NOTHING;

-- Itens do modelo Leve
WITH leve_modelo AS (
    SELECT id FROM checklist_modelos WHERE nome = 'Leve - Pré-viagem' LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes) VALUES
((SELECT id FROM leve_modelo), 1, 'Iluminação geral', 'ok', 'media', false, true,
 '["Farol queimado","Lanterna quebrada","Seta inoperante","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 2, 'Pneus', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco insuficiente","Deformação","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 3, 'Freio de serviço', 'ok', 'alta', false, true,
 '["Curso longo","Ruído","Baixa eficiência","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 4, 'Para-brisa', 'ok', 'baixa', false, false,
 '["Trinca","Palheta gasta","Reservatório vazio","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 5, 'Níveis fluidos', 'ok', 'baixa', false, false,
 '["Óleo baixo","Água baixa","Combustível baixo","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 6, 'Cinto de segurança', 'ok', 'alta', false, true,
 '["Sem trava","Rasgado","Fixação solta","Outros"]'::jsonb),
((SELECT id FROM leve_modelo), 7, 'Documentação', 'ok', 'media', false, true,
 '["CRLV vencido","Seguro vencido","Outros"]'::jsonb)
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- ========== EXEMPLO CHECKLIST APROVADO ==========
INSERT INTO checklists (codigo, viagem_id, veiculo_id, motorista_id, modelo_id, tipo, odometro_ini, geo_inicio, status, dt_inicio, duracao_minutos) VALUES
('CL-20240115-EXEMPLO01', 1, 1, 1, 1, 'pre', 250000, 
 '{"lat": -22.3765, "lng": -41.7869, "address": "Macaé/RJ"}', 
 'aprovado', '2024-01-15 05:30:00', 12)
ON CONFLICT (codigo) DO NOTHING;

-- Respostas do checklist aprovado
WITH exemplo_checklist AS (
    SELECT id FROM checklists WHERE codigo = 'CL-20240115-EXEMPLO01' LIMIT 1
), carreta_itens AS (
    SELECT id, ordem FROM checklist_itens ci 
    WHERE ci.modelo_id = (SELECT id FROM checklist_modelos WHERE nome = 'Carreta - Pré-viagem' LIMIT 1)
    ORDER BY ordem
)
INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao) 
SELECT 
    (SELECT id FROM exemplo_checklist),
    ci.id,
    'ok',
    CASE ci.ordem 
        WHEN 1 THEN 'Engate funcionando perfeitamente'
        WHEN 2 THEN 'Quinta roda travando corretamente'
        WHEN 3 THEN 'Carga bem amarrada'
        ELSE 'Item OK'
    END
FROM carreta_itens ci
ON CONFLICT DO NOTHING;

-- ========== EXEMPLO CHECKLIST COM PROBLEMA ==========
INSERT INTO checklists (codigo, viagem_id, veiculo_id, motorista_id, modelo_id, tipo, odometro_ini, geo_inicio, status, dt_inicio, duracao_minutos) VALUES
('CL-20240115-PROBLEMA02', 2, 2, 2, 
 (SELECT id FROM checklist_modelos WHERE nome = 'Cavalo - Pré-viagem' LIMIT 1), 
 'pre', 180050, 
 '{"lat": -22.5322, "lng": -41.9487, "address": "Rio das Ostras/RJ"}',
 'reprovado', '2024-01-15 07:45:00', 18)
ON CONFLICT (codigo) DO NOTHING;

-- Respostas com problemas
WITH problema_checklist AS (
    SELECT id FROM checklists WHERE codigo = 'CL-20240115-PROBLEMA02' LIMIT 1
), cavalo_itens AS (
    SELECT id, ordem FROM checklist_itens ci 
    WHERE ci.modelo_id = (SELECT id FROM checklist_modelos WHERE nome = 'Cavalo - Pré-viagem' LIMIT 1)
    ORDER BY ordem
)
INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao, opcao_defeito) 
SELECT 
    (SELECT id FROM problema_checklist),
    ci.id,
    CASE ci.ordem 
        WHEN 1 THEN 'nao_ok'  -- Freios com problema
        WHEN 3 THEN 'nao_ok'  -- Iluminação com problema
        ELSE 'ok'
    END,
    CASE ci.ordem 
        WHEN 1 THEN 'Freio com ruído anormal'
        WHEN 3 THEN 'Farol direito queimado'
        ELSE 'Item OK'
    END,
    CASE ci.ordem 
        WHEN 1 THEN 'Ruído anormal'
        WHEN 3 THEN 'Farol queimado'
        ELSE NULL
    END
FROM cavalo_itens ci
ON CONFLICT DO NOTHING;

-- Defeitos gerados automaticamente
INSERT INTO defeitos (codigo, checklist_id, item_id, veiculo_id, severidade, descricao, status) VALUES
('DEF-20240115-001', 
 (SELECT id FROM checklists WHERE codigo = 'CL-20240115-PROBLEMA02' LIMIT 1),
 (SELECT id FROM checklist_itens WHERE descricao = 'Freios de serviço' LIMIT 1),
 2, 'alta', 'Freio com ruído anormal - Ruído anormal', 'aberto'),
('DEF-20240115-002',
 (SELECT id FROM checklists WHERE codigo = 'CL-20240115-PROBLEMA02' LIMIT 1), 
 (SELECT id FROM checklist_itens WHERE descricao = 'Iluminação e setas' LIMIT 1),
 2, 'media', 'Farol direito queimado - Farol queimado', 'aberto')
ON CONFLICT (codigo) DO NOTHING;

-- Ordens de serviço correspondentes
INSERT INTO ordens_servico (numero, veiculo_id, defeito_id, status, custo_peca, custo_mo) VALUES
('OS-20240115-0001', 2, (SELECT id FROM defeitos WHERE codigo = 'DEF-20240115-001' LIMIT 1), 'aberta', 450.00, 150.00),
('OS-20240115-0002', 2, (SELECT id FROM defeitos WHERE codigo = 'DEF-20240115-002' LIMIT 1), 'aberta', 45.00, 50.00)
ON CONFLICT (numero) DO NOTHING;

-- Atualizar trigger para gerar numero da OS após inserção
CREATE OR REPLACE FUNCTION update_os_numero_after()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ordens_servico 
    SET numero = 'OS-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(NEW.id::TEXT, 4, '0')
    WHERE id = NEW.id AND numero IS NULL;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_os_numero_after 
    AFTER INSERT ON ordens_servico 
    FOR EACH ROW 
    WHEN (NEW.numero IS NULL)
    EXECUTE FUNCTION update_os_numero_after();