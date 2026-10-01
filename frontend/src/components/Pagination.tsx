import styles from './Pagination.module.css';

interface PaginationProps {
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, totalPages, total, onPageChange }: PaginationProps) {
  const totalLabel = `${total} ${total === 1 ? 'produto' : 'produtos'}`;

  return (
    <nav className={styles.pagination} aria-label="Paginação">
      {totalPages > 1 && (
        <button type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Anterior
        </button>
      )}
      <span className={styles.info} aria-live="polite">
        {totalPages > 1 ? `Página ${page} de ${totalPages} · ${totalLabel}` : totalLabel}
      </span>
      {totalPages > 1 && (
        <button type="button" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
          Próxima
        </button>
      )}
    </nav>
  );
}
