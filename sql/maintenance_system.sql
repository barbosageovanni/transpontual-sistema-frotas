-- ========== SISTEMA DE MANUTENÇÃO PREVENTIVA ==========
-- Integração com tabela de veículos existente
-- Baseado nas imagens fornecidas pelo usuário

-- ========== 1. TIPOS DE EQUIPAMENTO ==========
CREATE TABLE IF NOT EXISTS tipos_equipamento (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE, -- CAVALO TRAÇÃO 6X2 3 EIXOS, TRUCK, CARRETA SIMPLES
    categoria VARCHAR(50), -- VEICULAR, INDUSTRIAL
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== 2. PLANOS DE MANUTENÇÃO ==========
CREATE TABLE IF NOT EXISTS planos_manutencao (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    descricao VARCHAR(300) NOT NULL, -- MANUTENÇÃO - CAVALO TRAÇÃO 6X2 3 EIXOS

    -- Configurações gerais
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    repeticao VARCHAR(50) DEFAULT 'Definida nos itens',
    quando VARCHAR(50) DEFAULT 'Definida nos itens',

    -- Tipos de equipamento que usam este plano (many-to-many)
    observacoes TEXT,

    -- Auditoria
    criado_por INTEGER REFERENCES usuarios(id),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== 3. RELAÇÃO PLANOS x TIPOS DE EQUIPAMENTO ==========
CREATE TABLE IF NOT EXISTS planos_tipos_equipamento (
    id SERIAL PRIMARY KEY,
    plano_id INTEGER NOT NULL REFERENCES planos_manutencao(id) ON DELETE CASCADE,
    tipo_equipamento_id INTEGER NOT NULL REFERENCES tipos_equipamento(id) ON DELETE CASCADE,

    CONSTRAINT uk_plano_tipo_equipamento UNIQUE (plano_id, tipo_equipamento_id)
);

-- ========== 4. ITENS DOS PLANOS DE MANUTENÇÃO ==========
CREATE TABLE IF NOT EXISTS planos_manutencao_itens (
    id SERIAL PRIMARY KEY,
    plano_id INTEGER NOT NULL REFERENCES planos_manutencao(id) ON DELETE CASCADE,

    -- Descrição do item
    descricao VARCHAR(500) NOT NULL, -- TROCA DE ÓLEO DO DIFERENCIAL
    tipo VARCHAR(50) NOT NULL DEFAULT 'Troca', -- Troca, Revisão, Inspeção, Limpeza
    categoria VARCHAR(50), -- Motor, Freios, Elétrica, Hidráulica

    -- Controle de periodicidade
    controle_por VARCHAR(10) NOT NULL CHECK (controle_por IN ('km', 'horas', 'dias')),
    intervalo_valor INTEGER NOT NULL, -- 60000 (km), 500 (horas), 30 (dias)
    km_inicial INTEGER DEFAULT 0, -- A partir de quantos km começar

    -- Configurações de alerta
    alerta_antecipacao INTEGER DEFAULT 0, -- Alertar X km/dias/horas antes
    alerta_tolerancia INTEGER DEFAULT 0, -- Tolerância após vencimento

    -- Ordem de execução
    ordem INTEGER NOT NULL DEFAULT 1,

    -- Status
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    obrigatoria BOOLEAN NOT NULL DEFAULT TRUE, -- Se bloqueia o veículo

    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_plano_item_ordem UNIQUE (plano_id, ordem)
);

-- ========== 5. VEÍCULOS x PLANOS (Vincular veículos aos planos) ==========
CREATE TABLE IF NOT EXISTS veiculos_planos_manutencao (
    id SERIAL PRIMARY KEY,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    plano_id INTEGER NOT NULL REFERENCES planos_manutencao(id) ON DELETE CASCADE,
    tipo_equipamento_id INTEGER REFERENCES tipos_equipamento(id),

    -- Data de início do plano para este veículo
    data_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    km_inicio INTEGER DEFAULT 0, -- KM inicial para cálculos

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_veiculo_plano UNIQUE (veiculo_id, plano_id)
);

-- ========== 6. HISTÓRICO DE ODÔMETRO ==========
CREATE TABLE IF NOT EXISTS historico_odometro (
    id SERIAL PRIMARY KEY,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,

    -- Leitura do odômetro
    km_atual BIGINT NOT NULL,
    km_anterior BIGINT,
    diferenca_km INTEGER, -- Calculado automaticamente

    -- Origem da leitura
    fonte VARCHAR(20) NOT NULL CHECK (fonte IN ('checklist', 'abastecimento', 'manutencao', 'manual')),
    referencia_id INTEGER, -- ID do checklist, abastecimento, etc.

    -- Dados da leitura
    data_leitura TIMESTAMP NOT NULL DEFAULT NOW(),
    observacoes TEXT,

    -- Auditoria
    registrado_por INTEGER REFERENCES usuarios(id),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== 7. CONTROLE DE MANUTENÇÕES (Estado atual de cada item) ==========
CREATE TABLE IF NOT EXISTS manutencoes_controle (
    id SERIAL PRIMARY KEY,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    plano_item_id INTEGER NOT NULL REFERENCES planos_manutencao_itens(id) ON DELETE CASCADE,

    -- Estado atual
    km_ultima_manutencao BIGINT DEFAULT 0,
    data_ultima_manutencao DATE,
    horas_ultima_manutencao INTEGER DEFAULT 0,

    -- Próxima manutenção
    km_proxima_manutencao BIGINT,
    data_proxima_manutencao DATE,
    horas_proxima_manutencao INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'em_dia' CHECK (
        status IN ('em_dia', 'vencendo', 'vencida', 'realizada')
    ),

    -- Alertas
    alerta_enviado BOOLEAN DEFAULT FALSE,
    data_alerta TIMESTAMP,

    -- Auditoria
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT uk_veiculo_plano_item UNIQUE (veiculo_id, plano_item_id)
);

-- ========== 8. HISTÓRICO DE MANUTENÇÕES REALIZADAS ==========
CREATE TABLE IF NOT EXISTS manutencoes_historico (
    id SERIAL PRIMARY KEY,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    plano_item_id INTEGER REFERENCES planos_manutencao_itens(id),
    ordem_servico_id INTEGER REFERENCES ordens_servico(id),

    -- Dados da manutenção
    descricao VARCHAR(500) NOT NULL,
    tipo_manutencao VARCHAR(20) NOT NULL CHECK (tipo_manutencao IN ('preventiva', 'corretiva', 'preditiva')),

    -- Quando foi realizada
    data_realizacao DATE NOT NULL,
    km_realizacao BIGINT,
    horas_realizacao INTEGER,

    -- Custos
    custo_mao_obra DECIMAL(10,2) DEFAULT 0,
    custo_pecas DECIMAL(10,2) DEFAULT 0,
    custo_terceiros DECIMAL(10,2) DEFAULT 0,
    custo_total DECIMAL(10,2) DEFAULT 0,

    -- Responsáveis
    responsavel_execucao VARCHAR(200),
    oficina_terceirizada VARCHAR(200),

    -- Detalhes
    pecas_utilizadas TEXT, -- JSON ou texto livre
    servicos_realizados TEXT,
    observacoes TEXT,

    -- Próxima manutenção (se aplicável)
    proxima_km BIGINT,
    proxima_data DATE,
    proxima_horas INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'concluida' CHECK (
        status IN ('concluida', 'pendente', 'cancelada')
    ),

    -- Auditoria
    registrado_por INTEGER REFERENCES usuarios(id),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== 9. MULTAS (Extensão da tabela existente com controle) ==========
-- Adicionar campo à tabela existente de multas
ALTER TABLE multas ADD COLUMN IF NOT EXISTS responsabilidade VARCHAR(20) DEFAULT 'condutor' CHECK (responsabilidade IN ('condutor', 'empresa'));
ALTER TABLE multas ADD COLUMN IF NOT EXISTS situacao VARCHAR(20) DEFAULT 'confirmada' CHECK (situacao IN ('confirmada', 'cancelada', 'recorrida', 'recusada'));

-- ========== 10. ALERTAS DO SISTEMA ==========
CREATE TABLE IF NOT EXISTS alertas_sistema (
    id SERIAL PRIMARY KEY,

    -- Tipo de alerta
    tipo VARCHAR(50) NOT NULL, -- manutencao_vencida, documento_vencendo, multa_pendente
    categoria VARCHAR(50), -- equipamento, documento, financeiro

    -- Entidade relacionada
    entidade_tipo VARCHAR(20) NOT NULL, -- veiculo, motorista, multa
    entidade_id INTEGER NOT NULL,
    referencia_id INTEGER, -- ID específico (plano_item, documento, etc.)

    -- Conteúdo do alerta
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NOT NULL,
    nivel VARCHAR(10) NOT NULL DEFAULT 'info' CHECK (nivel IN ('info', 'warning', 'danger')),

    -- Dados específicos (JSON flexível)
    dados JSONB,

    -- Controle
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    visualizado BOOLEAN NOT NULL DEFAULT FALSE,
    data_vencimento DATE, -- Quando o alerta expira

    -- Auditoria
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    visualizado_em TIMESTAMP,
    visualizado_por INTEGER REFERENCES usuarios(id)
);

-- ========== ÍNDICES ==========

-- Tipos de Equipamento
CREATE INDEX IF NOT EXISTS idx_tipos_equipamento_nome ON tipos_equipamento(nome);
CREATE INDEX IF NOT EXISTS idx_tipos_equipamento_ativo ON tipos_equipamento(ativo);

-- Planos de Manutenção
CREATE INDEX IF NOT EXISTS idx_planos_manutencao_codigo ON planos_manutencao(codigo);
CREATE INDEX IF NOT EXISTS idx_planos_manutencao_ativo ON planos_manutencao(ativo);

-- Itens dos Planos
CREATE INDEX IF NOT EXISTS idx_planos_itens_plano_id ON planos_manutencao_itens(plano_id);
CREATE INDEX IF NOT EXISTS idx_planos_itens_tipo ON planos_manutencao_itens(tipo);
CREATE INDEX IF NOT EXISTS idx_planos_itens_controle_por ON planos_manutencao_itens(controle_por);

-- Veículos x Planos
CREATE INDEX IF NOT EXISTS idx_veiculos_planos_veiculo_id ON veiculos_planos_manutencao(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_veiculos_planos_plano_id ON veiculos_planos_manutencao(plano_id);
CREATE INDEX IF NOT EXISTS idx_veiculos_planos_ativo ON veiculos_planos_manutencao(ativo);

-- Histórico Odômetro
CREATE INDEX IF NOT EXISTS idx_historico_odometro_veiculo_id ON historico_odometro(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_historico_odometro_data ON historico_odometro(data_leitura);
CREATE INDEX IF NOT EXISTS idx_historico_odometro_fonte ON historico_odometro(fonte);

-- Controle de Manutenções
CREATE INDEX IF NOT EXISTS idx_manutencoes_controle_veiculo_id ON manutencoes_controle(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_manutencoes_controle_status ON manutencoes_controle(status);
CREATE INDEX IF NOT EXISTS idx_manutencoes_controle_proxima_data ON manutencoes_controle(data_proxima_manutencao);

-- Histórico de Manutenções
CREATE INDEX IF NOT EXISTS idx_manutencoes_historico_veiculo_id ON manutencoes_historico(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_manutencoes_historico_data ON manutencoes_historico(data_realizacao);
CREATE INDEX IF NOT EXISTS idx_manutencoes_historico_tipo ON manutencoes_historico(tipo_manutencao);

-- Alertas
CREATE INDEX IF NOT EXISTS idx_alertas_sistema_tipo ON alertas_sistema(tipo);
CREATE INDEX IF NOT EXISTS idx_alertas_sistema_entidade ON alertas_sistema(entidade_tipo, entidade_id);
CREATE INDEX IF NOT EXISTS idx_alertas_sistema_ativo ON alertas_sistema(ativo);
CREATE INDEX IF NOT EXISTS idx_alertas_sistema_nivel ON alertas_sistema(nivel);

-- ========== TRIGGERS ==========

-- Trigger para atualizar km_atual do veículo quando há nova leitura
CREATE OR REPLACE FUNCTION atualizar_km_veiculo()
RETURNS TRIGGER AS $$
BEGIN
    -- Atualizar km_atual na tabela veiculos
    UPDATE veiculos
    SET km_atual = NEW.km_atual,
        atualizado_em = NOW()
    WHERE id = NEW.veiculo_id;

    -- Calcular diferença se há km anterior
    IF NEW.km_anterior IS NOT NULL THEN
        NEW.diferenca_km = NEW.km_atual - NEW.km_anterior;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_km_veiculo
    BEFORE INSERT ON historico_odometro
    FOR EACH ROW EXECUTE FUNCTION atualizar_km_veiculo();

-- Trigger para recalcular manutenções quando km é atualizado
CREATE OR REPLACE FUNCTION recalcular_manutencoes()
RETURNS TRIGGER AS $$
BEGIN
    -- Atualizar status das manutenções baseado no novo km
    UPDATE manutencoes_controle mc
    SET
        status = CASE
            WHEN NEW.km_atual >= mc.km_proxima_manutencao THEN 'vencida'
            WHEN NEW.km_atual >= (mc.km_proxima_manutencao - 1000) THEN 'vencendo' -- 1000km antes
            ELSE 'em_dia'
        END,
        atualizado_em = NOW()
    WHERE mc.veiculo_id = NEW.veiculo_id
    AND mc.km_proxima_manutencao IS NOT NULL;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_recalcular_manutencoes
    AFTER INSERT ON historico_odometro
    FOR EACH ROW EXECUTE FUNCTION recalcular_manutencoes();

-- ========== VIEWS PARA RELATÓRIOS ==========

-- View de alertas de manutenção
CREATE OR REPLACE VIEW v_alertas_manutencao AS
SELECT
    v.id as veiculo_id,
    v.placa,
    v.modelo,
    v.marca,
    v.km_atual,
    te.nome as tipo_equipamento,
    pm.descricao as plano_manutencao,
    pmi.descricao as item_manutencao,
    pmi.tipo as tipo_manutencao,
    mc.km_proxima_manutencao,
    mc.data_proxima_manutencao,
    mc.status,
    CASE
        WHEN mc.km_proxima_manutencao IS NOT NULL
        THEN mc.km_proxima_manutencao - v.km_atual
        ELSE NULL
    END as km_restantes,
    CASE
        WHEN mc.data_proxima_manutencao IS NOT NULL
        THEN mc.data_proxima_manutencao - CURRENT_DATE
        ELSE NULL
    END as dias_restantes
FROM veiculos v
JOIN veiculos_planos_manutencao vpm ON vpm.veiculo_id = v.id
JOIN planos_manutencao pm ON pm.id = vpm.plano_id
JOIN tipos_equipamento te ON te.id = vpm.tipo_equipamento_id
JOIN planos_manutencao_itens pmi ON pmi.plano_id = pm.id
JOIN manutencoes_controle mc ON mc.veiculo_id = v.id AND mc.plano_item_id = pmi.id
WHERE v.ativo = true
AND vpm.ativo = true
AND pm.ativo = true
AND pmi.ativo = true
AND mc.status IN ('vencendo', 'vencida')
ORDER BY mc.status DESC, km_restantes ASC;

-- View de previsão de manutenções
CREATE OR REPLACE VIEW v_previsao_manutencoes AS
SELECT
    v.id as veiculo_id,
    v.placa,
    v.modelo,
    v.marca,
    v.km_atual,
    te.nome as tipo_equipamento,
    pm.descricao as plano_manutencao,
    pmi.descricao as item_manutencao,
    pmi.tipo as tipo_manutencao,
    mc.km_proxima_manutencao,
    mc.data_proxima_manutencao,
    mc.status,
    CASE
        WHEN mc.km_proxima_manutencao IS NOT NULL
        THEN mc.km_proxima_manutencao - v.km_atual
        ELSE NULL
    END as km_restantes
FROM veiculos v
JOIN veiculos_planos_manutencao vpm ON vpm.veiculo_id = v.id
JOIN planos_manutencao pm ON pm.id = vpm.plano_id
JOIN tipos_equipamento te ON te.id = vpm.tipo_equipamento_id
JOIN planos_manutencao_itens pmi ON pmi.plano_id = pm.id
JOIN manutencoes_controle mc ON mc.veiculo_id = v.id AND mc.plano_item_id = pmi.id
WHERE v.ativo = true
AND vpm.ativo = true
AND pm.ativo = true
AND pmi.ativo = true
AND mc.status = 'em_dia'
ORDER BY km_restantes ASC, mc.data_proxima_manutencao ASC;

-- ========== FUNÇÕES UTILITÁRIAS ==========

-- Função para inserir leitura de odômetro
CREATE OR REPLACE FUNCTION inserir_leitura_odometro(
    p_veiculo_id INTEGER,
    p_km_atual BIGINT,
    p_fonte VARCHAR(20),
    p_referencia_id INTEGER DEFAULT NULL,
    p_observacoes TEXT DEFAULT NULL,
    p_usuario_id INTEGER DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_km_anterior BIGINT;
    v_historico_id INTEGER;
BEGIN
    -- Buscar km anterior
    SELECT km_atual INTO v_km_anterior
    FROM veiculos
    WHERE id = p_veiculo_id;

    -- Inserir no histórico
    INSERT INTO historico_odometro (
        veiculo_id, km_atual, km_anterior, fonte,
        referencia_id, observacoes, registrado_por
    ) VALUES (
        p_veiculo_id, p_km_atual, v_km_anterior, p_fonte,
        p_referencia_id, p_observacoes, p_usuario_id
    ) RETURNING id INTO v_historico_id;

    RETURN v_historico_id;
END;
$$ LANGUAGE plpgsql;

-- Função para gerar alertas automáticos
CREATE OR REPLACE FUNCTION gerar_alertas_manutencao()
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    r RECORD;
BEGIN
    -- Limpar alertas antigos de manutenção
    DELETE FROM alertas_sistema
    WHERE tipo = 'manutencao_vencida'
    AND criado_em < NOW() - INTERVAL '1 day';

    -- Gerar novos alertas para manutenções vencidas/vencendo
    FOR r IN
        SELECT * FROM v_alertas_manutencao
        WHERE status IN ('vencida', 'vencendo')
    LOOP
        INSERT INTO alertas_sistema (
            tipo, categoria, entidade_tipo, entidade_id, referencia_id,
            titulo, descricao, nivel, dados
        ) VALUES (
            'manutencao_vencida',
            'equipamento',
            'veiculo',
            r.veiculo_id,
            r.veiculo_id,
            'Alerta de equipamento ' || r.placa,
            r.item_manutencao,
            CASE WHEN r.status = 'vencida' THEN 'danger' ELSE 'warning' END,
            jsonb_build_object(
                'placa', r.placa,
                'tipo_equipamento', r.tipo_equipamento,
                'plano', r.plano_manutencao,
                'item', r.item_manutencao,
                'km_restantes', r.km_restantes,
                'status', r.status
            )
        ) ON CONFLICT DO NOTHING;

        v_count := v_count + 1;
    END LOOP;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;