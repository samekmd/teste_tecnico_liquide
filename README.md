# Liquide — Case Técnico: consulta de produtos e ofertas

Aplicação para consultar produtos e ofertas de lojas a partir da API da Liquide.

- **Backend (FastAPI)**: API intermediária que consulta a API externa, trata os dados inconsistentes, calcula o preço médio, oferece busca/paginação, exporta Excel e gera sugestões de título/descrição com IA.
- **Frontend (React + Vite)**: listagem com busca e paginação, detalhes do produto com as ofertas, exportação e botão "Aprimorar com IA". Conversa **somente** com o backend.

---

## Como executar

### Pré-requisitos

- Python 3.11+ e [uv](https://docs.astral.sh/uv/)
- Node.js 20.19+ ou 22.12+ (exigência do Vite) e npm

### 1. Variáveis de ambiente

O backend lê o `.env` da **raiz do repositório**:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `PRODUCTS_API_URL` | `https://agente.liquide.com.br/case/api/products` | API externa de produtos |
| `CACHE_TTL_SECONDS` | `300` | Tempo de vida do cache em memória |
| `CORS_ORIGINS` | `http://localhost:5173` | Origens liberadas (separadas por vírgula) |
| `GROQ_API_KEY` | vazio | Chave da Groq. **Opcional**: sem ela o app funciona e só a IA fica indisponível |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Modelo usado na Groq |
| `VITE_API_URL` (em `frontend/.env`) | `http://localhost:8000` | URL do backend usada pelo frontend |

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

API em `http://localhost:8000` — documentação interativa em `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface em `http://localhost:5173`.

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verificação de saúde |
| GET | `/api/products?search=&page=1&page_size=20` | Listagem paginada (máx. 20 por página) com busca por título, EAN e categoria |
| GET | `/api/products/{id}` | Detalhe do produto com todas as ofertas e o status de cada dado |
| GET | `/api/products/export` | Excel com todos os produtos e o preço médio |
| GET | `/api/products/export/irregularities` | Excel com os dados irregulares encontrados |
| POST | `/api/products/{id}/enhance` | Sugestão de título e descrição gerada por IA |

---

## Organização da solução

```
backend/app/
├── main.py                     # app, CORS, rotas, tratamento de erros (502 / 503)
├── config.py                   # configurações lidas do .env (pydantic-settings)
├── routes/products.py          # rotas /api/products — só recebem e delegam
├── schemas/product.py          # modelos de resposta (Pydantic)
├── services/
│   ├── products_client.py      # httpx + cache em memória com TTL
│   ├── pricing.py              # preço médio e detecção de outliers (funções puras)
│   ├── product_service.py      # normalização, busca, paginação e detalhe
│   ├── irregularity_service.py # levantamento dos dados irregulares
│   └── export_service.py       # geração das planilhas .xlsx
├── utils/parsing.py            # parse_price / parse_stock / parse_store (funções puras)
└── agent/enhancer.py           # integração com o LLM (Groq)

frontend/src/
├── pages/                      # Listagem e Detalhes
├── components/                 # tabela/cards, busca, paginação, ofertas, IA, exportação
├── hooks/                      # estado de cada chamada (listagem, detalhe, IA, exportação)
├── services/api.ts             # único ponto que conhece as URLs do backend
└── types/                      # tipos espelhando o contrato da API
```

**Dependências em uma direção só:** `routes → services → utils`. As rotas não têm regra de negócio. As regras de dados ficam em funções puras e pequenas (`parsing.py`, `pricing.py`), fáceis de ler e de testar isoladamente.

**Fluxo de uma requisição:**

1. `products_client` devolve a lista bruta da API externa, usando o cache se ainda estiver válido.
2. `product_service` normaliza cada produto: classifica preço, estoque e loja de cada oferta e calcula a média com `pricing`.
3. A rota devolve a página, o detalhe, a planilha ou a sugestão da IA.

A API externa não tem paginação, filtro nem rota por id: ela devolve um array com todos os produtos. Por isso o backend busca a lista inteira e guarda em cache, e busca, paginação, detalhe e exportação são feitos sobre esse cache.

---

## Decisões sobre os dados recebidos

**Princípio: os dados não são corrigidos, são classificados.** Cada oferta continua visível nos detalhes com um status que explica o problema; o status só decide se ela participa do preço médio. Cada regra está comentada no código.

### Preço (`parse_price`)

| Recebido | Exemplo | Status | Entra na média? |
|---|---|---|---|
| Número maior que zero | `2411.01` | `valid` | Sim (se não for outlier) |
| Zero ou negativo | `0`, `-3499.9` | `non_positive` | Não (regra do case) |
| `null` / ausente | `null` | `missing` | Não |
| Texto não numérico | `"valor_indisponivel"` | `invalid_format` | Não |
| Texto numérico | `"2411.01"`, `"2.411,01"`, `"R$ 2.411,01"` | convertido e classificado como número | Conforme o valor |
| `true`/`false`, NaN, infinito | — | `invalid_format` | Não |

- `bool` é verificado antes de número, porque em Python `True` também é `int` (viraria preço 1,0).
- O valor original é devolvido para a interface sempre que for numérico, mesmo negativo, para o usuário ver o que veio da API.

### Outliers e preço médio (`pricing.py`)

O case indica que ofertas válidas do mesmo produto não deveriam variar mais de **15%** entre si (constante `PRICE_TOLERANCE`, definida em um único lugar).

- **3 ou mais preços válidos**: calcula-se a **mediana**. A oferta que se afasta mais de 15% dela recebe o status `outlier` e sai da média. A mediana foi escolhida porque um único valor discrepante não a desloca; a média seria puxada pelo próprio erro.
- **Exatamente 2 preços** com diferença acima de 15% (medida em relação ao menor): não há como saber qual está errado, então **os dois entram na média** e o produto recebe `price_warning`, exibido como "preços divergentes".
- **1 preço**: entra normalmente.
- **Nenhum preço válido**: `average_price = null` ("Indisponível" na interface; célula vazia no Excel).
- O arredondamento para 2 casas é feito apenas na saída.

Casos reais que validam a regra:

| Produto | Preços válidos | Resultado |
|---|---|---|
| iPhone | 4611.46 / 4658.06 / 5453.71 | 5453.71 é outlier (+17% da mediana); média 4634.76 |
| Apple Watch | 3441.82 / 2934.73 | diferença de 17% → ambos na média (3188.28) + aviso |
| Nintendo Switch | 0 / 2464.85 / 2161.71 | 0 fica fora; os outros dois diferem 14% → média 2313.28 |

### Estoque (`parse_stock`)

- Inteiro maior ou igual a zero → `valid`. **Estoque 0 é válido**: a oferta aparece normalmente e participa da média (regra do case).
- Negativo (`-3`) → `invalid`, exibido como "Não informado".
- `null`, ausente ou não numérico → `missing`.
- Estoque e preço são independentes: estoque inválido **não** tira a oferta da média.

### Loja (`parse_store`)

- Vazia, só espaços, `null` ou ausente → "Loja não identificada" (`store_identified = false`). A oferta **continua na média**: o problema é de identificação, não de preço.

### Produto

- `offers` ausente ou que não seja lista → produto sem ofertas.
- Campos de texto ausentes → string vazia. Um produto com problema nunca quebra a listagem.
- Títulos repetidos com EAN diferente (ex.: dois "Caixa JBL") são produtos distintos: não há deduplicação por título.
- Produto sem id válido é ignorado; id duplicado mantém o primeiro. Os dois casos geram um aviso no log.

### Consulta à API externa

- Cache em memória com TTL (300 s por padrão) e `asyncio.Lock`, para que várias requisições simultâneas não disparem várias chamadas externas.
- Timeout de 10 s. Se a API falhar e existir cache antigo, ele é servido (com aviso no log). Sem cache algum, a resposta é **502** com mensagem clara.

### Busca

Sem diferenciar maiúsculas de minúsculas e **sem acento** ("eletronicos" encontra "Eletrônicos"), aplicada em título, EAN e categoria.

---

## Uso da IA e o que acontece se ela falhar

Na tela de detalhes, o botão **"Aprimorar com IA"** chama `POST /api/products/{id}/enhance`, que devolve um título mais descritivo e uma descrição comercial.

- **Provedor**: Groq, via `langchain-groq`. É uma única chamada ao modelo com saída estruturada (`with_structured_output`), que já devolve `{ title, description }` validado pelo Pydantic.
- **Entrada**: apenas título, categoria, descrição e EAN. Preços e lojas não são enviados, porque não influenciam o texto.
- **Prompt** em português, pedindo para **não inventar especificações** que não estejam nos dados. A temperatura é baixa (0.3), para o modelo reescrever e não criar.
- **Nada é salvo**: a sugestão aparece em uma área separada ("Sugestão da IA") e o produto original não é alterado.

**Se a IA falhar** — chave não configurada, timeout (20 s), erro do provedor (chave inválida, modelo indisponível) ou resposta vazia:

- o backend registra o erro real no log e responde **503** com `{"detail": "Serviço de IA indisponível no momento."}`;
- o restante da aplicação não é afetado: o app sobe normalmente sem `GROQ_API_KEY` e as outras rotas continuam funcionando;
- no frontend, a área de sugestão mostra "Não foi possível gerar a sugestão agora." e o resto da página continua funcionando.

---

## Exportação dos dados

As planilhas são geradas **em memória** (`openpyxl` + `BytesIO`), sem gravar arquivo em disco, e baixadas pelos botões da listagem.

### `produtos.xlsx` — `GET /api/products/export`

- Todos os produtos, ignorando a busca e a paginação da tela.
- Colunas, nesta ordem: `id`, `ean`, `titulo`, `preço médio`.
- O preço médio vem da **mesma função** usada na listagem e no detalhe, para que exista uma única fonte de verdade.
- O EAN é gravado como **texto**, para o Excel não mostrar notação científica (`7,89E+12`) nem perder zeros à esquerda.
- O preço médio é numérico com formato `0.00`; a célula fica vazia quando não há média.

### `produtos_irregulares.xlsx` — `GET /api/products/export/irregularities`

Relatório para ajudar a corrigir os dados na origem. Cada linha é um dado irregular:

- Colunas: `id`, `ean`, `titulo`, `loja`, `campo`, `valor recebido`, `problema`.
- O valor aparece **exatamente como veio da API** (`-3499.9`, `null`, `"valor_indisponivel"`, `""`).
- Os status vêm da mesma normalização da listagem, sem regras duplicadas.
- Também entram os problemas do produto como um todo: preços divergentes e produto sem ofertas.

