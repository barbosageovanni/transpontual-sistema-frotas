# 🔧 Configuração do Supabase - Sistema de Manutenção

## 📋 Pré-requisitos

O sistema de manutenção está pronto para integração com a tabela `veiculos` do Supabase. Para ativar a integração real:

## 🛠️ Configuração das Variáveis de Ambiente

### 1. Criar arquivo `.env`
Crie um arquivo `.env` na pasta `flask_dashboard/app/`:

```bash
# Configurações do Supabase
SUPABASE_URL=https://seu-projeto-id.supabase.co
SUPABASE_ANON_KEY=sua-chave-anon-aqui

# Configurações da Aplicação
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=sua-secret-key-aqui
```

### 2. Obter Credenciais do Supabase

1. **URL do Projeto**:
   - Acesse seu projeto no Supabase
   - Vá em Settings > API
   - Copie a "Project URL"

2. **Anon Key**:
   - Na mesma página (Settings > API)
   - Copie a "anon public" key

### 3. Verificar Estrutura da Tabela

A tabela `veiculos` deve ter a seguinte estrutura:

```sql
create table public.veiculos (
  id serial not null,
  placa text not null,
  renavam text null,
  ano integer null,
  modelo text null,
  km_atual bigint null default 0,
  ativo boolean not null default true,
  criado_em timestamp without time zone not null default now(),
  marca character varying(100) null,
  tipo character varying(50) null,
  em_manutencao boolean not null default false,
  observacoes_manutencao text null,
  constraint veiculos_pkey primary key (id),
  constraint veiculos_placa_key unique (placa)
);
```

## 🔍 Testando a Integração

### 1. Endpoint de Teste
Acesse: `http://localhost:8050/test/supabase`

**Resposta esperada se configurado:**
```json
{
  "status": "success",
  "total_veiculos": 10,
  "veiculos": [...],
  "tipos_encontrados": ["CAVALOMECANICO", "TRUCK", "CARRETA"],
  "config": {
    "supabase_url": "https://seu-projeto.supabase.co",
    "tem_api_key": true
  }
}
```

**Resposta se usando fallback:**
```json
{
  "status": "success",
  "total_veiculos": 5,
  "usando_fallback": true
}
```

### 2. Verificar Logs
No console do servidor, procure por:
- ✅ `Carregados X veículos do Supabase` - Integração funcionando
- ⚠️ `Usando dados de fallback` - Usando dados de exemplo

## 🚀 Funcionalidades Ativas

### Com Supabase Configurado:
- ✅ Busca veículos reais da empresa
- ✅ Vinculação de planos a veículos específicos por placa
- ✅ Histórico de manutenção por veículo
- ✅ Relatórios baseados em dados reais

### Sem Supabase (Fallback):
- ✅ Funciona com dados de exemplo
- ✅ Todas as funcionalidades testáveis
- ✅ Interface completa funcional

## 📊 Tipos de Veículo Suportados

O sistema reconhece os seguintes tipos na coluna `tipo`:

- **EMPILHADEIRA**
- **TRUCK**
- **CARRETA**
- **CAVALOMECANICO** (Cavalo Mecânico)
- **TOCO**

## 🔧 Mapeamento de Campos

| Campo Supabase | Campo Sistema | Descrição |
|----------------|---------------|-----------|
| `id` | `id` | ID único do veículo |
| `placa` | `placa` | Placa do veículo (UPPER) |
| `modelo` | `modelo` | Modelo do veículo |
| `ano` | `ano` | Ano de fabricação |
| `km_atual` | `km_atual` | Quilometragem atual |
| `tipo` | `tipo` | Tipo do equipamento |
| `marca` | `marca` | Marca do veículo |
| `ativo` | `ativo` | Se veículo está ativo |
| `em_manutencao` | `em_manutencao` | Se está em manutenção |

## 🚨 Troubleshooting

### Erro "Supabase API error: 401"
- Verificar se a `SUPABASE_ANON_KEY` está correta
- Verificar se as Row Level Security (RLS) permitem leitura

### Erro "Connection timeout"
- Verificar se a `SUPABASE_URL` está correta
- Verificar conexão com internet

### Nenhum veículo carregado
- Verificar se existem veículos com `ativo = true`
- Verificar se a tabela `veiculos` existe

## 📱 URLs do Sistema

- **Planos de Manutenção**: `/maintenance/plans`
- **Novo Plano**: `/maintenance/plans/new`
- **Histórico do Veículo**: `/maintenance/vehicle/<id>/history`
- **Relatório do Veículo**: `/maintenance/vehicle/<id>/report`
- **Teste Supabase**: `/test/supabase`

---

## 💡 Próximos Passos

1. **Configurar credenciais** no arquivo `.env`
2. **Testar integração** via `/test/supabase`
3. **Criar planos** vinculados a veículos reais
4. **Gerar relatórios** por placa específica

O sistema está **100% pronto** para trabalhar com dados reais do Supabase!