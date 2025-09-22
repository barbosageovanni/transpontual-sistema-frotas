-- ==============================
-- Catálogo Avançado de Checklist + Avarias
-- Sistema Transpontual - Módulo 1 Completo
-- ==============================

-- ==================
-- MODELO: CARRETA PESADA - PRÉ-VIAGEM
-- ==================
WITH carreta_pre AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Carreta Pesada - Pré-viagem', 'pre', 'pesado', 
            'Checklist obrigatório para carretas e semirreboques antes da viagem', 25)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM carreta_pre), 1, 'engate', 'pino_rei', 'Engate / Pino-rei',
     'Verificar condição do pino-rei, trava de engate e ausência de folgas excessivas',
     'ok_nok', 'critica', true, true, true,
     '["Folga excessiva no pino-rei","Trava do engate com desgaste","Engate não trava corretamente","Excesso de graxa/sujeira","Pino de segurança ausente","Rachadura na quinta roda","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 2, 'engate', 'quinta_roda', 'Quinta roda / travamento',
     'Inspeção do sistema de travamento da quinta roda e conexões',
     'ok_nok', 'critica', true, true, true,
     '["Trava não engata completamente","Pino de travamento solto/faltante","Jogo excessivo na articulação","Vazamento de graxa","Deformação estrutural","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 3, 'carga', 'amarracao', 'Amarração da carga (lona/cintas)',
     'Verificar fixação da carga, estado das cintas e lona de proteção',
     'ok_nok', 'alta', true, true, true,
     '["Cinta desgastada/cortada","Catraca quebrada/defeituosa","Lona rasgada","Carga solta/mal amarrada","Excesso de peso","Distribuição inadequada","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 4, 'pneus', 'estado', 'Pneus da carreta',
     'Inspeção visual dos pneus: pressão, sulco, deformações e fixação',
     'ok_nok', 'critica', true, true, true,
     '["Pressão baixa","Sulco abaixo do mínimo (1,6mm)","Fissura/bolha na banda","Desgaste irregular","Parafusos frouxos","Pneu careca","Objeto perfurante","Válvula defeituosa","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 5, 'iluminacao', 'traseira', 'Iluminação traseira/lanternas',
     'Teste de funcionamento de toda iluminação traseira e sinalização',
     'ok_nok', 'media', false, true, false,
     '["Lanterna quebrada/trincada","Lâmpada queimada","Sem funcionamento","Conector elétrico solto","Fiação aparente/ressecada","Luz de freio inoperante","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 6, 'freios', 'sistema_ar', 'Freios e conexões de ar',
     'Verificação do sistema pneumático de freios e conexões',
     'ok_nok', 'critica', true, true, true,
     '["Vazamento de ar audível","Mangueira danificada/ressecada","Engate rápido com folga","Cilindro/freio travando","Pressão insuficiente","Válvula defeituosa","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 7, 'carroceria', 'parachoques', 'Para-lamas / Parachoque traseiro',
     'Inspeção visual de para-lamas e parachoque traseiro',
     'ok_nok', 'baixa', false, false, false,
     '["Quebrado/trincado","Solto/mal fixado","Peça faltante","Deformação","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 8, 'suspensao', 'ar', 'Suspensão / bolsa de ar',
     'Verificar sistema de suspensão pneumática e nivelamento',
     'ok_nok', 'alta', true, true, true,
     '["Bolsa furada/vazando","Nivelamento irregular","Barulho anormal","Válvula defeituosa","Compressor com problema","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 9, 'vazamentos', 'fluidos', 'Vazamentos visíveis',
     'Inspeção de vazamentos de óleo, graxa ou outros fluidos',
     'ok_nok', 'alta', true, true, true,
     '["Óleo do diferencial","Graxa do cubo da roda","Combustível","Fluido hidráulico","Vazamento grande (poças)","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 10, 'documentacao', 'geral', 'Documentação / placas',
     'Verificar documentos obrigatórios e legibilidade das placas',
     'ok_nok', 'media', false, true, false,
     '["Placa ilegível/danificada","Lacre ANTT violado","CRLV vencido","Seguro obrigatório vencido","Certificado de vistoria vencido","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 11, 'sinalizacao', 'refletivos', 'Refletores / fita refletiva',
     'Verificar refletores laterais e traseiros conforme legislação',
     'ok_nok', 'baixa', false, false, false,
     '["Refletor ausente/quebrado","Fita refletiva descolando","Baixa reflexão/opaca","Fora do padrão","Outros"]'),
     
    ((SELECT id FROM carreta_pre), 12, 'engate', 'bitrem', 'Travas de rodotrem/bitrem',
     'Verificar travas e conexões específicas para composições múltiplas',
     'ok_nok', 'critica', false, true, true,
     '["Trava aberta/mal posicionada","Pino de segurança ausente","Excesso de folga","Mecanismo emperrado","Outros"]');

