-- ========== DADOS DE EXEMPLO PARA SISTEMA DE MANUTENÇÃO ==========
-- Baseado nos veículos reais da empresa

-- ========== 1. TIPOS DE EQUIPAMENTO ==========
INSERT INTO tipos_equipamento (nome, categoria, descricao) VALUES
('CAVALO TRAÇÃO 6X2 3 EIXOS', 'VEICULAR', 'Caminhão trator pesado para longas distâncias'),
('TRUCK', 'VEICULAR', 'Caminhão truck para cargas médias'),
('CARRETA SIMPLES', 'VEICULAR', 'Carreta semi-reboque simples'),
('BITRUCK', 'VEICULAR', 'Caminhão bitruck para cargas urbanas'),
('VAN', 'VEICULAR', 'Van para cargas leves e entregas urbanas')
ON CONFLICT (nome) DO NOTHING;

-- ========== 2. PLANOS DE MANUTENÇÃO ==========
INSERT INTO planos_manutencao (codigo, descricao, ativo) VALUES
('PLAN-001', 'MANUTENÇÃO - CAVALO MECÂNICO', true),
('PLAN-002', 'MANUTENÇÃO - TRUCK', true),
('PLAN-003', 'MANUTENÇÃO - CARRETA SIMPLES', true),
('PLAN-004', 'MANUTENÇÃO - TOCO', true),
('PLAN-005', 'MANUTENÇÃO - EMPILHADEIRA', true)
ON CONFLICT (codigo) DO NOTHING;

-- ========== 3. RELAÇÃO PLANOS x TIPOS DE EQUIPAMENTO ==========
INSERT INTO planos_tipos_equipamento (plano_id, tipo_equipamento_id)
SELECT p.id, t.id
FROM planos_manutencao p, tipos_equipamento t
WHERE (p.codigo = 'PLAN-001' AND t.nome = 'CAVALO TRAÇÃO 6X2 3 EIXOS')
   OR (p.codigo = 'PLAN-002' AND t.nome = 'TRUCK')
   OR (p.codigo = 'PLAN-003' AND t.nome = 'CARRETA SIMPLES')
   OR (p.codigo = 'PLAN-004' AND t.nome = 'BITRUCK')
   OR (p.codigo = 'PLAN-005' AND t.nome = 'VAN')
ON CONFLICT (plano_id, tipo_equipamento_id) DO NOTHING;

-- ========== 4. ITENS DOS PLANOS - CAVALO TRAÇÃO ==========
WITH plano_cavalo AS (SELECT id FROM planos_manutencao WHERE codigo = 'PLAN-001')
INSERT INTO planos_manutencao_itens (plano_id, descricao, tipo, categoria, controle_por, intervalo_valor, km_inicial, alerta_antecipacao, ordem) VALUES
((SELECT id FROM plano_cavalo), 'TROCA DE ÓLEO DO DIFERENCIAL', 'Troca', 'Transmissão', 'km', 60000, 0, 5000, 1),
((SELECT id FROM plano_cavalo), 'TROCA DE FILTRO DE ÓLEO', 'Troca', 'Motor', 'km', 30000, 0, 3000, 2),
((SELECT id FROM plano_cavalo), 'TROCA DE ÓLEO DO MOTOR', 'Troca', 'Motor', 'km', 15000, 0, 1000, 3),
((SELECT id FROM plano_cavalo), 'REVISÃO DO SISTEMA DE FREIOS', 'Revisão', 'Freios', 'km', 40000, 0, 2000, 4),
((SELECT id FROM plano_cavalo), 'TROCA DE FILTRO DE AR', 'Troca', 'Motor', 'km', 25000, 0, 2000, 5),
((SELECT id FROM plano_cavalo), 'REVISÃO DA CAIXA DE DIREÇÃO', 'Revisão', 'Direção', 'km', 50000, 0, 3000, 6),
((SELECT id FROM plano_cavalo), 'TROCA DE FILTRO DE COMBUSTÍVEL', 'Troca', 'Motor', 'km', 30000, 0, 2000, 7),
((SELECT id FROM plano_cavalo), 'INSPEÇÃO DOS PNEUS', 'Inspeção', 'Rodagem', 'km', 10000, 0, 500, 8)
ON CONFLICT (plano_id, ordem) DO NOTHING;

