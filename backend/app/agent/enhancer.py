"""Integração com LLM (Groq) para sugerir título e descrição."""

import asyncio
import logging

from langchain_groq import ChatGroq

from app.config import get_settings
from app.schemas.product import EnhancedProduct, ProductDetail

logger = logging.getLogger(__name__)

ENHANCE_TIMEOUT_SECONDS = 20.0
# Temperatura baixa: o objetivo é reescrever com clareza, não criar conteúdo novo.
TEMPERATURE = 0.3

SYSTEM_PROMPT = """Você é um redator de e-commerce. Reescreva o título e a descrição de um produto \
em português do Brasil.

Regras:
- Título: mais descritivo que o original, com no máximo 80 caracteres.
- Descrição: comercial e clara, de 2 a 4 frases.
- Use somente as informações fornecidas. NÃO invente especificações (medidas, capacidade, \
cor, modelo, voltagem, materiais, compatibilidade etc.) que não estejam nos dados.
- O EAN serve apenas para identificar o produto; não o inclua no texto.
- Se a descrição original estiver vazia ou for pobre, escreva uma descrição genérica e fiel \
ao título e à categoria, sem acrescentar características."""


class EnhancerUnavailableError(Exception):
    """A IA não pôde gerar a sugestão (sem chave, timeout ou erro do provedor)."""


def _build_product_message(product: ProductDetail) -> str:
    # Só os dados textuais do produto: preços e lojas são irrelevantes para o texto.
    return (
        f"Título: {product.title or '(vazio)'}\n"
        f"Categoria: {product.category or '(vazia)'}\n"
        f"Descrição: {product.description or '(vazia)'}\n"
        f"EAN: {product.ean or '(vazio)'}"
    )


async def enhance_product(product: ProductDetail) -> EnhancedProduct:
    """Gera uma sugestão de título e descrição. Nada é salvo nem altera o produto original."""
    settings = get_settings()
    # Sem chave o app funciona normalmente; apenas esta funcionalidade fica indisponível.
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY não configurada; sugestão de IA indisponível")
        raise EnhancerUnavailableError

    try:
        # Cliente criado na chamada (e não no import) para o app subir sem a chave.
        llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=TEMPERATURE,
            timeout=ENHANCE_TIMEOUT_SECONDS,
            max_retries=1,
        ).with_structured_output(EnhancedProduct)
        messages = [("system", SYSTEM_PROMPT), ("human", _build_product_message(product))]
        # wait_for garante o teto total de tempo, incluindo a nova tentativa.
        result = await asyncio.wait_for(llm.ainvoke(messages), ENHANCE_TIMEOUT_SECONDS)
        if not isinstance(result, EnhancedProduct):
            raise ValueError(f"Resposta inesperada do modelo: {result!r}")
        if not result.title.strip() or not result.description.strip():
            raise ValueError("Modelo retornou título ou descrição vazios")
    except Exception as exc:
        # O erro real fica no log; o cliente recebe apenas uma mensagem genérica (503).
        logger.exception("Falha ao gerar sugestão de IA para o produto %s", product.id)
        raise EnhancerUnavailableError from exc

    return EnhancedProduct(title=result.title.strip(), description=result.description.strip())
