"""Cria o app FastAPI, configura CORS, inclui routers e handlers de erro."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.enhancer import EnhancerUnavailableError
from app.config import get_settings
from app.routes import products
from app.services.products_client import ExternalAPIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Liquide Products API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)


@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": "Não foi possível consultar a API de produtos no momento."},
    )


@app.exception_handler(EnhancerUnavailableError)
async def enhancer_unavailable_handler(
    request: Request, exc: EnhancerUnavailableError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Serviço de IA indisponível no momento."})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