-- ==================
-- MODELO: CAVALO MECÂNICO - PRÉ-VIAGEM
-- ==================
WITH cavalo_pre AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Cavalo Mecânico - Pré-viagem', 'pre', 'pesado', 
            'Checklist para caminhões tratores antes da viagem', 20)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM cavalo_pre), 1, 'freios', 'servico', 'Freios (pedal / estacionamento)',
     'Teste de eficiência dos freios de serviço e estacionamento',
     'ok_nok', 'critica', false, true, true,
     '["Eficiência baixa","Curso longo do pedal","Ruído anormal","Freio de estacionamento frouxo","Luz de freio inoperante","Vazamento no circuito","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 2, 'pneus', 'dianteiros', 'Pneus do cavalo mecânico',
     'Inspeção completa dos pneus do cavalo (dianteiros e traseiros)',
     'ok_nok', 'critica', true, true, true,
     '["Pressão baixa","Sulco abaixo do mínimo","Fissura/bolha","Desgaste irregular","Parafusos frouxos","Pneu careca","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 3, 'iluminacao', 'geral', 'Iluminação e setas',
     'Verificação completa do sistema elétrico de iluminação',
     'ok_nok', 'media', false, true, false,
     '["Farol queimado/trincado","Lanterna quebrada","Seta inoperante","Fora de foco","Pisca-alerta defeituoso","Luz de placa apagada","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 4, 'direcao', 'sistema', 'Direção / folga / ruído',
     'Teste do sistema de direção hidráulica e mecânica',
     'ok_nok', 'critica', false, true, true,
     '["Folga excessiva no volante","Vazamento fluido direção","Barulho anormal na direção","Direção dura/pesada","Vibração no volante","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 5, 'motor', 'vazamentos', 'Vazamentos (motor/câmbio)',
     'Inspeção de vazamentos no compartimento do motor',
     'ok_nok', 'alta', true, true, true,
     '["Óleo do motor","Óleo do câmbio","Sistema de refrigeração/água","Combustível","Fluido de freio","Vazamento grande","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 6, 'parabrisa', 'visibilidade', 'Para-brisa e limpadores',
     'Verificar integridade do para-brisa e sistema limpador',
     'ok_nok', 'baixa', false, false, false,
     '["Trinca no para-brisa","Palheta gasta/ressecada","Reservatório vazio","Esguicho entupido","Vidro opaco/embaçado","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 7, 'espelhos', 'retrovisores', 'Retrovisores',
     'Inspeção dos espelhos retrovisores e laterais',
     'ok_nok', 'media', false, false, false,
     '["Espelho quebrado/trincado","Solto/com folga","Sistema de ajuste inoperante","Visibilidade comprometida","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 8, 'tacografo', 'equipamento', 'Tacógrafo',
     'Verificação do tacógrafo e disco diagrama',
     'ok_nok', 'media', false, false, false,
     '["Sem lacre/lacre violado","Sem disco ou disco vencido","Falha na leitura","Ponteiros parados","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 9, 'seguranca', 'extintor', 'Extintor de incêndio',
     'Verificação do extintor obrigatório e acessórios de segurança',
     'ok_nok', 'alta', false, false, true,
     '["Extintor vencido","Pressão baixa/nula","Lacre violado","Suporte solto/quebrado","Extintor ausente","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 10, 'seguranca', 'cinto', 'Cinto de segurança',
     'Teste de funcionamento do cinto de segurança',
     'ok_nok', 'critica', false, true, false,
     '["Fivela não trava","Cinto rasgado/cortado","Fixação solta","Mecanismo travado","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 11, 'documentacao', 'veiculo', 'Documentação do veículo',
     'Conferência dos documentos obrigatórios do veículo',
     'ok_nok', 'media', false, true, false,
     '["CRLV vencido","Seguro obrigatório vencido","ANTT/RNTRC irregular","Lacres irregulares","IPVA em atraso","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 12, 'fluidos', 'niveis', 'Fluidos (óleo/água/Arla)',
     'Verificação dos níveis de fluidos essenciais',
     'ok_nok', 'media', false, false, true,
     '["Nível baixo óleo motor","Nível baixo água radiador","Arla 32 em nível baixo","Óleo hidráulico baixo","Combustível insuficiente","Outros"]'),
     
    ((SELECT id FROM cavalo_pre), 13, 'equipamentos', 'auxiliares', 'Buzina / equipamentos auxiliares',
     'Teste de buzina e equipamentos auxiliares obrigatórios',
     'ok_nok', 'baixa', false, false, false,
     '["Buzina inoperante","Som intermitente","Triângulo ausente","Macaco/chaves ausentes","Kit primeiros socorros vencido","Outros"]');

