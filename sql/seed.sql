-- sql/seed.sql
-- Dados iniciais para o Sistema Transpontual

-- ========== USUÁRIOS E MOTORISTAS ==========

-- Usuário administrador
INSERT INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES
('Administrador Sistema', 'admin@transpontual.com', 'admin123', 'gestor', true),
('João Silva', 'joao.silva@transpontual.com', 'motorista123', 'motorista', true),
('Maria Santos', 'maria.santos@transpontual.com', 'motorista123', 'motorista', true),
('Carlos Lima', 'carlos.lima@transpontual.com', 'motorista123', 'motorista', true),
('José Mecânico', 'jose.mecanico@transpontual.com', 'mecanico123', 'mecanico', true),
('Ana Gestora', 'ana.gestora@transpontual.com', 'gestor123', 'gestor', true)
ON CONFLICT (email) DO NOTHING;

-- Motoristas
INSERT INTO motoristas (nome, cnh, categoria, validade_cnh, telefone, endereco, cidade, estado, data_admissao, usuario_id, ativo) VALUES
('João Silva Santos', '12345678900', 'E', '2028-12-31', '(22) 99999-1111', 'Rua das Flores, 123', 'Macaé', 'RJ', '2020-01-15', 
    (SELECT id FROM usuarios WHERE email = 'joao.silva@transpontual.com'), true),
('Maria Santos Oliveira', '22345678900', 'D', '2027-08-15', '(22) 99999-2222', 'Av. Brasil, 456', 'Campos dos Goytacazes', 'RJ', '2021-03-10',
    (SELECT id FROM usuarios WHERE email = 'maria.santos@transpontual.com'), true),
('Carlos Lima Souza', '32345678900', 'E', '2029-05-20', '(22) 99999-3333', 'Rua do Porto, 789', 'Rio das Ostras', 'RJ', '2019-07-22',
    (SELECT id FROM usuarios WHERE email = 'carlos.lima@transpontual.com'), true),
('Roberto Cruz', '42345678900', 'E', '2026-11-10', '(22) 99999-4444', 'Estrada do Interior, 100', 'Casimiro de Abreu', 'RJ', '2022-02-01', NULL, true),
('Fernando Alves', '52345678900', 'D', '2028-03-25', '(22) 99999-5555', 'Rua Central, 200', 'Nova Friburgo', 'RJ', '2020-09-15', NULL, true),
('Ricardo Pereira', '62345678900', 'E', '2025-07-18', '(22) 99999-6666', 'Av. Principal, 300', 'Macaé', 'RJ', '2018-12-03', NULL, true)
ON CONFLICT DO NOTHING;

-- ========== VEÍCULOS ==========

INSERT INTO veiculos (placa, renavam, chassi, ano, modelo, marca, cor, tipo, categoria, combustivel, km_atual, capacidade_carga, proprietario, status, ativo) VALUES
-- Cavalos mecânicos
('RTA1A23', '00999887766', '9BWZZZ377VT004251', 2019, 'Constellation 17.280', 'Volkswagen', 'Branco', 'cavalo', 'E', 'diesel', 250000, 17280, 'proprio', 'ativo', true),
('RTA2B34', '00999887767', '9BFXXZ2B0CXX12345', 2020, 'FH 460', 'Volvo', 'Azul', 'cavalo', 'E', 'diesel', 180050, 18000, 'proprio', 'ativo', true),
('RTA3C45', '00999887768', '9BSR4X2V0KX123456', 2018, 'R 450', 'Scania', 'Branco', 'cavalo', 'E', 'diesel', 320000, 18000, 'proprio', 'ativo', true),
('RTA4D56', '00999887769', '9BM958220LX789012', 2017, 'Actros 2651', 'Mercedes-Benz', 'Prata', 'cavalo', 'E', 'diesel', 410000, 26000, 'proprio', 'ativo', true),
('RTA5E67', '00999887770', 'XLRXXX4E0EX345678', 2021, 'XF 480', 'DAF', 'Branco', 'cavalo', 'E', 'diesel', 120000, 20000, 'proprio', 'ativo', true),