-- ========== 5. ITENS DOS PLANOS - TRUCK ==========
WITH plano_truck AS (SELECT id FROM planos_manutencao WHERE codigo = 'PLAN-002')
INSERT INTO planos_manutencao_itens (plano_id, descricao, tipo, categoria, controle_por, intervalo_valor, km_inicial, alerta_antecipacao, ordem) VALUES
((SELECT id FROM plano_truck), 'TROCA DE ÓLEO DO MOTOR', 'Troca', 'Motor', 'km', 15000, 0, 1000, 1),
((SELECT id FROM plano_truck), 'TROCA DE FILTROS', 'Troca', 'Motor', 'km', 15000, 0, 1000, 2),
((SELECT id FROM plano_truck), 'REVISÃO GERAL', 'Revisão', 'Geral', 'km', 50000, 0, 3000, 3),
((SELECT id FROM plano_truck), 'TROCA DE ÓLEO DO DIFERENCIAL', 'Troca', 'Transmissão', 'km', 45000, 0, 3000, 4),
((SELECT id FROM plano_truck), 'REVISÃO DOS FREIOS', 'Revisão', 'Freios', 'km', 30000, 0, 2000, 5)
ON CONFLICT (plano_id, ordem) DO NOTHING;

-- ========== 6. VINCULAR VEÍCULOS EXISTENTES AOS PLANOS ==========
-- Primeiro, vamos verificar alguns veículos existentes e criar tipos se necessário

-- Inserir alguns veículos de exemplo se não existirem
INSERT INTO veiculos (placa, modelo, marca, tipo, km_atual, status) VALUES
('XAV-0000', 'CAVALO TRAÇÃO 6X2 3 EIXOS', 'SCANIA', 'cavalo', 125000, 'ativo'),
('XAV-0001', 'CAVALO TRAÇÃO 6X2 3 EIXOS', 'SCANIA', 'cavalo', 89000, 'ativo'),
('XAV-0002', 'CAVALO TRAÇÃO 6X2 3 EIXOS', 'SCANIA', 'cavalo', 156000, 'ativo'),
('ATA-4352', 'CONSTELLATION', 'VOLKSWAGEN', 'cavalo', 98000, 'ativo'),
('MAR-L001', 'TRUCK', 'MERCEDES', 'cavalo', 76000, 'ativo')
ON CONFLICT (placa) DO NOTHING;

-- Vincular veículos aos planos baseado no tipo
WITH vinculacoes AS (
    SELECT
        v.id as veiculo_id,
        CASE
            WHEN v.modelo LIKE '%CAVALO%' OR v.modelo LIKE '%CONSTELLATION%'
            THEN (SELECT id FROM planos_manutencao WHERE codigo = 'PLAN-001')
            WHEN v.modelo LIKE '%TRUCK%'
            THEN (SELECT id FROM planos_manutencao WHERE codigo = 'PLAN-002')
            ELSE (SELECT id FROM planos_manutencao WHERE codigo = 'PLAN-001')
        END as plano_id,
        CASE
            WHEN v.modelo LIKE '%CAVALO%' OR v.modelo LIKE '%CONSTELLATION%'
            THEN (SELECT id FROM tipos_equipamento WHERE nome = 'CAVALO TRAÇÃO 6X2 3 EIXOS')
            WHEN v.modelo LIKE '%TRUCK%'
            THEN (SELECT id FROM tipos_equipamento WHERE nome = 'TRUCK')
            ELSE (SELECT id FROM tipos_equipamento WHERE nome = 'CAVALO TRAÇÃO 6X2 3 EIXOS')
        END as tipo_equipamento_id,
        v.km_atual
    FROM veiculos v
    WHERE v.ativo = true
    AND v.placa IN ('XAV-0000', 'XAV-0001', 'XAV-0002', 'ATA-4352', 'MAR-L001')
)
INSERT INTO veiculos_planos_manutencao (veiculo_id, plano_id, tipo_equipamento_id, km_inicio)
SELECT veiculo_id, plano_id, tipo_equipamento_id, km_atual
FROM vinculacoes
WHERE plano_id IS NOT NULL
ON CONFLICT (veiculo_id, plano_id) DO NOTHING;

