"""Rotas /api/products (listagem, detalhe, exportação e sugestão com IA)."""

from fastapi import APIRouter, HTTPException, Query, Response

from app.agent import enhancer
from app.schemas.product import EnhancedProduct, ProductDetail, ProductPage
from app.services import export_service, irregularity_service, product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def list_products(
    search: str | None = Query(None, description="Busca em título, EAN e categoria"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=20),
) -> ProductPage:
    return await product_service.list_products(search, page, page_size)


def _xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content,
        media_type=export_service.XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# As rotas /export precisam ser declaradas antes de /{product_id}; caso contrário "export"
# seria interpretado como id e a requisição falharia com 422.
@router.get("/export")
async def export_products() -> Response:
    # Exporta todos os produtos, ignorando busca e paginação.
    products = await product_service.get_all_products()
    content = export_service.build_products_workbook(products)
    return _xlsx_response(content, export_service.EXPORT_FILENAME)


@router.get("/export/irregularities")
async def export_irregularities() -> Response:
    # Uma linha por dado irregular, com o valor como veio da API, EAN e título do produto.
    rows = await irregularity_service.get_irregularities()
    content = export_service.build_irregularities_workbook(rows)
    return _xlsx_response(content, export_service.IRREGULARITIES_FILENAME)


async def _get_product_or_404(product_id: int) -> ProductDetail:
    product = await product_service.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return product


@router.get("/{product_id}")
async def get_product(product_id: int) -> ProductDetail:
    return await _get_product_or_404(product_id)


@router.post("/{product_id}/enhance")
async def enhance_product(product_id: int) -> EnhancedProduct:
    # Apenas sugere título/descrição; o produto original não é alterado.
    product = await _get_product_or_404(product_id)
    return await enhancer.enhance_product(product)