-- Carretas
('RTB1F78', '00999887771', '9BWZZZ377VT004252', 2018, 'Bitrem Graneleiro', 'Guerra', 'Branco', 'carreta', 'E', 'diesel', 180000, 35000, 'proprio', 'ativo', true),
('RTB2G89', '00999887772', '9BWZZZ377VT004253', 2019, 'Sider 3 Eixos', 'Librelato', 'Azul', 'carreta', 'E', 'diesel', 220000, 30000, 'proprio', 'ativo', true),
('RTB3H90', '00999887773', '9BWZZZ377VT004254', 2020, 'Baú Frigorífico', 'Krone', 'Branco', 'carreta', 'E', 'diesel', 95000, 28000, 'proprio', 'ativo', true),
('RTB4I01', '00999887774', '9BWZZZ377VT004255', 2017, 'Prancha 4 Eixos', 'Facchini', 'Amarelo', 'carreta', 'E', 'diesel', 380000, 40000, 'proprio', 'ativo', true),

-- Veículos leves
('RTC1J12', '00999887775', '9BWZZZ377VT004256', 2021, 'Sprinter 415', 'Mercedes-Benz', 'Branco', 'van', 'D', 'diesel', 45000, 1500, 'proprio', 'ativo', true),
('RTC2K23', '00999887776', '9BWZZZ377VT004257', 2020, 'Master 2.3', 'Renault', 'Prata', 'van', 'D', 'diesel', 72000, 1300, 'proprio', 'ativo', true),
('RTC3L34', '00999887777', '9BWZZZ377VT004258', 2022, 'Daily 70C16', 'Iveco', 'Branco', 'leve', 'C', 'diesel', 28000, 3500, 'proprio', 'ativo', true),
('RTC4M45', '00999887778', '9BWZZZ377VT004259', 2019, 'HR 2.5', 'Hyundai', 'Branco', 'leve', 'C', 'diesel', 89000, 2800, 'proprio', 'ativo', true)
ON CONFLICT (placa) DO NOTHING;

-- ========== MODELOS DE CHECKLIST ==========

-- Modelo para CARRETA - Pré-viagem
WITH carreta_modelo AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, versao, descricao, criado_por, ativo)
    VALUES ('Carreta - Pré-viagem', 'pre', 'carreta', 1, 'Checklist completo para inspeção pré-viagem de carretas', 1, true)
    ON CONFLICT DO NOTHING
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, categoria, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes, instrucoes) VALUES
((SELECT id FROM carreta_modelo LIMIT 1), 1, 'Engate / Pino-rei', 'acoplamento', 'ok', 'alta', false, true, 
 '["Folga no pino-rei","Trava com desgaste","Engate sem travar","Excesso de graxa/sujeira","Pino danificado","Outros"]', 
 'Verificar se o pino-rei está firme, sem folgas excessivas e com trava funcionando corretamente.'),

((SELECT id FROM carreta_modelo LIMIT 1), 2, 'Quinta roda / travamento', 'acoplamento', 'ok', 'alta', false, true,
 '["Trava não engata","Pino de travamento solto","Jogo excessivo","Lubrificação inadequada","Desgaste na quinta roda","Outros"]',
 'Verificar o travamento da quinta roda e ausência de folgas anormais.'),

((SELECT id FROM carreta_modelo LIMIT 1), 3, 'Amarração da carga (lona/cintas)', 'carga', 'ok', 'alta', true, true,
 '["Cinta desgastada","Catraca quebrada","Lona rasgada","Carga solta","Amarração insuficiente","Excesso de peso","Outros"]',
 'Verificar se a carga está devidamente amarrada e protegida. Obrigatório tirar foto.'),

((SELECT id FROM carreta_modelo LIMIT 1), 4, 'Pneus da carreta', 'pneus', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco abaixo do mínimo","Fissura/bolha","Desgaste irregular","Parafusos frouxos","Pneu careca","Outros"]',
 'Verificar pressão, sulco (mín. 1.6mm) e integridade de todos os pneus. Tirar foto se houver problemas.'),

((SELECT id FROM carreta_modelo LIMIT 1), 5, 'Iluminação traseira/lanternas', 'eletrica', 'ok', 'media', false, true,
 '["Lanterna quebrada","Sem funcionamento","Conector elétrico solto","Fiação aparente","Lâmpada queimada","Outros"]',
 'Testar funcionamento das lanternas traseiras, setas e freio.'),

