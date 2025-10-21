# Solução: Erro de Conexão com API Local

## Problema Identificado

**Erro:** "Erro de conexão com a API: Verifique se o backend está rodando na porta 8005"

## Causa

O dashboard Flask estava tentando se conectar ao backend FastAPI na porta 8005, mas o backend não estava iniciado ou ainda estava em processo de inicialização.

## Solução Aplicada

### 1. Iniciado Backend FastAPI
```bash
cd backend_fastapi
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### 2. Verificação de Status
- **Backend (FastAPI):** http://localhost:8005/health ✅
- **Dashboard (Flask):** http://localhost:8050/ ✅

### 3. Configuração Verificada
Arquivo: `flask_dashboard/app/.env`
```
API_BASE=http://127.0.0.1:8005
```

## Como Iniciar o Sistema Local Corretamente

### Método 1: Usando o Script Automático (RECOMENDADO)
```bash
iniciar_sistema_local_fix.bat
```

Este script:
1. Verifica se Python está instalado
2. Instala todas as dependências necessárias
3. Inicia o backend FastAPI em uma janela separada
4. Aguarda 5 segundos para o backend inicializar
5. Inicia o dashboard Flask em outra janela
6. Abre automaticamente os navegadores

### Método 2: Manualmente (para debug)

**Terminal 1 - Backend:**
```bash
cd backend_fastapi
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

**Terminal 2 - Dashboard (aguardar 5-10 segundos):**
```bash
cd flask_dashboard
python app/dashboard.py
```

## Verificação de Funcionamento

### 1. Teste o Backend
```bash
python -c "import requests; print(requests.get('http://localhost:8005/health').json())"
```

Resposta esperada:
```json
{
  "status": "healthy",
  "api": "online",
  "timestamp": "2025-10-21T...",
  "service": "transpontual-fleet-api"
}
```

### 2. Teste o Dashboard
```bash
python -c "import requests; print(requests.get('http://localhost:8050/').status_code)"
```

Resposta esperada: `200`

## Endpoints Disponíveis

### Backend (Porta 8005)
- **API Docs:** http://localhost:8005/docs
- **Health Check:** http://localhost:8005/health
- **Debug Database:** http://localhost:8005/debug/database
- **Root:** http://localhost:8005/

### Dashboard (Porta 8050)
- **Dashboard Principal:** http://localhost:8050/
- **Veículos:** http://localhost:8050/vehicles
- **Motoristas:** http://localhost:8050/drivers
- **Checklists:** http://localhost:8050/checklists
- **Novo Checklist:** http://localhost:8050/checklists/new

## Troubleshooting

### Se o erro persistir:

1. **Verificar se as portas estão em uso:**
   ```bash
   netstat -ano | findstr ":8005"
   netstat -ano | findstr ":8050"
   ```

2. **Matar processos Python presos:**
   ```bash
   taskkill /F /IM python.exe
   ```

3. **Limpar cache do Python:**
   ```bash
   cd backend_fastapi
   rmdir /s /q __pycache__
   cd app
   rmdir /s /q __pycache__
   ```

4. **Reinstalar dependências:**
   ```bash
   cd backend_fastapi
   pip install -r requirements.txt --force-reinstall
   ```

5. **Verificar arquivo .env:**
   - Confirmar que `flask_dashboard/app/.env` contém `API_BASE=http://127.0.0.1:8005`
   - Confirmar que `backend_fastapi/.env` contém as credenciais do banco de dados

## Aviso de Autocomplete (Segurança)

**Aviso do Chrome:** "Input elements should have autocomplete attributes"

### O que é:
Um aviso de boas práticas de segurança do Chrome para formulários de senha.

### Solução:
Adicionar atributo `autocomplete="current-password"` no campo de senha no template de login.

Isso será corrigido em uma próxima atualização dos templates.

## Status Atual

✅ Backend FastAPI rodando na porta 8005
✅ Dashboard Flask rodando na porta 8050
✅ Conexão entre Dashboard e API funcionando
✅ Banco de dados Supabase conectado
✅ Sistema pronto para uso

## Próximos Passos

1. Acesse http://localhost:8050 para usar o dashboard
2. Faça login com credenciais de teste (se necessário criar usuário via `/debug/create-test-user`)
3. Teste as funcionalidades de veículos, motoristas e checklists
