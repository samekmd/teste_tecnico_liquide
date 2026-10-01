import type { Offer } from '../types/product';
import { formatOfferPrice, formatStock, PRICE_STATUS_LABEL } from '../utils/format';
import styles from './OffersTable.module.css';

interface OffersTableProps {
  offers: Offer[];
}

export default function OffersTable({ offers }: OffersTableProps) {
  if (offers.length === 0) {
    return <p className={styles.empty}>Nenhuma oferta disponível.</p>;
  }

  return (
    <>
      <div className={styles.wrapper}>
        <table className={styles.table}>
          <caption className="visually-hidden">Ofertas do produto</caption>
          <thead>
            <tr>
              <th scope="col">Loja</th>
              <th scope="col" className={styles.number}>
                Preço
              </th>
              <th scope="col" className={styles.number}>
                Estoque
              </th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer, index) => (
              <tr key={`${offer.store}-${index}`}>
                <td className={offer.store_identified ? undefined : styles.muted}>{offer.store}</td>
                <td className={styles.number}>
                  <span className={offer.price === null ? styles.muted : undefined}>
                    {formatOfferPrice(offer)}
                  </span>
                  {!offer.included_in_average && (
                    <span className={styles.badge} title={PRICE_STATUS_LABEL[offer.price_status]}>
                      {offer.price_status === 'outlier' ? 'fora da média (diverge > 15%)' : 'fora da média'}
                    </span>
                  )}
                </td>
                <td className={offer.stock_status === 'valid' ? styles.number : `${styles.number} ${styles.muted}`}>
                  {formatStock(offer)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={styles.legend}>
        Ofertas marcadas como <strong>fora da média</strong> não entram no cálculo do preço médio: preço
        ausente, inválido, zero/negativo ou que diverge mais de 15% das demais ofertas.
      </p>
    </>
  );
}
