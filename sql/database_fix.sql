-- ===============================================
-- CORREÇÃO DA ESTRUTURA DO BANCO TRANSPONTUAL
-- ===============================================

-- Verificar e corrigir estrutura da tabela comprovantes
DO $$
BEGIN
    -- Verificar se a tabela existe e tem a estrutura correta
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'comprovantes' AND table_schema = 'public'
    ) THEN
        -- Criar tabela comprovantes se não existir
        CREATE TABLE comprovantes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            nome_arquivo VARCHAR(255) NOT NULL,
            caminho_arquivo VARCHAR(500) NOT NULL,
            hash_arquivo VARCHAR(64) UNIQUE NOT NULL,
            tamanho_arquivo BIGINT,
            tipo_arquivo VARCHAR(10) DEFAULT 'PDF',
            status VARCHAR(20) DEFAULT 'UPLOADED' CHECK (status IN ('UPLOADED', 'PROCESSING', 'PROCESSED', 'ERROR', 'DUPLICATE')),
            banco_origem VARCHAR(50),
            tipo_documento VARCHAR(30),
            erro_processamento TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        );
        
        RAISE NOTICE 'Tabela comprovantes criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela comprovantes já existe';
    END IF;
    
    -- Verificar se a coluna usuario_id existe (e remover se existir)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'comprovantes' 
        AND column_name = 'usuario_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE comprovantes DROP COLUMN usuario_id;
        RAISE NOTICE 'Coluna usuario_id removida da tabela comprovantes';
    END IF;
    
    -- Verificar se a coluna usuario_upload_id existe (e remover se existir)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'comprovantes' 
        AND column_name = 'usuario_upload_id'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE comprovantes DROP COLUMN usuario_upload_id;
        RAISE NOTICE 'Coluna usuario_upload_id removida da tabela comprovantes';
    END IF;
    
END $$;

-- ===============================================
-- VERIFICAR E CORRIGIR TABELA TRANSACOES
-- ===============================================

DO $$
BEGIN
    -- Verificar se a tabela transacoes existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'transacoes' AND table_schema = 'public'
    ) THEN
        -- Criar tabela transacoes se não existir
        CREATE TABLE transacoes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            comprovante_id UUID REFERENCES comprovantes(id) ON DELETE CASCADE,
            data_transacao DATE NOT NULL,
            data_vencimento DATE,
            descricao TEXT NOT NULL,
            valor DECIMAL(15,2) NOT NULL,
            tipo_transacao VARCHAR(20) DEFAULT 'DEBITO' CHECK (tipo_transacao IN ('DEBITO', 'CREDITO')),
            
            -- Dados do comprovante
            banco VARCHAR(50),
            agencia VARCHAR(10),
            conta VARCHAR(20),
            documento VARCHAR(100),
            
            -- Identificação do beneficiário/pagador
            beneficiario VARCHAR(200),
            cnpj_cpf_beneficiario VARCHAR(18),
            
            -- Classificação
            centro_custo_id INTEGER REFERENCES centros_custo(id),
            fornecedor_id INTEGER REFERENCES fornecedores(id),
            classificacao_automatica BOOLEAN DEFAULT false,
            classificacao_manual BOOLEAN DEFAULT false,
            
            -- Conciliação
            conciliado BOOLEAN DEFAULT false,
            data_conciliacao TIMESTAMP,
            usuario_conciliacao UUID REFERENCES usuarios(id),
            observacoes_conciliacao TEXT,
            
            -- Auditoria
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by UUID REFERENCES usuarios(id),
            updated_by UUID REFERENCES usuarios(id)
        );
        
        RAISE NOTICE 'Tabela transacoes criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela transacoes já existe';
    END IF;
END $$;

-- ===============================================
-- VERIFICAR E CORRIGIR OUTRAS TABELAS
-- ===============================================

-- Tabela usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    perfil VARCHAR(50) DEFAULT 'USER' CHECK (perfil IN ('ADMIN', 'USER', 'VIEWER')),
    ativo BOOLEAN DEFAULT true,
    ultimo_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela centros_custo
