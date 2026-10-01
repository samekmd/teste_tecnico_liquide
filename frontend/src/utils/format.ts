import type { Offer, PriceStatus } from '../types/product';

const currencyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

export function formatCurrency(value: number | null): string {
  return value === null ? 'Indisponível' : currencyFormatter.format(value);
}

/** Motivo de cada status de preço, usado no badge "fora da média". */
export const PRICE_STATUS_LABEL: Record<PriceStatus, string> = {
  valid: '',
  non_positive: 'Preço zero ou negativo',
  missing: 'Preço não informado',
  invalid_format: 'Preço em formato inválido',
  outlier: 'Diverge mais de 15% das demais ofertas',
};

export function formatOfferPrice(offer: Offer): string {
  if (offer.price !== null) return currencyFormatter.format(offer.price);
  return offer.price_status === 'missing' ? 'Não informado' : 'Inválido';
}

export function formatStock(offer: Offer): string {
  return offer.stock_status === 'valid' && offer.stock !== null ? String(offer.stock) : 'Não informado';
}

/**
 * Divide a descrição em tópicos para exibição.
 * Separa em ", " (vírgula + espaço, preservando decimais como "15,6") e junta fragmentos
 * de uma só palavra ao tópico anterior: "resolução 4K, HDR" → "resolução 4K HDR".
 */
export function splitDescription(description: string): string[] {
  const items: string[] = [];
  for (const fragment of description.trim().split(', ')) {
    const text = fragment.trim();
    if (!text) continue;
    if (!/\s/.test(text) && items.length > 0) {
      items[items.length - 1] += ` ${text}`;
    } else {
      items.push(text);
    }
  }
  return items;
}

/**
 * Divide um texto em prosa (ex.: descrição sugerida pela IA) em tópicos, um por frase.
 * Só corta em ".", "!" ou "?" seguidos de espaço e de maiúscula/dígito/aspas, preservando
 * "12.000 BTUs". Como em splitDescription, só o último tópico mantém o ponto final.
 */
export function splitSentences(text: string): string[] {
  const sentences = text
    .trim()
    .split(/(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9"“])/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  return sentences.map((sentence, index) =>
    index < sentences.length - 1 ? sentence.replace(/\.$/, '') : sentence,
  );
}
