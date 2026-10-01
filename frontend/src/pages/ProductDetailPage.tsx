import { useLocation, useNavigate, useParams } from 'react-router-dom';
import AiSuggestion from '../components/AiSuggestion';
import OffersTable from '../components/OffersTable';
import StatusMessage from '../components/StatusMessage';
import { useEnhance } from '../hooks/useEnhance';
import { useProduct } from '../hooks/useProduct';
import { formatCurrency, splitDescription } from '../utils/format';
import styles from './ProductDetailPage.module.css';

/** Query string da listagem (busca/página) guardada ao abrir os detalhes. */
function getListSearch(state: unknown): string {
  if (state && typeof state === 'object' && 'from' in state && typeof state.from === 'string') {
    return state.from;
  }
  return '';
}

export default function ProductDetailPage() {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: product, loading, error, retry } = useProduct(id);
  const enhance = useEnhance(id);

  const renderContent = () => {
    if (error) {
      return <StatusMessage variant="error" message={error} onRetry={retry} />;
    }
    if (loading || !product) {
      return <StatusMessage variant="loading" message="Carregando produto..." />;
    }
    const descriptionItems = splitDescription(product.description);
    const showSuggestion = enhance.loading || enhance.data !== null;

    return (
      <>
        <div className={showSuggestion ? `${styles.overview} ${styles.withSuggestion}` : styles.overview}>
          <section className={styles.info}>
            <h1>{product.title}</h1>
            <dl className={styles.facts}>
              <div>
                <dt>EAN</dt>
                <dd className={styles.ean}>{product.ean}</dd>
              </div>
              <div>
                <dt>Categoria</dt>
                <dd>{product.category}</dd>
              </div>
              <div>
                <dt>Preço médio</dt>
                <dd className={product.average_price === null ? styles.muted : styles.price}>
                  {formatCurrency(product.average_price)}
                </dd>
              </div>
            </dl>
            {product.price_warning && (
              <p className={styles.warning} role="note">
                As duas ofertas deste produto diferem mais de 15% entre si; confira os preços.
              </p>
            )}
            {descriptionItems.length > 1 ? (
              <ul className={styles.descriptionList}>
                {descriptionItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className={styles.description}>{product.description}</p>
            )}
            <div className={styles.enhance}>
              <button
                type="button"
                className={styles.enhanceButton}
                onClick={enhance.retry}
                disabled={enhance.loading}
              >
                {enhance.loading ? 'Gerando...' : enhance.data ? 'Gerar novamente' : 'Aprimorar com IA'}
              </button>
              {enhance.error && (
                <p className={styles.enhanceError} role="alert">
                  {enhance.error}
                </p>
              )}
            </div>
          </section>
          {showSuggestion && <AiSuggestion suggestion={enhance.data} loading={enhance.loading} />}
        </div>

        <section className={styles.offers} aria-labelledby="offers-title">
          <h2 id="offers-title">Ofertas</h2>
          <OffersTable offers={product.offers} />
        </section>
      </>
    );
  };

  return (
    <main className={styles.page}>
      <button type="button" className={styles.back} onClick={() => navigate(`/${getListSearch(location.state)}`)}>
        ← Voltar
      </button>
      {renderContent()}
    </main>
  );
}