((SELECT id FROM carreta_modelo LIMIT 1), 6, 'Freios e conexões de ar', 'freios', 'ok', 'alta', true, true,
 '["Vazamento de ar","Mangueira danificada","Engate rápido com folga","Cilindro/freio travando","Pressão insuficiente","Outros"]',
 'Verificar sistema pneumático, vazamentos e eficiência dos freios.'),

((SELECT id FROM carreta_modelo LIMIT 1), 7, 'Para-lamas / Parachoque traseiro', 'carroceria', 'ok', 'media', false, false,
 '["Quebrado","Solto","Faltante","Deformado","Outros"]',
 'Verificar integridade e fixação dos para-lamas e parachoque.'),

((SELECT id FROM carreta_modelo LIMIT 1), 8, 'Suspensão / bolsa de ar', 'suspensao', 'ok', 'alta', true, true,
 '["Bolsa furada","Nivelamento irregular","Barulho anormal","Vazamento","Amortecedor danificado","Outros"]',
 'Verificar nivelamento e ausência de vazamentos na suspensão pneumática.'),

((SELECT id FROM carreta_modelo LIMIT 1), 9, 'Vazamentos visíveis', 'geral', 'ok', 'alta', true, true,
 '["Óleo diferencial","Graxa cubo","Combustível","Hidráulico","Água/arrefecimento","Outros"]',
 'Inspecionar toda a parte inferior em busca de vazamentos. Fotografar se encontrado.'),

((SELECT id FROM carreta_modelo LIMIT 1), 10, 'Documentação / placas', 'documentos', 'ok', 'media', false, true,
 '["Placa ilegível","Lacre violado","CRLV vencido","Seguro vencido","ANTT irregular","Outros"]',
 'Verificar documentação obrigatória e legibilidade das placas.'),

((SELECT id FROM carreta_modelo LIMIT 1), 11, 'Refletores / fita refletiva', 'seguranca', 'ok', 'baixa', false, false,
 '["Ausente","Descolando","Baixa reflexão","Danificado","Outros"]',
 'Verificar presença e estado dos refletores laterais e traseiros.'),

((SELECT id FROM carreta_modelo LIMIT 1), 12, 'Travas de rodotrem/bitrem', 'acoplamento', 'ok', 'alta', false, true,
 '["Trava aberta","Pino de segurança ausente","Excesso de folga","Desgaste na trava","Outros"]',
 'Para rodotrem/bitrem: verificar travamento entre unidades.')
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- Modelo para CAVALO MECÂNICO - Pré-viagem
WITH cavalo_modelo AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, versao, descricao, criado_por, ativo)
    VALUES ('Cavalo - Pré-viagem', 'pre', 'cavalo', 1, 'Checklist completo para inspeção pré-viagem de cavalos mecânicos', 1, true)
    ON CONFLICT DO NOTHING
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, categoria, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes, instrucoes) VALUES
((SELECT id FROM cavalo_modelo LIMIT 1), 1, 'Freios (pedal / estacionamento)', 'freios', 'ok', 'alta', false, true,
 '["Eficiência baixa","Ruído anormal","Luz de freio inoperante","Pedal baixo","Freio de mão solto","Outros"]',
 'Testar eficiência do freio de serviço e estacionamento.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 2, 'Pneus do cavalo', 'pneus', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco abaixo do mínimo","Fissura/bolha","Parafusos frouxos","Desgaste irregular","Outros"]',
 'Verificar pressão, sulco e integridade de todos os pneus do cavalo.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 3, 'Iluminação e setas', 'eletrica', 'ok', 'media', false, true,
 '["Farol queimado","Lanterna quebrada","Fora de foco","Seta não funciona","Luz de ré inoperante","Outros"]',
 'Testar funcionamento de todos os sistemas de iluminação.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 4, 'Direção / folga / ruído', 'direcao', 'ok', 'alta', false, true,
 '["Folga excessiva","Vazamento fluido","Barulho anormal","Vibração no volante","Direção pesada","Outros"]',
 'Verificar folga no volante (máx. 2cm) e funcionamento da direção.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 5, 'Vazamentos (motor/câmbio)', 'motor', 'ok', 'alta', true, true,
 '["Óleo motor","Óleo câmbio","Refrigeração/água","Combustível","Fluido hidráulico","Outros"]',
 'Inspecionar vazamentos na parte inferior do motor e câmbio.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 6, 'Para-brisa e limpadores', 'cabine', 'ok', 'baixa', false, false,
 '["Trincado","Palheta gasta","Reservatório vazio","Borrifador entupido","Outros"]',
 'Verificar integridade do para-brisa e funcionamento dos limpadores.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 7, 'Retrovisores', 'cabine', 'ok', 'baixa', false, false,
 '["Quebrado","Solto","Ajuste inoperante","Rachadura","Outros"]',
 'Verificar integridade e ajuste dos retrovisores externos.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 8, 'Tacógrafo', 'instrumentos', 'ok', 'media', false, false,
 '["Sem lacre","Sem registro","Falha de leitura","Display com defeito","Outros"]',
 'Verificar funcionamento do tacógrafo e integridade dos lacres.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 9, 'Extintor de incêndio', 'seguranca', 'ok', 'media', false, false,
 '["Vencido","Pressão baixa","Lacre violado","Suporte solto","Ausente","Outros"]',
 'Verificar validade, pressão e fixação do extintor.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 10, 'Cinto de segurança', 'seguranca', 'ok', 'alta', false, true,
 '["Sem trava","Rasgado","Fixação solta","Fivela com defeito","Outros"]',
 'Testar funcionamento e integridade dos cintos de segurança.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 11, 'Documentação do veículo', 'documentos', 'ok', 'media', false, true,
 '["CRLV vencido","Seguro vencido","Lacres irregulares","ANTT vencida","Outros"]',
 'Verificar validade de toda documentação obrigatória.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 12, 'Fluídos (óleo/água/Arla)', 'motor', 'ok', 'baixa', false, false,
 '["Nível baixo óleo","Nível baixo água","Arla baixo","Fluido direção baixo","Outros"]',
 'Verificar níveis de todos os fluídos do veículo.'),

