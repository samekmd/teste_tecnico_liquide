import type { EnhancedProduct } from '../types/product';
import { splitSentences } from '../utils/format';
import styles from './AiSuggestion.module.css';

interface AiSuggestionProps {
  suggestion: EnhancedProduct | null;
  loading: boolean;
}

function renderDescription(description: string) {
  const items = splitSentences(description);
  if (items.length <= 1) {
    return <p className={styles.description}>{description}</p>;
  }
  return (
    <ul className={styles.descriptionList}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default function AiSuggestion({ suggestion, loading }: AiSuggestionProps) {
  return (
    <section className={styles.suggestion} aria-labelledby="ai-title" aria-live="polite" aria-busy={loading}>
      <div>
        <h2 id="ai-title">Sugestão da IA</h2>
        <p className={styles.note}>Gerada automaticamente; nada foi salvo.</p>
      </div>
      {suggestion ? (
        <div className={loading ? styles.stale : undefined}>
          <h3>{suggestion.title}</h3>
          {renderDescription(suggestion.description)}
        </div>
      ) : (
        loading && <p className={styles.note}>Gerando sugestão...</p>
      )}
    </section>
  );
}
