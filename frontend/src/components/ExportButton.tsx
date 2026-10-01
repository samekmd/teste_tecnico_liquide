import { useExport, type ExportKind } from '../hooks/useExport';
import styles from './ExportButton.module.css';

interface ExportButtonProps {
  kind: ExportKind;
  label: string;
  title: string;
  variant?: 'primary' | 'secondary';
}

export default function ExportButton({ kind, label, title, variant = 'primary' }: ExportButtonProps) {
  const { exporting, error, runExport } = useExport(kind);

  return (
    <div className={styles.export}>
      <button
        type="button"
        className={`${styles.button} ${styles[variant]}`}
        onClick={() => void runExport()}
        disabled={exporting}
        aria-busy={exporting}
        title={title}
      >
        {exporting ? 'Exportando...' : label}
      </button>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