((SELECT id FROM cavalo_modelo LIMIT 1), 13, 'Buzina / equipamentos auxiliares', 'eletrica', 'ok', 'baixa', false, false,
 '["Inoperante","Intermitente","Som fraco","Outros"]',
 'Testar funcionamento da buzina e equipamentos auxiliares.')
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- Modelo para VEÍCULO LEVE - Pré-viagem
WITH leve_modelo AS (
    INSERT INTO checklist_modelos (nome, tipo, categoria_veiculo, versao, descricao, criado_por, ativo)
    VALUES ('Leve - Pré-viagem', 'pre', 'leve', 1, 'Checklist para inspeção pré-viagem de veículos leves e utilitários', 1, true)
    ON CONFLICT DO NOTHING
    RETURNING id
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, categoria, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes, instrucoes) VALUES
((SELECT id FROM leve_modelo LIMIT 1), 1, 'Iluminação geral', 'eletrica', 'ok', 'media', false, true,
 '["Farol queimado","Lanterna quebrada","Seta inoperante","Luz de freio não funciona","Outros"]',
 'Testar funcionamento de faróis, lanternas, setas e luzes de freio.'),

((SELECT id FROM leve_modelo LIMIT 1), 2, 'Pneus', 'pneus', 'ok', 'alta', true, true,
 '["Pressão baixa","Sulco abaixo do mínimo","Deformação/bolha","Parafusos frouxos","Pneu careca","Outros"]',
 'Verificar pressão, sulco (mín. 1.6mm) e integridade de todos os pneus.'),

((SELECT id FROM leve_modelo LIMIT 1), 3, 'Freio de serviço', 'freios', 'ok', 'alta', false, true,
 '["Curso longo","Ruído","Baixa eficiência","Pedal esponjoso","Outros"]',
 'Testar eficiência e ruídos anormais no sistema de freios.'),

((SELECT id FROM leve_modelo LIMIT 1), 4, 'Para-brisa/limpadores', 'cabine', 'ok', 'baixa', false, false,
 '["Trinca","Palheta gasta","Reservatório vazio","Borrifador com defeito","Outros"]',
 'Verificar integridade do para-brisa e funcionamento dos limpadores.'),

((SELECT id FROM leve_modelo LIMIT 1), 5, 'Níveis (óleo/água)', 'motor', 'ok', 'baixa', false, false,
 '["Óleo baixo","Água baixa","Combustível baixo","Outros"]',
 'Verificar níveis de óleo, água e combustível.'),

