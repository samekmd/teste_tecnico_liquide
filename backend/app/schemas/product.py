"""Modelos Pydantic de resposta da API de produtos."""

from pydantic import BaseModel, Field

from app.utils.parsing import PriceStatus, StockStatus


class Offer(BaseModel):
    store: str
    store_identified: bool
    # Preço original quando numérico (mesmo zero ou negativo); null quando ausente/inválido.
    price: float | None
    price_status: PriceStatus
    stock: int | None
    stock_status: StockStatus
    included_in_average: bool


class ProductSummary(BaseModel):
    id: int
    ean: str
    title: str
    category: str
    average_price: float | None
    offers_count: int
    price_warning: bool


class ProductDetail(BaseModel):
    id: int
    ean: str
    title: str
    category: str
    description: str
    average_price: float | None
    price_warning: bool
    offers: list[Offer]


class ProductPage(BaseModel):
    items: list[ProductSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class EnhancedProduct(BaseModel):
    # Usado como saída estruturada do modelo de IA e como resposta da rota de sugestão.
    title: str = Field(description="Título mais descritivo para o produto")
    description: str = Field(description="Descrição comercial clara do produto")


class Irregularity(BaseModel):
    """Um dado irregular encontrado em um produto (uma linha da planilha de irregularidades)."""

    product_id: int
    ean: str
    title: str
    # "-" quando a irregularidade é do produto e não de uma oferta específica.
    store: str
    field: str
    # Valor exatamente como veio da API externa, para facilitar a correção na origem.
    received_value: str
    problem: str
