import { useCallback, useEffect, useState } from 'react';
import { getProducts } from '../services/api';
import type { ProductPage } from '../types/product';

interface RequestResult<T> {
  key: string | null;
  data: T | null;
  error: string | null;
}

interface UseProductsResult {
  data: ProductPage | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useProducts(search: string, page: number): UseProductsResult {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<RequestResult<ProductPage>>({ key: null, data: null, error: null });
  const requestKey = `${search}|${page}|${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    getProducts({ search, page, signal: controller.signal })
      .then((data) => setResult({ key: requestKey, data, error: null }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const error = err instanceof Error ? err.message : 'Erro inesperado.';
        setResult((prev) => ({ key: requestKey, data: prev.data, error }));
      });

    return () => controller.abort();
  }, [search, page, requestKey]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);

  // Carregando enquanto a resposta da requisição atual não chegou.
  const loading = result.key !== requestKey;

  return { data: result.data, loading, error: loading ? null : result.error, retry };
}