-- ==================
-- MODELO: VEÍCULO LEVE - PRÉ-VIAGEM  
-- ==================
WITH leve_pre AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Veículo Leve - Pré-viagem', 'pre', 'leve', 
            'Checklist para veículos de passeio, pickups e utilitários leves', 10)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM leve_pre), 1, 'iluminacao', 'geral', 'Iluminação geral',
     'Verificação de faróis, lanternas e sistema de sinalização',
     'ok_nok', 'media', false, true, false,
     '["Farol queimado","Lanterna quebrada/queimada","Seta inoperante","Pisca-alerta defeituoso","Luz de freio inoperante","Outros"]'),
     
    ((SELECT id FROM leve_pre), 2, 'pneus', 'completo', 'Pneus',
     'Inspeção visual completa dos pneus incluindo estepe',
     'ok_nok', 'critica', true, true, true,
     '["Pressão baixa","Sulco abaixo mínimo","Deformação/bolha","Parafusos frouxos","Estepe murcho","Objeto perfurante","Outros"]'),
     
    ((SELECT id FROM leve_pre), 3, 'freios', 'servico', 'Freio de serviço',
     'Teste do sistema de freios e freio de mão',
     'ok_nok', 'critica', false, true, true,
     '["Curso longo do pedal","Ruído/chiado","Baixa eficiência","Freio de mão frouxo","Vibração na frenagem","Outros"]'),
     
    ((SELECT id FROM leve_pre), 4, 'parabrisa', 'limpadores', 'Para-brisa/limpadores',
     'Verificar integridade do para-brisa e limpadores',
     'ok_nok', 'baixa', false, false, false,
     '["Trinca no vidro","Palheta gasta","Reservatório vazio","Esguicho entupido","Outros"]'),
     
    ((SELECT id FROM leve_pre), 5, 'fluidos', 'niveis', 'Níveis (óleo/água)',
     'Verificação dos níveis de óleo do motor e água do radiador',
     'ok_nok', 'media', false, false, true,
     '["Óleo baixo/sujo","Água baixa","Combustível insuficiente","Fluido freio baixo","Outros"]'),
     
    ((SELECT id FROM leve_pre), 6, 'seguranca', 'cinto', 'Cinto de segurança',
     'Teste de funcionamento dos cintos dianteiros e traseiros',
     'ok_nok', 'critica', false, true, false,
     '["Fivela não trava","Cinto rasgado","Fixação solta","Mecanismo travado","Outros"]'),
     
    ((SELECT id FROM leve_pre), 7, 'documentacao', 'veiculo', 'Documentação',
     'Conferência dos documentos obrigatórios',
     'ok_nok', 'media', false, true, false,
     '["CRLV vencido","Seguro obrigatório vencido","IPVA atrasado","CNH vencida","Outros"]');

-- ==================
-- MODELOS PÓS-VIAGEM (MAIS SIMPLES)
-- ==================

-- Modelo genérico pós-viagem para veículos pesados
WITH pos_pesado AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Veículo Pesado - Pós-viagem', 'pos', 'pesado', 
            'Checklist de encerramento para veículos pesados', 15)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, exige_observacao, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM pos_pesado), 1, 'geral', 'danos', 'Danos externos identificados',
     'Verificar se houve algum dano durante a viagem',
     'ok_nok', 'media', true, true, false, true,
     '["Risco na pintura","Amassado na carroceria","Vidro trincado","Dano no para-choque","Outros"]'),
     
    ((SELECT id FROM pos_pesado), 2, 'limpeza', 'cabine', 'Limpeza da cabine',
     'Verificar condições de limpeza e organização da cabine',
     'ok_nok', 'baixa', false, false, false, false,
     '["Cabine suja","Lixo deixado","Objetos pessoais esquecidos","Outros"]'),
     
    ((SELECT id FROM pos_pesado), 3, 'combustivel', 'nivel', 'Nível de combustível',
     'Registrar nível de combustível ao final da viagem',
     'numero', 'baixa', false, true, false, false, '[]'),
     
    ((SELECT id FROM pos_pesado), 4, 'ocorrencias', 'viagem', 'Ocorrências durante a viagem',
     'Relatar qualquer ocorrência relevante durante o percurso',
     'texto', 'baixa', false, true, false, false, '[]');

