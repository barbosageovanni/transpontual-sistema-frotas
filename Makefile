# Makefile
# Makefile para Sistema Transpontual
.PHONY: help setup dev prod test clean backup logs

# Variáveis
COMPOSE_DEV = docker-compose
COMPOSE_PROD = docker-compose -f docker-compose.prod.yml

help: ## Mostrar este help
	@echo "Sistema Transpontual - Comandos Disponíveis:"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configurar ambiente inicial
	@echo "🚀 Configurando Sistema Transpontual..."
	python scripts/setup.py

dev: ## Iniciar ambiente de desenvolvimento
	@echo "🔧 Iniciando ambiente de desenvolvimento..."
	$(COMPOSE_DEV) up -d
	@echo "✅ Serviços iniciados!"
	@echo "📍 API: http://localhost:8005/docs"
	@echo "📍 Dashboard: http://localhost:8050"

prod: ## Iniciar ambiente de produção
	@echo "🚀 Iniciando ambiente de produção..."
	$(COMPOSE_PROD) up -d
	@echo "✅ Produção iniciada!"

stop: ## Parar todos os serviços
	@echo "⏹️  Parando serviços..."
	$(COMPOSE_DEV) down

restart: ## Reiniciar todos os serviços
	@echo "🔄 Reiniciando serviços..."
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) up -d

test: ## Executar testes
	@echo "🧪 Executando testes..."
	$(COMPOSE_DEV) run --rm backend pytest -v
	$(COMPOSE_DEV) run --rm dashboard python -m pytest

build: ## Reconstruir containers
	@echo "🔨 Reconstruindo containers..."
	$(COMPOSE_DEV) build --no-cache

clean: ## Limpar containers e volumes
	@echo "🧹 Limpando ambiente..."
	$(COMPOSE_DEV) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

logs: ## Visualizar logs
	$(COMPOSE_DEV) logs -f

logs-api: ## Logs apenas da API
	$(COMPOSE_DEV) logs -f backend

logs-dashboard: ## Logs apenas do Dashboard
	$(COMPOSE_DEV) logs -f dashboard

backup: ## Fazer backup do banco de dados
	@echo "💾 Criando backup..."
	python scripts/backup_db.py

health: ## Verificar status dos serviços
	@echo "🔍 Verificando saúde dos serviços..."
	python scripts/health_check.py

shell-api: ## Shell no container da API
	$(COMPOSE_DEV) exec backend bash

shell-db: ## Shell no container do banco
	$(COMPOSE_DEV) exec db psql -U postgres -d transpontual_db

migrate: ## Aplicar migrações do banco
	@echo "📊 Aplicando migrações..."
	python scripts/apply_sql.py

seed: ## Popular dados de exemplo
	@echo "🌱 Populando dados iniciais..."
	python scripts/seed_database.py

reset-db: ## Resetar banco de dados (CUIDADO!)
	@echo "⚠️  RESETANDO BANCO DE DADOS..."
	@read -p "Tem certeza? Digite 'RESET' para confirmar: " confirm && [ "$$confirm" = "RESET" ]
	$(COMPOSE_DEV) down -v
	$(COMPOSE_DEV) up -d db
	sleep 10
	python scripts/apply_sql.py

install: ## Instalar dependências Python localmente
	@echo "📦 Instalando dependências..."
	pip install -r backend_fastapi/requirements.txt
	pip install -r flask_dashboard/requirements.txt

format: ## Formatar código Python
	@echo "✨ Formatando código..."
	black backend_fastapi/ flask_dashboard/ scripts/
	isort backend_fastapi/ flask_dashboard/ scripts/

lint: ## Verificar qualidade do código
	@echo "🔍 Verificando código..."
	flake8 backend_fastapi/ flask_dashboard/ scripts/
	mypy backend_fastapi/

update: ## Atualizar dependências
	@echo "📦 Atualizando dependências..."
	$(COMPOSE_DEV) pull
	pip install --upgrade pip

docs: ## Gerar documentação
	@echo "📚 Gerando documentação..."
	@echo "API Docs: http://localhost:8005/docs"
	@echo "ReDoc: http://localhost:8005/redoc"

status: ## Mostrar status dos containers
	$(COMPOSE_DEV) ps

# Comandos de produção
deploy: ## Deploy completo em produção
	@echo "🚀 Deploy em produção..."
	git pull origin main
	$(COMPOSE_PROD) down
	$(COMPOSE_PROD) build
	$(COMPOSE_PROD) up -d
	@echo "✅ Deploy concluído!"

# Comandos de monitoramento
monitor: ## Mostrar uso de recursos
	@echo "📊 Monitorando recursos..."
	$(COMPOSE_DEV) stats

# Aliases úteis
up: dev ## Alias para 'dev'
down: stop ## Alias para 'stop'
ps: status ## Alias para 'status'