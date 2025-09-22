#!/bin/bash
# ==============================
# Script de Deploy para Railway
# Sistema de Gestão de Frotas - Transpontual
# ==============================

set -e

echo "========================================"
echo "Deploy Railway - Sistema de Gestão de Frotas"
echo "Transpontual"
echo "========================================"

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "Erro: Railway CLI não está instalado"
    echo "Instale com: npm install -g @railway/cli"
    echo "Ou visite: https://railway.app/cli"
    exit 1
fi

# Verificar se está logado no Railway
if ! railway whoami &> /dev/null; then
    echo "Você precisa fazer login no Railway"
    echo "Execute: railway login"
    exit 1
fi

echo "1. Verificando projeto Railway..."
# Verificar se tem um projeto Railway configurado
if [ ! -f ".railway/project.json" ]; then
    echo "Projeto Railway não encontrado."
    echo "Execute 'railway init' para criar um novo projeto"
    echo "Ou 'railway link' para conectar a um projeto existente"
    exit 1
fi

echo "2. Fazendo deploy do Backend (FastAPI)..."
cd backend_fastapi
railway up --service backend
cd ..

echo "3. Fazendo deploy do Dashboard (Flask)..."
cd flask_dashboard
railway up --service dashboard
cd ..

echo "4. Adicionando banco PostgreSQL..."
echo "IMPORTANTE: Adicione um banco PostgreSQL no painel do Railway"
echo "1. Acesse https://railway.app/dashboard"
echo "2. Selecione seu projeto"
echo "3. Clique em '+ New' e selecione 'Database' > 'PostgreSQL'"
echo "4. Configure as variáveis de ambiente (veja instruções abaixo)"

echo "========================================"
echo "Deploy Railway concluído!"
echo "========================================"
echo ""
echo "PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure as variáveis de ambiente no Railway:"
echo "   - DATABASE_URL (fornecida automaticamente pelo PostgreSQL)"
echo "   - JWT_SECRET (gere uma chave segura)"
echo "   - FLASK_SECRET_KEY (gere uma chave segura)"
echo "   - ENV=production"
echo ""
echo "2. Para gerar chaves seguras:"
echo "   openssl rand -hex 32"
echo ""
echo "3. Configure o API_BASE no dashboard:"
echo "   - Obtenha a URL do backend no Railway"
echo "   - Configure API_BASE=https://seu-backend.railway.app"
echo ""
echo "4. Execute migrações do banco:"
echo "   railway run --service backend python -c \"from app.database import engine, Base; Base.metadata.create_all(bind=engine)\""
echo ""
echo "5. Crie o usuário administrador:"
echo "   railway run --service backend python create_admin.py"
echo ""
echo "========================================"