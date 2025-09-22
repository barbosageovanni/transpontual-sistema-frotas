-- ==============================
-- Catálogo de Checklist + Avarias (Carreta / Cavalo / Leve)
-- Executar no Supabase (schema público)
-- ==============================

-- 0) Campo de opções (lista de avarias por item)
ALTER TABLE IF EXISTS checklist_itens
  ADD COLUMN IF NOT EXISTS opcoes jsonb NOT NULL DEFAULT '[]'::jsonb;

-- 0.1) Índice de unicidade para evitar duplicar itens por ordem dentro do modelo
CREATE UNIQUE INDEX IF NOT EXISTS ux_checklist_itens_modelo_ordem
  ON checklist_itens (modelo_id, ordem);

-- ==================
-- MODELO: CARRETA
-- ==================
WITH chosen AS (
  SELECT id FROM checklist_modelos WHERE nome = 'Carreta - Pré-viagem'
  UNION ALL
  SELECT id FROM (INSERT INTO checklist_modelos (nome, tipo, versao, ativo)
                  VALUES ('Carreta - Pré-viagem', 'pre', 1, true)
                  ON CONFLICT DO NOTHING
                  RETURNING id) ins
  LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes)
VALUES
  ((SELECT id FROM chosen), 1, 'Engate / Pino-rei',                 'ok', 'alta',  false, true,  '["Folga no pino-rei","Trava com desgaste","Engate sem travar","Excesso de graxa/sujeira","Outros"]'),
  ((SELECT id FROM chosen), 2, 'Quinta roda / travamento',          'ok', 'alta',  false, true,  '["Trava não engata","Pino de travamento solto","Jogo excessivo","Outros"]'),
  ((SELECT id FROM chosen), 3, 'Amarração da carga (lona/cintas)',  'ok', 'alta',  true,  true,  '["Cinta desgastada","Catraca quebrada","Lona rasgada","Carga solta","Outros"]'),
  ((SELECT id FROM chosen), 4, 'Pneus da carreta',                  'ok', 'alta',  true,  true,  '["Pressão baixa","Sulco abaixo do mínimo","Fissura/bolha","Desgaste irregular","Parafusos frouxos","Outros"]'),
  ((SELECT id FROM chosen), 5, 'Iluminação traseira/lanternas',     'ok', 'media', false, true,  '["Lanterna quebrada","Sem funcionamento","Conector elétrico solto","Fiação aparente","Outros"]'),
  ((SELECT id FROM chosen), 6, 'Freios e conexões de ar',           'ok', 'alta',  true,  true,  '["Vazamento de ar","Mangueira danificada","Engate rápido com folga","Cilindro/freio travando","Outros"]'),
  ((SELECT id FROM chosen), 7, 'Para-lamas / Parachoque traseiro',  'ok', 'media', false, false, '["Quebrado","Solto","Faltante","Outros"]'),
  ((SELECT id FROM chosen), 8, 'Suspensão / bolsa de ar',           'ok', 'alta',  true,  true,  '["Bolsa furada","Nivelamento irregular","Barulho anormal","Outros"]'),
  ((SELECT id FROM chosen), 9, 'Vazamentos visíveis',               'ok', 'alta',  true,  true,  '["Óleo diferencial","Graxa cubo","Combustível","Hidráulico","Outros"]'),
  ((SELECT id FROM chosen),10, 'Documentação / placas',             'ok', 'media', false, true,  '["Placa ilegível","Lacre violado","CRLV vencido","Outros"]'),
  ((SELECT id FROM chosen),11, 'Refletores / fita refletiva',       'ok', 'baixa', false, false, '["Ausente","Descolando","Baixa reflexão","Outros"]'),
  ((SELECT id FROM chosen),12, 'Travas de rodotrem/bitrem',         'ok', 'alta',  false, true,  '["Trava aberta","Pino de segurança ausente","Excesso de folga","Outros"]')
ON CONFLICT (modelo_id, ordem) DO UPDATE SET
  descricao = EXCLUDED.descricao,
  severidade = EXCLUDED.severidade,
  exige_foto = EXCLUDED.exige_foto,
  bloqueia_viagem = EXCLUDED.bloqueia_viagem,
  opcoes = EXCLUDED.opcoes;

-- ==================
-- MODELO: CAVALO MECÂNICO (CAMINHÃO TRACTOR)
-- ==================
WITH chosen AS (
  SELECT id FROM checklist_modelos WHERE nome = 'Cavalo - Pré-viagem'
  UNION ALL
  SELECT id FROM (INSERT INTO checklist_modelos (nome, tipo, versao, ativo)
                  VALUES ('Cavalo - Pré-viagem', 'pre', 1, true)
                  ON CONFLICT DO NOTHING
                  RETURNING id) ins
  LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes)
