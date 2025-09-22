# Sistema de Manutenção Preventiva - Transpontual

## 📋 Visão Geral

Este sistema implementa um controle completo de manutenção preventiva integrado à tabela de veículos existente. Baseado nas imagens fornecidas, o sistema controla:

- **Planos de Manutenção** por tipo de equipamento
- **Alertas Automáticos** de manutenção vencida
- **Previsão de Manutenções** para planejamento
- **Histórico Completo** de todas as manutenções
- **Controle de Odômetro** automatizado
- **Dashboard de Multas** com gráficos

## 🗄️ Estrutura do Banco de Dados

### 1. **Tabelas Principais**

#### `tipos_equipamento`
Define os tipos de equipamento (CAVALO TRAÇÃO, TRUCK, CARRETA, etc.)
```sql
- id, nome, categoria, descricao, ativo
```

#### `planos_manutencao`
Planos de manutenção principais
```sql
- id, codigo, descricao, ativo, repeticao, quando
```

#### `planos_manutencao_itens`
Itens específicos de cada plano (Troca de óleo, revisão de freios, etc.)
```sql
- id, plano_id, descricao, tipo, controle_por (km/horas/dias)
- intervalo_valor, alerta_antecipacao, ordem
```

#### `veiculos_planos_manutencao`
**Liga veículos existentes aos planos de manutenção**
```sql
- id, veiculo_id, plano_id, tipo_equipamento_id
- data_inicio, km_inicio, ativo
```

### 2. **Tabelas de Controle**

#### `manutencoes_controle`
**Estado atual de cada manutenção para cada veículo**
```sql
- veiculo_id, plano_item_id
- km_ultima_manutencao, km_proxima_manutencao
- status (em_dia, vencendo, vencida)
```

#### `historico_odometro`
**Todas as leituras de odômetro**
```sql
- veiculo_id, km_atual, km_anterior, diferenca_km
- fonte (checklist, abastecimento, manual)
- data_leitura, referencia_id
```

#### `manutencoes_historico`
**Histórico de todas as manutenções realizadas**
```sql
- veiculo_id, descricao, data_realizacao, km_realizacao
- custo_total, responsavel_execucao, status
```

### 3. **Tabelas de Alertas**

#### `alertas_sistema`
**Alertas automáticos do sistema**
```sql
- tipo, entidade_tipo, entidade_id
- titulo, descricao, nivel, dados (JSON)
- ativo, visualizado
```

## 🔄 Como Funciona o Controle

### 1. **Configuração Inicial**
```sql
-- 1. Criar tipos de equipamento
INSERT INTO tipos_equipamento (nome) VALUES ('CAVALO TRAÇÃO 6X2 3 EIXOS');

-- 2. Criar plano de manutenção
INSERT INTO planos_manutencao (codigo, descricao)
VALUES ('PLAN-001', 'MANUTENÇÃO - CAVALO TRAÇÃO 6X2 3 EIXOS');

-- 3. Adicionar itens ao plano
INSERT INTO planos_manutencao_itens (plano_id, descricao, intervalo_valor, controle_por)
VALUES (1, 'TROCA DE ÓLEO DO MOTOR', 15000, 'km');

-- 4. Vincular veículo ao plano
INSERT INTO veiculos_planos_manutencao (veiculo_id, plano_id, km_inicio)
VALUES (1, 1, 125000);
```

### 2. **Controle Automático**

#### **Quando o odômetro é atualizado:**
```sql
-- Trigger automático recalcula todas as manutenções
UPDATE manutencoes_controle
SET status = CASE
    WHEN km_atual >= km_proxima_manutencao THEN 'vencida'
    WHEN km_atual >= (km_proxima_manutencao - 1000) THEN 'vencendo'
    ELSE 'em_dia'
END;
```

#### **Atualização de KM via função:**
```sql
-- Inserir nova leitura de odômetro
SELECT inserir_leitura_odometro(veiculo_id, novo_km, 'checklist', checklist_id);

-- Gerar alertas automáticos
SELECT gerar_alertas_manutencao();
```

### 3. **Controle por Diferentes Critérios**

O sistema suporta 3 tipos de controle:

#### **Por Quilometragem (km)**
```sql
controle_por = 'km'
intervalo_valor = 15000  -- A cada 15.000 km
```

#### **Por Horas de Uso**
```sql
controle_por = 'horas'
intervalo_valor = 500    -- A cada 500 horas
```

#### **Por Data/Tempo**
```sql
controle_por = 'dias'
intervalo_valor = 90     -- A cada 90 dias
```

## 📊 Views e Relatórios