-- Modelo genérico pós-viagem para veículos leves
WITH pos_leve AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Veículo Leve - Pós-viagem', 'pos', 'leve', 
            'Checklist de encerramento para veículos leves', 8)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, exige_observacao, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM pos_leve), 1, 'geral', 'danos', 'Danos identificados',
     'Verificar se houve danos durante o uso do veículo',
     'ok_nok', 'media', true, true, false, true,
     '["Arranhão","Amassado","Vidro danificado","Outros"]'),
     
    ((SELECT id FROM pos_leve), 2, 'limpeza', 'interno', 'Limpeza interna',
     'Verificar limpeza e organização interna',
     'ok_nok', 'baixa', false, false, false, false,
     '["Interior sujo","Lixo no veículo","Outros"]'),
     
    ((SELECT id FROM pos_leve), 3, 'combustivel', 'nivel', 'Nível combustível final',
     'Registrar nível de combustível',
     'numero', 'baixa', false, true, false, false, '[]');

-- ==================
-- MODELO EXTRAORDINÁRIO/MANUTENÇÃO
-- ==================
WITH extra_manutencao AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos)
    VALUES ('Checklist Extraordinário - Manutenção', 'extra', 'todos', 
            'Checklist para situações especiais e manutenção preventiva', 30)
    ON CONFLICT (nome, tipo) WHERE ativo = true DO UPDATE SET 
        descricao = EXCLUDED.descricao,
        tempo_estimado_minutos = EXCLUDED.tempo_estimado_minutos
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada, tipo_resposta, severidade, exige_foto, exige_observacao, bloqueia_viagem, gera_os, opcoes) VALUES
    ((SELECT id FROM extra_manutencao), 1, 'motor', 'funcionamento', 'Funcionamento do motor',
     'Verificação detalhada do funcionamento do motor',
     'ok_nok', 'alta', false, true, true, true,
     '["Motor falhando","Ruído anormal","Fumaça excessiva","Temperatura alta","Baixa potência","Outros"]'),
     
    ((SELECT id FROM extra_manutencao), 2, 'transmissao', 'cambio', 'Sistema de transmissão',
     'Verificar câmbio, embreagem e transmissão',
     'ok_nok', 'alta', false, true, true, true,
     '["Câmbio duro","Embreagem patinando","Ruído na transmissão","Vazamento óleo câmbio","Outros"]'),
     
    ((SELECT id FROM extra_manutencao), 3, 'suspensao', 'completa', 'Sistema de suspensão',
     'Inspeção completa da suspensão dianteira e traseira',
     'ok_nok', 'media', true, true, false, true,
     '["Amortecedor vazando","Mola quebrada","Bucha gasta","Ruído na suspensão","Outros"]'),
     
    ((SELECT id FROM extra_manutencao), 4, 'eletrica', 'sistema', 'Sistema elétrico',
     'Verificação do sistema elétrico geral',
     'ok_nok', 'media', false, true, false, true,
     '["Bateria fraca","Alternador com problema","Fiação ressecada","Fusível queimado","Outros"]'),
     
    ((SELECT id FROM extra_manutencao), 5, 'observacoes', 'gerais', 'Observações gerais',
     'Campo livre para observações adicionais',
     'texto', 'baixa', false, true, false, false, '[]');

-- ==================
-- FUNÇÃO PARA CLONAR MODELOS DE CHECKLIST
-- ==================
CREATE OR REPLACE FUNCTION clone_checklist_modelo(modelo_id_original INT, novo_nome TEXT) 
RETURNS INT AS $$
DECLARE
    novo_modelo_id INT;
    item_record RECORD;
