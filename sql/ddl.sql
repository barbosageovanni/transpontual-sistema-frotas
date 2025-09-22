-- sql/ddl.sql
-- Schema completo do Sistema Transpontual
-- PostgreSQL 14+

-- ========== EXTENSÕES ==========
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ========== TABELAS PRINCIPAIS ==========

-- Usuários do sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    papel VARCHAR(20) NOT NULL CHECK (papel IN ('gestor','mecanico','motorista')),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_login TIMESTAMP,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Motoristas
CREATE TABLE IF NOT EXISTS motoristas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    cnh VARCHAR(20),
    categoria VARCHAR(5),
    validade_cnh DATE,
    telefone VARCHAR(20),
    endereco TEXT,
    cep VARCHAR(10),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    data_nascimento DATE,
    data_admissao DATE,
    usuario_id INTEGER REFERENCES usuarios(id),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Veículos
CREATE TABLE IF NOT EXISTS veiculos (
    id SERIAL PRIMARY KEY,
    placa VARCHAR(10) UNIQUE NOT NULL,
    renavam VARCHAR(20),
    chassi VARCHAR(30),
    ano INTEGER,
    modelo VARCHAR(100),
    marca VARCHAR(50),
    cor VARCHAR(30),
    tipo VARCHAR(20) CHECK (tipo IN ('carreta','cavalo','leve','utilitario','van')),
    categoria VARCHAR(10), -- A, B, C, D, E
    combustivel VARCHAR(20) DEFAULT 'diesel',
    km_atual BIGINT DEFAULT 0,
    capacidade_carga INTEGER, -- kg
    lugares INTEGER DEFAULT 2,
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo','manutencao','inativo','vendido')),
    proprietario VARCHAR(20) DEFAULT 'proprio' CHECK (proprietario IN ('proprio','terceiro','agregado')),
    valor_fipe DECIMAL(12,2),
    valor_seguro DECIMAL(12,2),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Viagens
CREATE TABLE IF NOT EXISTS viagens (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    motorista_id INTEGER NOT NULL REFERENCES motoristas(id),
    origem TEXT,
    destino TEXT,
    cliente VARCHAR(200),
    tipo_carga VARCHAR(100),
    peso_carga DECIMAL(8,2),
    valor_frete DECIMAL(10,2),
    data_partida TIMESTAMP,
    data_chegada_prevista TIMESTAMP,
    data_chegada_real TIMESTAMP,
    km_inicial BIGINT,
    km_final BIGINT,
    km_total INTEGER,
    status VARCHAR(20) DEFAULT 'planejada' CHECK (
        status IN ('planejada','em_andamento','finalizada','cancelada','bloqueada')
    ),
    observacoes TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 1: CHECKLIST VEICULAR ==========

-- Modelos de checklist (templates)
CREATE TABLE IF NOT EXISTS checklist_modelos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('pre','pos','extra')),
    categoria_veiculo VARCHAR(20), -- carreta, cavalo, leve
    versao INTEGER NOT NULL DEFAULT 1,
    descricao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_por INTEGER REFERENCES usuarios(id),
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Itens dos modelos de checklist
CREATE TABLE IF NOT EXISTS checklist_itens (
    id SERIAL PRIMARY KEY,
    modelo_id INTEGER NOT NULL REFERENCES checklist_modelos(id) ON DELETE CASCADE,
    ordem INTEGER NOT NULL,
    descricao VARCHAR(500) NOT NULL,
    categoria VARCHAR(50), -- freios, pneus, iluminacao, documentos, etc
    tipo_resposta VARCHAR(10) NOT NULL DEFAULT 'ok' CHECK (tipo_resposta IN ('ok','na','obs','foto')),
    severidade VARCHAR(10) NOT NULL DEFAULT 'media' CHECK (severidade IN ('baixa','media','alta','critica')),
    exige_foto BOOLEAN NOT NULL DEFAULT FALSE,
    bloqueia_viagem BOOLEAN NOT NULL DEFAULT FALSE,
    opcoes JSONB DEFAULT '[]'::jsonb, -- Lista de opções para defeitos específicos
    instrucoes TEXT, -- Instruções detalhadas para o item
    peso_score INTEGER DEFAULT 1, -- Peso para cálculo de score
    
    CONSTRAINT uk_checklist_item_ordem UNIQUE (modelo_id, ordem)
);

-- Checklists executados
CREATE TABLE IF NOT EXISTS checklists (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    viagem_id INTEGER REFERENCES viagens(id),
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    motorista_id INTEGER NOT NULL REFERENCES motoristas(id),
    modelo_id INTEGER NOT NULL REFERENCES checklist_modelos(id),
    
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('pre','pos','extra')),
    
    -- Dados de odômetro
    odometro_ini BIGINT,
    odometro_fim BIGINT,
    
    -- Geolocalização
    geo_inicio TEXT, -- JSON com lat, lng, address
    geo_fim TEXT,
    
    -- Controle de tempo
    dt_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    dt_fim TIMESTAMP,
    duracao_minutos INTEGER, -- Calculado automaticamente
    
    -- Status e controle
    status VARCHAR(20) NOT NULL DEFAULT 'pendente' CHECK (
        status IN ('pendente','em_andamento','aprovado','reprovado','cancelado')
    ),
    
    -- Dados finais
    assinatura_motorista TEXT, -- Base64 da assinatura digital
    observacoes_gerais TEXT,
    score_final INTEGER, -- Score calculado baseado nas respostas
    
    -- Auditoria
    ip_inicio INET,
    ip_fim INET,
    device_info JSONB, -- Informações do dispositivo
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Respostas dos checklists
CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    checklist_id INTEGER NOT NULL REFERENCES checklists(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES checklist_itens(id),
    
    valor VARCHAR(20) NOT NULL CHECK (valor IN ('ok','nao_ok','na')),
    observacao TEXT,
    opcao_defeito VARCHAR(200), -- Opção específica selecionada da lista
    foto_url TEXT, -- URL da foto anexada
    geo TEXT, -- Coordenadas GPS do momento da resposta
    
    dt TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uk_checklist_resposta UNIQUE (checklist_id, item_id)
);

-- ========== MÓDULO 2: MANUTENÇÃO E DEFEITOS ==========

-- Defeitos identificados
CREATE TABLE IF NOT EXISTS defeitos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    
    -- Origem do defeito
    checklist_id INTEGER NOT NULL REFERENCES checklists(id),
    item_id INTEGER NOT NULL REFERENCES checklist_itens(id),
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    
    -- Classificação
    categoria VARCHAR(50) NOT NULL DEFAULT 'geral',
    severidade VARCHAR(10) NOT NULL CHECK (severidade IN ('baixa','media','alta','critica')),
    prioridade VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (prioridade IN ('baixa','normal','alta','urgente')),
    
    -- Descrição
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NOT NULL,
    observacao TEXT,
    foto_urls TEXT, -- URLs das fotos, separadas por vírgula
    
    -- Status e controle
    status VARCHAR(20) NOT NULL DEFAULT 'identificado' CHECK (
        status IN ('identificado','aberto','em_andamento','aguardando_peca','resolvido','cancelado')
    ),
    
    -- Custos
    custo_estimado DECIMAL(10,2),
    custo_real DECIMAL(10,2),
    
    -- Datas
    identificado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    aberto_em TIMESTAMP,
    resolvido_em TIMESTAMP,
    prazo_resolucao TIMESTAMP,
    
    -- Responsáveis
    identificado_por INTEGER REFERENCES usuarios(id),
    responsavel_resolucao INTEGER REFERENCES usuarios(id),
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Ordens de serviço
CREATE TABLE IF NOT EXISTS ordens_servico (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(50) UNIQUE NOT NULL,
    
    -- Vinculação
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    defeito_id INTEGER REFERENCES defeitos(id),
    
    -- Tipo e classificação
    tipo VARCHAR(20) NOT NULL DEFAULT 'corretiva' CHECK (tipo IN ('preventiva','corretiva','preditiva','emergencial')),
    prioridade VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (prioridade IN ('baixa','normal','alta','urgente')),
    
    -- Descrição
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT NOT NULL,
    servicos_realizados TEXT,
    pecas_utilizadas TEXT,
    observacoes TEXT,
    
    -- Responsáveis
    responsavel_abertura VARCHAR(100),
    responsavel_execucao VARCHAR(100),
    mecanico_responsavel VARCHAR(100),
    aprovador VARCHAR(100),
    
    -- Controle de tempo
    abertura_dt TIMESTAMP NOT NULL DEFAULT NOW(),
    inicio_execucao_dt TIMESTAMP,
    conclusao_dt TIMESTAMP,
    aprovacao_dt TIMESTAMP,
    prazo_execucao TIMESTAMP,
    
    -- Custos detalhados
    custo_peca DECIMAL(10,2) DEFAULT 0,
    custo_mo DECIMAL(10,2) DEFAULT 0, -- mão de obra
    custo_terceiros DECIMAL(10,2) DEFAULT 0,
    custo_total DECIMAL(10,2) DEFAULT 0,
    
    -- Controle administrativo
    centro_custo VARCHAR(50),
    conta_contabil VARCHAR(20),
    fornecedor VARCHAR(200),
    nota_fiscal VARCHAR(50),
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'aberta' CHECK (
        status IN ('aberta','aprovada','em_execucao','aguardando_peca','finalizada','cancelada')
    ),
    
    -- Dados do veículo
    km_veiculo INTEGER, -- KM no momento da abertura
    
    -- Anexos e documentos
    anexos TEXT, -- URLs de anexos separadas por vírgula
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 3: COMBUSTÍVEL (ESTRUTURA BASE) ==========

CREATE TABLE IF NOT EXISTS abastecimentos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    motorista_id INTEGER NOT NULL REFERENCES motoristas(id),
    
    data_abastecimento TIMESTAMP NOT NULL DEFAULT NOW(),
    km_veiculo INTEGER,
    litros DECIMAL(8,2) NOT NULL,
    valor_litro DECIMAL(6,3) NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    
    tipo_combustivel VARCHAR(20) DEFAULT 'diesel',
    posto_nome VARCHAR(200),
    posto_cnpj VARCHAR(20),
    endereco TEXT,
    
    forma_pagamento VARCHAR(20), -- dinheiro, cartao, vale
    numero_cupom VARCHAR(50),
    numero_cartao VARCHAR(50),
    
    observacoes TEXT,
    foto_cupom_url TEXT,
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 4: DESPESAS (ESTRUTURA BASE) ==========

CREATE TABLE IF NOT EXISTS despesas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    viagem_id INTEGER REFERENCES viagens(id),
    veiculo_id INTEGER REFERENCES veiculos(id),
    motorista_id INTEGER NOT NULL REFERENCES motoristas(id),
    
    tipo VARCHAR(20) NOT NULL, -- pedagio, alimentacao, hospedagem, manutencao, outros
    categoria VARCHAR(50),
    descricao TEXT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    data_despesa TIMESTAMP NOT NULL,
    
    local TEXT,
    comprovante_url TEXT,
    numero_documento VARCHAR(50),
    
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente','aprovada','reprovada','paga')),
    observacoes TEXT,
    
    aprovado_por INTEGER REFERENCES usuarios(id),
    aprovado_em TIMESTAMP,
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 5: MULTAS (ESTRUTURA BASE) ==========

CREATE TABLE IF NOT EXISTS multas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    motorista_id INTEGER REFERENCES motoristas(id),
    
    numero_auto VARCHAR(50) UNIQUE,
    data_infracao TIMESTAMP NOT NULL,
    data_vencimento DATE,
    orgao_autuador VARCHAR(100),
    local_infracao TEXT,
    
    codigo_infracao VARCHAR(20),
    descricao_infracao TEXT NOT NULL,
    categoria VARCHAR(20), -- leve, media, grave, gravissima
    
    valor_original DECIMAL(10,2) NOT NULL,
    valor_desconto DECIMAL(10,2) DEFAULT 0,
    valor_juros DECIMAL(10,2) DEFAULT 0,
    valor_total DECIMAL(10,2) NOT NULL,
    
    pontos_cnh INTEGER DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'pendente' CHECK (
        status IN ('pendente','paga','em_recurso','cancelada','prescrita')
    ),
    
    observacoes TEXT,
    anexos TEXT,
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 6: PNEUS (ESTRUTURA BASE) ==========

CREATE TABLE IF NOT EXISTS pneus (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    numero_serie VARCHAR(100),
    
    marca VARCHAR(50),
    modelo VARCHAR(100),
    medida VARCHAR(20), -- 295/80R22.5
    tipo VARCHAR(20), -- radial, diagonal
    categoria VARCHAR(10), -- novo, recapado
    
    data_compra DATE,
    valor_compra DECIMAL(10,2),
    fornecedor VARCHAR(200),
    nota_fiscal VARCHAR(50),
    
    km_inicial INTEGER DEFAULT 0,
    km_atual INTEGER DEFAULT 0,
    km_total INTEGER DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'estoque' CHECK (
        status IN ('estoque','instalado','retirado','recapagem','descarte')
    ),
    
    veiculo_id INTEGER REFERENCES veiculos(id),
    posicao VARCHAR(20), -- dianteira_esquerda, traseira_direita_1, etc
    data_instalacao TIMESTAMP,
    data_retirada TIMESTAMP,
    
    observacoes TEXT,
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 7: DOCUMENTOS (ESTRUTURA BASE) ==========

CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    
    entidade_tipo VARCHAR(20) NOT NULL CHECK (entidade_tipo IN ('veiculo','motorista','empresa')),
    entidade_id INTEGER NOT NULL, -- ID do veículo, motorista, etc
    
    tipo_documento VARCHAR(50) NOT NULL, -- crlv, cnh, seguro, licenca_operacao
    numero_documento VARCHAR(100),
    orgao_emissor VARCHAR(100),
    
    data_emissao DATE,
    data_vencimento DATE,
    data_renovacao DATE,
    
    status VARCHAR(20) DEFAULT 'vigente' CHECK (
        status IN ('vigente','vencido','vencendo','renovado','cancelado')
    ),
    
    valor DECIMAL(10,2), -- Valor pago pelo documento
    observacoes TEXT,
    arquivo_url TEXT,
    
    alerta_vencimento BOOLEAN DEFAULT TRUE,
    dias_alerta INTEGER DEFAULT 30,
    
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== MÓDULO 8: AUDITORIA E LOGS ==========

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    acao VARCHAR(50) NOT NULL, -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    tabela VARCHAR(50),
    registro_id INTEGER,
    dados_anteriores JSONB,
    dados_novos JSONB,
    ip INET,
    user_agent TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ========== ÍNDICES ==========

-- Usuários
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON usuarios(papel);
CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(ativo);

-- Motoristas
CREATE INDEX IF NOT EXISTS idx_motoristas_nome ON motoristas(nome);
CREATE INDEX IF NOT EXISTS idx_motoristas_cnh ON motoristas(cnh);
CREATE INDEX IF NOT EXISTS idx_motoristas_validade_cnh ON motoristas(validade_cnh);
CREATE INDEX IF NOT EXISTS idx_motoristas_ativo ON motoristas(ativo);
CREATE INDEX IF NOT EXISTS idx_motoristas_usuario_id ON motoristas(usuario_id);

-- Veículos
CREATE INDEX IF NOT EXISTS idx_veiculos_placa ON veiculos(placa);
CREATE INDEX IF NOT EXISTS idx_veiculos_tipo ON veiculos(tipo);
CREATE INDEX IF NOT EXISTS idx_veiculos_status ON veiculos(status);
CREATE INDEX IF NOT EXISTS idx_veiculos_ativo ON veiculos(ativo);

-- Viagens
CREATE INDEX IF NOT EXISTS idx_viagens_veiculo_id ON viagens(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_viagens_motorista_id ON viagens(motorista_id);
CREATE INDEX IF NOT EXISTS idx_viagens_status ON viagens(status);
CREATE INDEX IF NOT EXISTS idx_viagens_data_partida ON viagens(data_partida);

-- Checklists
CREATE INDEX IF NOT EXISTS idx_checklists_codigo ON checklists(codigo);
CREATE INDEX IF NOT EXISTS idx_checklists_veiculo_id ON checklists(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_checklists_motorista_id ON checklists(motorista_id);
CREATE INDEX IF NOT EXISTS idx_checklists_modelo_id ON checklists(modelo_id);
CREATE INDEX IF NOT EXISTS idx_checklists_status ON checklists(status);
CREATE INDEX IF NOT EXISTS idx_checklists_tipo ON checklists(tipo);
CREATE INDEX IF NOT EXISTS idx_checklists_dt_inicio ON checklists(dt_inicio);
CREATE INDEX IF NOT EXISTS idx_checklists_dt_fim ON checklists(dt_fim);

-- Checklist Respostas
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_checklist_id ON checklist_respostas(checklist_id);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_item_id ON checklist_respostas(item_id);
CREATE INDEX IF NOT EXISTS idx_checklist_respostas_valor ON checklist_respostas(valor);

-- Defeitos
CREATE INDEX IF NOT EXISTS idx_defeitos_codigo ON defeitos(codigo);
CREATE INDEX IF NOT EXISTS idx_defeitos_veiculo_id ON defeitos(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_checklist_id ON defeitos(checklist_id);
CREATE INDEX IF NOT EXISTS idx_defeitos_status ON defeitos(status);
CREATE INDEX IF NOT EXISTS idx_defeitos_severidade ON defeitos(severidade);
CREATE INDEX IF NOT EXISTS idx_defeitos_identificado_em ON defeitos(identificado_em);

-- Ordens de Serviço
CREATE INDEX IF NOT EXISTS idx_ordens_servico_numero ON ordens_servico(numero);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_veiculo_id ON ordens_servico(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_defeito_id ON ordens_servico(defeito_id);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_status ON ordens_servico(status);
CREATE INDEX IF NOT EXISTS idx_ordens_servico_abertura_dt ON ordens_servico(abertura_dt);

-- Auditoria
CREATE INDEX IF NOT EXISTS idx_audit_logs_usuario_id ON audit_logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_acao ON audit_logs(acao);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tabela ON audit_logs(tabela);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Índices compostos para performance
CREATE INDEX IF NOT EXISTS idx_checklists_veiculo_status ON checklists(veiculo_id, status);
CREATE INDEX IF NOT EXISTS idx_checklists_data_status ON checklists(dt_inicio, status);
CREATE INDEX IF NOT EXISTS idx_defeitos_veiculo_status ON defeitos(veiculo_id, status);
CREATE INDEX IF NOT EXISTS idx_os_veiculo_status ON ordens_servico(veiculo_id, status);

-- ========== TRIGGERS ==========

-- Trigger para atualizar campo 'atualizado_em'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger em todas as tabelas com campo 'atualizado_em'
CREATE TRIGGER trigger_usuarios_updated_at BEFORE UPDATE ON usuarios 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_motoristas_updated_at BEFORE UPDATE ON motoristas 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_veiculos_updated_at BEFORE UPDATE ON veiculos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_viagens_updated_at BEFORE UPDATE ON viagens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_checklists_updated_at BEFORE UPDATE ON checklists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_defeitos_updated_at BEFORE UPDATE ON defeitos 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_ordens_servico_updated_at BEFORE UPDATE ON ordens_servico 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para gerar códigos automáticos
CREATE OR REPLACE FUNCTION generate_codigo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.codigo IS NULL OR NEW.codigo = '' THEN
        NEW.codigo := TG_ARGV[0] || '-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(NEW.id::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ========== VIEWS MATERIALIZADAS ==========

-- View resumo de checklists
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_checklist_summary AS
SELECT 
    DATE(c.dt_inicio) as data,
    COUNT(*) as total_checklists,
    COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
    COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
    COUNT(*) FILTER (WHERE c.status IN ('pendente', 'em_andamento')) as pendentes,
    ROUND(AVG(c.duracao_minutos), 1) as tempo_medio_minutos,
    COUNT(DISTINCT c.veiculo_id) as veiculos_distintos,
    COUNT(DISTINCT c.motorista_id) as motoristas_distintos
FROM checklists c
WHERE c.dt_inicio >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(c.dt_inicio)
ORDER BY data DESC;

CREATE UNIQUE INDEX ON mv_checklist_summary (data);

-- View top itens com problemas
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_problemas AS
SELECT 
    ci.id,
    ci.descricao,
    ci.categoria,
    ci.severidade,
    COUNT(cr.id) as total_nao_ok,
    COUNT(cr.id) * 100.0 / NULLIF(
        (SELECT COUNT(*) FROM checklist_respostas cr2 
         JOIN checklists c2 ON c2.id = cr2.checklist_id
         WHERE cr2.item_id = ci.id 
         AND c2.dt_inicio >= CURRENT_DATE - INTERVAL '30 days'), 0
    ) as percentual_nao_ok
FROM checklist_itens ci
JOIN checklist_respostas cr ON cr.item_id = ci.id
JOIN checklists c ON c.id = cr.checklist_id
WHERE cr.valor = 'nao_ok'
AND c.dt_inicio >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ci.id, ci.descricao, ci.categoria, ci.severidade
HAVING COUNT(cr.id) > 0
ORDER BY total_nao_ok DESC, percentual_nao_ok DESC;

-- View performance de motoristas
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_motorista_performance AS
SELECT 
    m.id,
    m.nome,
    COUNT(c.id) as total_checklists,
    COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
    COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
    ROUND(COUNT(*) FILTER (WHERE c.status = 'aprovado') * 100.0 / NULLIF(COUNT(c.id), 0), 1) as taxa_aprovacao,
    ROUND(AVG(c.duracao_minutos), 1) as tempo_medio_minutos,
    COUNT(d.id) as defeitos_identificados
FROM motoristas m
LEFT JOIN checklists c ON c.motorista_id = m.id AND c.dt_inicio >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN defeitos d ON d.checklist_id = c.id
WHERE m.ativo = true
GROUP BY m.id, m.nome
HAVING COUNT(c.id) > 0
ORDER BY taxa_aprovacao DESC, tempo_medio_minutos ASC;

-- Função para refresh das views materializadas
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_checklist_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_problemas;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_motorista_performance;
END;
$$ LANGUAGE plpgsql;