((SELECT id FROM leve_modelo LIMIT 1), 6, 'Cinto de segurança', 'seguranca', 'ok', 'alta', false, true,
 '["Sem trava","Rasgado","Fixação solta","Fivela com defeito","Outros"]',
 'Testar funcionamento dos cintos de segurança dianteiros.'),

((SELECT id FROM leve_modelo LIMIT 1), 7, 'Documentação', 'documentos', 'ok', 'media', false, true,
 '["CRLV vencido","Seguro vencido","Outros"]',
 'Verificar validade da documentação obrigatória.')
ON CONFLICT (modelo_id, ordem) DO NOTHING;

-- ========== VIAGENS DE EXEMPLO ==========

INSERT INTO viagens (codigo, veiculo_id, motorista_id, origem, destino, cliente, tipo_carga, peso_carga, valor_frete, data_partida, data_chegada_prevista, status) VALUES
('VG-20240115-001', 1, 1, 'Macaé/RJ', 'Campos dos Goytacazes/RJ', 'Petrobras', 'Equipamentos industriais', 15000.00, 2500.00, 
 '2024-01-15 06:00:00', '2024-01-15 10:00:00', 'planejada'),
('VG-20240115-002', 2, 2, 'Rio das Ostras/RJ', 'Vitória/ES', 'Vale S.A.', 'Peças automotivas', 8500.00, 3200.00,
 '2024-01-15 08:00:00', '2024-01-15 18:00:00', 'planejada'),
('VG-20240115-003', 3, 3, 'Campos/RJ', 'Belo Horizonte/MG', 'Multilog', 'Produtos alimentícios', 22000.00, 4800.00,
 '2024-01-15 05:00:00', '2024-01-16 14:00:00', 'planejada')
ON CONFLICT (codigo) DO NOTHING;

-- ========== CHECKLISTS DE EXEMPLO ==========

-- Checklist aprovado
WITH checklist_exemplo AS (
    INSERT INTO checklists (codigo, viagem_id, veiculo_id, motorista_id, modelo_id, tipo, odometro_ini, geo_inicio, status, dt_inicio, duracao_minutos, score_final)
    VALUES ('CL-20240115-ABC001', 1, 1, 1, 1, 'pre', 250000, 
            '{"lat": -22.3765, "lng": -41.7869, "address": "Macaé/RJ"}', 
            'aprovado', '2024-01-15 05:30:00', 12, 95)
    RETURNING id
)
-- Respostas do checklist (todas OK)
INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao) VALUES
((SELECT id FROM checklist_exemplo), 1, 'ok', 'Engate funcionando perfeitamente'),
((SELECT id FROM checklist_exemplo), 2, 'ok', 'Quinta roda travando corretamente'),
((SELECT id FROM checklist_exemplo), 3, 'ok', 'Carga bem amarrada'),
((SELECT id FROM checklist_exemplo), 4, 'ok', 'Pneus em bom estado'),
((SELECT id FROM checklist_exemplo), 5, 'ok', 'Luzes funcionando'),
((SELECT id FROM checklist_exemplo), 6, 'ok', 'Sistema de freios OK'),
((SELECT id FROM checklist_exemplo), 7, 'ok', 'Para-lamas íntegros'),
((SELECT id FROM checklist_exemplo), 8, 'ok', 'Suspensão normal'),
((SELECT id FROM checklist_exemplo), 9, 'ok', 'Sem vazamentos'),
((SELECT id FROM checklist_exemplo), 10, 'ok', 'Documentação em dia'),
((SELECT id FROM checklist_exemplo), 11, 'ok', 'Refletores OK'),
((SELECT id FROM checklist_exemplo), 12, 'ok', 'Não se aplica');

