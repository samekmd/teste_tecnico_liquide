import { useCallback, useEffect, useState } from 'react';
import { getProduct } from '../services/api';
import type { ProductDetail } from '../types/product';

interface RequestResult<T> {
  key: string | null;
  data: T | null;
  error: string | null;
}

interface UseProductResult {
  data: ProductDetail | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useProduct(id: string): UseProductResult {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<RequestResult<ProductDetail>>({ key: null, data: null, error: null });
  const requestKey = `${id}|${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    getProduct(id, controller.signal)
      .then((data) => setResult({ key: requestKey, data, error: null }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const error = err instanceof Error ? err.message : 'Erro inesperado.';
        setResult((prev) => ({ key: requestKey, data: prev.data, error }));
      });

    return () => controller.abort();
  }, [id, requestKey]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);

  // Carregando enquanto a resposta da requisição atual não chegou.
  const loading = result.key !== requestKey;

  return { data: result.data, loading, error: loading ? null : result.error, retry };
}