VALUES
  ((SELECT id FROM chosen), 1, 'Freios (pedal / estacionamento)', 'ok', 'alta',  false, true,  '["Eficiência baixa","Ruído anormal","Luz de freio inoperante","Outros"]'),
  ((SELECT id FROM chosen), 2, 'Pneus do cavalo',                 'ok', 'alta',  true,  true,  '["Pressão baixa","Sulco abaixo do mínimo","Fissura/bolha","Parafusos frouxos","Outros"]'),
  ((SELECT id FROM chosen), 3, 'Iluminação e setas',              'ok', 'media', false, true,  '["Farol queimado","Lanterna quebrada","Fora de foco","Outros"]'),
  ((SELECT id FROM chosen), 4, 'Direção / folga / ruído',         'ok', 'alta',  false, true,  '["Folga excessiva","Vazamento fluido","Barulho anormal","Outros"]'),
  ((SELECT id FROM chosen), 5, 'Vazamentos (motor/câmbio)',       'ok', 'alta',  true,  true,  '["Óleo motor","Óleo câmbio","Refrigeração/água","Combustível","Outros"]'),
  ((SELECT id FROM chosen), 6, 'Para-brisa e limpadores',         'ok', 'baixa', false, false, '["Trincado","Palheta gasta","Reservatório vazio","Outros"]'),
  ((SELECT id FROM chosen), 7, 'Retrovisores',                    'ok', 'baixa', false, false, '["Quebrado","Solto","Ajuste inoperante","Outros"]'),
  ((SELECT id FROM chosen), 8, 'Tacógrafo',                       'ok', 'media', false, false, '["Sem lacre","Sem registro","Falha de leitura","Outros"]'),
  ((SELECT id FROM chosen), 9, 'Extintor de incêndio',            'ok', 'media', false, false, '["Vencido","Pressão baixa","Lacre violado","Suporte solto","Outros"]'),
  ((SELECT id FROM chosen),10, 'Cinto de segurança',              'ok', 'alta',  false, true,  '["Sem trava","Rasgado","Fixação solta","Outros"]'),
  ((SELECT id FROM chosen),11, 'Documentação do veículo',         'ok', 'media', false, true,  '["CRLV vencido","Seguro vencido","Lacres irregulares","Outros"]'),
  ((SELECT id FROM chosen),12, 'Fluídos (óleo/água/Arla)',        'ok', 'baixa', false, false, '["Nível baixo óleo","Nível baixo água","Arla baixo","Outros"]'),
  ((SELECT id FROM chosen),13, 'Buzina / equipamentos auxiliares','ok', 'baixa', false, false, '["Inoperante","Intermitente","Outros"]')
ON CONFLICT (modelo_id, ordem) DO UPDATE SET
  descricao = EXCLUDED.descricao,
  severidade = EXCLUDED.severidade,
  exige_foto = EXCLUDED.exige_foto,
  bloqueia_viagem = EXCLUDED.bloqueia_viagem,
  opcoes = EXCLUDED.opcoes;

-- ==================
-- MODELO: VEÍCULO LEVE
-- ==================
WITH chosen AS (
  SELECT id FROM checklist_modelos WHERE nome = 'Leve - Pré-viagem'
  UNION ALL
  SELECT id FROM (INSERT INTO checklist_modelos (nome, tipo, versao, ativo)
                  VALUES ('Leve - Pré-viagem', 'pre', 1, true)
                  ON CONFLICT DO NOTHING
                  RETURNING id) ins
  LIMIT 1
)
INSERT INTO checklist_itens (modelo_id, ordem, descricao, tipo_resposta, severidade, exige_foto, bloqueia_viagem, opcoes)
VALUES
  ((SELECT id FROM chosen), 1, 'Iluminação geral',      'ok', 'media', false, true,  '["Farol queimado","Lanterna quebrada","Seta inoperante","Outros"]'),
  ((SELECT id FROM chosen), 2, 'Pneus',                 'ok', 'alta',  true,  true,  '["Pressão baixa","Sulco abaixo do mínimo","Deformação/bolha","Parafusos frouxos","Outros"]'),
  ((SELECT id FROM chosen), 3, 'Freio de serviço',      'ok', 'alta',  false, true,  '["Curso longo","Ruído","Baixa eficiência","Outros"]'),
  ((SELECT id FROM chosen), 4, 'Para-brisa/limpadores', 'ok', 'baixa', false, false, '["Trinca","Palheta gasta","Reservatório vazio","Outros"]'),
  ((SELECT id FROM chosen), 5, 'Níveis (óleo/água)',    'ok', 'baixa', false, false, '["Óleo baixo","Água baixa","Outros"]'),
  ((SELECT id FROM chosen), 6, 'Cinto de segurança',    'ok', 'alta',  false, true,  '["Sem trava","Rasgado","Fixação solta","Outros"]'),
  ((SELECT id FROM chosen), 7, 'Documentação',          'ok', 'media', false, true,  '["CRLV vencido","Seguro vencido","Outros"]')
ON CONFLICT (modelo_id, ordem) DO UPDATE SET
  descricao = EXCLUDED.descricao,
  severidade = EXCLUDED.severidade,
  exige_foto = EXCLUDED.exige_foto,
  bloqueia_viagem = EXCLUDED.bloqueia_viagem,
  opcoes = EXCLUDED.opcoes;
