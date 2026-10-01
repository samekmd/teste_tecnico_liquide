# CLAUDE.md — Frontend (React + Vite)

Interface para consultar produtos e ofertas. Consome **apenas** o backend próprio (FastAPI) — nunca chamar a API externa da Liquide diretamente.

Contexto: case técnico com tempo sugerido de ~3h. Priorizar interface **simples, intuitiva e responsiva**. Não adicionar bibliotecas sem necessidade clara.

## Telas e comportamento

### Listagem (`/`)
- Barra de busca no topo; **ao lado dela, botão "Exportar Excel"**.
- Tabela com colunas: **EAN, Título, Categoria, Preço médio** e uma coluna de ação com botão **"Detalhes"** por linha.
- Máximo de **20 produtos por vez** (paginação no backend via `page`/`page_size=20`). Controles de paginação abaixo da tabela: anterior / próxima + "Página X de Y" + total de produtos.
- Busca com debounce (~300ms); ao mudar o termo, voltar para a página 1. Busca e página ficam na URL (`?search=tv&page=2`) para que "voltar" dos detalhes preserve o estado.
- Estados obrigatórios: carregando, erro (com botão "Tentar novamente"), lista vazia ("Nenhum produto encontrado para '...'").
- Preço médio `null` → "Indisponível". Produto com `price_warning` → pequeno indicador "preços divergentes" (com `title`/tooltip explicativo).

### Detalhes (`/produtos/:id`)
- Botão "Voltar" para a listagem (preservando busca/página).
- Informações do produto: título, EAN, categoria, descrição, preço médio.
- Tabela de ofertas: **Loja, Preço, Estoque** + indicação de status:
  - preço `non_positive`, `missing`, `invalid_format` → mostrar valor original (quando houver) ou "Inválido"/"Não informado", com badge "fora da média".
  - preço `outlier` → badge "fora da média (diverge > 15%)".
  - estoque 0 → "0" normal (é válido). Estoque inválido/ausente → "Não informado".
  - loja não identificada → texto em itálico/cinza.
- Uma legenda curta explicando por que algumas ofertas não entram na média.
- Botão **"Aprimorar com IA"** (fase final): ao clicar, chama `POST /api/products/{id}/enhance` e mostra o resultado em **área separada** das informações originais (lado a lado no desktop, empilhado no mobile), rotulada como "Sugestão da IA". Durante a chamada: botão desabilitado + "Gerando...". Em erro: mensagem inline ("Não foi possível gerar a sugestão agora.") sem afetar o resto da página. Nada é salvo.

### Exportação
- O botão faz download de `GET /api/products/export` — o arquivo contém **todos** os produtos, não só os visíveis. Implementar via `fetch` → `blob` → link temporário, para poder mostrar "Exportando..." e tratar erro. Nome do arquivo: `produtos.xlsx`.
- Ao lado, botão **"Exportar irregularidades"** (estilo secundário): baixa `GET /api/products/export/irregularities` como `produtos_irregulares.xlsx` — uma linha por dado irregular vindo da API (preço, estoque, loja). Mesmo fluxo e tratamento de erro; ambos usam `useExport(kind)`.

## Responsividade
- Mobile first. Abaixo de ~640px a tabela de produtos vira **lista de cards** (EAN, título, categoria, preço, botão Detalhes) — não usar scroll horizontal na listagem.
- Busca e botão de exportar: lado a lado no desktop, empilhados no mobile (botão em largura total).
- Alvos de toque ≥ 44px. Testar em 375px e 1280px.

## Estrutura

```
src/
├── main.tsx              # bootstrap + BrowserRouter
├── App.tsx               # rotas
├── vite-env.d.ts         # tipagem de import.meta.env (VITE_API_URL)
├── pages/
│   ├── ProductListPage.tsx
│   └── ProductDetailPage.tsx
├── components/
│   ├── SearchBar.tsx
│   ├── ExportButton.tsx
│   ├── ProductTable.tsx      # tabela no desktop / cards no mobile
│   ├── Pagination.tsx
│   ├── OffersTable.tsx
│   ├── AiSuggestion.tsx
│   └── StatusMessage.tsx     # loading / erro / vazio
├── hooks/
│   ├── useProducts.ts        # listagem paginada + busca
│   ├── useProduct.ts         # detalhe
│   ├── useEnhance.ts         # chamada de IA sob demanda
│   └── useDebounce.ts
├── services/
│   └── api.ts                # único lugar que conhece URLs e faz fetch
├── types/
│   └── product.ts            # tipos espelhando o contrato do backend
└── utils/
    └── format.ts             # formatCurrency (pt-BR, BRL), labels de status
```

