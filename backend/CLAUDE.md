# CLAUDE.md — Backend (FastAPI)

API intermediária entre o frontend e a API externa da Liquide. Consulta os produtos, normaliza os dados inconsistentes, calcula o preço médio, pagina/busca, exporta Excel e (por último) gera sugestões de título/descrição com IA.

Contexto: case técnico com tempo sugerido de ~3h. Priorizar **simples, funcional e explicável** sobre abstrações. Não criar camadas, padrões ou dependências que não sejam usados.

## Fonte de dados

- Endpoint único: `GET https://agente.liquide.com.br/case/api/products`
- Retorna um **array JSON plano** (sem paginação, sem filtro, sem rota por id). Hoje são ~50 produtos.
- **Proibido** salvar o JSON no repositório, criar fixtures com a base real ou copiar dados para dentro do projeto. A URL deve ser tratada como API externa e consultada em tempo de execução. (Testes usam dados sintéticos pequenos escritos à mão.)

Formato recebido:

```json
{
  "id": 1, "ean": "7890000000017", "title": "...", "category": "...", "description": "...",
  "offers": [{ "store": "Magazine Luiza", "price": 2411.01, "stock": 7 }]
}
```

Como não existe rota por produto, o backend busca a lista inteira, normaliza e mantém **cache em memória com TTL** (padrão 300s, configurável). Detalhe, busca, paginação e exportação leem desse cache.

- Cliente HTTP: `httpx.AsyncClient` com timeout (~10s).
- Se a API externa falhar e houver cache antigo, servir o cache antigo (log de warning). Sem cache nenhum → `502` com mensagem clara.
- Proteger o refresh com `asyncio.Lock` para não disparar várias requisições simultâneas.

## Regras de tratamento dos dados (núcleo do case)

Toda regra abaixo deve ter **comentário no código** explicando o problema e a decisão (exigência explícita do case). Os dados nunca são "corrigidos": a oferta continua visível nos detalhes, só recebe um status e pode ser excluída do cálculo da média.

### Preço — `utils/parsing.py::parse_price`
Retorna `(valor: float | None, status)`.

| Entrada | Exemplo real | Status | Entra na média? |
|---|---|---|---|
| número > 0 | `2411.01` | `valid` | sim (se não for outlier) |
| zero ou negativo | `0`, `-3499.9` | `non_positive` | não (regra do case) |
| `null` / ausente | `null` | `missing` | não |
| string não numérica | `"valor_indisponivel"` | `invalid_format` | não |
| string numérica | `"2411.01"`, `"2.411,01"`, `"R$ 2.411,01"` | tentar converter → `valid`/`non_positive`; falhou → `invalid_format` | conforme resultado |
| `bool`, NaN, infinito | — | `invalid_format` | não |

Atenção: `bool` é subclasse de `int` em Python — checar antes.

### Outliers de preço — `services/pricing.py`
Referência do case: ofertas válidas do mesmo produto não deveriam variar mais de 15% entre si.

Regra adotada (usar a **mediana** por ser robusta a um único valor discrepante):
1. Considerar só ofertas com status `valid`.
2. Se houver **3 ou mais**: calcular a mediana; oferta com `abs(preço - mediana) / mediana > 0.15` recebe status `outlier` e sai da média.
3. Se houver **exatamente 2** e elas diferirem mais de 15%: não há como saber qual está errada → **ambas entram na média**, mas o produto recebe `price_warning = true` (exibido na UI como "preços divergentes").
4. Se houver 1: entra na média normalmente.
5. Nenhuma oferta válida → `average_price = null` (UI mostra "Indisponível"; Excel deixa a célula vazia).

Arredondar a média para 2 casas apenas na saída. Constante `PRICE_TOLERANCE = 0.15` em um único lugar.

Casos reais que validam a regra: iPhone (4611 / 4658 / 5453 → 5453 é outlier), Apple Watch (2 ofertas com ~17% de diferença → warning), Nintendo Switch (preço 0 fora da média; as outras duas ~14% → ok).

### Estoque — `utils/parsing.py::parse_stock`
- inteiro ≥ 0 → `valid`. **Estoque 0 é válido**: oferta aparece normalmente e participa da média se o preço for válido (regra do case).
- negativo (`-3`) → `invalid`, valor exibido como `null`.
- `null` / ausente / não numérico → `missing`.
- Estoque inválido **não** afeta o preço médio (são informações independentes).

### Loja — `utils/parsing.py::parse_store`
- `""`, só espaços, `null` ou ausente → `"Loja não identificada"` com `store_identified = false`. A oferta continua válida para a média (o problema é de identificação, não de preço).

### Produto
- `offers` ausente ou não-lista → lista vazia.
- Campos de texto ausentes → string vazia; nunca quebrar a listagem por causa de um produto.
- Títulos repetidos com EAN diferente (ex.: dois "Caixa JBL") são produtos distintos — não deduplicar por título.
- Se aparecer `id` duplicado, manter o primeiro e logar warning.

## Estrutura

