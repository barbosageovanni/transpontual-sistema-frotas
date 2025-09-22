-- Migration: Adicionar campos de manutenção à tabela veiculos
-- Data: 2025-09-16

-- Adicionar colunas de manutenção
ALTER TABLE veiculos
ADD COLUMN em_manutencao BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN observacoes_manutencao TEXT;

-- Comentários nas colunas
COMMENT ON COLUMN veiculos.em_manutencao IS 'Indica se o veículo está em manutenção';
COMMENT ON COLUMN veiculos.observacoes_manutencao IS 'Descrição da manutenção em andamento';

-- Atualizar registros existentes (todos começam como operacionais)
UPDATE veiculos SET em_manutencao = FALSE WHERE em_manutencao IS NULL;