BEGIN
    -- Inserir novo modelo baseado no original
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos, versao, versao_anterior_id)
    SELECT novo_nome, tipo, categoria_veiculo, descricao, tempo_estimado_minutos, versao + 1, id
    FROM checklist_modelos WHERE id = modelo_id_original
    RETURNING id INTO novo_modelo_id;
    
    -- Copiar todos os itens
    FOR item_record IN 
        SELECT * FROM checklist_itens WHERE modelo_id = modelo_id_original ORDER BY ordem
    LOOP
        INSERT INTO checklist_itens (
            modelo_id, ordem, categoria, subcategoria, descricao, descricao_detalhada,
            tipo_resposta, opcoes, severidade, exige_foto, exige_observacao,
            bloqueia_viagem, gera_os, codigo_item, valor_min, valor_max, unidade
        ) VALUES (
            novo_modelo_id, item_record.ordem, item_record.categoria, item_record.subcategoria,
            item_record.descricao, item_record.descricao_detalhada, item_record.tipo_resposta,
            item_record.opcoes, item_record.severidade, item_record.exige_foto, item_record.exige_observacao,
            item_record.bloqueia_viagem, item_record.gera_os, item_record.codigo_item,
            item_record.valor_min, item_record.valor_max, item_record.unidade
        );
    END LOOP;
    
    RETURN novo_modelo_id;
END;
$$ LANGUAGE plpgsql;

-- ==================
-- VIEW PARA CONSULTA RÁPIDA DE MODELOS
-- ==================
CREATE OR REPLACE VIEW vw_checklist_modelos_completo AS
SELECT 
    cm.id,
    cm.uuid,
    cm.nome,
    cm.tipo,
    cm.categoria_veiculo,
    cm.versao,
    cm.ativo,
    cm.obrigatorio,
    cm.tempo_estimado_minutos,
    COUNT(ci.id) as total_itens,
    COUNT(ci.id) FILTER (WHERE ci.bloqueia_viagem = true) as itens_bloqueantes,
    COUNT(ci.id) FILTER (WHERE ci.exige_foto = true) as itens_com_foto,
    COUNT(ci.id) FILTER (WHERE ci.severidade = 'critica') as itens_criticos,
    cm.criado_em,
    u.nome as criado_por_nome
FROM checklist_modelos cm
LEFT JOIN checklist_itens ci ON ci.modelo_id = cm.id AND ci.ativo = true
LEFT JOIN usuarios u ON u.id = cm.criado_por
GROUP BY cm.id, cm.uuid, cm.nome, cm.tipo, cm.categoria_veiculo, cm.versao, 
         cm.ativo, cm.obrigatorio, cm.tempo_estimado_minutos, cm.criado_em, u.nome;

-- ==================
-- DADOS DE EXEMPLO PARA DESENVOLVIMENTO
-- ==================

-- Inserir veículos de exemplo se não existirem
INSERT INTO veiculos (placa, renavam, ano, modelo, marca, categoria, km_atual, proprietario) VALUES
('ABC1234', '12345678901', 2019, 'Constellation 24.280', 'Volkswagen', 'pesado', 280000, 'proprio'),
('DEF5678', '23456789012', 2020, 'FH 460', 'Volvo', 'pesado', 150000, 'proprio'),
('GHI9012', '34567890123', 2018, 'R450', 'Scania', 'pesado', 420000, 'proprio'),
('JKL3456', '45678901234', 2021, 'Actros 2651', 'Mercedes-Benz', 'pesado', 95000, 'proprio'),
('MNO7890', '56789012345', 2022, 'Amarok', 'Volkswagen', 'leve', 35000, 'proprio')
ON CONFLICT (placa) DO NOTHING;

-- Inserir motoristas de exemplo se não existirem  
INSERT INTO motoristas (nome, cnh, categoria_cnh, validade_cnh, status) VALUES
('João da Silva Santos', '12345678900', 'E', '2026-12-31', 'ativo'),
('Maria Oliveira Costa', '23456789011', 'E', '2025-08-15', 'ativo'),
('Carlos Roberto Lima', '34567890122', 'D', '2027-03-20', 'ativo'),
('Ana Paula Ferreira', '45678901233', 'B', '2026-06-10', 'ativo'),
('Pedro Henrique Souza', '56789012344', 'E', '2025-11-25', 'ativo')
ON CONFLICT (cnh) DO NOTHING;

-- Comentários nas tabelas do catálogo
COMMENT ON TABLE checklist_modelos IS 'Modelos/templates de checklist para diferentes tipos de veículos';
COMMENT ON TABLE checklist_itens IS 'Itens individuais que compõem cada modelo de checklist';
COMMENT ON COLUMN checklist_itens.opcoes IS 'Array JSON com opções de avarias/problemas para cada item';
COMMENT ON COLUMN checklist_itens.bloqueia_viagem IS 'Se verdadeiro, resposta "não OK" impede liberação do veículo';
COMMENT ON COLUMN checklist_itens.gera_os IS 'Se verdadeiro, resposta "não OK" gera automaticamente ordem de serviço';
