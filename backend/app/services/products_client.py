"""Cliente httpx da API externa de produtos com cache em memória (TTL)."""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10.0

# A API externa não tem paginação nem rota por id: busca-se a lista inteira e ela é
# mantida em memória por CACHE_TTL_SECONDS, evitando uma chamada externa a cada requisição.
_cache: list[dict[str, Any]] | None = None
_cached_at: float = 0.0
# Garante que apenas uma requisição atualize o cache por vez quando ele expira.
_lock = asyncio.Lock()


class ExternalAPIError(Exception):
    """A API externa falhou e não existe cache para servir."""


def _is_cache_fresh() -> bool:
    ttl = get_settings().cache_ttl_seconds
    return _cache is not None and time.monotonic() - _cached_at < ttl


async def _request_products() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(get_settings().products_api_url)
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Formato inesperado da API externa: {type(data).__name__}")
    return data


async def fetch_products() -> list[dict[str, Any]]:
    """Retorna a lista bruta de produtos, usando o cache enquanto ele estiver válido."""
    global _cache, _cached_at

    if _is_cache_fresh():
        return _cache  # type: ignore[return-value]

    async with _lock:
        # Outra requisição pode ter atualizado o cache enquanto esta aguardava o lock.
        if _is_cache_fresh():
            return _cache  # type: ignore[return-value]

        try:
            products = await _request_products()
        except (httpx.HTTPError, ValueError) as exc:
            # Se a API externa falhar, servir dados antigos é melhor que ficar sem resposta.
            if _cache is not None:
                logger.warning("Falha ao consultar a API externa; servindo cache antigo: %s", exc)
                return _cache
            logger.error("Falha ao consultar a API externa e não há cache: %s", exc)
            raise ExternalAPIError from exc

        _cache = products
        _cached_at = time.monotonic()
        logger.info("Cache de produtos atualizado com %d itens", len(products))
        return products
