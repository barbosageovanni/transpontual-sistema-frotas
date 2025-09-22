# scripts/setup.py
"""
Script de setup inicial do Sistema Transpontual
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(message):
    """Imprimir passo do setup"""
    print(f"\n🔧 {message}")
    print("-" * 60)

def run_command(command, check=True):
    """Executar comando shell"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar: {command}")
        print(f"Erro: {e.stderr}")
        return False

def check_requirements():
    """Verificar requisitos do sistema"""
    print_step("Verificando requisitos do sistema")
    
    requirements = {
        "docker": "Docker é necessário para executar o sistema",
        "docker-compose": "Docker Compose é necessário para orquestração",
        "python3": "Python 3.11+ é necessário",
        "git": "Git é necessário para controle de versão"
    }
    
    missing = []
    for req, desc in requirements.items():
        if not shutil.which(req):
            missing.append(f"❌ {req}: {desc}")
        else:
            print(f"✅ {req}: Encontrado")
    
    if missing:
        print("\n❌ Requisitos ausentes:")
        for item in missing:
            print(f"  {item}")
        return False
    
    return True

def setup_environment():
    """Configurar arquivo de ambiente"""
    print_step("Configurando arquivo de ambiente")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ Arquivo .env.example não encontrado")
        return False
    
    if env_file.exists():
        response = input("📄 Arquivo .env já existe. Sobrescrever? (y/N): ")
        if response.lower() != 'y':
            print("✅ Mantendo .env existente")
            return True
    
    try:
        shutil.copy(env_example, env_file)
        print("✅ Arquivo .env criado com sucesso")
        print("⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar .env: {e}")
        return False

def build_containers():
    """Construir containers Docker"""
    print_step("Construindo containers Docker")
    
    return run_command("docker-compose build --no-cache")

def setup_database():
    """Configurar banco de dados"""
    print_step("Configurando banco de dados")
    
    # Iniciar apenas o banco
    if not run_command("docker-compose up -d db"):
        return False
    
    # Aguardar banco ficar pronto
    print("⏳ Aguardando banco de dados ficar pronto...")
    if not run_command("docker-compose exec db pg_isready -U postgres", check=False):
        print("⚠️  Aguardando mais tempo...")
        run_command("sleep 10")
    
    # Aplicar migrações
    print("📊 Aplicando schema do banco...")
    return run_command("python scripts/apply_sql.py")

def seed_initial_data():
    """Popular dados iniciais"""
    print_step("Populando dados iniciais")
    
    return run_command("python scripts/seed_database.py")

def start_services():
    """Iniciar todos os serviços"""
    print_step("Iniciando todos os serviços")
    
    return run_command("docker-compose up -d")

def verify_setup():
    """Verificar se setup foi bem-sucedido"""
    print_step("Verificando instalação")
    
    services = {
        "API": "http://localhost:8005/health",
        "Dashboard": "http://localhost:8050"
    }
    
    import time
    import requests
    
    print("⏳ Aguardando serviços ficarem prontos...")
    time.sleep(10)
    
    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service}: Online")
            else:
                print(f"⚠️  {service}: Resposta {response.status_code}")
        except requests.RequestException:
            print(f"❌ {service}: Offline ou inacessível")

def main():
    """Executar setup completo"""
    print("🚀 Setup do Sistema Transpontual")
    print("=" * 60)
    
    steps = [
        ("Verificar requisitos", check_requirements),
        ("Configurar ambiente", setup_environment),
        ("Construir containers", build_containers),
        ("Configurar banco", setup_database),
        ("Popular dados iniciais", seed_initial_data),
        ("Iniciar serviços", start_services),
        ("Verificar instalação", verify_setup)
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Falha no passo: {step_name}")
            print("🛑 Setup interrompido")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Setup concluído com sucesso!")
    print("\n📍 URLs dos serviços:")
    print("   • API: http://localhost:8005/docs")
    print("   • Dashboard: http://localhost:8050")
    print("\n🔑 Login padrão:")
    print("   • Email: admin@transpontual.com")
    print("   • Senha: admin123")
    print("\n⚠️  IMPORTANTE: Altere a senha padrão em produção!")

if __name__ == "__main__":
    main()







