"""Configurações da aplicação, lidas do .env (ver .env.example na raiz do repositório)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# O .env fica na raiz do repositório (compartilhado com o frontend), dois níveis acima de app/.
# Resolver pelo caminho do arquivo garante a leitura independente do diretório de execução.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # extra="ignore": o .env da raiz pode ter variáveis que não pertencem ao backend.
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # Defaults iguais ao .env.example para o app subir mesmo sem .env.
    products_api_url: str = "https://agente.liquide.com.br/case/api/products"
    cache_ttl_seconds: int = 300
    # Mantido como str: com list[str] o pydantic-settings tentaria decodificar o valor como JSON.
    cors_origins: str = "http://localhost:5173"
    # Opcional: sem chave o app sobe normalmente e só a rota de IA responde 503.
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"

    @property
    def cors_origins_list(self) -> list[str]:
        """Aceita várias origens separadas por vírgula no .env."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
