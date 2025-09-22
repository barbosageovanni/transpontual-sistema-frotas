# 🚀 GUIA DE DEPLOY - SISTEMA GESTÃO DE FROTAS

## 📋 ARQUIVOS PREPARADOS ✅

### **Backend FastAPI**
- ✅ `backend_fastapi/Dockerfile` - Otimizado para Railway
- ✅ `backend_fastapi/railway.json` - Configuração de deploy
- ✅ `backend_fastapi/requirements.txt` - Dependências

### **Frontend Flask Dashboard**  
- ✅ `flask_dashboard/Dockerfile` - Otimizado com gunicorn
- ✅ `flask_dashboard/railway.json` - Configuração de deploy
- ✅ `flask_dashboard/requirements.txt` - Dependências + gunicorn

---

## 🎯 PLANO DE EXECUÇÃO

### **FASE 1: DEPLOY BACKEND API (HOJE)**

#### **1. Criar Projeto Railway (Backend)**
```bash
# 1. Acessar: https://railway.app
# 2. Criar novo projeto: "transpontual-api"
# 3. Conectar repositório GitHub
# 4. Selecionar pasta: backend_fastapi/
```

#### **2. Configurar Variáveis de Ambiente**
```bash
DATABASE_URL=postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require
SUPABASE_URL=https://lijtncazuwnbydeqtoyz.supabase.co  
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpanRuY2F6dXduYnlkZXF0b3l6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY1MTU3NDEsImV4cCI6MjA0MjA5MTc0MX0.VBiQx7_XzT_B5BHkANy5m-3vnJxrJ_4TsGcvJEobhNI
```

#### **3. Configurar Domínio Personalizado**
```bash
# Sugestão: api.transpontual.app.br
```

---

### **FASE 2: DEPLOY FRONTEND DASHBOARD (AMANHÃ)**

#### **1. Criar Projeto Railway (Frontend)**
```bash
# 1. Criar novo projeto: "transpontual-dashboard"
# 2. Conectar mesmo repositório GitHub
# 3. Selecionar pasta: flask_dashboard/
```

#### **2. Configurar Variáveis de Ambiente**
```bash
# API Backend
API_BASE=https://api.transpontual.app.br

# Supabase (mesmo do backend)
SUPABASE_URL=https://lijtncazuwnbydeqtoyz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpanRuY2F6dXduYnlkZXF0b3l6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY1MTU3NDEsImV4cCI6MjA0MjA5MTc0MX0.VBiQx7_XzT_B5BHkANy5m-3vnJxrJ_4TsGcvJEobhNI
DATABASE_URL=postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require

# Flask Config
FLASK_ENV=production
SECRET_KEY=transpontual-secret-key-2024
```

#### **3. Configurar Domínio Principal**
```bash
# Domínio: dashboard.transpontual.app.br
# (Substituir o sistema atual)
```

---

## ⚙️ CHECKLIST DE DEPLOY

### **Backend API**
- [ ] Projeto criado no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy realizado com sucesso
- [ ] Health check funcionando: `/health`
- [ ] Endpoints principais testados: `/api/v1/vehicles`
- [ ] Domínio personalizado configurado

### **Frontend Dashboard**  
- [ ] Projeto criado no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy realizado com sucesso
- [ ] Login funcionando
- [ ] Conexão com API testada
- [ ] Módulos principais funcionando
- [ ] Domínio principal configurado

---

## 🔧 COMANDOS ÚTEIS

### **Logs Railway**
```bash
# Backend
railway logs --service transpontual-api

# Frontend  
railway logs --service transpontual-dashboard
```

### **Redeploy**
```bash
railway redeploy --service nome-do-servico
```

### **Rollback**
```bash
railway rollback --service nome-do-servico
```

---

## 🚨 TROUBLESHOOTING

### **Erro de Conexão com Banco**
- Verificar DATABASE_URL
- Confirmar IP whitelisting no Supabase
- Testar conexão manual

### **Erro 502/503**
- Verificar health check
- Conferir PORT binding
- Verificar logs de startup

### **Erro de Build**
- Verificar Dockerfile
- Confirmar requirements.txt
- Verificar dependências do sistema

---

## 💰 CUSTOS ESTIMADOS

- **Backend API**: ~$5-10/mês
- **Frontend Dashboard**: ~$5-10/mês  
- **Total Railway**: ~$10-20/mês
- **Supabase**: $0 (Free tier)

---

## 🎯 PRÓXIMOS PASSOS

1. **HOJE**: Deploy do Backend API
2. **AMANHÃ**: Deploy do Frontend Dashboard
3. **TERÇA**: Testes de integração completos
4. **QUARTA**: Switch do domínio principal

**Sistema estará 100% funcional em produção!**
