import { useCallback, useState } from 'react';
import { exportIrregularities, exportProducts } from '../services/api';

export type ExportKind = 'products' | 'irregularities';

const EXPORTS: Record<
  ExportKind,
  { fetchFile: () => Promise<Blob>; filename: string; errorMessage: string }
> = {
  products: {
    fetchFile: exportProducts,
    filename: 'produtos.xlsx',
    errorMessage: 'Não foi possível exportar os produtos.',
  },
  irregularities: {
    fetchFile: exportIrregularities,
    filename: 'produtos_irregulares.xlsx',
    errorMessage: 'Não foi possível exportar as irregularidades.',
  },
};

interface UseExportResult {
  exporting: boolean;
  error: string | null;
  runExport: () => Promise<void>;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Revogar só depois que o navegador iniciou o download.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Baixa a planilha do tipo `kind` gerada pelo backend. */
export function useExport(kind: ExportKind): UseExportResult {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runExport = useCallback(async () => {
    const { fetchFile, filename, errorMessage } = EXPORTS[kind];
    setExporting(true);
    setError(null);
    try {
      downloadBlob(await fetchFile(), filename);
    } catch (err: unknown) {
      const detail = err instanceof Error ? ` ${err.message}` : '';
      setError(`${errorMessage}${detail}`);
    } finally {
      setExporting(false);
    }
  }, [kind]);

  return { exporting, error, runExport };
}