-- ========== 7. INICIALIZAR CONTROLE DE MANUTENÇÕES ==========
-- Criar registros de controle para todos os itens de planos vinculados
WITH controles AS (
    SELECT DISTINCT
        vpm.veiculo_id,
        pmi.id as plano_item_id,
        v.km_atual,
        pmi.intervalo_valor,
        pmi.km_inicial
    FROM veiculos_planos_manutencao vpm
    JOIN planos_manutencao_itens pmi ON pmi.plano_id = vpm.plano_id
    JOIN veiculos v ON v.id = vpm.veiculo_id
    WHERE vpm.ativo = true
    AND pmi.ativo = true
)
INSERT INTO manutencoes_controle (
    veiculo_id,
    plano_item_id,
    km_ultima_manutencao,
    km_proxima_manutencao,
    status
)
SELECT
    veiculo_id,
    plano_item_id,
    km_inicial,
    km_inicial + intervalo_valor,
    CASE
        WHEN km_atual >= (km_inicial + intervalo_valor) THEN 'vencida'
        WHEN km_atual >= (km_inicial + intervalo_valor - 3000) THEN 'vencendo'
        ELSE 'em_dia'
    END
FROM controles
ON CONFLICT (veiculo_id, plano_item_id) DO NOTHING;

-- ========== 8. HISTÓRICO DE ODÔMETRO ==========
-- Inserir algumas leituras de exemplo para demonstrar o funcionamento
INSERT INTO historico_odometro (veiculo_id, km_atual, fonte, observacoes, data_leitura) VALUES
((SELECT id FROM veiculos WHERE placa = 'XAV-0000'), 125000, 'manual', 'Leitura inicial do sistema', NOW() - INTERVAL '1 day'),
((SELECT id FROM veiculos WHERE placa = 'XAV-0001'), 89000, 'manual', 'Leitura inicial do sistema', NOW() - INTERVAL '1 day'),
((SELECT id FROM veiculos WHERE placa = 'XAV-0002'), 156000, 'manual', 'Leitura inicial do sistema', NOW() - INTERVAL '1 day'),
((SELECT id FROM veiculos WHERE placa = 'ATA-4352'), 98000, 'manual', 'Leitura inicial do sistema', NOW() - INTERVAL '1 day'),
((SELECT id FROM veiculos WHERE placa = 'MAR-L001'), 76000, 'manual', 'Leitura inicial do sistema', NOW() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;

-- ========== 9. HISTÓRICO DE MANUTENÇÕES ==========
-- Inserir algumas manutenções realizadas para demonstrar
INSERT INTO manutencoes_historico (
    veiculo_id, plano_item_id, descricao, tipo_manutencao,
    data_realizacao, km_realizacao, custo_total, responsavel_execucao, status
) VALUES
((SELECT id FROM veiculos WHERE placa = 'XAV-0000'),
 (SELECT pmi.id FROM planos_manutencao_itens pmi
  JOIN planos_manutencao pm ON pm.id = pmi.plano_id
  WHERE pm.codigo = 'PLAN-001' AND pmi.descricao = 'TROCA DE ÓLEO DO MOTOR'),
 'Troca de óleo do motor - Óleo 15W40', 'preventiva',
 CURRENT_DATE - INTERVAL '30 days', 110000, 350.00, 'João Silva - Mecânico', 'concluida'),

((SELECT id FROM veiculos WHERE placa = 'ATA-4352'),
 (SELECT pmi.id FROM planos_manutencao_itens pmi
  JOIN planos_manutencao pm ON pm.id = pmi.plano_id
  WHERE pm.codigo = 'PLAN-001' AND pmi.descricao = 'TROCA DE FILTROS'),
 'Troca de filtros de ar e combustível', 'preventiva',
 CURRENT_DATE - INTERVAL '15 days', 85000, 180.00, 'Carlos Santos - Mecânico', 'concluida')
ON CONFLICT DO NOTHING;

-- ========== 10. DADOS DE MULTAS ==========
-- Atualizar algumas multas existentes com novos campos
UPDATE multas SET
    responsabilidade = 'condutor',
    situacao = 'confirmada'
WHERE responsabilidade IS NULL;

-- Inserir algumas multas de exemplo se não existirem
INSERT INTO multas (
    codigo, veiculo_id, motorista_id, numero_auto, data_infracao,
    descricao_infracao, categoria, valor_original, valor_total,
    pontos_cnh, status, responsabilidade, situacao
) VALUES
('MLT-001', (SELECT id FROM veiculos WHERE placa = 'XAV-0000'),
 (SELECT id FROM motoristas LIMIT 1), 'AUTO123456',
 CURRENT_DATE - INTERVAL '30 days',
 'Excesso de velocidade em rodovia', 'gravissima', 880.41, 880.41,
 7, 'pendente', 'condutor', 'confirmada'),

('MLT-002', (SELECT id FROM veiculos WHERE placa = 'ATA-4352'),
 (SELECT id FROM motoristas LIMIT 1), 'AUTO789012',
 CURRENT_DATE - INTERVAL '45 days',
 'Estacionamento irregular', 'media', 195.23, 195.23,
 4, 'paga', 'empresa', 'confirmada'),

('MLT-003', (SELECT id FROM veiculos WHERE placa = 'MAR-L001'),
 (SELECT id FROM motoristas LIMIT 1), 'AUTO345678',
 CURRENT_DATE - INTERVAL '60 days',
 'Transitar em faixa exclusiva', 'grave', 293.47, 293.47,
 5, 'em_recurso', 'condutor', 'recorrida')
ON CONFLICT (codigo) DO NOTHING;

-- ========== 11. GERAR ALERTAS AUTOMÁTICOS ==========
-- Executar função para gerar alertas baseados no estado atual
SELECT gerar_alertas_manutencao();

-- ========== 12. FUNÇÃO PARA SIMULAR ATUALIZAÇÕES DE KM ==========
-- Esta função pode ser usada para simular viagens e atualizações de odômetro
CREATE OR REPLACE FUNCTION simular_viagem(
    p_placa VARCHAR(10),
    p_km_adicional INTEGER,
    p_observacao TEXT DEFAULT 'Viagem simulada'
)
RETURNS TEXT AS $$
DECLARE
    v_veiculo_id INTEGER;
    v_km_atual BIGINT;
    v_novo_km BIGINT;
    v_resultado TEXT;
BEGIN
    -- Buscar veículo
    SELECT id, km_atual INTO v_veiculo_id, v_km_atual
    FROM veiculos
    WHERE placa = p_placa;

    IF v_veiculo_id IS NULL THEN
        RETURN 'Veículo não encontrado: ' || p_placa;
    END IF;

    -- Calcular novo km
    v_novo_km := v_km_atual + p_km_adicional;

    -- Inserir nova leitura
    PERFORM inserir_leitura_odometro(
        v_veiculo_id,
        v_novo_km,
        'manual',
        NULL,
        p_observacao,
        NULL
    );

    -- Regenerar alertas
    PERFORM gerar_alertas_manutencao();

    v_resultado := 'Veículo ' || p_placa || ': ' || v_km_atual || ' -> ' || v_novo_km || ' km';

    RETURN v_resultado;
END;
$$ LANGUAGE plpgsql;

-- ========== EXEMPLOS DE USO ==========
/*
-- Para simular uma viagem de 500km no veículo XAV-0000:
SELECT simular_viagem('XAV-0000', 500, 'Viagem São Paulo - Rio de Janeiro');

-- Para verificar alertas de manutenção:
SELECT * FROM v_alertas_manutencao;

-- Para verificar previsão de manutenções:
SELECT * FROM v_previsao_manutencoes LIMIT 10;

-- Para ver histórico de km de um veículo:
SELECT * FROM historico_odometro
WHERE veiculo_id = (SELECT id FROM veiculos WHERE placa = 'XAV-0000')
ORDER BY data_leitura DESC;
*/