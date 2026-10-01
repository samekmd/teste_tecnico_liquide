import { Navigate, Route, Routes } from 'react-router-dom';
import ProductListPage from './pages/ProductListPage';
import ProductDetailPage from './pages/ProductDetailPage';
import styles from './App.module.css';

export default function App() {
  return (
    <>
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <span className={styles.brand}>Produtos e Ofertas</span>
        </div>
      </header>
      <div className={styles.content}>
        <Routes>
          <Route path="/" element={<ProductListPage />} />
          <Route path="/produtos/:id" element={<ProductDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  );
}
