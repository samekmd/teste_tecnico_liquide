import type { EnhancedProduct, ProductDetail, ProductPage } from '../types/product';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const PAGE_SIZE = 20;

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
      return body.detail;
    }
  } catch {
    // corpo não é JSON; usa mensagem genérica
  }
  return `Erro ${response.status} ao acessar o servidor.`;
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new Error('Não foi possível conectar ao servidor.');
  }
  if (!response.ok) throw new Error(await errorMessage(response));
  return response;
}

interface GetProductsParams {
  search: string;
  page: number;
  signal?: AbortSignal;
}

export async function getProducts({ search, page, signal }: GetProductsParams): Promise<ProductPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
  if (search) params.set('search', search);
  const response = await request(`/api/products?${params}`, { signal });
  return (await response.json()) as ProductPage;
}

export async function getProduct(id: string, signal?: AbortSignal): Promise<ProductDetail> {
  const response = await request(`/api/products/${encodeURIComponent(id)}`, { signal });
  return (await response.json()) as ProductDetail;
}

export async function exportProducts(): Promise<Blob> {
  const response = await request('/api/products/export');
  return response.blob();
}

export async function exportIrregularities(): Promise<Blob> {
  const response = await request('/api/products/export/irregularities');
  return response.blob();
}

export async function enhanceProduct(id: string, signal?: AbortSignal): Promise<EnhancedProduct> {
  const response = await request(`/api/products/${encodeURIComponent(id)}/enhance`, { method: 'POST', signal });
  return (await response.json()) as EnhancedProduct;
}
