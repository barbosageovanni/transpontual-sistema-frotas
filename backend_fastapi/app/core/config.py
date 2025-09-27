# backend_fastapi/app/core/config.py
"""
Aplicação: configurações centrais (BaseSettings)
"""
from functools import lru_cache
from typing import Optional, List
from pathlib import Path
import os

from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Database (sem default sensível; exigir via .env/ambiente)
    DATABASE_URL: str = ""

    # Security
    JWT_SECRET: str = "dev-jwt-secret-change-in-production"
    JWT_EXPIRES_MINUTES: int = 1440  # 24 horas

    # Storage
    STORAGE_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # External APIs (opcionais)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    WHATSAPP_API_URL: Optional[str] = None
    WHATSAPP_TOKEN: Optional[str] = None

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL é obrigatório. Informe via .env ou variável de ambiente.")
        return v

    @field_validator("STORAGE_DIR")
    @classmethod
    def create_storage_dir(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)
        return v

    model_config = {
        # Mantemos compatibilidade, mas o carregamento inicial via load_dotenv já cuida do caminho
        "env_file": None,
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Singleton para configurações.

    Carrega variáveis de ambiente de um arquivo .env mesmo quando o
    processo é iniciado dentro de subpastas (ex.: backend_fastapi/).
    """
    # 1) Para Render, tenta carregar .env.render primeiro
    here = Path(__file__).resolve()
    for parent in here.parents:
        render_env = parent / ".env.render"
        if render_env.is_file():
            print(f"Loading Render environment: {render_env}")
            load_dotenv(render_env, override=True)
            break

    # 2) Tenta carregar .env da raiz do repositório (onde há docker-compose.yml)
    repo_env_loaded = False
    for parent in here.parents:
        if (parent / "docker-compose.yml").is_file() and (parent / ".env").is_file():
            load_dotenv(parent / ".env", override=False)
            repo_env_loaded = True
            break

    # 3) Fallback: carrega o .env do diretório atual se existir
    if not repo_env_loaded:
        cwd_env = Path.cwd() / ".env"
        if cwd_env.is_file():
            load_dotenv(cwd_env, override=False)

    # 4) Force DATABASE_URL if not set (Render fallback)
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=30&tcp_keepalives_idle=10&tcp_keepalives_interval=5&tcp_keepalives_count=3"
        print("FALLBACK: DATABASE_URL set from hardcoded fallback")

    return Settings()
