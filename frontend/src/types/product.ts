export type PriceStatus = 'valid' | 'non_positive' | 'missing' | 'invalid_format' | 'outlier';
export type StockStatus = 'valid' | 'invalid' | 'missing';

export interface ProductSummary {
  id: number;
  ean: string;
  title: string;
  category: string;
  average_price: number | null;
  offers_count: number;
  price_warning: boolean;
}

export interface ProductPage {
  items: ProductSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Offer {
  store: string;
  store_identified: boolean;
  price: number | null;
  price_status: PriceStatus;
  stock: number | null;
  stock_status: StockStatus;
  included_in_average: boolean;
}

export interface ProductDetail extends Omit<ProductSummary, 'offers_count'> {
  description: string;
  offers: Offer[];
}

export interface EnhancedProduct {
  title: string;
  description: string;
}
