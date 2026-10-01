import { useCallback, useEffect, useRef, useState } from 'react';
import { enhanceProduct } from '../services/api';
import type { EnhancedProduct } from '../types/product';

interface UseEnhanceResult {
  data: EnhancedProduct | null;
  loading: boolean;
  error: string | null;
  /** Dispara (ou repete) a geração sob demanda. */
  retry: () => void;
}

export function useEnhance(id: string): UseEnhanceResult {
  const [data, setData] = useState<EnhancedProduct | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  // Outro produto → descarta a sugestão anterior.
  const [prevId, setPrevId] = useState(id);
  if (id !== prevId) {
    setPrevId(id);
    setData(null);
    setError(null);
    setLoading(false);
  }

  // Cancela a chamada em andamento ao trocar de produto ou sair da página.
  useEffect(() => () => controllerRef.current?.abort(), [id]);

  const retry = useCallback(() => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setLoading(true);
    setError(null);
    enhanceProduct(id, controller.signal)
      .then(setData)
      .catch(() => {
        if (!controller.signal.aborted) setError('Não foi possível gerar a sugestão agora.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [id]);

  return { data, loading, error, retry };
}
