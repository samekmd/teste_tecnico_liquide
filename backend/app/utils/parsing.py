"""Funções puras de parsing: parse_price, parse_stock e parse_store.

A API externa entrega preço, estoque e loja com tipos e valores inconsistentes. Estas funções
nunca "corrigem" o dado: devolvem o valor interpretado e um status que explica o que foi
encontrado, para a oferta continuar visível e o cálculo da média decidir se ela participa.
"""

import math
import re
from typing import Any, Literal

# "outlier" não é produzido por parse_price: é atribuído depois, pela análise de preços
# do produto (services/pricing.py). Fica no mesmo tipo para a resposta usar um só campo.
PriceStatus = Literal["valid", "non_positive", "missing", "invalid_format", "outlier"]
StockStatus = Literal["valid", "invalid", "missing"]

UNIDENTIFIED_STORE = "Loja não identificada"

_NUMERIC_PATTERN = re.compile(r"-?\d+(\.\d+)?")


def _classify_number(value: float) -> tuple[float | None, PriceStatus]:
    # NaN e infinito não representam preço algum.
    if not math.isfinite(value):
        return None, "invalid_format"
    # Regra do case: preço zero ou negativo não entra na média. O valor original é mantido
    # para a interface poder exibir o que a API enviou.
    if value <= 0:
        return float(value), "non_positive"
    return float(value), "valid"


def _normalize_numeric_string(text: str) -> str:
    """Converte "2.411,01", "2,411.01", "2411,01" e "1.234.567" para o formato do float()."""
    has_comma, has_dot = "," in text, "." in text
    if has_comma and has_dot:
        # Com os dois separadores, o que aparece por último é o decimal e o outro é de milhar.
        if text.rfind(",") > text.rfind("."):
            return text.replace(".", "").replace(",", ".")
        return text.replace(",", "")
    if has_comma:
        # Só vírgula: tratada como decimal (padrão brasileiro).
        return text.replace(",", ".")
    if text.count(".") > 1:
        # Vários pontos só fazem sentido como separador de milhar.
        return text.replace(".", "")
    return text


def parse_price(value: Any) -> tuple[float | None, PriceStatus]:
    """Interpreta o preço de uma oferta e devolve (valor, status)."""
    # Preço ausente (null ou campo inexistente, que chega aqui como None).
    if value is None:
        return None, "missing"

    # bool é subclasse de int em Python (True == 1): precisa ser rejeitado antes da checagem
    # numérica, senão True viraria um preço de 1.0.
    if isinstance(value, bool):
        return None, "invalid_format"

    if isinstance(value, (int, float)):
        return _classify_number(value)

    if isinstance(value, str):
        # Strings numéricas ("2411.01", "2.411,01", "R$ 2.411,01") são convertidas em vez de
        # descartadas; textos como "valor_indisponivel" ficam como formato inválido.
        text = value.replace("R$", "").replace(" ", "").strip()
        if not text:
            return None, "missing"
        normalized = _normalize_numeric_string(text)
        # A regex evita aceitar "nan", "inf" ou "1e5", que o float() converteria.
        if not _NUMERIC_PATTERN.fullmatch(normalized):
            return None, "invalid_format"
        return _classify_number(float(normalized))

    # Listas, objetos ou qualquer outro tipo inesperado.
    return None, "invalid_format"


def _classify_stock(value: int) -> tuple[int | None, StockStatus]:
    # Regra do case: estoque 0 é válido (a oferta aparece normalmente e entra na média).
    # Estoque negativo não existe; fica marcado como inválido e o valor não é exibido.
    if value < 0:
        return None, "invalid"
    return value, "valid"


def parse_stock(value: Any) -> tuple[int | None, StockStatus]:
    """Interpreta o estoque de uma oferta e devolve (valor, status).

    Estoque e preço são informações independentes: estoque inválido não tira a oferta da média.
    """
    # bool é subclasse de int; True/False não são quantidades.
    if value is None or isinstance(value, bool):
        return None, "missing"

    if isinstance(value, int):
        return _classify_stock(value)

    if isinstance(value, float):
        # 7.0 é uma quantidade inteira válida; 2.5, NaN ou infinito não são.
        if math.isfinite(value) and value.is_integer():
            return _classify_stock(int(value))
        return None, "invalid"

    if isinstance(value, str):
        try:
            return _classify_stock(int(value.strip()))
        except ValueError:
            return None, "missing"

    return None, "missing"


def parse_store(value: Any) -> tuple[str, bool]:
    """Interpreta o nome da loja e devolve (nome, loja_identificada).

    Loja vazia ou ausente é um problema de identificação, não de preço: a oferta continua
    válida para a média, apenas exibida como "Loja não identificada".
    """
    if isinstance(value, str) and value.strip():
        return value.strip(), True
    return UNIDENTIFIED_STORE, False
