# 🚀 Guia de Deploy - Sistema de Gestão de Frotas

## Transpontual - Deploy em Produção

---

## 📋 Pré-requisitos

Antes de iniciar o deploy, certifique-se de que você possui:

- **Docker** instalado (versão 20.10 ou superior)
- **Docker Compose** instalado (versão 2.0 ou superior)
- **Git** para clonar o repositório
- **Pelo menos 2GB de RAM** disponível
- **Pelo menos 10GB de espaço em disco**

## 🔧 Instalação Rápida

### 1. Clone o Repositório
```bash
git clone [URL_DO_REPOSITORIO]
cd sistema_gestão_frotas
```

### 2. Configure as Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e configure:
# - Senhas seguras para o banco de dados
# - Chave JWT secreta
# - Chave secreta do Flask
# - Outras configurações necessárias
```

### 3. Execute o Deploy

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```cmd
deploy.bat
```

## 🔐 Configuração de Segurança

### Variáveis Obrigatórias no .env

```env
# ALTERE ESTAS CONFIGURAÇÕES!
DATABASE_URL=postgresql://postgres:SUA_SENHA_SUPER_SEGURA@db:5432/frotadb
JWT_SECRET=SUA_CHAVE_JWT_COM_PELO_MENOS_32_CARACTERES_ALEATÓRIOS
FLASK_SECRET_KEY=SUA_CHAVE_SECRETA_DO_FLASK_TAMBÉM_LONGA
POSTGRES_PASSWORD=SUA_SENHA_SUPER_SEGURA
```

### 🔑 Geração de Senhas Seguras

**Para JWT_SECRET e FLASK_SECRET_KEY:**
```bash
# Linux/macOS
openssl rand -hex 32

# Python (qualquer sistema)
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🌐 Deploy Manual (Passo a Passo)

### 1. Preparar Ambiente
```bash
# Verificar Docker
docker --version
docker-compose --version

# Parar containers existentes
docker-compose down
```

### 2. Construir e Iniciar
```bash
# Construir imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f
```

### 3. Configurar Banco de Dados
```bash
# Executar migrações
docker-compose exec backend python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Criar usuário administrador
docker-compose exec backend python create_admin.py
```

## 📊 Verificação do Deploy

### Serviços Disponíveis
- **Dashboard**: http://localhost:8050
- **API**: http://localhost:8005
- **Documentação da API**: http://localhost:8005/docs

### Credenciais Iniciais
- **Email**: admin@transpontual.com
- **Senha**: admin123

**⚠️ IMPORTANTE**: Altere a senha do administrador imediatamente após o primeiro login!

### Verificar Status
```bash
# Status dos containers
docker-compose ps

# Logs dos serviços
docker-compose logs dashboard
docker-compose logs backend
docker-compose logs db
```

## 🔄 Comandos Úteis

### Gerenciamento de Containers
```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: remove dados!)
docker-compose down -v

# Reiniciar um serviço específico
docker-compose restart backend

# Rebuild sem cache
docker-compose build --no-cache

# Ver logs em tempo real
docker-compose logs -f backend
```

### Backup do Banco de Dados
```bash
# Criar backup
docker-compose exec db pg_dump -U postgres frotadb > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose exec -T db psql -U postgres frotadb < backup_arquivo.sql
```

### Atualizações
```bash
# Baixar atualizações
git pull origin main

# Rebuild e restart
docker-compose down
docker-compose build
docker-compose up -d
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Verificar logs
docker-compose logs [nome_do_serviço]

# Verificar configuração
docker-compose config
```

#### Erro de conexão com banco
```bash
# Verificar se o banco está rodando
docker-compose ps db

# Verificar logs do banco
docker-compose logs db

# Testar conexão manual
docker-compose exec db psql -U postgres -d frotadb -c "SELECT 1;"
```

#### Porta já em uso
```bash
# Verificar o que está usando a porta
netstat -tulpn | grep :8050

# Alterar porta no .env
DASHBOARD_PORT=8050
API_PORT=8005
```

#### Problemas de permissão
```bash
# Linux: corrigir permissões de arquivos
sudo chown -R $USER:$USER .
chmod +x deploy.sh
```

## 🔧 Configurações Avançadas

### Proxy Reverso (Nginx)

Para produção com domínio próprio, adicione no docker-compose.yml:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    - ./nginx/ssl:/etc/nginx/ssl
  depends_on:
    - dashboard
```

### SSL/HTTPS

1. Obtenha certificados SSL (Let's Encrypt)
2. Configure nginx com SSL
3. Redirecione HTTP para HTTPS

### Monitoramento

Adicione serviços de monitoramento:
- **Portainer** para gerenciar containers
- **Grafana + Prometheus** para métricas
- **Logs centralizados** com ELK Stack

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs: `docker-compose logs`
2. Consulte a documentação da API: http://localhost:8005/docs
3. Verifique as configurações no arquivo .env
4. Contate o suporte técnico

---

**✅ Deploy Concluído com Sucesso!**

O Sistema de Gestão de Frotas da Transpontual está agora em execução!