-- Checklist com problemas (reprovado)
WITH checklist_problema AS (
    INSERT INTO checklists (codigo, viagem_id, veiculo_id, motorista_id, modelo_id, tipo, odometro_ini, geo_inicio, status, dt_inicio, duracao_minutos, score_final)
    VALUES ('CL-20240115-DEF002', 2, 2, 2, 2, 'pre', 180050,
            '{"lat": -22.5322, "lng": -41.9487, "address": "Rio das Ostras/RJ"}',
            'reprovado', '2024-01-15 07:45:00', 18, 75)
    RETURNING id
)
INSERT INTO checklist_respostas (checklist_id, item_id, valor, observacao, opcao_defeito) VALUES
((SELECT id FROM checklist_problema), 14, 'nao_ok', 'Freio com ruído anormal ao pressionar', 'Ruído anormal'),
((SELECT id FROM checklist_problema), 15, 'ok', 'Pneus OK'),
((SELECT id FROM checklist_problema), 16, 'nao_ok', 'Farol direito queimado', 'Farol queimado'),
((SELECT id FROM checklist_problema), 17, 'ok', 'Direção normal'),
((SELECT id FROM checklist_problema), 18, 'nao_ok', 'Pequeno vazamento de óleo do motor', 'Óleo motor'),
((SELECT id FROM checklist_problema), 19, 'ok', 'Para-brisa íntegro'),
((SELECT id FROM checklist_problema), 20, 'ok', 'Retrovisores OK'),
((SELECT id FROM checklist_problema), 21, 'ok', 'Tacógrafo funcionando'),
((SELECT id FROM checklist_problema), 22, 'ok', 'Extintor dentro da validade'),
((SELECT id FROM checklist_problema), 23, 'ok', 'Cintos OK'),
((SELECT id FROM checklist_problema), 24, 'ok', 'Documentação em dia'),
((SELECT id FROM checklist_problema), 25, 'ok', 'Níveis normais'),
((SELECT id FROM checklist_problema), 26, 'ok', 'Buzina funcionando');

-- ========== DEFEITOS E ORDENS DE SERVIÇO ==========

-- Defeito do freio (do checklist reprovado)
WITH defeito_freio AS (
    INSERT INTO defeitos (codigo, checklist_id, item_id, veiculo_id, categoria, severidade, prioridade, titulo, descricao, status, identificado_em, identificado_por)
    VALUES ('DEF-20240115-001', 
            (SELECT id FROM checklists WHERE codigo = 'CL-20240115-DEF002'),
            (SELECT id FROM checklist_itens WHERE descricao = 'Freios (pedal / estacionamento)'),
            2, 'freios', 'alta', 'alta', 'Ruído anormal no freio',
            'Freio apresentando ruído anormal ao pressionar o pedal - Ruído anormal',
            'identificado', '2024-01-15 08:03:00', 2)
    RETURNING id
)
INSERT INTO ordens_servico (numero, veiculo_id, defeito_id, tipo, prioridade, titulo, descricao, responsavel_abertura, status, km_veiculo) VALUES
('OS-20240115-0001', 2, (SELECT id FROM defeito_freio), 'corretiva', 'alta', 
 'Correção ruído no freio', 
 'Investigar e corrigir ruído anormal no sistema de freios do veículo RTA2B34',
 'Maria Santos Oliveira', 'aberta', 180050);

-- Defeito da iluminação
WITH defeito_farol AS (
    INSERT INTO defeitos (codigo, checklist_id, item_id, veiculo_id, categoria, severidade, prioridade, titulo, descricao, status, identificado_em, identificado_por)
    VALUES ('DEF-20240115-002',
            (SELECT id FROM checklists WHERE codigo = 'CL-20240115-DEF002'),
            (SELECT id FROM checklist_itens WHERE descricao = 'Iluminação e setas'),
            2, 'eletrica', 'media', 'normal', 'Farol queimado',
            'Farol direito queimado - Farol queimado',
            'identificado', '2024-01-15 08:05:00', 2)
    RETURNING id
)
INSERT INTO ordens_servico (numero, veiculo_id, defeito_id, tipo, prioridade, titulo, descricao, responsavel_abertura, status, km_veiculo) VALUES
('OS-20240115-0002', 2, (SELECT id FROM defeito_farol), 'corretiva', 'normal',
 'Substituição farol direito',
 'Substituir lâmpada do farol direito queimada do veículo RTA2B34',
 'Maria Santos Oliveira', 'aberta', 180050);

-- ========== DOCUMENTOS DE EXEMPLO ==========

-- CNHs dos motoristas
INSERT INTO documentos (codigo, entidade_tipo, entidade_id, tipo_documento, numero_documento, orgao_emissor, data_emissao, data_vencimento, status, dias_alerta) VALUES
('DOC-CNH-001', 'motorista', 1, 'cnh', '12345678900', 'DETRAN-RJ', '2023-01-15', '2028-12-31', 'vigente', 60),
('DOC-CNH-002', 'motorista', 2, 'cnh', '22345678900', 'DETRAN-RJ', '2022-08-15', '2027-08-15', 'vigente', 60),
('DOC-CNH-003', 'motorista', 3, 'cnh', '32345678900', 'DETRAN-RJ', '2024-05-20', '2029-05-20', 'vigente', 60);

