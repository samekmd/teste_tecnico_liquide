import type { ProductSummary } from '../types/product';
import { formatCurrency } from '../utils/format';
import styles from './ProductTable.module.css';

interface ProductTableProps {
  products: ProductSummary[];
  onDetails: (id: number) => void;
}

const PRICE_WARNING_HINT =
  'As duas ofertas deste produto diferem mais de 15% entre si; não é possível saber qual preço está correto.';

function renderPrice(product: ProductSummary) {
  return (
    <>
      <span className={product.average_price === null ? styles.unavailable : undefined}>
        {formatCurrency(product.average_price)}
      </span>
      {product.price_warning && (
        <span className={styles.warning} title={PRICE_WARNING_HINT}>
          preços divergentes
        </span>
      )}
    </>
  );
}

// Duas marcações alternadas por CSS: cards abaixo de 640px, tabela a partir daí.
export default function ProductTable({ products, onDetails }: ProductTableProps) {
  return (
    <>
      <ul className={styles.cards}>
        {products.map((product) => (
          <li key={product.id}>
            <article className={styles.card}>
              <h2 className={styles.cardTitle}>{product.title}</h2>
              <dl className={styles.cardFacts}>
                <dt>EAN</dt>
                <dd className={styles.ean}>{product.ean}</dd>
                <dt>Categoria</dt>
                <dd>{product.category}</dd>
                <dt>Preço médio</dt>
                <dd>{renderPrice(product)}</dd>
              </dl>
              <button
                type="button"
                className={styles.cardButton}
                onClick={() => onDetails(product.id)}
                aria-label={`Ver detalhes de ${product.title}`}
              >
                Detalhes
              </button>
            </article>
          </li>
        ))}
      </ul>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <caption className="visually-hidden">Lista de produtos</caption>
          <thead>
            <tr>
              <th scope="col">EAN</th>
              <th scope="col">Título</th>
              <th scope="col">Categoria</th>
              <th scope="col" className={styles.price}>
                Preço médio
              </th>
              <th scope="col">
                <span className="visually-hidden">Ações</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td className={styles.ean}>{product.ean}</td>
                <td>{product.title}</td>
                <td>{product.category}</td>
                <td className={styles.price}>{renderPrice(product)}</td>
                <td className={styles.action}>
                  <button
                    type="button"
                    onClick={() => onDetails(product.id)}
                    aria-label={`Ver detalhes de ${product.title}`}
                  >
                    Detalhes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
