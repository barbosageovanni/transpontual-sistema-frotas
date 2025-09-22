# scripts/health_check.py
"""
Script de health check dos serviços
"""
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def check_service(name, url, timeout=5):
    """Verificar status de um serviço"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"⚠️  {name}: HTTP {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    """Verificar todos os serviços"""
    print("🔍 Health Check - Sistema Transpontual")
    print("-" * 40)
    
    services = [
        ("API Backend", "http://localhost:8005/health"),
        ("Dashboard", "http://localhost:8050"),
        ("API Docs", "http://localhost:8005/docs")
    ]
    
    all_healthy = True
    
    for name, url in services:
        if not check_service(name, url):
            all_healthy = False
    
    print("-" * 40)
    if all_healthy:
        print("🎉 Todos os serviços estão funcionando!")
        sys.exit(0)
    else:
        print("⚠️  Alguns serviços apresentam problemas")
        sys.exit(1)

if __name__ == "__main__":
    main()