### 1. **View de Alertas de Manutenção**
```sql
SELECT * FROM v_alertas_manutencao;
-- Retorna: placa, item_manutencao, km_restantes, status
```

### 2. **View de Previsão**
```sql
SELECT * FROM v_previsao_manutencoes;
-- Retorna: equipamentos em dia com previsão de próxima manutenção
```

## 🚨 Sistema de Alertas

### **Níveis de Alerta:**
- **🟢 Em Dia**: Manutenção dentro do prazo
- **🟡 Vencendo**: Faltam menos de 1000km ou dias de antecedência
- **🔴 Vencida**: Manutenção passou do prazo

### **Geração Automática:**
```sql
-- Executar diariamente para gerar novos alertas
SELECT gerar_alertas_manutencao();
```

## 📱 Interface do Dashboard

### **URLs Implementadas:**
- `/maintenance/plans` - Lista de planos de manutenção
- `/maintenance/forecast` - Previsão de alertas
- `/maintenance/alerts` - Alertas vencidos
- `/fines` - Dashboard de multas
- `/` (aba VEÍCULO) - Alertas integrados

### **Dados Reais vs Exemplo:**
O sistema busca dados reais da API, com fallback para dados de exemplo:

```python
def generate_maintenance_alerts():
    alertas_response = api_request('/maintenance/alerts-data')
    if not alertas_response:
        # Fallback para dados de exemplo baseados nos veículos reais
        return dados_exemplo_baseados_em_veiculos_reais()
```

## 🔧 Funções Utilitárias

### **1. Inserir Leitura de Odômetro**
```sql
SELECT inserir_leitura_odometro(
    veiculo_id := 1,
    km_atual := 130000,
    fonte := 'checklist',
    referencia_id := 123,
    observacoes := 'Leitura após checklist'
);
```

### **2. Simular Viagem (Para Testes)**
```sql
SELECT simular_viagem('XAV-0000', 500, 'Viagem SP-RJ');
-- Adiciona 500km ao veículo e recalcula alertas
```

### **3. Registrar Manutenção Realizada**
```sql
INSERT INTO manutencoes_historico (
    veiculo_id, descricao, data_realizacao,
    km_realizacao, custo_total
) VALUES (1, 'Troca de óleo completa', CURRENT_DATE, 130000, 350.00);
```

## 🔄 Fluxo Completo de Uma Manutenção

### **1. Planejamento**
```
Veículo XAV-0000 (125.000 km)
→ Plano: CAVALO TRAÇÃO 6X2 3 EIXOS
→ Próxima troca de óleo: 135.000 km
→ Status: em_dia (faltam 10.000 km)
```

### **2. Alerta Automático**
```
KM atual: 134.000 km
→ Sistema detecta: faltam 1.000 km
→ Status muda para: vencendo
→ Gera alerta automático
→ Aparece no dashboard
```

### **3. Manutenção Realizada**
```sql
-- Registrar manutenção
INSERT INTO manutencoes_historico (...);

-- Atualizar controle
UPDATE manutencoes_controle
SET km_ultima_manutencao = 135000,
    km_proxima_manutencao = 150000,
    status = 'em_dia';
```

## 📈 Relatórios Disponíveis

### **1. Dashboard Principal**
- Total de alertas por nível
- Equipamentos com manutenção vencida
- Previsão dos próximos 30 dias

### **2. Dashboard de Multas**
- Multas confirmadas e valores
- Ranking de condutores
- Gráficos por classificação e situação

### **3. Relatórios de Manutenção**
- Histórico por veículo
- Custos por período
- Performance de preventivas vs corretivas

## 🛠️ Instalação e Configuração

### **1. Executar Scripts SQL**
```bash
psql -d transpontual -f sql/maintenance_system.sql
psql -d transpontual -f sql/maintenance_seed.sql
```

### **2. Executar Dashboard**
```bash
cd flask_dashboard/app
python dashboard.py
```

### **3. Acessar Sistema**
```
http://localhost:8050/
http://localhost:8050/maintenance/plans
http://localhost:8050/fines
```

## 🔮 Próximos Passos

1. **Integração com API Real** - Conectar aos endpoints reais
2. **Notificações Push** - Alertas por email/SMS
3. **App Mobile** - Interface para motoristas
4. **Integração com ERP** - Sincronização de custos
5. **Relatórios Avançados** - BI e analytics
6. **Ordens de Serviço** - Fluxo completo de manutenção

---

## 📞 Suporte

Para dúvidas ou sugestões sobre o sistema de manutenção preventiva, consulte este documento ou as views SQL disponíveis no banco de dados.