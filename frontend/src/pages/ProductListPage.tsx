import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import ExportButton from '../components/ExportButton';
import Pagination from '../components/Pagination';
import ProductTable from '../components/ProductTable';
import SearchBar from '../components/SearchBar';
import StatusMessage from '../components/StatusMessage';
import { useDebounce } from '../hooks/useDebounce';
import { useProducts } from '../hooks/useProducts';
import styles from './ProductListPage.module.css';

function parsePage(value: string | null): number {
  const page = Number(value);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  const search = searchParams.get('search') ?? '';
  const page = parsePage(searchParams.get('page'));
  const { data, loading, error, retry } = useProducts(search, page);

  const [term, setTerm] = useState(search);
  const debouncedTerm = useDebounce(term.trim(), 300);

  // URL mudou por fora (voltar do navegador / dos detalhes) → sincroniza o input.
  const [prevSearch, setPrevSearch] = useState(search);
  if (search !== prevSearch) {
    setPrevSearch(search);
    if (search !== term.trim()) setTerm(search);
  }

  // Termo estabilizado e diferente da URL → grava na URL e volta para a página 1.
  // Só age quando o debounce alcançou o input, para não reescrever a URL com um termo antigo.
  useEffect(() => {
    if (debouncedTerm !== term.trim() || debouncedTerm === search) return;
    setSearchParams(
      (params) => {
        if (debouncedTerm) params.set('search', debouncedTerm);
        else params.delete('search');
        params.delete('page');
        return params;
      },
      { replace: true },
    );
  }, [debouncedTerm, term, search, setSearchParams]);

  const goToPage = (nextPage: number, replace = false) => {
    setSearchParams(
      (params) => {
        if (nextPage > 1) params.set('page', String(nextPage));
        else params.delete('page');
        return params;
      },
      { replace },
    );
  };

  // Página fora do intervalo (ex.: URL editada à mão) → volta para a última página.
  useEffect(() => {
    if (data && data.total_pages > 0 && page > data.total_pages) {
      goToPage(data.total_pages, true);
    }
  });

  const handlePageChange = (nextPage: number) => {
    goToPage(nextPage);
    window.scrollTo({ top: 0 });
  };

  const handleDetails = (id: number) => {
    navigate(`/produtos/${id}`, { state: { from: location.search } });
  };

  const renderContent = () => {
    if (error) {
      return <StatusMessage variant="error" message={error} onRetry={retry} />;
    }
    // Sem dados ainda, ou página além da última (o efeito acima redireciona).
    if (!data || (data.items.length === 0 && data.total > 0)) {
      return <StatusMessage variant="loading" message="Carregando produtos..." />;
    }
    if (data.items.length === 0) {
      return (
        <StatusMessage
          variant="empty"
          message={search ? `Nenhum produto encontrado para '${search}'.` : 'Nenhum produto disponível.'}
        />
      );
    }
    return (
      <>
        <div className={loading ? styles.reloading : undefined} aria-busy={loading}>
          <ProductTable products={data.items} onDetails={handleDetails} />
        </div>
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={handlePageChange}
        />
      </>
    );
  };

  return (
    <main className={styles.page}>
      <h1>Produtos</h1>
      <div className={styles.toolbar}>
        <SearchBar value={term} onChange={setTerm} />
        <div className={styles.actions}>
          <ExportButton
            kind="products"
            label="Exportar Excel"
            title="Exporta todos os produtos, não só os da página atual."
          />
          <ExportButton
            kind="irregularities"
            label="Exportar irregularidades"
            title="Exporta os dados que vieram em formato irregular da API: preços, estoques e lojas."
            variant="secondary"
          />
        </div>
      </div>
      {renderContent()}
    </main>
  );
}
