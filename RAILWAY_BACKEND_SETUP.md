# 🚀 Configuração do Backend FastAPI no Railway

## 1. Criar Novo Serviço

No Railway Dashboard:

1. **Clique em "New Service"**
2. **Selecione "GitHub Repository"**
3. **Conecte o repositório**: `transpontual-sistema-frotas`
4. **Nome do serviço**: `transpontual-backend-api`

---

## 2. Configurações do Serviço

### 📁 **Root Directory**
```
backend_fastapi
```

### 🚀 **Start Command**
```bash
python server.py
```

### 📋 **Variables (Environment)**

```bash
DATABASE_URL=postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require

SUPABASE_URL=https://lijtncazuwnbydeqtoyz.supabase.co

SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpanRuY2F6dXduYnlkZXF0b3l6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY1MTU3NDEsImV4cCI6MjA0MjA5MTc0MX0.VBiQx7_XzT_B5BHkANy5m-3vnJxrJ_4TsGcvJEobhNI

PORT=8000
```

### 🔧 **Deploy Settings**
- **Auto Deploy**: `Enabled`
- **Build Command**: `Automatic`
- **Health Check Path**: `/health`
- **Health Check Timeout**: `300s`

---

## 3. Após Deploy - URLs Esperadas

Após o deploy bem-sucedido, você terá:

### ✅ **Backend FastAPI (NOVO)**
```
https://transpontual-backend-api-production-XXXX.up.railway.app
```

**Endpoints disponíveis:**
- `GET /health` → Status da API
- `POST /api/v1/auth/login` → Login de usuários
- `GET /docs` → Documentação Swagger
- `GET /api/v1/vehicles` → Listar veículos

### 🔧 **Frontend Flask (ATUAL)**
```
https://transpontual-sistema-frotas-production-6938.up.railway.app
```

---

## 4. Configurar Frontend

Após o backend estar funcionando, **atualize a variável API_BASE no frontend**:

**No serviço frontend (`production-6938`):**

```bash
API_BASE=https://transpontual-backend-api-production-XXXX.up.railway.app
```

*Substitua `XXXX` pela URL real gerada pelo Railway*

---

## 5. Testes de Verificação

### ✅ **1. Backend funcionando:**
```bash
curl https://transpontual-backend-api-production-XXXX.up.railway.app/health
```
**Resultado esperado:**
```json
{
  "status": "healthy",
  "api": "online",
  "timestamp": "2024-09-24T17:30:00",
  "service": "transpontual-fleet-api"
}
```

### ✅ **2. Login funcionando:**
```bash
curl -X POST https://transpontual-backend-api-production-XXXX.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@transpontual.com", "senha": "123456"}'
```

**Resultado esperado:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {...}
}
```

---

## 6. Credenciais de Teste

### 👤 **Usuário Admin**
- **Email**: `admin@transpontual.com`
- **Senha**: `123456`

---

## 7. Solução de Problemas

### ❌ **Se não funcionar:**

1. **Verificar logs do Railway**:
   - Deve mostrar: `✅ FastAPI app imported successfully`
   - Deve mostrar: `🚀 Starting server on 0.0.0.0:XXXX`

2. **Verificar Root Directory**:
   - Deve ser exatamente: `backend_fastapi`

3. **Verificar arquivo requirements.txt**:
   - O Railway deve instalar FastAPI, uvicorn, etc.

4. **Testar localmente**:
   ```bash
   cd backend_fastapi
   python server.py
   ```

---

## 8. Próximos Passos

Após o backend funcionando:

1. ✅ **Testar login no frontend**
2. ✅ **Configurar domínio personalizado**
3. ✅ **Implementar arquitetura híbrida**
4. ✅ **Deploy em transpontualexpress.com**

---

## 📞 Suporte

Se houver problemas:
1. Verificar logs do Railway
2. Testar endpoints com curl
3. Confirmar variáveis de ambiente
4. Verificar Root Directory

**🎯 Objetivo: Backend FastAPI funcionando independentemente!**