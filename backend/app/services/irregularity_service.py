"""Levantamento dos dados irregulares dos produtos (base da planilha de irregularidades)."""

import json
from typing import Any

from app.schemas.product import Irregularity, Offer, ProductDetail
from app.services.pricing import PRICE_TOLERANCE
from app.services.product_service import normalize_products
from app.services.products_client import fetch_products

_TOLERANCE_PCT = f"{PRICE_TOLERANCE:.0%}"

PRICE_PROBLEMS = {
    "non_positive": "Preço zero ou negativo (excluído da média)",
    "missing": "Preço ausente (excluído da média)",
    "invalid_format": "Preço em formato inválido (excluído da média)",
    "outlier": f"Preço mais de {_TOLERANCE_PCT} distante da mediana das ofertas (excluído da média)",
}
STOCK_PROBLEMS = {
    "invalid": "Estoque negativo ou inválido",
    "missing": "Estoque ausente ou não numérico",
}
UNIDENTIFIED_STORE_PROBLEM = "Loja não identificada (oferta mantida na média)"
DIVERGENT_PRICES_PROBLEM = (
    f"Duas ofertas com diferença acima de {_TOLERANCE_PCT}; ambas mantidas na média"
)
NO_OFFERS_PROBLEM = "Produto sem ofertas"


def _format_raw(data: dict[str, Any], key: str) -> str:
    # O valor é mostrado como veio da API: o JSON deixa claro se era texto ("..."), número
    # ou null; chave inexistente aparece como "(ausente)".
    if key not in data:
        return "(ausente)"
    return json.dumps(data[key], ensure_ascii=False)


def _offer_irregularities(
    product: ProductDetail, offer: Offer, raw_offer: dict[str, Any]
) -> list[Irregularity]:
    def row(field: str, key: str, problem: str) -> Irregularity:
        return Irregularity(
            product_id=product.id, ean=product.ean, title=product.title, store=offer.store,
            field=field, received_value=_format_raw(raw_offer, key), problem=problem,
        )

    # Uma oferta pode ter mais de um dado irregular; cada um vira uma linha.
    rows: list[Irregularity] = []
    if offer.price_status in PRICE_PROBLEMS:
        rows.append(row("preço", "price", PRICE_PROBLEMS[offer.price_status]))
    if offer.stock_status in STOCK_PROBLEMS:
        rows.append(row("estoque", "stock", STOCK_PROBLEMS[offer.stock_status]))
    if not offer.store_identified:
        rows.append(row("loja", "store", UNIDENTIFIED_STORE_PROBLEM))
    return rows


def _product_irregularities(product: ProductDetail, raw: dict[str, Any]) -> list[Irregularity]:
    def row(field: str, received_value: str, problem: str) -> Irregularity:
        return Irregularity(
            product_id=product.id, ean=product.ean, title=product.title, store="-",
            field=field, received_value=received_value, problem=problem,
        )

    if not product.offers:
        return [row("ofertas", _format_raw(raw, "offers"), NO_OFFERS_PROBLEM)]
    if product.price_warning:
        prices = " / ".join(
            f"{offer.price:.2f}" for offer in product.offers if offer.price_status == "valid"
        )
        return [row("preço", prices, DIVERGENT_PRICES_PROBLEM)]
    return []


def find_irregularities(raw_products: list[Any]) -> list[Irregularity]:
    """Lista os dados irregulares a partir da lista bruta da API.

    Os status vêm da normalização já existente (mesmas regras da listagem); a lista bruta é
    usada só para mostrar o valor original, que a normalização descarta quando é inválido.
    """
    # Mesmo critério de duplicados da normalização: vale o primeiro produto com cada id.
    raw_by_id: dict[int, dict[str, Any]] = {}
    for raw in raw_products:
        if isinstance(raw, dict) and isinstance(raw.get("id"), int):
            raw_by_id.setdefault(raw["id"], raw)

    rows: list[Irregularity] = []
    for product in normalize_products(raw_products):
        raw = raw_by_id[product.id]
        raw_offers = raw.get("offers") if isinstance(raw.get("offers"), list) else []
        # A normalização preserva ordem e quantidade das ofertas, então o zip é seguro.
        for offer, raw_offer in zip(product.offers, raw_offers):
            raw_offer = raw_offer if isinstance(raw_offer, dict) else {}
            rows.extend(_offer_irregularities(product, offer, raw_offer))
        rows.extend(_product_irregularities(product, raw))
    return rows


async def get_irregularities() -> list[Irregularity]:
    return find_irregularities(await fetch_products())