CREATE TABLE IF NOT EXISTS centros_custo (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(50) NOT NULL,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela fornecedores
CREATE TABLE IF NOT EXISTS fornecedores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    documento VARCHAR(20),
    tipo_documento VARCHAR(10) CHECK (tipo_documento IN ('CPF', 'CNPJ')),
    banco VARCHAR(100),
    agencia VARCHAR(10),
    conta VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================================
-- CRIAR ÍNDICES PARA PERFORMANCE
-- ===============================================

-- Índices para comprovantes
CREATE INDEX IF NOT EXISTS idx_comprovantes_hash ON comprovantes(hash_arquivo);
CREATE INDEX IF NOT EXISTS idx_comprovantes_status ON comprovantes(status);
CREATE INDEX IF NOT EXISTS idx_comprovantes_created_at ON comprovantes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comprovantes_banco ON comprovantes(banco_origem);

-- Índices para transacoes
CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes(data_transacao DESC);
CREATE INDEX IF NOT EXISTS idx_transacoes_valor ON transacoes(valor DESC);
CREATE INDEX IF NOT EXISTS idx_transacoes_centro_custo ON transacoes(centro_custo_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_beneficiario ON transacoes USING gin(beneficiario gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_transacoes_comprovante ON transacoes(comprovante_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_conciliado ON transacoes(conciliado);

-- ===============================================
-- INSERIR DADOS BÁSICOS
-- ===============================================

-- Usuário administrador padrão
INSERT INTO usuarios (email, senha, nome, perfil) 
VALUES ('admin@transpontual.com', 'admin123', 'Administrador', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- Centros de custo básicos
INSERT INTO centros_custo (codigo, nome, categoria) VALUES
('OP001', 'Operacional - Combustível', 'OPERACIONAL'),
('OP002', 'Operacional - Manutenção', 'OPERACIONAL'),
('OP003', 'Operacional - Pedágios', 'OPERACIONAL'),
('FP001', 'Folha de Pagamento - Motoristas', 'FOLHA_PAGAMENTO'),
('FP002', 'Folha de Pagamento - Administrativo', 'FOLHA_PAGAMENTO'),
('AD001', 'Administrativo - Escritório', 'ADMINISTRATIVO'),
('AD002', 'Administrativo - Marketing', 'ADMINISTRATIVO'),
('TR001', 'Tributário - Impostos', 'TRIBUTARIO'),
('FN001', 'Financeiro - Empréstimos', 'FINANCEIRO')
ON CONFLICT (codigo) DO NOTHING;

-- ===============================================
-- VERIFICAÇÕES FINAIS
-- ===============================================

-- Verificar estrutura final
DO $$
DECLARE
    comp_count INTEGER;
    trans_count INTEGER;
    user_count INTEGER;
    centro_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO comp_count FROM information_schema.tables WHERE table_name = 'comprovantes';
    SELECT COUNT(*) INTO trans_count FROM information_schema.tables WHERE table_name = 'transacoes';
    SELECT COUNT(*) INTO user_count FROM information_schema.tables WHERE table_name = 'usuarios';
    SELECT COUNT(*) INTO centro_count FROM information_schema.tables WHERE table_name = 'centros_custo';
    
    RAISE NOTICE '=== VERIFICAÇÃO FINAL ===';
    RAISE NOTICE 'Tabela comprovantes: %', CASE WHEN comp_count > 0 THEN 'OK' ELSE 'ERRO' END;
    RAISE NOTICE 'Tabela transacoes: %', CASE WHEN trans_count > 0 THEN 'OK' ELSE 'ERRO' END;
    RAISE NOTICE 'Tabela usuarios: %', CASE WHEN user_count > 0 THEN 'OK' ELSE 'ERRO' END;
    RAISE NOTICE 'Tabela centros_custo: %', CASE WHEN centro_count > 0 THEN 'OK' ELSE 'ERRO' END;
    
    -- Verificar dados básicos
    SELECT COUNT(*) INTO user_count FROM usuarios WHERE email = 'admin@transpontual.com';
    SELECT COUNT(*) INTO centro_count FROM centros_custo;
    
    RAISE NOTICE 'Usuário admin: %', CASE WHEN user_count > 0 THEN 'OK' ELSE 'ERRO' END;
    RAISE NOTICE 'Centros de custo: % registros', centro_count;
    
    RAISE NOTICE '=== CORREÇÃO CONCLUÍDA ===';
END $$;