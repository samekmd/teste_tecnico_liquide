"""Cálculo do preço médio e detecção de outliers de preço.

Funções puras: recebem apenas os preços com status "valid" de um produto (já filtrados por
parse_price). Quem chama usa os índices devolvidos para marcar as ofertas como "outlier".
"""

import statistics
from typing import NamedTuple

# Referência do case: ofertas válidas do mesmo produto não deveriam variar mais de 15% entre si.
PRICE_TOLERANCE = 0.15


class PriceSummary(NamedTuple):
    # Sem arredondamento: o arredondamento para 2 casas é feito só na saída (API/Excel).
    average_price: float | None
    # Índices (na lista de preços válidos recebida) das ofertas que saem da média.
    outlier_indexes: set[int]
    price_warning: bool


def find_outliers(valid_prices: list[float]) -> set[int]:
    """Índices dos preços que se afastam mais de 15% da mediana (só com 3 ou mais preços).

    A mediana é usada em vez da média por ser robusta a um único valor discrepante: a média
    seria "puxada" pelo próprio outlier e poderia esconder o problema.
    """
    if len(valid_prices) < 3:
        return set()
    median = statistics.median(valid_prices)
    return {
        index
        for index, price in enumerate(valid_prices)
        if abs(price - median) / median > PRICE_TOLERANCE
    }


def has_divergent_pair(valid_prices: list[float]) -> bool:
    """Indica se há exatamente 2 preços com diferença acima de 15%.

    Com só dois valores não há como saber qual está errado, então nenhum é descartado: o
    produto apenas recebe um aviso. A diferença é medida em relação ao menor preço; usando o
    maior como base, casos como 2934.73 x 3441.82 (17% acima do menor) passariam sem aviso.
    """
    if len(valid_prices) != 2:
        return False
    lowest, highest = min(valid_prices), max(valid_prices)
    return (highest - lowest) / lowest > PRICE_TOLERANCE


def summarize_prices(valid_prices: list[float]) -> PriceSummary:
    """Calcula o preço médio do produto, os outliers excluídos e o aviso de divergência."""
    # Sem nenhuma oferta válida não há média (a interface mostra "Indisponível").
    if not valid_prices:
        return PriceSummary(average_price=None, outlier_indexes=set(), price_warning=False)

    outliers = find_outliers(valid_prices)
    included = [price for index, price in enumerate(valid_prices) if index not in outliers]
    return PriceSummary(
        average_price=statistics.fmean(included),
        outlier_indexes=outliers,
        price_warning=has_divergent_pair(valid_prices),
    )