```
app/
├── main.py              # cria o app, CORS, inclui routers, handlers de erro
├── config.py            # Settings (pydantic-settings), lê .env
├── routes/
│   └── products.py      # todas as rotas /api/products
├── schemas/
│   └── product.py       # modelos Pydantic de resposta
├── services/
│   ├── products_client.py  # httpx + cache TTL da API externa
│   ├── pricing.py          # média + detecção de outliers
│   ├── product_service.py  # normalização, busca, paginação, detalhe
│   └── export_service.py   # geração do .xlsx
├── utils/
│   └── parsing.py       # parse_price, parse_stock, parse_store (funções puras)
└── agent/
    └── enhancer.py      # integração com LLM (última fase)
```

Regras de dependência: `routes` → `services` → `utils`. Rotas não contêm regra de negócio. `utils` e `pricing` são funções puras (fáceis de testar).

## Contrato da API

Prefixo `/api`. Respostas em JSON com chaves em inglês snake_case.

### `GET /api/products?search=&page=1&page_size=20`
- `search`: opcional, case-insensitive e **sem acento**, aplicado em título, EAN e categoria.
- `page_size`: padrão 20, **máximo 20** (validar com `Query(le=20)`), mínimo 1. `page` ≥ 1.
- Resposta:
```json
{
  "items": [{ "id": 1, "ean": "...", "title": "...", "category": "...",
              "average_price": 2411.01, "offers_count": 1, "price_warning": false }],
  "total": 50, "page": 1, "page_size": 20, "total_pages": 3
}
```

### `GET /api/products/{id}`
Produto completo + ofertas. `404` se não existir.
```json
{
  "id": 4, "ean": "...", "title": "...", "category": "...", "description": "...",
  "average_price": null, "price_warning": false,
  "offers": [{ "store": "Mercado Livre", "store_identified": true,
               "price": -3499.9, "price_status": "non_positive",
               "stock": 17, "stock_status": "valid",
               "included_in_average": false }]
}
```
Devolver o preço original quando for numérico (mesmo negativo) para a UI poder mostrar; `null` quando ausente/inválido.

### `GET /api/products/export`
- Declarar **antes** de `/{id}` no router (senão "export" vira id e dá 422).
- Exporta **todos** os produtos (ignora paginação e busca).
- Colunas exatamente, nesta ordem: `id`, `ean`, `titulo`, `preço médio`.
- EAN como **texto** (evita notação científica / perda de zeros). Preço médio numérico com formato `0.00`; vazio quando `null`.
- Usa a mesma função de média da listagem (uma única fonte de verdade).
- Gerar em memória (`BytesIO`) e devolver com `media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"` e `Content-Disposition: attachment; filename="produtos.xlsx"`.

### `POST /api/products/{id}/enhance` (última fase)
- Resposta: `{ "title": "...", "description": "..." }`.
- Sem `GROQ_API_KEY`, timeout ou erro do provedor → `503` com `{ "detail": "Serviço de IA indisponível no momento." }`. Nunca derrubar o app nem afetar outras rotas.

### `GET /health`
`{ "status": "ok" }`.

## Agente de IA (fazer por último)

- Provedor: **Groq** via `langchain-groq` (o case aceita Groq, Hugging Face ou Ollama).
- Um único chamado ao modelo com `with_structured_output(EnhancedProduct)`; não precisa de grafo/LangGraph.
- Entrada: título, categoria, descrição e EAN do produto (não enviar preços/lojas, irrelevantes para o texto).
- Prompt em português, pedindo título mais descritivo e descrição comercial clara, **sem inventar especificações** que não estejam nos dados. Temperatura baixa (~0.3).
- Timeout ~20s. Capturar exceções e converter em `503`. Log do erro real, mensagem genérica para o cliente.
- Nada é salvo nem altera o produto original.
- O app deve subir normalmente sem `GROQ_API_KEY`.

## Configuração

`.env` (nunca commitar; manter `.env.example` versionado):

```
PRODUCTS_API_URL=https://agente.liquide.com.br/case/api/products
CACHE_TTL_SECONDS=300
CORS_ORIGINS=http://localhost:5173
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
```

## Comandos

```bash
uv sync                                   # instala dependências
uv run uvicorn app.main:app --reload      # sobe em http://localhost:8000 (docs em /docs)
uv run pytest                             # testes
```

## Dependências

Necessárias: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `pydantic-settings`, `openpyxl`, `langchain-groq` (+ `langchain-core`). Dev: `pytest`, `pytest-asyncio`.
Não usar: banco de dados (sem `psycopg`), `langgraph`, `langfuse`, `openrouter` — não fazem parte deste case. Não adicionar dependências sem necessidade clara.

## Convenções

- Python 3.11+, type hints em tudo, `async` nas rotas e no cliente HTTP.
- Código e identificadores em inglês; comentários de decisões de dados e mensagens ao usuário em português.
- Funções pequenas; nada de classes onde uma função resolve.
- Logs com `logging` (sem `print`).

## Ordem de desenvolvimento

1. Config + cliente HTTP com cache → `GET /api/products` retornando os dados brutos.
2. `utils/parsing.py` + `services/pricing.py`.
3. Schemas, listagem paginada com busca, detalhe por id.
4. Exportação Excel.
5. Agente de IA.
6. README (como rodar, organização, decisões de dados, uso da IA e falhas, exportação, o que mudaria com muitos produtos).