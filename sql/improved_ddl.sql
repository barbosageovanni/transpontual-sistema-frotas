-- ==============================
-- Schema PostgreSQL Melhorado - Transpontual Checklist
-- Módulo 1: Checklist Veicular (Completo)
-- Módulos 2-8: Estrutura Base
-- ==============================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==============================
-- MÓDULO 1: CHECKLIST VEICULAR
-- ==============================

-- Tabela de usuários com auditoria
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('gestor','mecanico','motorista','admin')),
    avatar_url TEXT,
    telefone TEXT,
    documento_cpf TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_login TIMESTAMP,
    tentativas_login INT DEFAULT 0,
    bloqueado_ate TIMESTAMP,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id),
    
    CONSTRAINT chk_email_formato CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Índices para usuários
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON usuarios(papel);
CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(ativo);
CREATE INDEX IF NOT EXISTS idx_usuarios_uuid ON usuarios(uuid);

-- Tabela de veículos melhorada
CREATE TABLE IF NOT EXISTS veiculos (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    placa TEXT UNIQUE NOT NULL,
    renavam TEXT,
    chassi TEXT,
    ano INT CHECK (ano > 1900 AND ano <= EXTRACT(YEAR FROM NOW()) + 1),
    modelo TEXT,
    marca TEXT,
    cor TEXT,
    combustivel TEXT CHECK (combustivel IN ('diesel','gasolina','etanol','gnv','eletrico','hibrido')),
    categoria TEXT CHECK (categoria IN ('leve','medio','pesado','especial')),
    km_atual BIGINT DEFAULT 0 CHECK (km_atual >= 0),
    capacidade_carga DECIMAL(10,2),
    capacidade_tanque DECIMAL(8,2),
    proprietario TEXT CHECK (proprietario IN ('proprio','terceiro','agregado')),
    seguradora TEXT,
    apolice_seguro TEXT,
    validade_seguro DATE,
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo','manutencao','acidente','vendido','baixado')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    observacoes TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para veículos
CREATE INDEX IF NOT EXISTS idx_veiculos_placa ON veiculos(placa);
CREATE INDEX IF NOT EXISTS idx_veiculos_status ON veiculos(status);
CREATE INDEX IF NOT EXISTS idx_veiculos_categoria ON veiculos(categoria);
CREATE INDEX IF NOT EXISTS idx_veiculos_ativo ON veiculos(ativo);
CREATE UNIQUE INDEX IF NOT EXISTS idx_veiculos_placa_ativa ON veiculos(placa) WHERE ativo = TRUE;

-- Tabela de motoristas melhorada
CREATE TABLE IF NOT EXISTS motoristas (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    nome TEXT NOT NULL,
    cnh TEXT,
    categoria_cnh TEXT CHECK (categoria_cnh IN ('A','B','C','D','E','AB','AC','AD','AE')),
    validade_cnh DATE,
    cpf TEXT,
    rg TEXT,
    telefone TEXT,
    endereco JSONB, -- {logradouro, cidade, estado, cep}
    data_nascimento DATE,
    data_admissao DATE,
    usuario_id INT REFERENCES usuarios(id),
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo','afastado','demitido','suspenso')),
    pontos_cnh INT DEFAULT 0 CHECK (pontos_cnh >= 0 AND pontos_cnh <= 40),
    observacoes TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para motoristas
CREATE INDEX IF NOT EXISTS idx_motoristas_cnh ON motoristas(cnh);
CREATE INDEX IF NOT EXISTS idx_motoristas_usuario ON motoristas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_motoristas_status ON motoristas(status);
CREATE INDEX IF NOT EXISTS idx_motoristas_ativo ON motoristas(ativo);
CREATE INDEX IF NOT EXISTS idx_motoristas_validade_cnh ON motoristas(validade_cnh);

-- Tabela de viagens melhorada
CREATE TABLE IF NOT EXISTS viagens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    codigo TEXT UNIQUE, -- Código interno da viagem
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    motorista_id INT NOT NULL REFERENCES motoristas(id),
    motorista_auxiliar_id INT REFERENCES motoristas(id),
    origem TEXT NOT NULL,
    destino TEXT NOT NULL,
    cliente TEXT,
    tipo_carga TEXT,
    peso_carga DECIMAL(10,2),
    valor_frete DECIMAL(12,2),
    data_partida_prevista TIMESTAMP,
    data_partida_real TIMESTAMP,
    data_chegada_prevista TIMESTAMP,
    data_chegada_real TIMESTAMP,
    km_inicial BIGINT,
    km_final BIGINT,
    distancia_planejada DECIMAL(8,2),
    distancia_real DECIMAL(8,2),
    status TEXT NOT NULL DEFAULT 'planejada' 
        CHECK (status IN ('planejada','liberada','em_andamento','finalizada','cancelada','bloqueada')),
    motivo_cancelamento TEXT,
    observacoes TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para viagens
CREATE INDEX IF NOT EXISTS idx_viagens_veiculo ON viagens(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_viagens_motorista ON viagens(motorista_id);
CREATE INDEX IF NOT EXISTS idx_viagens_status ON viagens(status);
CREATE INDEX IF NOT EXISTS idx_viagens_data_partida ON viagens(data_partida_prevista);
CREATE INDEX IF NOT EXISTS idx_viagens_data_criacao ON viagens(criado_em);
CREATE INDEX IF NOT EXISTS idx_viagens_codigo ON viagens(codigo);

-- Tabela de modelos de checklist com versionamento
CREATE TABLE IF NOT EXISTS checklist_modelos (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra','manutencao')),
    categoria_veiculo TEXT CHECK (categoria_veiculo IN ('leve','medio','pesado','especial','todos')),
    versao INT NOT NULL DEFAULT 1,
    versao_anterior_id INT REFERENCES checklist_modelos(id),
    descricao TEXT,
    tempo_estimado_minutos INT DEFAULT 15,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    obrigatorio BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para modelos de checklist
CREATE INDEX IF NOT EXISTS idx_checklist_modelos_tipo ON checklist_modelos(tipo);
CREATE INDEX IF NOT EXISTS idx_checklist_modelos_categoria ON checklist_modelos(categoria_veiculo);
CREATE INDEX IF NOT EXISTS idx_checklist_modelos_ativo ON checklist_modelos(ativo);

-- Tabela de itens de checklist melhorada
CREATE TABLE IF NOT EXISTS checklist_itens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    modelo_id INT NOT NULL REFERENCES checklist_modelos(id) ON DELETE CASCADE,
    ordem INT NOT NULL,
    categoria TEXT NOT NULL, -- Ex: 'freios', 'pneus', 'iluminacao', 'documentacao'
    subcategoria TEXT, -- Ex: 'freio_servico', 'freio_estacionamento'
    descricao TEXT NOT NULL,
    descricao_detalhada TEXT,
    tipo_resposta TEXT NOT NULL CHECK (tipo_resposta IN ('ok_nok','ok_nok_na','texto','numero','foto','multipla')),
    opcoes JSONB DEFAULT '[]'::jsonb, -- Lista de opções para múltipla escolha ou avarias
    severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta','critica')),
    exige_foto BOOLEAN NOT NULL DEFAULT FALSE,
    exige_observacao BOOLEAN NOT NULL DEFAULT FALSE,
    bloqueia_viagem BOOLEAN NOT NULL DEFAULT FALSE,
    gera_os BOOLEAN NOT NULL DEFAULT FALSE, -- Gera Ordem de Serviço automática
    codigo_item TEXT, -- Código interno para relatórios
    valor_min DECIMAL(10,2), -- Para respostas numéricas
    valor_max DECIMAL(10,2),
    unidade TEXT, -- Ex: 'mm', 'bar', 'km/h'
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id),
    
    CONSTRAINT uq_checklist_item_ordem UNIQUE (modelo_id, ordem)
);

-- Índices para itens de checklist
CREATE INDEX IF NOT EXISTS idx_checklist_itens_modelo ON checklist_itens(modelo_id);
CREATE INDEX IF NOT EXISTS idx_checklist_itens_categoria ON checklist_itens(categoria);
CREATE INDEX IF NOT EXISTS idx_checklist_itens_severidade ON checklist_itens(severidade);
CREATE INDEX IF NOT EXISTS idx_checklist_itens_bloqueia ON checklist_itens(bloqueia_viagem);
CREATE INDEX IF NOT EXISTS idx_checklist_itens_ordem ON checklist_itens(modelo_id, ordem);

-- Tabela principal de checklists
CREATE TABLE IF NOT EXISTS checklists (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    codigo TEXT UNIQUE, -- Código sequencial do checklist
    viagem_id INT REFERENCES viagens(id),
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    motorista_id INT NOT NULL REFERENCES motoristas(id),
    modelo_id INT NOT NULL REFERENCES checklist_modelos(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('pre','pos','extra','manutencao')),
    odometro_ini BIGINT CHECK (odometro_ini >= 0),
    odometro_fim BIGINT CHECK (odometro_fim >= 0),
    geo_inicio TEXT, -- JSON com coordenadas
    geo_fim TEXT,
    dt_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    dt_fim TIMESTAMP,
    duracao_minutos INT,
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente','em_andamento','aprovado','reprovado','cancelado')),
    score_aprovacao DECIMAL(5,2), -- Percentual de itens OK
    total_itens INT DEFAULT 0,
    itens_ok INT DEFAULT 0,
    itens_nok INT DEFAULT 0,
    itens_na INT DEFAULT 0,
    tem_bloqueios BOOLEAN DEFAULT FALSE,
    assinatura_motorista TEXT, -- Base64 da assinatura digital
    ip_address INET,
    user_agent TEXT,
    app_version TEXT,
    dispositivo_info JSONB, -- Info do dispositivo móvel
    observacoes_gerais TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    finalizado_em TIMESTAMP,
    sincronizado_em TIMESTAMP, -- Para controle de sync offline
    criado_por INT REFERENCES usuarios(id),
    
    CONSTRAINT chk_odometro_fim CHECK (odometro_fim IS NULL OR odometro_fim >= odometro_ini),
    CONSTRAINT chk_duracao CHECK (duracao_minutos IS NULL OR duracao_minutos >= 0)
);

-- Índices para checklists
CREATE INDEX IF NOT EXISTS idx_checklists_veiculo ON checklists(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_checklists_motorista ON checklists(motorista_id);
CREATE INDEX IF NOT EXISTS idx_checklists_status ON checklists(status);
CREATE INDEX IF NOT EXISTS idx_checklists_tipo ON checklists(tipo);
CREATE INDEX IF NOT EXISTS idx_checklists_data_inicio ON checklists(dt_inicio);
CREATE INDEX IF NOT EXISTS idx_checklists_viagem ON checklists(viagem_id);
CREATE INDEX IF NOT EXISTS idx_checklists_bloqueios ON checklists(tem_bloqueios) WHERE tem_bloqueios = TRUE;
CREATE INDEX IF NOT EXISTS idx_checklists_codigo ON checklists(codigo);

-- Tabela de respostas do checklist melhorada
CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    checklist_id INT NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    valor TEXT NOT NULL, -- 'ok', 'nao_ok', 'na', ou valor específico
    valor_numerico DECIMAL(15,4), -- Para respostas numéricas
    opcao_selecionada TEXT, -- Para múltipla escolha
    observacao TEXT,
    foto_url TEXT,
    foto_thumbnail_url TEXT,
    geo TEXT, -- Coordenadas da resposta
    dt TIMESTAMP NOT NULL DEFAULT NOW(),
    tempo_resposta_segundos INT, -- Tempo gasto no item
    revisao_necessaria BOOLEAN DEFAULT FALSE,
    revisado_em TIMESTAMP,
    revisado_por INT REFERENCES usuarios(id),
    observacao_revisao TEXT,
    
    CONSTRAINT uq_checklist_resposta UNIQUE (checklist_id, item_id)
);

-- Índices para respostas
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_checklist ON checklist_respostas(checklist_id);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_item ON checklist_respostas(item_id);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_valor ON checklist_respostas(valor);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_dt ON checklist_respostas(dt);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_revisao ON checklist_respostas(revisao_necessaria) WHERE revisao_necessaria = TRUE;

-- Tabela de defeitos identificados
CREATE TABLE IF NOT EXISTS defeitos (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    codigo TEXT UNIQUE, -- Código do defeito
    checklist_id INT NOT NULL REFERENCES checklists(id),
    item_id INT NOT NULL REFERENCES checklist_itens(id),
    resposta_id INT NOT NULL REFERENCES checklist_respostas(id),
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    severidade TEXT NOT NULL CHECK (severidade IN ('baixa','media','alta','critica')),
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL,
    descricao_detalhada TEXT,
    impacto TEXT, -- Descrição do impacto na operação
    status TEXT NOT NULL DEFAULT 'identificado'
        CHECK (status IN ('identificado','aberto','em_andamento','aguardando_peca','resolvido','nao_procede')),
    prioridade TEXT DEFAULT 'normal' CHECK (prioridade IN ('baixa','normal','alta','urgente')),
    tempo_estimado_horas DECIMAL(6,2),
    custo_estimado DECIMAL(12,2),
    data_limite_resolucao TIMESTAMP,
    resolvido_em TIMESTAMP,
    observacoes TEXT,
    fotos_adicionais JSONB DEFAULT '[]'::jsonb, -- URLs das fotos
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para defeitos
CREATE INDEX IF NOT EXISTS idx_defeitos_checklist ON defeitos(checklist_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_veiculo ON defeitos(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_status ON defeitos(status);
CREATE INDEX IF NOT EXISTS idx_defeitos_severidade ON defeitos(severidade);
CREATE INDEX IF NOT EXISTS idx_defeitos_prioridade ON defeitos(prioridade);
CREATE INDEX IF NOT EXISTS idx_defeitos_data_limite ON defeitos(data_limite_resolucao);
CREATE INDEX IF NOT EXISTS idx_defeitos_codigo ON defeitos(codigo);

-- Tabela de ordens de serviço melhorada
CREATE TABLE IF NOT EXISTS ordens_servico (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_os TEXT UNIQUE NOT NULL, -- Número da OS
    veiculo_id INT NOT NULL REFERENCES veiculos(id),
    defeito_id INT REFERENCES defeitos(id),
    tipo_servico TEXT NOT NULL CHECK (tipo_servico IN ('preventiva','corretiva','preditiva','emergencial')),
    descricao TEXT NOT NULL,
    servicos_executados TEXT,
    mecanico_responsavel TEXT,
    fornecedor_externo TEXT,
    local_execucao TEXT DEFAULT 'oficina_interna',
    abertura_dt TIMESTAMP NOT NULL DEFAULT NOW(),
    inicio_execucao_dt TIMESTAMP,
    previsao_conclusao_dt TIMESTAMP,
    conclusao_dt TIMESTAMP,
    encerramento_dt TIMESTAMP,
    custo_peca DECIMAL(12,2) DEFAULT 0,
    custo_mo DECIMAL(12,2) DEFAULT 0,
    custo_terceiros DECIMAL(12,2) DEFAULT 0,
    custo_total DECIMAL(12,2) GENERATED ALWAYS AS (custo_peca + custo_mo + custo_terceiros) STORED,
    km_execucao BIGINT,
    centro_custo TEXT,
    numero_nf TEXT, -- Nota fiscal das peças
    status TEXT NOT NULL DEFAULT 'aberta'
        CHECK (status IN ('aberta','aguardando_aprovacao','aprovada','em_execucao','aguardando_peca','concluida','fechada','cancelada')),
    observacoes TEXT,
    aprovado_por INT REFERENCES usuarios(id),
    aprovado_em TIMESTAMP,
    valor_aprovado DECIMAL(12,2),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    criado_por INT REFERENCES usuarios(id)
);

-- Índices para ordens de serviço
CREATE INDEX IF NOT EXISTS idx_os_veiculo ON ordens_servico(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_os_defeito ON ordens_servico(defeito_id);
CREATE INDEX IF NOT EXISTS idx_os_status ON ordens_servico(status);
CREATE INDEX IF NOT EXISTS idx_os_tipo ON ordens_servico(tipo_servico);
CREATE INDEX IF NOT EXISTS idx_os_data_abertura ON ordens_servico(abertura_dt);
CREATE INDEX IF NOT EXISTS idx_os_numero ON ordens_servico(numero_os);

-- Tabela de logs de auditoria
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    tabela TEXT NOT NULL,
    registro_id INT NOT NULL,
    operacao TEXT NOT NULL CHECK (operacao IN ('INSERT','UPDATE','DELETE')),
    dados_anteriores JSONB,
    dados_novos JSONB,
    usuario_id INT REFERENCES usuarios(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Índice composto para consultas frequentes
    INDEX (tabela, registro_id, timestamp DESC)
);

-- Tabela de sessões de sync (para controle offline)
CREATE TABLE IF NOT EXISTS sync_sessions (
    id SERIAL PRIMARY KEY,
    dispositivo_id TEXT NOT NULL,
    usuario_id INT NOT NULL REFERENCES usuarios(id),
    ultimo_sync TIMESTAMP NOT NULL DEFAULT NOW(),
    dados_pendentes JSONB DEFAULT '{}'::jsonb,
    versao_app TEXT,
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo','inativo','erro')),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_sync_dispositivo_usuario UNIQUE (dispositivo_id, usuario_id)
);

-- ==============================
-- VIEWS MATERIALIZADAS PARA PERFORMANCE
-- ==============================

-- View de summary de checklists
CREATE MATERIALIZED VIEW IF NOT EXISTS vw_checklist_summary AS
SELECT 
    DATE_TRUNC('day', c.dt_inicio) as data,
    c.tipo,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
    COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
    COUNT(*) FILTER (WHERE c.status = 'pendente') as pendentes,
    AVG(c.score_aprovacao) as score_medio,
    AVG(c.duracao_minutos) as duracao_media,
    COUNT(*) FILTER (WHERE c.tem_bloqueios) as com_bloqueios
FROM checklists c
WHERE c.dt_inicio >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', c.dt_inicio), c.tipo;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_checklist_summary ON vw_checklist_summary(data, tipo);

-- View de top itens reprovados
CREATE MATERIALIZED VIEW IF NOT EXISTS vw_top_itens_reprovados AS
SELECT 
    i.categoria,
    i.descricao,
    COUNT(*) as total_respostas,
    COUNT(*) FILTER (WHERE r.valor = 'nao_ok') as reprovacoes,
    ROUND(COUNT(*) FILTER (WHERE r.valor = 'nao_ok') * 100.0 / COUNT(*), 2) as taxa_reprovacao
FROM checklist_respostas r
JOIN checklist_itens i ON i.id = r.item_id  
JOIN checklists c ON c.id = r.checklist_id
WHERE c.dt_inicio >= NOW() - INTERVAL '30 days'
GROUP BY i.categoria, i.descricao
HAVING COUNT(*) >= 10 -- Mínimo de 10 respostas
ORDER BY taxa_reprovacao DESC;

-- View de performance por motorista
CREATE MATERIALIZED VIEW IF NOT EXISTS vw_motorista_performance AS
SELECT 
    m.id as motorista_id,
    m.nome,
    COUNT(c.id) as total_checklists,
    COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
    COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
    ROUND(COUNT(*) FILTER (WHERE c.status = 'aprovado') * 100.0 / COUNT(c.id), 2) as taxa_aprovacao,
    AVG(c.duracao_minutos) as tempo_medio_minutos,
    COUNT(*) FILTER (WHERE c.tem_bloqueios) as checklists_com_bloqueio
FROM motoristas m
LEFT JOIN checklists c ON c.motorista_id = m.id AND c.dt_inicio >= NOW() - INTERVAL '90 days'
WHERE m.ativo = TRUE
GROUP BY m.id, m.nome
HAVING COUNT(c.id) > 0;

-- Função para refresh automático das views materializadas
CREATE OR REPLACE FUNCTION refresh_materialized_views() 
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY vw_checklist_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY vw_top_itens_reprovados; 
    REFRESH MATERIALIZED VIEW CONCURRENTLY vw_motorista_performance;
END;
$$ LANGUAGE plpgsql;

-- ==============================
-- TRIGGERS DE AUDITORIA E AUTOMAÇÃO
-- ==============================

-- Função de auditoria genérica
CREATE OR REPLACE FUNCTION audit_trigger_function() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (tabela, registro_id, operacao, dados_anteriores, usuario_id)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD), NULL);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (tabela, registro_id, operacao, dados_anteriores, dados_novos, usuario_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW), NULL);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (tabela, registro_id, operacao, dados_novos, usuario_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), NULL);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualização automática de timestamps
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers de timestamp
CREATE TRIGGER trg_usuarios_timestamp BEFORE UPDATE ON usuarios 
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_veiculos_timestamp BEFORE UPDATE ON veiculos 
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_motoristas_timestamp BEFORE UPDATE ON motoristas 
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_viagens_timestamp BEFORE UPDATE ON viagens 
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Trigger para geração de códigos automáticos
CREATE OR REPLACE FUNCTION generate_codes() RETURNS trigger AS $$
BEGIN
    IF TG_TABLE_NAME = 'checklists' AND NEW.codigo IS NULL THEN
        NEW.codigo = 'CHK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                     LPAD(NEXTVAL('checklists_id_seq')::TEXT, 6, '0');
    ELSIF TG_TABLE_NAME = 'defeitos' AND NEW.codigo IS NULL THEN
        NEW.codigo = 'DEF-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                     LPAD(NEXTVAL('defeitos_id_seq')::TEXT, 6, '0');
    ELSIF TG_TABLE_NAME = 'ordens_servico' AND NEW.numero_os IS NULL THEN
        NEW.numero_os = 'OS-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                        LPAD(NEXTVAL('ordens_servico_id_seq')::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_checklists_codigo BEFORE INSERT ON checklists 
    FOR EACH ROW EXECUTE FUNCTION generate_codes();
CREATE TRIGGER trg_defeitos_codigo BEFORE INSERT ON defeitos 
    FOR EACH ROW EXECUTE FUNCTION generate_codes();
CREATE TRIGGER trg_os_numero BEFORE INSERT ON ordens_servico 
    FOR EACH ROW EXECUTE FUNCTION generate_codes();

-- Trigger para cálculo automático de métricas do checklist
CREATE OR REPLACE FUNCTION calculate_checklist_metrics() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Recalcular métricas do checklist
        WITH stats AS (
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE valor = 'ok') as ok_count,
                COUNT(*) FILTER (WHERE valor = 'nao_ok') as nok_count,
                COUNT(*) FILTER (WHERE valor = 'na') as na_count
            FROM checklist_respostas cr
            JOIN checklist_itens ci ON ci.id = cr.item_id
            WHERE cr.checklist_id = NEW.checklist_id
        ),
        bloqueios AS (
            SELECT COUNT(*) > 0 as tem_bloqueios
            FROM checklist_respostas cr
            JOIN checklist_itens ci ON ci.id = cr.item_id
            WHERE cr.checklist_id = NEW.checklist_id 
              AND ci.bloqueia_viagem = TRUE 
              AND cr.valor = 'nao_ok'
        )
        UPDATE checklists 
        SET 
            total_itens = stats.total,
            itens_ok = stats.ok_count,
            itens_nok = stats.nok_count,
            itens_na = stats.na_count,
            score_aprovacao = CASE 
                WHEN stats.total > 0 THEN ROUND(stats.ok_count * 100.0 / stats.total, 2)
                ELSE 0 
            END,
            tem_bloqueios = bloqueios.tem_bloqueios,
            atualizado_em = NOW()
        FROM stats, bloqueios
        WHERE id = NEW.checklist_id;
        
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_checklist_metrics AFTER INSERT OR UPDATE ON checklist_respostas 
    FOR EACH ROW EXECUTE FUNCTION calculate_checklist_metrics();

-- ==============================
-- ESTRUTURAS BASE PARA MÓDULOS FUTUROS
-- ==============================

-- Módulo 2: Manutenções (estrutura base)
CREATE TABLE IF NOT EXISTS manutencoes_programadas (
    id SERIAL PRIMARY KEY,
    veiculo_id INT REFERENCES veiculos(id),
    tipo TEXT CHECK (tipo IN ('preventiva','preditiva')),
    descricao TEXT,
    km_programado BIGINT,
    dias_programado INT,
    status TEXT DEFAULT 'programada',
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Módulo 3: Abastecimentos (estrutura base)
CREATE TABLE IF NOT EXISTS abastecimentos (
    id SERIAL PRIMARY KEY,
    veiculo_id INT REFERENCES veiculos(id),
    motorista_id INT REFERENCES motoristas(id),
    data_abastecimento TIMESTAMP DEFAULT NOW(),
    posto TEXT,
    litros DECIMAL(8,3),
    valor_total DECIMAL(10,2),
    km_abastecimento BIGINT,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Módulo 4: Despesas de viagem (estrutura base)
CREATE TABLE IF NOT EXISTS despesas_viagem (
    id SERIAL PRIMARY KEY,
    viagem_id INT REFERENCES viagens(id),
    motorista_id INT REFERENCES motoristas(id),
    tipo TEXT CHECK (tipo IN ('pedagio','combustivel','alimentacao','hospedagem','outros')),
    valor DECIMAL(10,2),
    data_despesa TIMESTAMP,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Criar usuário admin padrão (apenas se não existir)
INSERT INTO usuarios (nome, email, senha_hash, papel, ativo)
VALUES ('Administrador', 'admin@transpontual.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOufVvPkWJZddx1j0lVqNJ8H2K1aOVOIG', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- Comentários nas tabelas principais
COMMENT ON TABLE usuarios IS 'Usuários do sistema com controle de acesso';
COMMENT ON TABLE veiculos IS 'Cadastro de veículos da frota';
COMMENT ON TABLE motoristas IS 'Cadastro de motoristas e condutores';  
COMMENT ON TABLE checklists IS 'Registros de checklists executados';
COMMENT ON TABLE checklist_respostas IS 'Respostas individuais dos itens de checklist';
COMMENT ON TABLE defeitos IS 'Defeitos identificados durante checklists';
COMMENT ON TABLE ordens_servico IS 'Ordens de serviço para correção de defeitos';

-- Constraints adicionais de integridade
ALTER TABLE checklists ADD CONSTRAINT chk_checklist_datas 
    CHECK (dt_fim IS NULL OR dt_fim >= dt_inicio);

ALTER TABLE checklists ADD CONSTRAINT chk_checklist_scores 
    CHECK (score_aprovacao IS NULL OR (score_aprovacao >= 0 AND score_aprovacao <= 100));

ALTER TABLE ordens_servico ADD CONSTRAINT chk_os_datas 
    CHECK (conclusao_dt IS NULL OR conclusao_dt >= abertura_dt);
