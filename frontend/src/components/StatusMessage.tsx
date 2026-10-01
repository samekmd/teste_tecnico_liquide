import styles from './StatusMessage.module.css';

interface StatusMessageProps {
  variant: 'loading' | 'error' | 'empty';
  message: string;
  onRetry?: () => void;
}

export default function StatusMessage({ variant, message, onRetry }: StatusMessageProps) {
  return (
    <div
      className={`${styles.status} ${styles[variant]}`}
      role={variant === 'error' ? 'alert' : 'status'}
      aria-live="polite"
    >
      {variant === 'loading' && <span className={styles.spinner} aria-hidden="true" />}
      <p>{message}</p>
      {variant === 'error' && onRetry && (
        <button type="button" onClick={onRetry}>
          Tentar novamente
        </button>
      )}
    </div>
  );
}
