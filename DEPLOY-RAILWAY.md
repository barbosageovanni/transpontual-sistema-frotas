# 🚄 Deploy no Railway - Sistema de Gestão de Frotas

## Transpontual - Deploy em Produção com Railway

---

## 🎆 Por que Railway?

- **Deploy rápido e fácil** com Git integration
- **PostgreSQL gerenciado** incluso
- **SSL/HTTPS automático**
- **Escala automática**
- **Logs centralizados**
- **Pricing justo** com tier gratuito

## 📋 Pré-requisitos

1. **Conta no Railway**: [railway.app](https://railway.app)
2. **Railway CLI**: `npm install -g @railway/cli`
3. **Git** configurado
4. **Repositório GitHub** com o código

## 🚀 Deploy Automático (Recomendado)

### 1. Login no Railway
```bash
railway login
```

### 2. Criar Projeto
```bash
# Na pasta do projeto
railway init
```

### 3. Deploy com Script
```bash
chmod +x deploy-railway.sh
./deploy-railway.sh
```

## 🔧 Deploy Manual (Passo a Passo)

### 1. Configurar Projeto Railway

1. Acesse [railway.app/dashboard](https://railway.app/dashboard)
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Conecte seu repositório

### 2. Adicionar Banco PostgreSQL

1. No projeto Railway, clique **"+ New"**
2. Selecione **"Database" > "PostgreSQL"**
3. O Railway criará automaticamente a `DATABASE_URL`

### 3. Configurar Backend (FastAPI)

1. Adicione um novo **Service**
2. Conecte ao repositório
3. Configure:
   - **Root Directory**: `backend_fastapi`
   - **Build Command**: `docker build -t backend .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### Variáveis de Ambiente - Backend:
```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=sua_chave_jwt_super_segura_32_caracteres
JWT_EXPIRES_MINUTES=1440
ENV=production
STORAGE_DIR=/app/uploads
```

### 4. Configurar Dashboard (Flask)

1. Adicione outro **Service**
2. Conecte ao mesmo repositório
3. Configure:
   - **Root Directory**: `flask_dashboard`
   - **Build Command**: `docker build -t dashboard .`
   - **Start Command**: `python run.py`

#### Variáveis de Ambiente - Dashboard:
```env
API_BASE=https://seu-backend-url.railway.app
FLASK_SECRET_KEY=sua_chave_flask_super_segura
FLASK_DEBUG=False
```

### 5. Executar Migrações

```bash
# Criar tabelas do banco
railway run --service backend python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Criar usuário administrador
railway run --service backend python create_admin.py
```

## 🔐 Configuração de Segurança

### Gerar Chaves Seguras

```bash
# JWT Secret (32+ caracteres)
openssl rand -hex 32

# Flask Secret Key
python -c "import secrets; print(secrets.token_hex(24))"
```

### Variáveis Obrigatórias

| Variável | Serviço | Descrição |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | URL do PostgreSQL (auto-gerada) |
| `JWT_SECRET` | Backend | Chave para tokens JWT |
| `FLASK_SECRET_KEY` | Dashboard | Chave para sessões Flask |
| `API_BASE` | Dashboard | URL do backend Railway |

## 🔄 Workflows de Deploy

### Deploy Automático via Git

O Railway automaticamente faz redeploy quando:
- Você faz push para a branch main
- Detecta mudanças no Dockerfile
- Variáveis de ambiente são alteradas

### Deploy Manual via CLI

```bash
# Deploy do backend
cd backend_fastapi
railway up --service backend

# Deploy do dashboard
cd flask_dashboard
railway up --service dashboard
```

## 📊 Monitoramento

### Logs em Tempo Real
```bash
# Logs do backend
railway logs --service backend

# Logs do dashboard
railway logs --service dashboard
```

### Métricas
- **CPU/RAM**: Disponíveis no dashboard Railway
- **Requests**: Metrics automáticas
- **Uptime**: Monitoring incluso

## 🔧 Comandos Úteis

### Gerenciamento de Serviços
```bash
# Listar serviços
railway status

# Conectar ao banco
railway connect postgres

# Executar comando no serviço
railway run --service backend python create_admin.py

# Abrir dashboard
railway open
```

### Backup do Banco
```bash
# Dump do banco
railway run --service postgres pg_dump $DATABASE_URL > backup.sql

# Restaurar backup
railway run --service postgres psql $DATABASE_URL < backup.sql
```

### Variáveis de Ambiente
```bash
# Listar variáveis
railway variables

# Adicionar variável
railway variables set JWT_SECRET=sua_chave_aqui

# Remover variável
railway variables delete OLD_VAR
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Build Failing
```bash
# Verificar logs de build
railway logs --deployment

# Verificar Dockerfile
cat backend_fastapi/Dockerfile
cat flask_dashboard/Dockerfile
```

#### Erro de Conexão com Banco
```bash
# Verificar DATABASE_URL
railway variables | grep DATABASE_URL

# Testar conexão
railway run --service backend python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### Dashboard não consegue acessar API
1. Verifique se `API_BASE` está configurado corretamente
2. URL deve ser: `https://seu-backend.railway.app`
3. Sem barra no final da URL

#### Erro de CORS
```python
# No backend, verificar configuração CORS em app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dashboard.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔒 Segurança em Produção

### Checklist de Segurança

- [ ] Senhas fortes configuradas
- [ ] JWT_SECRET com 32+ caracteres
- [ ] FLASK_DEBUG=False
- [ ] CORS configurado corretamente
- [ ] HTTPS ativado (automático no Railway)
- [ ] Logs monitorados
- [ ] Backup do banco configurado

### Domínio Customizado (Opcional)

1. Configure um domínio no Railway
2. Adicione CNAME no seu DNS
3. SSL será configurado automaticamente

## 💰 Custos Railway

### Tier Gratuito
- **$5 de crédito** por mês
- **512MB RAM** por serviço
- **1GB de storage** no PostgreSQL

### Tier Pago
- **$10/mês** por workspace
- **Recursos ilimitados**
- **Suporte prioritário**

## 🔗 URLs Úteis

- **Dashboard Railway**: https://railway.app/dashboard
- **Documentação**: https://docs.railway.app
- **CLI Reference**: https://docs.railway.app/develop/cli
- **Templates**: https://railway.app/templates

## 🎉 Deploy Concluído!

Após o deploy bem-sucedido:

1. **Dashboard**: `https://seu-dashboard.railway.app`
2. **API**: `https://seu-backend.railway.app`
3. **Docs da API**: `https://seu-backend.railway.app/docs`

### Credenciais Iniciais
- **Email**: admin@transpontual.com
- **Senha**: admin123

**⚠️ IMPORTANTE**: Altere a senha do administrador imediatamente!

---

**✅ Sistema de Gestão de Frotas da Transpontual no ar!**