# Correções de Implantação no Render

## Problemas Identificados

### 1. Build Command Incompleto
**Problema:** O `buildCommand` no `render.yaml` estava instalando apenas `requirements.txt` da raiz, ignorando dependências específicas do backend e dashboard.

**Correção aplicada em `render.yaml:5-9`:**
```yaml
buildCommand: |
  pip install --upgrade pip && \
  pip install -r requirements.txt && \
  pip install -r backend_fastapi/requirements.txt || true && \
  pip install -r flask_dashboard/requirements.txt || true
```

### 2. Health Check Endpoint Ausente
**Problema:** O servidor unificado (server.py) não tinha endpoint `/health` para o health check do Render.

**Correção aplicada em `server.py:177-186`:**
```python
@app.route('/health')
def health_check():
    from flask import jsonify
    return jsonify({
        "status": "healthy",
        "service": "transpontual-unified-server",
        "dashboard": "online",
        "api": "online" if threading.active_count() > 1 else "starting",
        "timestamp": time.time()
    }), 200
```

### 3. Configuração de Portas
**Problema:** Porta interna da API (8005) e porta externa do Render (10000) não estavam bem documentadas.

**Correção aplicada em `render.yaml:40-41`:**
```yaml
- key: INTERNAL_API_PORT
  value: 8005
```

## Arquitetura de Implantação

```
Render (Porta 10000)
    ↓
server.py (Flask Dashboard + Proxy)
    ↓
FastAPI Backend (Porta 8005 - Interna)
    ↓
Supabase PostgreSQL
```

## Endpoints Disponíveis

- **Dashboard:** https://[seu-app].onrender.com/
- **API Docs:** https://[seu-app].onrender.com/docs
- **Health Check:** https://[seu-app].onrender.com/health
- **Debug DB:** https://[seu-app].onrender.com/debug/database

## Variáveis de Ambiente Configuradas

- `DATABASE_URL`: Conexão com Supabase PostgreSQL
- `JWT_SECRET`: Chave secreta para tokens JWT
- `PORT`: 10000 (porta padrão do Render)
- `INTERNAL_API_PORT`: 8005 (porta interna da API)
- `ENV`: production
- `DEBUG`: false
- `PYTHONIOENCODING`: utf-8

## Próximos Passos para Deploy

1. Commit das alterações:
   ```bash
   git add render.yaml server.py
   git commit -m "fix: corrigir configuração de deploy no Render"
   git push origin main
   ```

2. O Render detectará automaticamente as mudanças e iniciará um novo deploy

3. Verificar logs de deploy no dashboard do Render

4. Testar health check: `https://[seu-app].onrender.com/health`

5. Verificar conexão com banco: `https://[seu-app].onrender.com/debug/database`

## Troubleshooting

### Se o health check falhar:
- Verificar logs do Render
- Confirmar que a porta 10000 está sendo usada
- Verificar se o Flask está iniciando corretamente

### Se a API não responder:
- Verificar se o FastAPI está rodando na porta 8005
- Checar logs de thread do server.py
- Testar endpoint: `/debug/database`

### Se houver erro de banco de dados:
- Verificar DATABASE_URL no painel do Render
- Confirmar que o Supabase está acessível
- Usar endpoint `/debug/reconnect` para forçar reconexão
