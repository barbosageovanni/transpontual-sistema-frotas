# Sistema de Gestão de Frotas — Base (Módulo 1: Checklist Veicular)

Este repositório contém o esqueleto de produção para:
- **FastAPI** (API principal, autenticação JWT, endpoints de checklist, veículos, upload de fotos);
- **Flask Dashboard** (KPI de checklist);
- **DDL PostgreSQL** (tabelas, índices, views);
- **PWA Mobile simples** (HTML/JS com service worker) para teste do checklist offline;
- **Jobs/ETL** de agregação (placeholder).

## Como rodar
1. Copie `.env.example` para `.env` e ajuste `DATABASE_URL` (local Postgres do compose ou a URL do Supabase).
2. `docker compose up -d --build`
3. API: http://localhost:8005/docs  
   Dashboard: http://localhost:8050  
   PWA de teste: abra `mobile_pwa/index.html` no navegador (ou sirva com qualquer http-server).

> Se usar Supabase, você pode **remover** o serviço `db` do compose ou apenas ignorá-lo e apontar `DATABASE_URL` para o Supabase.

## Migrações
Neste starter usamos **DDL SQL** direta em `sql/ddl.sql`. Em produção, recomendo criar migrações Alembic baseadas nesses modelos.

## Estrutura
```
backend_fastapi/
flask_dashboard/
mobile_pwa/
etl_jobs/
sql/
```

## Segurança
- Tokens JWT assinado com `JWT_SECRET` (alterar!)
- Upload de imagens salvo em `${STORAGE_DIR}` (padrão `/data/uploads` no container)

## Próximos passos
- Substituir PWA simples por app React/Capacitor.
- Adicionar CI/CD e testes mais abrangentes.


---

## Seeds rápidos (admin, veículos, motoristas, checklist)
1. Configure `DATABASE_URL` no `.env` (ou exporte no shell).
2. Rode:
   ```bash
   python -m pip install SQLAlchemy psycopg2-binary
   python scripts/apply_sql.py
   ```
3. Login DEV:
   - **email**: `admin@transpontual.com`
   - **senha**: `admin123`
> Em produção, troque para hash bcrypt real (o backend aceita senha em texto apenas para seed DEV).

## API do Checklist (JWT)
Endpoints principais sob `GET/POST /api/v1/...`. Autenticação Bearer JWT obtida em `/api/v1/auth/login`.

- Auth
  - `POST /api/v1/auth/login` { email, senha } → { access_token, token_type, user }
  - `GET /api/v1/users/me` → dados do usuário atual

- Modelos (requer papel gestor)
  - `GET /api/v1/checklist/modelos` → lista ativos
  - `POST /api/v1/checklist/modelos` { nome, tipo, ativo } → cria modelo
  - `PUT /api/v1/checklist/modelos/{id}` { nome?, tipo?, ativo? } → atualiza
  - `DELETE /api/v1/checklist/modelos/{id}` → soft-delete (ativo=false)

- Itens do Modelo (requer papel gestor para escrever)
  - `GET /api/v1/checklist/modelos/{modelo_id}/itens` → lista itens
  - `POST /api/v1/checklist/modelos/{modelo_id}/itens`
    - Body: { modelo_id, ordem>=1, descricao, tipo_resposta in [ok, nao_ok, na], severidade in [baixa, media, alta], exige_foto, bloqueia_viagem }
  - `PUT /api/v1/checklist/itens/{item_id}` → atualiza campos acima
  - `DELETE /api/v1/checklist/itens/{item_id}` → remove item

- Execução do Checklist (usuário autenticado)
  - `GET /api/v1/checklist` → lista com filtros e paginação
    - Query: `page` (>=1), `per_page` (1..100), `status`, `tipo`, `veiculo_id`, `motorista_id`, `modelo_id`, `placa`, `motorista_nome`, `odometro_ini_min`, `odometro_ini_max`, `data_inicio` (YYYY-MM-DD), `data_fim` (YYYY-MM-DD), `order_by` (campo, ex.: dt_inicio), `order_dir` (asc|desc)
    - Resposta item: `{ id, veiculo_id, veiculo_placa, veiculo_modelo, motorista_id, motorista_nome, modelo_id, tipo, status, dt_inicio, dt_fim, odometro_ini, odometro_fim }`
    - Envelope: `{ items: [...], page, per_page, total, pages }`
  - `POST /api/v1/checklist/start`
    - Body: { veiculo_id, motorista_id, modelo_id, tipo, odometro_ini? }
    - Regras: tipo deve bater com o do modelo; odometro_ini >= 0; status retorna `em_andamento`.
  - `POST /api/v1/checklist/answer`
    - Body: { checklist_id, respostas: [{ item_id, valor in [ok, nao_ok, na], observacao? }] }
    - Regras: item_id deve pertencer ao modelo do checklist.
  - `POST /api/v1/checklist/finish`
    - Body: { checklist_id, odometro_fim? }
    - Regras: se informado, odometro_fim >= odometro_ini; status vai para `aprovado`.
  - `GET /api/v1/checklist/{id}` → detalhes do checklist (itens + respostas)

- KPIs
  - `GET /api/v1/kpis/summary` → { total, aprovados, reprovados, taxa_aprovacao }
  - `GET /api/v1/checklist/stats/summary` → { total_checklists, taxa_aprovacao }

### Exemplo rápido (PowerShell)
1) Login
```
$token = (Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/v1/auth/login -Body (@{email='admin@transpontual.com'; senha='admin123'} | ConvertTo-Json) -ContentType 'application/json').access_token
$headers = @{ Authorization = "Bearer $token" }
```
2) Criar modelo (gestor)
```
Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/v1/checklist/modelos -Headers $headers -Body (@{nome='Pré-viagem Leve'; tipo='pre'; ativo=$true} | ConvertTo-Json) -ContentType 'application/json'
```
3) Listar itens do modelo
```
Invoke-RestMethod -Method Get -Uri http://localhost:8005/api/v1/checklist/modelos/1/itens -Headers $headers
```
4) Iniciar checklist (como motorista)
```
$tokenM = (Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/v1/auth/login -Body (@{email='motorista@test.com'; senha='motorista123'} | ConvertTo-Json) -ContentType 'application/json').access_token
$headersM = @{ Authorization = "Bearer $tokenM" }
Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/v1/checklist/start -Headers $headersM -Body (@{veiculo_id=1; motorista_id=1; modelo_id=1; tipo='pre'; odometro_ini=100000} | ConvertTo-Json) -ContentType 'application/json'
```
5) Listar checklists (página 1, 20 por página)
```
Invoke-RestMethod -Method Get -Uri "http://localhost:8005/api/v1/checklist?page=1&per_page=20" -Headers $headersM
```
6) Filtrar por placa e motorista
```
Invoke-RestMethod -Method Get -Uri "http://localhost:8005/api/v1/checklist?placa=RTA&motorista_nome=Joao" -Headers $headersM
```
7) Filtrar por modelo e odômetro inicial (faixa)
```
Invoke-RestMethod -Method Get -Uri "http://localhost:8005/api/v1/checklist?modelo_id=1&odometro_ini_min=50000&odometro_ini_max=200000" -Headers $headersM
```

## Acessando o Checklist
- Via Swagger: abra `http://localhost:8005/docs` e use os endpoints `/api/v1/checklist/...`.
- Para obter um checklist específico: `GET /api/v1/checklist/{id}` (use o `id` retornado pelo `start`).
- Para listar modelos e seus itens: `GET /api/v1/checklist/modelos` e `GET /api/v1/checklist/modelos/{id}/itens`.
