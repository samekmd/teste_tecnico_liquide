"""Normalização dos produtos, busca, paginação e detalhe."""

import logging
import math
import unicodedata
from typing import Any

from app.schemas.product import Offer, ProductDetail, ProductPage, ProductSummary
from app.services.pricing import PriceSummary, summarize_prices
from app.services.products_client import fetch_products
from app.utils.parsing import parse_price, parse_stock, parse_store

logger = logging.getLogger(__name__)


def _text(value: Any) -> str:
    # Campos de texto ausentes viram string vazia e outros tipos (ex.: EAN numérico) viram
    # texto: um campo ruim não pode quebrar a listagem inteira.
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value)


def _normalize_offers(raw_offers: Any) -> tuple[list[Offer], PriceSummary]:
    # "offers" ausente ou que não é lista é tratado como produto sem ofertas.
    if not isinstance(raw_offers, list):
        raw_offers = []

    parsed: list[dict[str, Any]] = []
    for raw in raw_offers:
        # Item que não é objeto vira oferta com todos os campos ausentes: continua visível
        # nos detalhes, mas não entra na média.
        offer = raw if isinstance(raw, dict) else {}
        store, store_identified = parse_store(offer.get("store"))
        price, price_status = parse_price(offer.get("price"))
        stock, stock_status = parse_stock(offer.get("stock"))
        parsed.append({
            "store": store, "store_identified": store_identified,
            "price": price, "price_status": price_status,
            "stock": stock, "stock_status": stock_status,
        })

    # A média considera só preços válidos; os índices de outlier devolvidos por
    # summarize_prices são relativos a essa lista e são mapeados de volta às ofertas.
    valid_positions = [i for i, offer in enumerate(parsed) if offer["price_status"] == "valid"]
    summary = summarize_prices([parsed[i]["price"] for i in valid_positions])
    for index in summary.outlier_indexes:
        parsed[valid_positions[index]]["price_status"] = "outlier"

    offers = [
        Offer(**offer, included_in_average=offer["price_status"] == "valid") for offer in parsed
    ]
    return offers, summary


def normalize_product(raw: dict[str, Any]) -> ProductDetail | None:
    """Converte um produto bruto da API no modelo normalizado (ou None se não tiver id válido)."""
    product_id = raw.get("id")
    # Sem id inteiro não há como abrir o detalhe do produto; ele é ignorado com log.
    # bool é subclasse de int e precisa ser excluído.
    if not isinstance(product_id, int) or isinstance(product_id, bool):
        logger.warning("Produto ignorado por não ter id válido: %r", product_id)
        return None

    offers, summary = _normalize_offers(raw.get("offers"))
    average = summary.average_price
    return ProductDetail(
        id=product_id,
        ean=_text(raw.get("ean")),
        title=_text(raw.get("title")),
        category=_text(raw.get("category")),
        description=_text(raw.get("description")),
        # Arredondamento para 2 casas apenas na saída; o cálculo usa o valor completo.
        average_price=round(average, 2) if average is not None else None,
        price_warning=summary.price_warning,
        offers=offers,
    )


def normalize_products(raw_products: list[Any]) -> list[ProductDetail]:
    """Normaliza a lista da API mantendo a ordem original."""
    products: list[ProductDetail] = []
    seen_ids: set[int] = set()
    for raw in raw_products:
        if not isinstance(raw, dict):
            logger.warning("Item ignorado por não ser um objeto: %r", raw)
            continue
        product = normalize_product(raw)
        if product is None:
            continue
        # id duplicado: mantém o primeiro, pois o detalhe precisa de um id único.
        # Títulos repetidos não são deduplicados (ex.: dois "Caixa JBL" com EAN diferente
        # são produtos distintos).
        if product.id in seen_ids:
            logger.warning("Produto com id duplicado ignorado: %s", product.id)
            continue
        seen_ids.add(product.id)
        products.append(product)
    return products


def _fold(text: str) -> str:
    # Remove acentos e ignora maiúsculas/minúsculas: "eletronicos" encontra "Eletrônicos".
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _matches(product: ProductDetail, term: str) -> bool:
    return any(term in _fold(field) for field in (product.title, product.ean, product.category))


async def get_all_products() -> list[ProductDetail]:
    # A normalização roda a cada requisição sobre o cache bruto: com ~50 produtos o custo é
    # desprezível e evita manter um segundo cache.
    return normalize_products(await fetch_products())


async def list_products(search: str | None, page: int, page_size: int) -> ProductPage:
    products = await get_all_products()

    term = _fold(search.strip()) if search else ""
    if term:
        products = [product for product in products if _matches(product, term)]

    total = len(products)
    start = (page - 1) * page_size
    items = [
        ProductSummary(
            id=product.id,
            ean=product.ean,
            title=product.title,
            category=product.category,
            average_price=product.average_price,
            offers_count=len(product.offers),
            price_warning=product.price_warning,
        )
        for product in products[start:start + page_size]
    ]
    return ProductPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


async def get_product(product_id: int) -> ProductDetail | None:
    products = await get_all_products()
    return next((product for product in products if product.id == product_id), None)
