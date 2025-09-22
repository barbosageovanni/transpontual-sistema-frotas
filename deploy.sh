#!/bin/bash
# ==============================
# Script de Deploy - Sistema de Gestão de Frotas
# Transpontual
# ==============================

set -e  # Parar em caso de erro

echo "========================================"
echo "Deploy do Sistema de Gestão de Frotas"
echo "Transpontual"
echo "========================================"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Erro: Docker Compose não está instalado"
    exit 1
fi

# Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    echo "Erro: Arquivo .env não encontrado"
    echo "Copie o arquivo .env.example para .env e configure as variáveis"
    exit 1
fi

# Verificar se as senhas padrão foram alteradas
if grep -q "MUDE_ESTA_SENHA" .env; then
    echo "Erro: Você deve alterar as senhas padrão no arquivo .env"
    exit 1
fi

echo "1. Parando containers existentes..."
docker-compose down

echo "2. Construindo imagens..."
docker-compose build

echo "3. Iniciando serviços..."
docker-compose up -d

echo "4. Aguardando banco de dados..."
sleep 10

echo "5. Executando migrações..."
docker-compose exec -T backend python -c "
from app.database import engine, Base
try:
    Base.metadata.create_all(bind=engine)
    print('Migrações executadas com sucesso')
except Exception as e:
    print(f'Erro nas migrações: {e}')
    exit(1)
"

echo "6. Criando usuário administrador..."
docker-compose exec -T backend python -c "
from app.database import SessionLocal
from app.models import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

# Verificar se já existe admin
existing_admin = db.query(Usuario).filter(Usuario.email == 'admin@transpontual.com').first()

if not existing_admin:
    admin_user = Usuario(
        nome='Administrador',
        email='admin@transpontual.com',
        senha=pwd_context.hash('admin123'),
        papel='admin',
        ativo=True
    )
    db.add(admin_user)
    db.commit()
    print('Usuário administrador criado: admin@transpontual.com / admin123')
else:
    print('Usuário administrador já existe')

db.close()
"

echo "========================================"
echo "Deploy concluído com sucesso!"
echo "========================================"
echo "Sistema disponível em:"
echo "Dashboard: http://localhost:8050"
echo "API: http://localhost:8005"
echo ""
echo "Credenciais iniciais:"
echo "Email: admin@transpontual.com"
echo "Senha: admin123"
echo ""
echo "IMPORTANTE: Altere a senha do administrador após o primeiro login!"
echo "========================================"

# Mostrar status dos containers
echo "Status dos containers:"
docker-compose ps