Regras:
- Componentes não fazem `fetch`; usam hooks. Hooks usam `services/api.ts`.
- `api.ts` lê a base de `import.meta.env.VITE_API_URL` (padrão `http://localhost:8000`), lança erro com mensagem útil quando `!response.ok`.
- Funções de `api.ts` são tipadas pelo retorno (`Promise<ProductPage>`, `Promise<ProductDetail>` etc.); a resposta do `fetch` é convertida com `as` apenas nesse ponto, nunca espalhada pelo código.
- Hooks retornam `{ data, loading, error, retry }` (tipados, ex.: `data: ProductPage | null`, `error: string | null`) e cancelam requisições obsoletas com `AbortController` (evita resposta antiga sobrescrever a nova durante a busca).
- Formatação de moeda sempre por `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`. Nenhum cálculo de preço no frontend — a média vem pronta do backend.

## Stack e dependências
- React + Vite (já inicializado). Remover o boilerplate padrão (contador, logos, CSS de exemplo).
- `react-router-dom` para as duas rotas.
- Estilo: CSS Modules + variáveis CSS globais em `src/index.css` (cores, espaçamentos). Sem biblioteca de UI.
- **TypeScript** (`.tsx` para componentes/páginas, `.ts` para hooks, services, types e utils) com `strict: true` (padrão do template Vite).
- Não adicionar React Query, Redux, axios etc. — `fetch` + hooks resolvem o escopo.

## Contrato do backend → `src/types/product.ts`

Os tipos espelham exatamente as respostas do backend (snake_case, sem renomear campos):

```ts
export type PriceStatus = 'valid' | 'non_positive' | 'missing' | 'invalid_format' | 'outlier';
export type StockStatus = 'valid' | 'invalid' | 'missing';

export interface ProductSummary {
  id: number;
  ean: string;
  title: string;
  category: string;
  average_price: number | null;
  offers_count: number;
  price_warning: boolean;
}

export interface ProductPage {
  items: ProductSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Offer {
  store: string;
  store_identified: boolean;
  price: number | null;
  price_status: PriceStatus;
  stock: number | null;
  stock_status: StockStatus;
  included_in_average: boolean;
}

export interface ProductDetail extends Omit<ProductSummary, 'offers_count'> {
  description: string;
  offers: Offer[];
}

export interface EnhancedProduct {
  title: string;
  description: string;
}
```

Rotas:
```
GET  /api/products?search=&page=1&page_size=20  → ProductPage
GET  /api/products/{id}                         → ProductDetail (404 se não existir)
GET  /api/products/export                       → arquivo .xlsx
GET  /api/products/export/irregularities        → arquivo .xlsx (dados irregulares)
POST /api/products/{id}/enhance                 → EnhancedProduct | 503 se IA indisponível
```

Se o contrato do backend mudar, atualizar este arquivo de tipos primeiro.

## Configuração

`.env.local` (não commitar; versionar `.env.example`):
```
VITE_API_URL=http://localhost:8000
```

## Comandos

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # roda tsc -b + build; deve passar sem erros de tipo
npm run lint
```

## Convenções
- Proibido `any`; usar `unknown` + estreitamento quando o tipo for incerto (ex.: erros em `catch`).
- Props tipadas com `interface XxxProps` no próprio arquivo do componente.
- Labels de status via `Record<PriceStatus, string>` em `utils/format.ts`, para o compilador acusar status sem tratamento.
- Componentes funcionais, um por arquivo, nome em PascalCase. Hooks começam com `use`.
- Código em inglês; textos da interface em português.
- Acessibilidade básica: `<label>` na busca, `<table>` semântica com `<th scope="col">`, botões reais (`<button>`), foco visível, `aria-live="polite"` nas mensagens de status.
- Sem lógica de negócio duplicada do backend.

## Ordem de desenvolvimento
1. Limpar boilerplate, `types/product.ts`, router, `services/api.ts`, estilos base.
2. Listagem: tabela + paginação + estados.
3. Busca com debounce sincronizada com a URL.
4. Página de detalhes + tabela de ofertas com status.
5. Responsividade (cards no mobile).
6. Botão de exportação.
7. "Aprimorar com IA".