-- CRLVs dos veículos
INSERT INTO documentos (codigo, entidade_tipo, entidade_id, tipo_documento, numero_documento, orgao_emissor, data_emissao, data_vencimento, status, dias_alerta) VALUES
('DOC-CRLV-001', 'veiculo', 1, 'crlv', 'CRLV123456', 'DETRAN-RJ', '2023-12-15', '2024-12-15', 'vencido', 30),
('DOC-CRLV-002', 'veiculo', 2, 'crlv', 'CRLV234567', 'DETRAN-RJ', '2024-01-10', '2025-01-10', 'vigente', 30),
('DOC-CRLV-003', 'veiculo', 3, 'crlv', 'CRLV345678', 'DETRAN-RJ', '2024-06-20', '2025-06-20', 'vigente', 30);

-- Seguros
INSERT INTO documentos (codigo, entidade_tipo, entidade_id, tipo_documento, numero_documento, orgao_emissor, data_emissao, data_vencimento, valor, status) VALUES
('DOC-SEG-001', 'veiculo', 1, 'seguro', 'SEG789012', 'Porto Seguro', '2024-01-01', '2025-01-01', 4500.00, 'vigente'),
('DOC-SEG-002', 'veiculo', 2, 'seguro', 'SEG890123', 'Bradesco Seguros', '2024-02-15', '2025-02-15', 5200.00, 'vigente'),
('DOC-SEG-003', 'veiculo', 3, 'seguro', 'SEG901234', 'Allianz', '2023-11-30', '2024-11-30', 4800.00, 'vencendo');

-- ========== ABASTECIMENTOS DE EXEMPLO ==========

INSERT INTO abastecimentos (codigo, veiculo_id, motorista_id, data_abastecimento, km_veiculo, litros, valor_litro, valor_total, tipo_combustivel, posto_nome, forma_pagamento) VALUES
('AB-20240110-001', 1, 1, '2024-01-10 14:30:00', 249800, 180.50, 5.89, 1063.35, 'diesel', 'Posto Shell BR-101', 'cartao'),
('AB-20240112-002', 2, 2, '2024-01-12 09:15:00', 179850, 165.20, 5.92, 978.38, 'diesel', 'Posto Ipiranga Centro', 'vale'),
('AB-20240113-003', 3, 3, '2024-01-13 16:45:00', 319750, 195.30, 5.87, 1146.41, 'diesel', 'Posto BR Rodovia', 'cartao');

-- ========== REFRESH DAS VIEWS MATERIALIZADAS ==========

-- Refresh inicial das views materializadas
SELECT refresh_materialized_views();

-- Inserir alguns logs de auditoria de exemplo
INSERT INTO audit_logs (usuario_id, acao, tabela, registro_id, ip, timestamp) VALUES
(1, 'LOGIN', 'usuarios', 1, '192.168.1.100', '2024-01-15 05:00:00'),
(2, 'CREATE', 'checklists', 1, '192.168.1.101', '2024-01-15 05:30:00'),
(2, 'CREATE', 'checklists', 2, '192.168.1.102', '2024-01-15 07:45:00'),
(5, 'CREATE', 'ordens_servico', 1, '192.168.1.103', '2024-01-15 09:00:00');

-- Adicionar comentários nas tabelas principais
COMMENT ON TABLE usuarios IS 'Usuários do sistema com diferentes papéis';
COMMENT ON TABLE motoristas IS 'Cadastro de motoristas da empresa';
COMMENT ON TABLE veiculos IS 'Frota de veículos (cavalos, carretas, leves)';
COMMENT ON TABLE checklists IS 'Checklists executados pelos motoristas';
COMMENT ON TABLE checklist_modelos IS 'Templates de checklist por tipo de veículo';
COMMENT ON TABLE checklist_itens IS 'Itens que compõem cada modelo de checklist';
COMMENT ON TABLE defeitos IS 'Defeitos identificados nos checklists';
COMMENT ON TABLE ordens_servico IS 'Ordens de serviço para correção de defeitos';